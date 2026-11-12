"""Structured logs: one JSON object per line on stdout, masked.

ECS ships stdout to CloudWatch Logs (awslogs driver), where CloudWatch Logs Insights
queries the JSON fields directly (docs/operations.md lists the queries). Each request
logs one ``event`` record per step: request, retrieval (results), tool calls,
answer, error, plus latency, tokens and cost; an ``audit`` record says who searched
or opened which document.

Masking: free text a user writes (questions, file names) can carry personal data
and secrets. Before a record is written, every string value is passed through
``mask``: e-mail addresses, Korean resident registration numbers, phone numbers,
card-like digit runs, AWS access keys and bearer tokens are replaced by a tag.
User ids are logged as a short hash, not as the Cognito id itself.
"""

import hashlib
import json
import re
import sys
import time
from typing import Any

PATTERNS = [
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "<email>"),
    (re.compile(r"\b\d{6}\s*-\s*[1-8]\d{6}\b"), "<rrn>"),  # 주민등록번호
    (re.compile(r"\b01[016789][-\s]?\d{3,4}[-\s]?\d{4}\b"), "<phone>"),
    (re.compile(r"\b(?:\d[ -]?){13,19}\b"), "<card>"),
    (re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"), "<aws-key>"),
    (re.compile(r"(?i)bearer\s+[\w\-.~+/]+=*"), "Bearer <token>"),
    (re.compile(r"\beyJ[\w-]+\.[\w-]+\.[\w-]+"), "<jwt>"),
]


def mask(text: str) -> str:
    for pat, tag in PATTERNS:
        text = pat.sub(tag, text)
    return text


def _masked(value: Any) -> Any:
    if isinstance(value, str):
        return mask(value)
    if isinstance(value, dict):
        return {k: _masked(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_masked(v) for v in value]
    return value


def user_hash(user_id: str) -> str:
    return hashlib.sha256(user_id.encode()).hexdigest()[:12]


def log(event: str, **fields: Any) -> None:
    record = {"ts": round(time.time(), 3), "event": event, **_masked(fields)}
    sys.stdout.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
    sys.stdout.flush()
