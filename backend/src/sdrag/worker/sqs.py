"""Upload queue in AWS: the file goes to S3, a message to SQS, a worker task takes it.

The API process stays responsive whatever the batch size: it only stores the files
and enqueues; worker tasks (worker/main.py) parse, embed and index, and more tasks
can be started to raise throughput. A message that fails is retried by SQS and,
after maxReceiveCount attempts, moved to the dead-letter queue (infra).

Waking the worker: the service scales on the queue's depth, but the alarm behind it
looks at 5-minute periods, so the first file of a batch waited 4-5 minutes for a
task to start (rehearsal deploy, 2026-11-12). After enqueuing, the API sets the
worker service to one task if it has none; the queue alarm adds more and takes them
back to zero when the queue is empty.
"""

import json
from pathlib import Path

import boto3


class SqsQueue:
    def __init__(self, queue_url: str, bucket: str, region: str, cluster: str = "",
                 service: str = "") -> None:  # fmt: skip
        self.url, self.bucket = queue_url, bucket
        self.sqs = boto3.client("sqs", region_name=region)
        self.s3 = boto3.client("s3", region_name=region)
        self.ecs = boto3.client("ecs", region_name=region)
        self.cluster, self.service = cluster, service

    def send(self, user: str, doc_id: str, path: Path, filename: str) -> None:
        key = f"uploads/{doc_id}/{filename}"
        self.s3.upload_file(str(path), self.bucket, key)
        path.unlink(missing_ok=True)
        body = {"user": user, "doc_id": doc_id, "key": key, "filename": filename}
        self.sqs.send_message(QueueUrl=self.url, MessageBody=json.dumps(body))

    def wake(self) -> None:
        """One worker task if there is none (see above)."""
        if not (self.cluster and self.service):
            return
        s = self.ecs.describe_services(cluster=self.cluster, services=[self.service])["services"][0]
        if s["desiredCount"] == 0:
            self.ecs.update_service(cluster=self.cluster, service=self.service, desiredCount=1)
