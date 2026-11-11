"""Application settings, read from environment variables.

In ECS, these come from the task definition (plain values) or Secrets Manager
(secrets). Locally, they can come from a .env file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SDRAG_", env_file=".env", extra="ignore")

    env: str = "local"
    aws_region: str = "ap-southeast-2"


settings = Settings()
