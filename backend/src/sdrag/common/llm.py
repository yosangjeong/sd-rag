"""Text LLM calls on Bedrock (Converse API), with an optional disk cache.

One small interface (``complete``) so the evaluation set builder, the judge and later
the answer generator can switch models by id. The cache is keyed by model, system
prompt, user prompt and settings: re-running a pipeline stage costs nothing and gives
the same output, which also makes generated evaluation data reproducible from the
cache.
"""

import hashlib
import json
import re
import threading
from dataclasses import asdict, dataclass
from pathlib import Path

import boto3
from botocore.config import Config


@dataclass
class Completion:
    text: str
    input_tokens: int
    output_tokens: int
    stop_reason: str


class BedrockChat:
    def __init__(self, model_id: str, region: str, client=None) -> None:
        self.client = client or boto3.client(
            "bedrock-runtime",
            region_name=region,
            config=Config(retries={"max_attempts": 8, "mode": "adaptive"}, read_timeout=300,
                          max_pool_connections=16),
        )  # fmt: skip
        self.model_id = self.name = model_id
        self.input_tokens = self.output_tokens = 0
        self._lock = threading.Lock()

    def complete(self, system: str, user: str, max_tokens: int = 1024,
                 temperature: float = 0.0) -> Completion:  # fmt: skip
        r = self.client.converse(
            modelId=self.model_id,
            system=[{"text": system}] if system else [],
            messages=[{"role": "user", "content": [{"text": user}]}],
            inferenceConfig={"maxTokens": max_tokens, "temperature": temperature},
        )
        text = "".join(c.get("text", "") for c in r["output"]["message"]["content"])
        u = r["usage"]
        with self._lock:
            self.input_tokens += u["inputTokens"]
            self.output_tokens += u["outputTokens"]
        return Completion(text, u["inputTokens"], u["outputTokens"], r["stopReason"])


class CachedChat:
    def __init__(self, inner: BedrockChat, cache_dir: Path) -> None:
        self.inner, self.dir, self.name = inner, Path(cache_dir), inner.name

    def complete(self, system: str, user: str, max_tokens: int = 1024,
                 temperature: float = 0.0) -> Completion:  # fmt: skip
        key = hashlib.sha256(
            json.dumps([self.name, system, user, max_tokens, temperature]).encode()
        ).hexdigest()
        path = self.dir / key[:2] / f"{key}.json"
        if path.exists():
            return Completion(**json.loads(path.read_text(encoding="utf-8")))
        c = self.inner.complete(system, user, max_tokens, temperature)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(c), ensure_ascii=False), encoding="utf-8")
        return c


def parse_json(text: str) -> dict | list | None:
    """The JSON value in a model answer: models wrap it in ```json fences or add a
    sentence before it, and reasoning models may prefix a <think> block."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    m = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.DOTALL)
    if m:
        text = m.group(1)
    starts = [i for i in (text.find("{"), text.find("[")) if i >= 0]
    if not starts:
        return None
    try:
        value, _ = json.JSONDecoder().raw_decode(text[min(starts) :])
        return value
    except json.JSONDecodeError:
        return None
