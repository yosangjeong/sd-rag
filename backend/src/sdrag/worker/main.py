"""Ingestion worker (an ECS service of its own): long-poll SQS, process, delete.

    python -m sdrag.worker.main

A message is deleted only after the job ran (done or failed is recorded either
way); if the task dies mid-job, the message becomes visible again after the
visibility timeout and another task retries it.
"""

import json
import tempfile
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
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / Path(job["filename"]).name
                s3.download_file(settings.upload_bucket, job["key"], str(path))
                process(job["user"], job["doc_id"], path, job["filename"], deps)
            sqs.delete_message(QueueUrl=settings.upload_queue_url, ReceiptHandle=m["ReceiptHandle"])


if __name__ == "__main__":
    main()
