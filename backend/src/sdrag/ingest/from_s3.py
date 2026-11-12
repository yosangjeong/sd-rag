"""Bulk-index the public corpus inside AWS, as a one-off ECS task.

The OpenSearch domain is in an isolated subnet, so the corpus is indexed from inside
the VPC: infra/scripts/upload_corpus.sh puts data/ (manifest, raw files, the scans)
and the OCR and embedding caches under s3://<bucket>/corpus/; this task downloads
them, runs the same pipeline as locally (pipeline.py) and writes new cache entries
back, so nothing already paid for (OCR pages, embeddings) is paid again.

    python -m sdrag.ingest.from_s3 --bucket <bucket> [--strategy structure]
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

import boto3

from sdrag.common.config import settings

WORK = Path("/tmp/corpus")


def sync_down(s3, bucket: str, prefix: str, dest: Path) -> int:
    n = 0
    for page in s3.get_paginator("list_objects_v2").paginate(Bucket=bucket, Prefix=prefix):
        for o in page.get("Contents", []):
            path = dest / o["Key"][len(prefix) :]
            path.parent.mkdir(parents=True, exist_ok=True)
            s3.download_file(bucket, o["Key"], str(path))
            n += 1
    return n


def sync_up(s3, bucket: str, prefix: str, src: Path, since: float) -> int:
    n = 0
    for path in src.rglob("*"):
        if path.is_file() and path.stat().st_mtime >= since:
            s3.upload_file(str(path), bucket, prefix + str(path.relative_to(src)))
            n += 1
    return n


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bucket", default=settings.upload_bucket)
    ap.add_argument("--strategy", default="structure")
    a = ap.parse_args()
    s3 = boto3.client("s3", region_name=settings.aws_region)
    print("files:", sync_down(s3, a.bucket, "corpus/data/", WORK / "data"), flush=True)
    for c in ("ocr", "embed"):
        print(f"{c} cache:", sync_down(s3, a.bucket, f"corpus/cache/{c}/", WORK / c), flush=True)
    started = time.time()
    env = os.environ | {"SDRAG_OCR_CACHE_DIR": str(WORK / "ocr"),
                        "SDRAG_EMBED_CACHE_DIR": str(WORK / "embed")}  # fmt: skip
    code = subprocess.call([sys.executable, "-m", "sdrag.ingest.pipeline", "--data", str(WORK / "data"),
                            "--strategy", a.strategy, "--index", settings.index,
                            "--stats", str(WORK / "stats.json")], env=env)  # fmt: skip
    for c in ("ocr", "embed"):
        print(f"{c} cache new:", sync_up(s3, a.bucket, f"corpus/cache/{c}/", WORK / c, started))
    if (WORK / "stats.json").exists():
        s3.upload_file(str(WORK / "stats.json"), a.bucket, f"corpus/ingest-{a.strategy}.json")
    sys.exit(code)


if __name__ == "__main__":
    main()
