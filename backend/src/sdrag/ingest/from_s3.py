"""Bulk-index the public corpus inside AWS, as a one-off ECS task.

The OpenSearch domain is in an isolated subnet, so the corpus is indexed from inside
the VPC: infra/scripts/upload_corpus.sh puts three archives under s3://<bucket>/corpus/
(the manifest and data/corpus/, the OCR cache, the embedding cache); this task
unpacks them, runs the same pipeline as locally (pipeline.py) and writes the caches
back if anything was added, so nothing already paid for (OCR pages, embeddings) is
paid again.

    python -m sdrag.ingest.from_s3 --bucket <bucket> [--strategy structure]
"""

import argparse
import os
import subprocess
import sys
import tarfile
from pathlib import Path

import boto3

from sdrag.common.config import settings

WORK = Path("/tmp/corpus")


def fetch(s3, bucket: str, name: str, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    archive = WORK / f"{name}.tgz"
    s3.download_file(bucket, f"corpus/{name}.tgz", str(archive))
    with tarfile.open(archive) as tar:
        tar.extractall(dest, filter="data")  # no absolute paths or links out of dest


def store(s3, bucket: str, name: str, src: Path, arcname: str) -> None:
    archive = WORK / f"{name}-new.tgz"
    with tarfile.open(archive, "w:gz") as tar:
        tar.add(src, arcname=arcname)
    s3.upload_file(str(archive), bucket, f"corpus/{name}.tgz")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bucket", default=settings.upload_bucket)
    ap.add_argument("--strategy", default="structure")
    a = ap.parse_args()
    s3 = boto3.client("s3", region_name=settings.aws_region)
    WORK.mkdir(parents=True, exist_ok=True)
    fetch(s3, a.bucket, "corpus", WORK)  # -> WORK/data/manifest.csv, WORK/data/corpus/
    fetch(s3, a.bucket, "ocr", WORK)  # -> WORK/ocr/
    fetch(s3, a.bucket, "embed", WORK)  # -> WORK/embed/
    caches = {"ocr": WORK / "ocr", "embed": WORK / "embed"}
    before = {k: sum(1 for _ in p.rglob("*.json")) for k, p in caches.items()}
    env = os.environ | {"SDRAG_OCR_CACHE_DIR": str(caches["ocr"]),
                        "SDRAG_EMBED_CACHE_DIR": str(caches["embed"])}  # fmt: skip
    code = subprocess.call([sys.executable, "-m", "sdrag.ingest.pipeline", "--data", str(WORK / "data"),
                            "--strategy", a.strategy, "--index", settings.index, "--replace-public",
                            "--stats", str(WORK / "stats.json")], env=env)  # fmt: skip
    for k, p in caches.items():
        added = sum(1 for _ in p.rglob("*.json")) - before[k]
        print(f"{k} cache: {added} new entries", flush=True)
        if added:
            store(s3, a.bucket, k, p, k)
    if (WORK / "stats.json").exists():
        s3.upload_file(str(WORK / "stats.json"), a.bucket, f"corpus/ingest-{a.strategy}.json")
    sys.exit(code)


if __name__ == "__main__":
    main()
