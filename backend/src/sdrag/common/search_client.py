"""The OpenSearch client: plain HTTP locally, IAM-signed HTTPS in AWS.

AWS OpenSearch Service authorizes each request by its SigV4 signature (the ECS task
role's credentials, refreshed by boto3), so no password exists to leak.
"""

from urllib.parse import urlparse

import boto3
from opensearchpy import OpenSearch, Urllib3AWSV4SignerAuth


def make_client(url: str, region: str, timeout: int = 60) -> OpenSearch:
    u = urlparse(url)
    if not u.hostname or not u.hostname.endswith(".amazonaws.com"):
        return OpenSearch(hosts=[url], timeout=timeout)
    auth = Urllib3AWSV4SignerAuth(boto3.Session().get_credentials(), region, "es")
    return OpenSearch(hosts=[{"host": u.hostname, "port": 443}], http_auth=auth, use_ssl=True,
                      verify_certs=True, timeout=timeout)  # fmt: skip
