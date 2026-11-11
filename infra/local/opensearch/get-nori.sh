#!/bin/bash
# Download the analysis-nori plugin for the local OpenSearch image and check its hash.
# Done on the host, not in the image build, so the build needs no network (and no
# corporate TLS root inside the image). AWS OpenSearch Service ships nori built in.
set -euo pipefail
cd "$(dirname "$0")"
V=3.7.0
SHA512=d6ee6f4fe8e2add29a6554ca4edc0731f4b34e121ed550595af5d1b7482ad08a0c0329accef5ed6577b496476d15b9bbee5b3ca8af88a8613f97c5a95c598c4f
F=analysis-nori-$V.zip
[ -f "$F" ] || curl -sfL -o "$F" "https://artifacts.opensearch.org/releases/plugins/analysis-nori/$V/$F"
echo "$SHA512  $F" | shasum -a 512 -c -
