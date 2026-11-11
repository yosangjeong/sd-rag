#!/bin/bash
# Local single-node OpenSearch (with nori) for development and evaluation runs.
# Security plugin off and bound to 127.0.0.1: never expose this outside the laptop.
#   infra/local/opensearch/up.sh        start (builds the image the first time)
#   docker rm -f sdrag-opensearch       stop (data stays in the sdrag-opensearch volume)
set -euo pipefail
cd "$(dirname "$0")"
./get-nori.sh >/dev/null
docker build -q -t sdrag-opensearch-local:3.7.0 . >/dev/null
docker rm -f sdrag-opensearch >/dev/null 2>&1 || true
docker run -d --name sdrag-opensearch \
  -e discovery.type=single-node \
  -e DISABLE_SECURITY_PLUGIN=true \
  -e DISABLE_INSTALL_DEMO_CONFIG=true \
  -e "OPENSEARCH_JAVA_OPTS=-Xms1g -Xmx1g" \
  -p 127.0.0.1:9200:9200 \
  -v sdrag-opensearch:/usr/share/opensearch/data \
  sdrag-opensearch-local:3.7.0 >/dev/null
for _ in $(seq 60); do
  curl -sf http://127.0.0.1:9200 >/dev/null && { echo "OpenSearch up on http://127.0.0.1:9200"; exit 0; }
  sleep 2
done
echo "OpenSearch did not start; see: docker logs sdrag-opensearch" >&2
exit 1
