"""Ingest one uploaded file: parse (OCR for scanned pages) -> chunk -> embed -> index.

The same steps as the corpus pipeline (ingest/pipeline.py), for a user's file: its
chunks are indexed with owner = the user, so only that user (and no one else)
searches them. The document record goes queued -> processing -> done | failed, with
per-stage timings: the brief asks for ingestion throughput and duration.

Queues: in AWS the API sends one SQS message per file and the worker service
(worker/main.py) long-polls the queue; locally (no queue URL) the API runs the job
in a thread pool. Either way the job is ``process``.
"""

import re
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from sdrag.common.logs import log, user_hash
from sdrag.ingest.chunk import chunk_structure, embed_input
from sdrag.ingest.corpus import CorpusDoc
from sdrag.ingest.parse import parse, sniff_format
from sdrag.retrieval.index import bulk_index, to_source

ALLOWED = {".pdf", ".docx", ".hwpx"}


def detect_lang(text: str) -> str:
    sample = text[:20000]
    return (
        "ko"
        if len(re.findall(r"[가-힣]", sample)) > len(re.findall(r"[A-Za-z]", sample)) / 3
        else "en"
    )


def process(user: str, doc_id: str, path: Path, filename: str, deps) -> dict:
    """deps: an object with store, client (OpenSearch), index, embedder, ocr."""
    deps.store.update_document(user, doc_id, status="processing")
    t0 = time.perf_counter()
    try:
        parsed = parse(path, ocr=deps.ocr)
        t1 = time.perf_counter()
        full = "\n".join(b.text for b in parsed.blocks)
        # a PDF is reported as a scan when at least half its pages needed OCR
        pages = {b.page for b in parsed.blocks if b.page}
        scanned = parsed.ocr_pages and 2 * len(parsed.ocr_pages) >= max(1, len(pages))
        file_type = "scan" if scanned else sniff_format(path)
        doc = CorpusDoc(f"u-{doc_id}", detect_lang(full), filename, file_type, ("upload",), path)
        chunks = chunk_structure(parsed, doc.id)
        vectors = deps.embedder.embed([embed_input(c, doc.title) for c in chunks]) if chunks else []
        t2 = time.perf_counter()
        ocr = set(parsed.ocr_pages)
        bulk_index(deps.client, deps.index,
                   [to_source(doc, c, v, ocr, owner=user) for c, v in zip(chunks, vectors, strict=True)])  # fmt: skip
        t3 = time.perf_counter()
        result = {"status": "done", "chunks": len(chunks), "lang": doc.lang, "file_type": file_type,
                  "ocr_pages": len(ocr), "parse_s": round(t1 - t0, 2), "embed_s": round(t2 - t1, 2),
                  "index_s": round(t3 - t2, 2), "finished": time.time()}  # fmt: skip
    except Exception as e:  # noqa: BLE001 - a bad file must not stop the worker
        result = {
            "status": "failed",
            "error": f"{type(e).__name__}: {e}"[:500],
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

    def wake(self) -> None:
        pass  # threads are always there
