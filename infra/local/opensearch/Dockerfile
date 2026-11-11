# Local development only: OpenSearch with the Korean analyzer (nori), the version
# AWS OpenSearch Service runs. Built and started by ./up.sh.
FROM opensearchproject/opensearch:3.7.0
# the plugin zip is mounted for this step only, so it stays out of the image
RUN --mount=type=bind,source=analysis-nori-3.7.0.zip,target=/tmp/analysis-nori.zip \
    /usr/share/opensearch/bin/opensearch-plugin install --batch file:///tmp/analysis-nori.zip
