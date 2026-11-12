"""Application settings, read from environment variables.

In ECS, these come from the task definition (plain values) or Secrets Manager
(secrets). Locally, they can come from a .env file.
"""

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SDRAG_", env_file=".env", extra="ignore")

    env: str = "local"
    aws_region: str = "ap-southeast-2"
    # OCR engine for scanned PDF pages: a Bedrock vision model (eval/ocr_bench.py)
    ocr_model: str = "qwen.qwen3-vl-235b-a22b"
    ocr_cache_dir: str = ""  # empty: no cache (set locally to avoid paying twice)
    # embeddings: Titan Text Embeddings v2 (eval/embed_bench.py)
    embed_model: str = "amazon.titan-embed-text-v2:0"
    embed_dims: int = 1024
    embed_cache_dir: str = ""
    # search index; local development runs infra/local/opensearch/up.sh
    opensearch_url: str = "http://127.0.0.1:9200"
    index: str = "chunks-structure"
    # reranker, query translation, agent and answers (eval/run_retrieval.py, dev set)
    llm_model: str = "zai.glm-4.7"
    # auth: "cognito" in AWS; "dev" locally (user from the X-Dev-User header)
    auth_mode: str = "dev"
    cognito_user_pool_id: str = ""
    cognito_client_id: str = ""
    # per-user records and uploads: DynamoDB table, S3 bucket and SQS queue in AWS;
    # empty = in memory / local disk / a thread (local runs)
    table: str = ""
    upload_bucket: str = ""
    upload_queue_url: str = ""
    upload_dir: str = "/tmp/sdrag-uploads"

    @model_validator(mode="after")
    def _no_dev_auth_in_aws(self):
        if self.env != "local" and self.auth_mode != "cognito":
            raise ValueError("auth_mode must be 'cognito' outside local development")
        return self


settings = Settings()
