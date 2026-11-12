"""HTTP API (FastAPI). Run locally with: uvicorn sdrag.api.main:app

Endpoints (all but /health need a signed-in user; see auth.py):

- POST /api/chat                 ask; answers with citations; stored in the conversation
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

import time
import uuid
from contextlib import asynccontextmanager
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace

from fastapi import Depends, FastAPI, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from sdrag.api import logs_api
from sdrag.api.auth import current_evaluator, current_user
from sdrag.api.store import DynamoStore, MemoryStore, new_id
from sdrag.common.config import settings
from sdrag.common.llm import BedrockChat
from sdrag.common.logs import log, user_hash
from sdrag.common.search_client import make_client
from sdrag.ingest.ocr import BedrockVisionOcr
from sdrag.retrieval.embed import TitanEmbedder
from sdrag.retrieval.index import PUBLIC, create_index, list_documents
from sdrag.service import RagService
from sdrag.worker.job import ALLOWED, LocalQueue

MAX_FILES, MAX_FILE_MB = 100, 50


@lru_cache(maxsize=1)
def deps() -> SimpleNamespace:
    """Clients built once per process (they are thread-safe and keep connections)."""
    client = make_client(settings.opensearch_url, settings.aws_region, 60)
    embedder = TitanEmbedder(settings.embed_model, settings.aws_region, settings.embed_dims)
    chat = BedrockChat(settings.llm_model, settings.aws_region)
    store = DynamoStore(settings.table, settings.aws_region) if settings.table else MemoryStore()
    d = SimpleNamespace(client=client, embedder=embedder, chat=chat, store=store,
                        index=settings.index, ocr=BedrockVisionOcr(settings.ocr_model, settings.aws_region),
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
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"],
                   allow_headers=["Authorization", "Content-Type", "X-Dev-User", "X-Dev-Groups"])  # fmt: skip


@app.middleware("http")
async def request_log(request: Request, call_next):
    rid = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
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
    conversation_id: str | None = None
    mode: str = Field(default="basic", pattern="^(basic|agent)$")
    documents: list[str] = Field(default_factory=list, max_length=50)  # search only these


@app.post("/api/chat")
def chat(body: ChatIn, request: Request, user: str = Depends(current_user)) -> dict:
    d, rid = deps(), request.state.rid
    history = []
    if body.conversation_id:
        conv = d.store.conversation(user, body.conversation_id)
        if not conv:
            raise HTTPException(404, "conversation not found")
        history = [{"role": m["role"], "text": m["text"]} for m in conv["messages"]]
    log("question", request_id=rid, user=user_hash(user), mode=body.mode, question=body.message,
        scope=body.documents)  # fmt: skip
    reply = d.service.ask(user, body.message, body.mode, rid, history, body.documents)
    citations = [vars(c) for c in reply.answer.citations]
    log("audit", action="search", request_id=rid, user=user_hash(user),
        documents=sorted({c["doc_id"] for c in citations}))  # fmt: skip
    now = time.time()
    conv = d.store.add_message(
        user, body.conversation_id, {"role": "user", "text": body.message, "ts": now}
    )
    msg = {"role": "assistant", "text": reply.answer.text, "citations": citations,
           "mode": reply.mode, "ts": time.time()}  # fmt: skip
    d.store.add_message(user, conv, msg)
    return {"conversation_id": conv, "answer": reply.answer.text, "citations": citations,
            "mode": reply.mode, "latency_ms": round(reply.latency_ms), "steps": reply.steps,
            "searched": reply.question,
            "tokens": {"input": reply.input_tokens, "output": reply.output_tokens}}  # fmt: skip


@app.get("/api/conversations")
def conversations(user: str = Depends(current_user)) -> list[dict]:
    return sorted(deps().store.conversations(user), key=lambda c: -float(c["ts"]))


@app.get("/api/conversations/{conv_id}")
def conversation(conv_id: str, user: str = Depends(current_user)) -> dict:
    c = deps().store.conversation(user, conv_id)
    if not c:
        raise HTTPException(404, "conversation not found")
    return c


@app.post("/api/documents")
async def upload(
    files: list[UploadFile], request: Request, user: str = Depends(current_user)
) -> dict:
    if not files or len(files) > MAX_FILES:
        raise HTTPException(400, f"send 1 to {MAX_FILES} files")
    d, accepted, rejected = deps(), [], []
    for f in files:
        name = Path(f.filename or "file").name
        if Path(name).suffix.lower() not in ALLOWED:
            rejected.append({"file": name, "reason": "only PDF, DOCX and HWPX"})
            continue
        data = await f.read()
        if len(data) > MAX_FILE_MB * 2**20:
            rejected.append({"file": name, "reason": f"over {MAX_FILE_MB} MB"})
            continue
        doc_id = new_id()
        local = Path(settings.upload_dir) / user_hash(user) / doc_id / name
        local.parent.mkdir(parents=True, exist_ok=True)
        local.write_bytes(data)
        d.store.put_document(user, {"id": doc_id, "file": name, "bytes": len(data),
                                    "status": "queued", "queued": time.time()})  # fmt: skip
        d.queue.send(user, doc_id, local, name)
        accepted.append({"id": doc_id, "file": name})
    if accepted:
        try:
            d.queue.wake()
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
