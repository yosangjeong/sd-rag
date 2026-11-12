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
import urllib.request
from pathlib import Path
from types import SimpleNamespace

import boto3

from sdrag.api.store import DynamoStore
from sdrag.common.config import settings
from sdrag.common.logs import log
from sdrag.common.search_client import make_client
from sdrag.ingest.ocr import BedrockVisionOcr
from sdrag.retrieval.embed import TitanEmbedder
from sdrag.worker.job import process


def protect(on: bool) -> None:
    """Ask ECS not to stop this task while it holds a job (no-op outside ECS)."""
    agent = os.environ.get("ECS_AGENT_URI")
    if not agent:
        return
    body = {"ProtectionEnabled": on} | ({"ExpiresInMinutes": 60} if on else {})
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
        ocr=BedrockVisionOcr(settings.ocr_model, settings.aws_region),
    )
    log("worker_start", queue=settings.upload_queue_url.rsplit("/", 1)[-1])
    while True:
        r = sqs.receive_message(QueueUrl=settings.upload_queue_url, MaxNumberOfMessages=1,
                                WaitTimeSeconds=20)  # fmt: skip
        for m in r.get("Messages", []):
            job = json.loads(m["Body"])
            protect(True)
            try:
                with tempfile.TemporaryDirectory() as tmp:
                    path = Path(tmp) / Path(job["filename"]).name
                    s3.download_file(settings.upload_bucket, job["key"], str(path))
                    process(job["user"], job["doc_id"], path, job["filename"], deps)
                sqs.delete_message(
                    QueueUrl=settings.upload_queue_url, ReceiptHandle=m["ReceiptHandle"]
                )
            finally:
                protect(False)


if __name__ == "__main__":
    main()
