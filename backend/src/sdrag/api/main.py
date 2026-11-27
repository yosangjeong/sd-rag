"""HTTP API (FastAPI). Run locally with: uvicorn sdrag.api.main:app

Endpoints (all but /health need a signed-in user; see auth.py):

- POST /api/chat                 ask; answers with citations; stored in the conversation
- POST /api/chat/stream          the same, streamed as NDJSON (stages, answer pieces, result)
- GET  /api/conversations        the user's conversations
- GET  /api/conversations/{id}   one conversation with its messages
- POST /api/documents            upload files (PDF, DOCX, HWPX; many at once)
- GET  /api/documents            the user's uploads and their processing status
- GET  /api/library              documents the user can search (to scope a question)
- GET  /api/logs/{preset}        fixed log queries, for the evaluators group only
- GET  /api/me                   the signed-in user (hash) and whether an evaluator
- GET  /api/source/{chunk_id}    the text of a cited chunk, to show where it is

Isolation: the user id comes only from the verified token; searches are limited to the
user's documents and the public corpus (service.py), records are keyed by user
(store.py), and /api/source refuses chunks of other users.

Every request gets a request id, logged with each step (common/logs.py); each search
and source view also writes an audit record.
"""

import hashlib
import json
import os
import queue
import re
import threading
import time
import uuid
from contextlib import asynccontextmanager
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace

from fastapi import Depends, FastAPI, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from sdrag.api import logs_api
from sdrag.api.auth import current_evaluator, current_user
from sdrag.api.store import DynamoStore, MemoryStore, new_id
from sdrag.common.config import settings
from sdrag.common.llm import BedrockChat
from sdrag.common.logs import log, user_hash
from sdrag.common.search_client import make_client
from sdrag.ingest.ocr import build_ocr
from sdrag.retrieval.embed import TitanEmbedder
from sdrag.retrieval.index import PUBLIC, create_index, list_documents
from sdrag.service import RagService
from sdrag.worker.job import ALLOWED, LocalQueue

MAX_FILES, MAX_FILE_MB = 100, 50
# files one user can upload per 24 hours: OCR is the cost (Qwen3-VL and the Textract
# check per scanned page), and 100 files of 300 scanned pages would be about $550
MAX_DAY_FILES = 30
MAX_NAME_BYTES = 200  # the file name is a path and an S3 key part (255 bytes on Linux)


@lru_cache(maxsize=1)
def deps() -> SimpleNamespace:
    """Clients built once per process (they are thread-safe and keep connections)."""
    client = make_client(settings.opensearch_url, settings.aws_region, 30)  # CloudFront allows 60
    embedder = TitanEmbedder(settings.embed_model, settings.aws_region, settings.embed_dims)
    # a request has 60 s at CloudFront: one model call gets 30 s and 3 attempts
    chat = BedrockChat(settings.llm_model, settings.aws_region, read_timeout=30, attempts=3)
    store = DynamoStore(settings.table, settings.aws_region) if settings.table else MemoryStore()
    d = SimpleNamespace(client=client, embedder=embedder, chat=chat, store=store,
                        index=settings.index, ocr=build_ocr(settings.ocr_model, settings.aws_region, settings.ocr_check),
                        service=RagService(client, settings.index, embedder, chat))  # fmt: skip
    if settings.upload_queue_url:
        from sdrag.worker.sqs import SqsQueue

        d.queue = SqsQueue(settings.upload_queue_url, settings.upload_bucket, settings.aws_region,
                           settings.worker_cluster, settings.worker_service)  # fmt: skip
    else:
        d.queue = LocalQueue(d)
    return d


@asynccontextmanager
async def lifespan(app: FastAPI):
    # a search outage must not keep the API (health checks, sign-in, logs) from starting:
    # the error is logged and searches fail until the index is reachable
    try:
        create_index(deps().client, settings.index, settings.embed_dims)  # no-op if it exists
    except Exception as e:  # noqa: BLE001
        log("error", path="startup", error=f"create_index: {type(e).__name__}: {e}")
    yield


app = FastAPI(title="SD RAG API", version="0.2.0", lifespan=lifespan)
if settings.env == "local":  # the Vite dev server; in AWS the page and /api/* share one origin
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"],
                       allow_headers=["Authorization", "Content-Type", "X-Dev-User", "X-Dev-Groups"])  # fmt: skip


