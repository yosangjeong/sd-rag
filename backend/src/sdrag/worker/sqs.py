"""Upload queue in AWS: the file goes to S3, a message to SQS, a worker task takes it.

The API process stays responsive whatever the batch size: it only stores the files
and enqueues; worker tasks (worker/main.py) parse, embed and index, and more tasks
can be started to raise throughput. A message that fails is retried by SQS and,
after maxReceiveCount attempts, moved to the dead-letter queue (infra).
"""

import json
from pathlib import Path

import boto3


class SqsQueue:
    def __init__(self, queue_url: str, bucket: str, region: str) -> None:
        self.url, self.bucket = queue_url, bucket
        self.sqs = boto3.client("sqs", region_name=region)
        self.s3 = boto3.client("s3", region_name=region)

    def send(self, user: str, doc_id: str, path: Path, filename: str) -> None:
        key = f"uploads/{doc_id}/{filename}"
        self.s3.upload_file(str(path), self.bucket, key)
        path.unlink(missing_ok=True)
        body = {"user": user, "doc_id": doc_id, "key": key, "filename": filename}
        self.sqs.send_message(QueueUrl=self.url, MessageBody=json.dumps(body))
