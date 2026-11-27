"""Ingest one uploaded file: parse (OCR for scanned pages) -> chunk -> embed -> index.

The same steps as the corpus pipeline (ingest/pipeline.py), for a user's file: its
chunks are indexed with owner = the user, so only that user (and no one else)
searches them. The document record goes queued -> processing -> done | failed, with
per-stage timings: the brief asks for ingestion throughput and duration.

Queues: in AWS the API sends one SQS message per file and the worker service
(worker/main.py) long-polls the queue; locally (no queue URL) the API runs the job
in a thread pool. Either way the job is ``process``.
"""

import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from sdrag.common.logs import log, user_hash
from sdrag.common.text import is_korean
from sdrag.ingest.chunk import chunk_structure, embed_input
from sdrag.ingest.corpus import CorpusDoc
from sdrag.ingest.parse import UnreadableFile, parse, sniff_format
from sdrag.retrieval.index import bulk_index, to_source

ALLOWED = {".pdf", ".docx", ".hwpx"}


def _transient(e: Exception) -> bool:
    from botocore.exceptions import ClientError, HTTPClientError
    from botocore.exceptions import ConnectionError as BotoConnectionError
    from opensearchpy import ConnectionError as SearchConnectionError
    from opensearchpy import TransportError
    from opensearchpy.helpers import BulkIndexError

    from sdrag.ingest.ocr import TRANSIENT_CODES, OcrError
    from sdrag.retrieval.index import RETRYABLE

    # unreachable or timed out even after botocore's own retries (Titan, DynamoDB, S3);
    # BedrockVisionOcr and TextractOcr already count these as transient
    if isinstance(e, SearchConnectionError | BotoConnectionError | HTTPClientError):
        return True
    if isinstance(e, OcrError):
        return e.transient
    if isinstance(e, BulkIndexError):  # documents the busy node kept refusing (429)
        return all(next(iter(x.values()), {}).get("status") == 429 for x in e.errors)
    if isinstance(e, TransportError):
        return e.status_code in RETRYABLE
    if isinstance(e, ClientError):
        return e.response.get("Error", {}).get("Code") in (
            *TRANSIENT_CODES,
            "ProvisionedThroughputExceededException",  # DynamoDB
            "RequestLimitExceeded",
            "SlowDown",  # S3
        )
    return False


def _shown(e: Exception) -> str:
    """The failure as the user sees it: UnreadableFile messages are written for the
    user; a damaged or password-protected file gets one too; anything else is reported
    by type, with the details in the log only."""
    import zipfile

    if isinstance(e, UnreadableFile):
        return str(e)
    if isinstance(e, zipfile.BadZipFile):
        return "파일이 손상되었거나 암호가 걸려 있어 열 수 없습니다"
    return f"처리 중 오류 ({type(e).__name__})"


def _remove_chunks(deps, doc: str, keep: list[str] | None = None) -> None:
    """Delete a document's chunks from the index, except the ids in `keep`."""
    query: dict = {"term": {"doc_id": doc}}
    if keep:
        query = {"bool": {"filter": [query], "must_not": [{"ids": {"values": keep}}]}}
    try:
        deps.client.delete_by_query(index=deps.index, body={"query": query},
                                    refresh=True, conflicts="proceed")  # fmt: skip
    except Exception as e:  # noqa: BLE001 - the failure is already being reported
        log("error", path="ingest-cleanup", doc_id=doc, error=f"{type(e).__name__}: {e}"[:300])


def detect_lang(text: str) -> str:
    """An upload's language from its first 20,000 characters (common/text.is_korean)."""
    return "ko" if is_korean(text[:20000]) else "en"


def process(user: str, doc_id: str, path: Path, filename: str, deps) -> dict:
    """deps: an object with store, client (OpenSearch), index, embedder, ocr."""
    deps.store.update_document(user, doc_id, status="processing", stage="parsing")
    t0 = time.perf_counter()

    def ocr_progress(done: int, total: int) -> None:  # every 5 pages and the last
        if done == total or done % 5 == 0:
            deps.store.update_document(user, doc_id, stage=f"OCR {done}/{total}")

    try:
        parsed = parse(path, ocr=deps.ocr, progress=ocr_progress)
        t1 = time.perf_counter()
        full = "\n".join(b.text for b in parsed.blocks)
        # a PDF is reported as a scan when at least half its pages needed OCR
        pages = {b.page for b in parsed.blocks if b.page}
        scanned = parsed.ocr_pages and 2 * len(parsed.ocr_pages) >= max(1, len(pages))
        file_type = "scan" if scanned else sniff_format(path)
        doc = CorpusDoc(f"u-{doc_id}", detect_lang(full), filename, file_type, ("upload",), path)
        chunks = chunk_structure(parsed, doc.id)
        if not chunks:
            raise UnreadableFile(
                "문서에서 글자를 찾지 못했습니다 (빈 문서이거나 읽을 수 없는 이미지)"
            )
        deps.store.update_document(user, doc_id, stage=f"embedding {len(chunks)} chunks")
        vectors = deps.embedder.embed([embed_input(c, doc.title) for c in chunks])
        t2 = time.perf_counter()
        ocr = set(parsed.ocr_pages)
        deps.store.update_document(user, doc_id, stage="indexing")
        bulk_index(deps.client, deps.index,
                   [to_source(doc, c, v, ocr, owner=user) for c, v in zip(chunks, vectors, strict=True)])  # fmt: skip
        # an earlier try of this file may have indexed more chunks (its OCR read a page
        # differently): those ids would stay searchable next to this result
        _remove_chunks(deps, doc.id, keep=[c.id for c in chunks])
        t3 = time.perf_counter()
        result = {"status": "done", "stage": "", "doc": doc.id, "chunks": len(chunks),
                  "unread_pages": len(parsed.needs_ocr_pages),  # OCR failed or no text
                  "lang": doc.lang, "file_type": file_type,
                  "ocr_pages": len(ocr), "ocr_replaced": len(parsed.ocr_replaced_pages),
                  "parse_s": round(t1 - t0, 2), "embed_s": round(t2 - t1, 2),
                  "index_s": round(t3 - t2, 2), "finished": time.time()}  # fmt: skip
    except Exception as e:  # noqa: BLE001 - a bad file must not stop the worker
        # a busy or unreachable service is worth another try (the queue redelivers);
        # a file that cannot be parsed is not
        transient = _transient(e)
        # UnreadableFile messages are written for the user; anything else is reported
        # by type, with the details in the log only
        shown = _shown(e)
        log("error", path="ingest", doc_id=doc_id, error=f"{type(e).__name__}: {e}"[:1000])
        if not transient:  # batches already indexed must not stay searchable
            _remove_chunks(deps, f"u-{doc_id}")
        result = {
            "status": "retrying" if transient else "failed",
            "stage": "",
            "error": shown[:300],
            "finished": time.time(),
        }
    deps.store.update_document(user, doc_id, **result)
    log(
        "ingest",
        user=user_hash(user),
        doc_id=doc_id,
        **{k: v for k, v in result.items() if k != "finished"},
    )
    return result


class LocalQueue:
    """Runs jobs in threads in the API process (local development only)."""

    def __init__(self, deps, workers: int = 4) -> None:
        self.deps, self.pool = deps, ThreadPoolExecutor(workers)

    def send(self, user: str, doc_id: str, path: Path, filename: str, key: str = "") -> None:
        self.pool.submit(process, user, doc_id, path, filename, self.deps)

    def wake(self, files: int = 1) -> None:
        pass  # threads are always there
