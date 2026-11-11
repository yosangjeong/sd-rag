"""Text embeddings: Amazon Titan Text Embeddings v2 on Bedrock.

Titan v2 was chosen by eval/embed_bench.py (docs/decisions.md): ahead across languages
on the corpus, level within a language, 8,192-token input, in-region. One request per
text (the API takes one), sent concurrently. ``CachedEmbedder`` keeps vectors on disk
keyed by model, dimensions and text, so re-indexing does not pay again.
"""

import hashlib
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Protocol

import boto3
from botocore.config import Config


class Embedder(Protocol):
    name: str
    dims: int

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class TitanEmbedder:
    def __init__(self, model_id: str, region: str, dims: int = 1024, client=None) -> None:
        self.client = client or boto3.client(
            "bedrock-runtime",
            region_name=region,
            config=Config(retries={"max_attempts": 8, "mode": "adaptive"}, max_pool_connections=16),
        )
        self.model_id, self.dims, self.name = model_id, dims, f"{model_id}:{dims}"
        self.input_tokens = 0  # running total, for cost reporting
        self._lock = threading.Lock()  # += from 8 threads is not atomic

    def _one(self, text: str) -> list[float]:
        r = self.client.invoke_model(
            modelId=self.model_id,
            body=json.dumps({"inputText": text, "dimensions": self.dims, "normalize": True}),
        )
        body = json.loads(r["body"].read())
        with self._lock:
            self.input_tokens += body["inputTextTokenCount"]
        return body["embedding"]

    def embed(self, texts: list[str]) -> list[list[float]]:
        with ThreadPoolExecutor(8) as pool:
            return list(pool.map(self._one, texts))


class CachedEmbedder:
    def __init__(self, inner: Embedder, cache_dir: Path) -> None:
        self.inner, self.dir = inner, Path(cache_dir)
        self.name, self.dims = inner.name, inner.dims

    def _path(self, text: str) -> Path:
        key = hashlib.sha256(f"{self.name}\n{text}".encode()).hexdigest()
        return self.dir / key[:2] / f"{key}.json"

    def embed(self, texts: list[str]) -> list[list[float]]:
        out: list[list[float] | None] = []
        missing: list[int] = []
        for i, t in enumerate(texts):
            p = self._path(t)
            out.append(json.loads(p.read_text()) if p.exists() else None)
            if out[-1] is None:
                missing.append(i)
        if missing:
            for i, vec in zip(missing, self.inner.embed([texts[i] for i in missing]), strict=True):
                p = self._path(texts[i])
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(json.dumps(vec))
                out[i] = vec
        return out  # type: ignore[return-value]
