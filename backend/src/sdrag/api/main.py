"""FastAPI entrypoint. Run with: uvicorn sdrag.api.main:app"""

from fastapi import FastAPI

from sdrag.common.config import settings

app = FastAPI(title="SD RAG API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness check used by the load balancer and ECS to decide if the task is healthy."""
    return {"status": "ok", "env": settings.env}
