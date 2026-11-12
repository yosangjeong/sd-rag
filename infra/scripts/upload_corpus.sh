#!/usr/bin/env bash
# Upload the corpus and the OCR / embedding caches for the in-VPC bulk index
# (backend/src/sdrag/ingest/from_s3.py). Run from the repository root after deploy:
#   AWS_PROFILE=sd-assignment infra/scripts/upload_corpus.sh <bucket>
set -euo pipefail
bucket="$1"
aws s3 cp data/manifest.csv "s3://$bucket/corpus/data/manifest.csv"
aws s3 sync data/raw "s3://$bucket/corpus/data/raw" \
  --exclude "*" --include "*.pdf" --include "*.hwpx" --include "*.docx" \
  --exclude "kr-truth/*" --exclude "ocr-bench/*" --exclude "embed-bench/*" --exclude "eval-cache/*"
aws s3 sync data/raw/ocr-cache "s3://$bucket/corpus/cache/ocr"
aws s3 sync data/raw/embed-cache "s3://$bucket/corpus/cache/embed"