@app.middleware("http")
async def request_log(request: Request, call_next):
    # always our own id: a client's, even well-formed, could join another request's
    # trail in the evaluators' log view (ids are shown in responses)
    rid = uuid.uuid4().hex[:12]
    request.state.rid = rid
    t = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception as e:
        log("error", request_id=rid, path=request.url.path, error=f"{type(e).__name__}: {e}")
        raise
    if request.url.path != "/health":  # the load balancer's checks, every 15 s per target
        log("request", request_id=rid, method=request.method, path=request.url.path,
            status=response.status_code, latency_ms=round(1000 * (time.perf_counter() - t)))  # fmt: skip
    response.headers["x-request-id"] = rid
    return response


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness check used by the load balancer and ECS to decide if the task is healthy."""
    return {"status": "ok", "env": settings.env}


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    conversation_id: str | None = Field(default=None, max_length=64)  # ids are ours (new_id)
    mode: str = Field(default="basic", pattern="^(basic|agent)$")
    documents: list[str] = Field(default_factory=list, max_length=50)  # search only these


def _history(d, user: str, body: ChatIn) -> list[dict]:
    if not body.conversation_id:
        return []
    conv = d.store.conversation(user, body.conversation_id)
    if not conv:
        raise HTTPException(404, "conversation not found")
    return [{"role": m["role"], "text": m["text"]} for m in conv["messages"]]


def _finish(d, user: str, body: ChatIn, rid: str, reply) -> dict:
    """Audit, store both turns, and the response body (both chat endpoints)."""
    citations = [vars(c) for c in reply.answer.citations]
    log("audit", action="search", request_id=rid, user=user_hash(user),
        documents=sorted({c["doc_id"] for c in citations}))  # fmt: skip
    now = time.time()
    conv = d.store.add_message(
        user, body.conversation_id, {"role": "user", "text": body.message, "ts": now}
    )
    msg = {"role": "assistant", "text": reply.answer.text, "citations": citations,
           "unchecked_figures": reply.answer.unchecked_figures, "mode": reply.mode,
           "steps": [{"tool": s.get("tool")} for s in reply.steps], "ts": time.time()}  # fmt: skip
    d.store.add_message(user, conv, msg)
    return {"conversation_id": conv, "answer": reply.answer.text, "citations": citations,
            "unchecked_figures": reply.answer.unchecked_figures,
            "mode": reply.mode, "latency_ms": round(reply.latency_ms), "steps": reply.steps,
            "searched": reply.question,
            "tokens": {"input": reply.input_tokens, "output": reply.output_tokens}}  # fmt: skip


@app.post("/api/chat")
def chat(body: ChatIn, request: Request, user: str = Depends(current_user)) -> dict:
    d, rid = deps(), request.state.rid
    history = _history(d, user, body)
    log("question", request_id=rid, user=user_hash(user), mode=body.mode, question=body.message,
        scope=body.documents)  # fmt: skip
    reply = d.service.ask(user, body.message, body.mode, rid, history, body.documents)
    return _finish(d, user, body, rid, reply)


@app.post("/api/chat/stream")
def chat_stream(body: ChatIn, request: Request, user: str = Depends(current_user)):
    """The same answer as /api/chat, sent as it is made: one JSON object per line
    (NDJSON) - {"type": "stage", "stage": "searching" | "ranking" | "writing"}, the
    answer's {"type": "delta", "text": ...} pieces as the model writes them (raw: source
    numbers not yet renumbered), {"type": "rewrite"} if the figure check sends the draft
    back, then {"type": "done", ...the /api/chat body} or {"type": "error", ...}. The
    page shows the deltas, then replaces them with the final text. A line goes out at
    least every 10 seconds, so CloudFront's 60 s wait between bytes is not reached by
    the searches either."""
    d, rid = deps(), request.state.rid
    history = _history(d, user, body)  # a 404 here is still a plain HTTP error
    log("question", request_id=rid, user=user_hash(user), mode=body.mode, question=body.message,
        scope=body.documents, stream=True)  # fmt: skip
    events: queue.Queue = queue.Queue()
    done = object()

    def run() -> None:
        try:
            reply = d.service.ask(user, body.message, body.mode, rid, history, body.documents,
                                  on_event=events.put)  # fmt: skip
            events.put({"type": "done"} | _finish(d, user, body, rid, reply))
        except Exception as e:  # noqa: BLE001 - reported in the stream, logged here
            log(
                "error",
                request_id=rid,
                path="/api/chat/stream",
                error=f"{type(e).__name__}: {e}"[:500],
            )
            events.put({"type": "error", "error": "답변을 만들지 못했습니다", "request_id": rid})
        finally:
            events.put(done)

    threading.Thread(target=run, daemon=True).start()

    def lines():
        while True:
            try:
                e = events.get(timeout=10)
            except queue.Empty:  # a keep-alive while the searches run
                yield b'{"type": "ping"}\n'
                continue
            if e is done:
                return
            yield (json.dumps(e, ensure_ascii=False, default=str) + "\n").encode()

    return StreamingResponse(lines(), media_type="application/x-ndjson",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})  # fmt: skip


@app.get("/api/conversations")
def conversations(user: str = Depends(current_user)) -> list[dict]:
    return sorted(deps().store.conversations(user), key=lambda c: -float(c["ts"]))


@app.get("/api/conversations/{conv_id}")
def conversation(conv_id: str, user: str = Depends(current_user)) -> dict:
    c = deps().store.conversation(user, conv_id) if len(conv_id) <= 64 else None
    if not c:
        raise HTTPException(404, "conversation not found")
    return c


def _save_capped(f: UploadFile, local: Path, limit: int) -> tuple[int, str] | None:
    """Copy the upload to disk in pieces, stopping at `limit` bytes: (size, SHA-256 of
    the content), or None when it is larger (nothing is held whole in memory)."""
    local.parent.mkdir(parents=True, exist_ok=True)
    n, digest = 0, hashlib.sha256()
    with local.open("wb") as out:
        while piece := f.file.read(2**20):
            n += len(piece)
            if n > limit:
                break
            digest.update(piece)
            out.write(piece)
    if n > limit:
        local.unlink(missing_ok=True)
        return None
    return n, digest.hexdigest()


def _looks_like(path: Path, suffix: str) -> bool:
    """The file's first bytes match its extension: "%PDF" within the first 1 KB for a
    PDF, a zip ("PK") for DOCX and HWPX (an old binary HWP renamed .hwpx is refused here,
    with a message, instead of failing in the worker)."""
    head = path.open("rb").read(1024)
    return b"%PDF" in head if suffix == ".pdf" else head.startswith(b"PK")


def _safe_name(raw: str) -> str:
    """The upload's file name without a path or control characters, cut to
    MAX_NAME_BYTES of UTF-8 keeping its extension (a longer one failed the whole batch:
    "File name too long")."""
    name = re.sub(r"[\x00-\x1f\x7f]", "", Path(raw.replace("\\", "/")).name) or "file"
    stem, suffix = os.path.splitext(name)
    while len((stem + suffix).encode()) > MAX_NAME_BYTES and stem:
        stem = stem[:-1]
    return (stem + suffix) or "file"


def _accept(d, user: str, f: UploadFile, name: str, have: dict, request: Request) -> dict:
    """Check, store and queue one uploaded file: {"id", "file"} or {"file", "reason"}."""
    if Path(name).suffix.lower() not in ALLOWED:
        return {"file": name, "reason": "only PDF, DOCX and HWPX"}
    doc_id = new_id()
    local = Path(settings.upload_dir) / user_hash(user) / doc_id / name
    saved = _save_capped(f, local, MAX_FILE_MB * 2**20)
    if saved is None:
        return {"file": name, "reason": f"over {MAX_FILE_MB} MB"}
    size, sha = saved
    if sha in have:
        local.unlink(missing_ok=True)
        return {"file": name, "reason": f"already uploaded (as {have[sha]})"}
    if not _looks_like(local, Path(name).suffix.lower()):
        local.unlink(missing_ok=True)
        reason = ("not a PDF file" if name.lower().endswith(".pdf")
                  else "not a DOCX/HWPX file (an old .hwp/.doc renamed? save it as HWPX, DOCX or PDF)")  # fmt: skip
        return {"file": name, "reason": reason}
    d.store.put_document(user, {"id": doc_id, "file": name, "bytes": size, "sha256": sha,
                                "status": "queued", "queued": time.time()})  # fmt: skip
    have[sha] = name  # the same file twice in one batch
    try:
        d.queue.send(user, doc_id, local, name)
    except Exception as e:  # noqa: BLE001 - S3 or SQS refused it: no message, no worker
        # a record left "queued" would never move and would block sending the file again
        d.store.update_document(user, doc_id, status="failed",
                                error="접수하지 못했습니다 (잠시 뒤 다시 올려 주세요)")  # fmt: skip
        del have[sha]
        local.unlink(missing_ok=True)
        log("error", request_id=request.state.rid, path="enqueue", error=f"{type(e).__name__}: {e}")
        return {"file": name, "reason": "could not be queued, try again"}
    return {"id": doc_id, "file": name}


# a plain def: FastAPI runs it in its thread pool, so the blocking S3 / SQS / DynamoDB
# calls of a large batch do not stall other requests and the health check
@app.post("/api/documents")
def upload(files: list[UploadFile], request: Request, user: str = Depends(current_user)) -> dict:
    if not files or len(files) > MAX_FILES:
        raise HTTPException(400, f"send 1 to {MAX_FILES} files")
    d, accepted, rejected = deps(), [], []
    mine = d.store.documents(user)
    # the same content uploaded again (not a failed one) would be indexed twice
    have = {x["sha256"]: x.get("file", "") for x in mine
            if x.get("sha256") and x.get("status") != "failed"}  # fmt: skip
    left = MAX_DAY_FILES - sum(1 for x in mine if float(x.get("queued", 0)) > time.time() - 86400)
    for f in files:
        name = _safe_name(f.filename or "file")
        if left <= 0:
            rejected.append({"file": name, "reason": f"daily limit of {MAX_DAY_FILES} files"})
            continue
        try:
            r = _accept(d, user, f, name, have, request)
        except Exception as e:  # noqa: BLE001 - one file's failure must not fail the batch
            log("error", request_id=request.state.rid, path="upload",
                error=f"{type(e).__name__}: {e}"[:300])  # fmt: skip
            r = {"file": name, "reason": "could not be saved, try again"}
        if "id" in r:
            accepted.append(r)
            left -= 1
        else:
            rejected.append(r)
    if accepted:
        try:
            d.queue.wake(len(accepted))
        except Exception as e:  # noqa: BLE001 - the queue alarm still scales the worker
            log(
                "error", request_id=request.state.rid, path="wake", error=f"{type(e).__name__}: {e}"
            )
    log("upload", request_id=request.state.rid, user=user_hash(user),
        accepted=len(accepted), rejected=len(rejected))  # fmt: skip
    return {"accepted": accepted, "rejected": rejected}


@app.get("/api/documents")
def documents(user: str = Depends(current_user)) -> list[dict]:
    return sorted(deps().store.documents(user), key=lambda x: -float(x.get("queued", 0)))


@app.get("/api/logs/{preset}")
def logs(preset: str, request: Request, minutes: int = 60, request_id: str = "",
         user: str = Depends(current_evaluator)) -> list[dict]:  # fmt: skip
    """Fixed log queries for evaluator accounts (logs_api.PRESETS)."""
    try:
        rows = logs_api.query(preset, minutes, request_id)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    except RuntimeError as e:  # the query failed or timed out: shown as an error, not "none"
        raise HTTPException(502, str(e)) from e
    log("audit", action="logs", request_id=request.state.rid, user=user_hash(user), preset=preset)
    return rows


@app.get("/api/me")
def me(request: Request, user: str = Depends(current_user)) -> dict:
    """Who is signed in; the UI shows the log viewer to evaluators."""
    h = request.headers
    try:
        current_evaluator(h.get("authorization"), h.get("x-dev-user"), h.get("x-dev-groups"))
        evaluator = True
    except HTTPException:
        evaluator = False
    return {"user": user_hash(user), "evaluator": evaluator}


@app.get("/api/library")
def library(user: str = Depends(current_user)) -> list[dict]:
    """Documents the user can search: the public corpus and their own uploads."""
    d = deps()
    docs = list_documents(d.client, d.index, [user, PUBLIC])
    return [x | {"mine": x["id"].startswith("u-")} for x in docs]


@app.get("/api/source/{chunk_id}")
def source(chunk_id: str, request: Request, user: str = Depends(current_user)) -> dict:
    d = deps()
    r = d.client.search(index=d.index, body={"size": 1, "query": {"bool": {"filter": [
        {"term": {"chunk_id": chunk_id}}, {"terms": {"owner": [user, PUBLIC]}}]}},
        "_source": {"excludes": ["embedding", "search_text"]}})  # fmt: skip
    hits = r["hits"]["hits"]
    if not hits:
        raise HTTPException(404, "source not found")  # also when it belongs to someone else
    s = hits[0]["_source"]
    log("audit", action="view", request_id=request.state.rid, user=user_hash(user),
        document=s["doc_id"], chunk=chunk_id)  # fmt: skip
    return s
