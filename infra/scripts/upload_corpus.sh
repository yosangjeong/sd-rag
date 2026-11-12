#!/usr/bin/env bash
# Upload what the in-VPC bulk index needs (backend/src/sdrag/ingest/from_s3.py):
# the manifest, the 53 indexed files (data/corpus/) and the OCR / embedding caches,
# each as one archive (13,000 small cache files took 13 minutes one by one).
#   AWS_PROFILE=sd-assignment infra/scripts/upload_corpus.sh <bucket>
set -euo pipefail
bucket="$1"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
tar -czf "$tmp/corpus.tgz" data/manifest.csv data/corpus
tar -czf "$tmp/ocr.tgz" -C data/raw ocr-cache
tar -czf "$tmp/embed.tgz" -C data/raw embed-cache
for f in corpus ocr embed; do aws s3 cp --only-show-errors "$tmp/$f.tgz" "s3://$bucket/corpus/$f.tgz"; done
ls -la "$tmp"
