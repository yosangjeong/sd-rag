"""Ingestion worker (an ECS service of its own): long-poll SQS, process, delete.

    python -m sdrag.worker.main

A message is deleted only after the job ran (done or failed is recorded either
way); if the task dies mid-job, the message becomes visible again after the
visibility timeout and another task retries it.

Scale-in protection: the service scales in when no message is *waiting*, which is
also the case while the last one is being processed; in the rehearsal deploy that
stopped a task mid-file and the file waited 30 minutes for its retry. A task now marks
itself protected (ECS agent endpoint) while it works on a message, so scale-in waits.
"""

import json
import os
import tempfile
import threading
import urllib.request
from pathlib import Path
from types import SimpleNamespace

import boto3

from sdrag.api.store import DynamoStore
from sdrag.common.config import settings
from sdrag.common.logs import log, user_hash
from sdrag.common.search_client import make_client
from sdrag.ingest.ocr import build_ocr
from sdrag.retrieval.embed import TitanEmbedder
from sdrag.worker.job import _remove_chunks, process

MAX_TRIES = 3  # jobs run at most this often; the queue's maxReceiveCount is one more
# (infra/stacks/data.py): a delivery after the last try means the task died mid-job each
# time, and that delivery only records the failure (else the record says "processing"
# forever while the message sits in the DLQ)


def protect(on: bool) -> None:
    """Ask ECS not to stop this task while it holds a job (no-op outside ECS)."""
    agent = os.environ.get("ECS_AGENT_URI")
    if not agent:
        return
    body = {"ProtectionEnabled": on} | ({"ExpiresInMinutes": 120} if on else {})
    req = urllib.request.Request(f"{agent}/task-protection/v1/state", data=json.dumps(body).encode(),
                                 method="PUT", headers={"Content-Type": "application/json"})  # fmt: skip
    try:
        urllib.request.urlopen(req, timeout=5).read()  # the local ECS agent
    except OSError as e:  # unprotected is the old behavior, not a reason to drop the job
        log("error", path="task-protection", error=f"{type(e).__name__}: {e}")


def main() -> None:
    sqs = boto3.client("sqs", region_name=settings.aws_region)
    s3 = boto3.client("s3", region_name=settings.aws_region)
    deps = SimpleNamespace(
        store=DynamoStore(settings.table, settings.aws_region),
        client=make_client(settings.opensearch_url, settings.aws_region, 120),
        index=settings.index,
        embedder=TitanEmbedder(settings.embed_model, settings.aws_region, settings.embed_dims),
        # a retry on the same task does not pay for the OCR of its pages again
        ocr=build_ocr(
            settings.ocr_model,
            settings.aws_region,
            settings.ocr_check,
            Path(tempfile.gettempdir()) / "sdrag-ocr-cache",
        ),
    )
    log("worker_start", queue=settings.upload_queue_url.rsplit("/", 1)[-1])
    while True:
        r = sqs.receive_message(QueueUrl=settings.upload_queue_url, MaxNumberOfMessages=1,
                                WaitTimeSeconds=20, AttributeNames=["ApproximateReceiveCount"])  # fmt: skip
        for m in r.get("Messages", []):
            try:
                handle(m, sqs, s3, deps)
            except Exception as e:  # noqa: BLE001 - one message must not stop the worker
                log("error", path="worker", error=f"{type(e).__name__}: {e}"[:500])
                _later(sqs, m["ReceiptHandle"], 60)


def _later(sqs, receipt: str, seconds: int) -> None:
    """Make the message visible again in `seconds` (the queue's DLQ counts the tries)."""
    try:
        sqs.change_message_visibility(QueueUrl=settings.upload_queue_url, ReceiptHandle=receipt,
                                      VisibilityTimeout=seconds)  # fmt: skip
    except Exception as e:  # noqa: BLE001 - a stale handle: the timeout makes it visible
        log("error", path="worker-visibility", error=f"{type(e).__name__}: {e}"[:300])


class Heartbeat:
    """While a job runs, push the message's visibility out every 5 minutes, so a long
    scan is not handed to the other worker at the queue's 30-minute timeout (it would
    be OCR'd twice, and this worker's delete would fail on a stale handle)."""

    def __init__(self, sqs, receipt: str, every: int = 300, extend: int = 1800) -> None:
        self.sqs, self.receipt, self.every, self.extend = sqs, receipt, every, extend
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)

    def _run(self) -> None:
        while not self.stop.wait(self.every):
            _later(self.sqs, self.receipt, self.extend)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *exc) -> None:
        self.stop.set()
        # a tick in flight must not push the visibility out after the caller's own
        # change (a retry would wait 30 minutes instead of 1)
        self.thread.join(timeout=10)


def _give_up(deps, job: dict, error: str) -> None:
    """A file no try could process: its chunks out of the index (a busy index may have
    taken some batches), the status "failed", and an "ingest" line like every other
    outcome (worker/job.py), so the evaluators' upload log ends where the file did."""
    _remove_chunks(deps, f"u-{job['doc_id']}")
    deps.store.update_document(job["user"], job["doc_id"], status="failed", stage="", error=error)
    log("ingest", user=user_hash(job["user"]), doc_id=job["doc_id"], status="failed",
        stage="", error=error)  # fmt: skip


def handle(m: dict, sqs, s3, deps) -> None:
    job = json.loads(m["Body"])
    receipt = m["ReceiptHandle"]
    receives = int(m.get("Attributes", {}).get("ApproximateReceiveCount", "1"))
    if receives > MAX_TRIES:  # every try died mid-job (out of memory, task stopped)
        _give_up(deps, job, "처리 도중 작업이 멈췄습니다 (재시도 끝)")
        sqs.delete_message(QueueUrl=settings.upload_queue_url, ReceiptHandle=receipt)
        return
    last_try = receives >= MAX_TRIES
    protect(True)
    try:
        with tempfile.TemporaryDirectory() as tmp, Heartbeat(sqs, receipt):
            path = Path(tmp) / Path(job["filename"]).name
            try:
                s3.download_file(settings.upload_bucket, job["key"], str(path))
            except Exception as e:  # noqa: BLE001 - leave the message for a retry
                log("error", path="worker-download", doc_id=job.get("doc_id"),
                    error=f"{type(e).__name__}: {e}"[:500])  # fmt: skip
                # stage "": a try that died mid-job may have left one
                result = {"status": "retrying", "stage": "", "error": "파일을 내려받지 못했습니다"}
                deps.store.update_document(job["user"], job["doc_id"], **result)  # not "queued"
                log("ingest", user=user_hash(job["user"]), doc_id=job["doc_id"], **result)
            else:
                result = process(job["user"], job["doc_id"], path, job["filename"], deps)
        if result["status"] == "retrying" and last_try:
            # the last try: say "failed" instead of "retrying" forever and delete it
            _give_up(deps, job, (result.get("error") or "처리하지 못했습니다") + " (재시도 끝)")
            sqs.delete_message(QueueUrl=settings.upload_queue_url, ReceiptHandle=receipt)
        elif result["status"] == "retrying":  # visible again in a minute
            _later(sqs, receipt, 60)
        else:
            sqs.delete_message(QueueUrl=settings.upload_queue_url, ReceiptHandle=receipt)
    finally:
        protect(False)


if __name__ == "__main__":
    main()
