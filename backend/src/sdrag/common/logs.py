"""Structured logs: one JSON object per line on stdout, masked.

ECS ships stdout to CloudWatch Logs (awslogs driver), where CloudWatch Logs Insights
queries the JSON fields directly (docs/operations.md lists the queries). Each request
logs one ``event`` record per step: request, retrieval (results), tool calls,
answer, error, plus latency, tokens and cost; an ``audit`` record says who searched
or opened which document.

Masking: free text a user writes (questions, file names) can carry personal data
and secrets. Before a record is written, every string value is passed through
``mask``: e-mail addresses, Korean resident registration numbers, phone numbers,
card-like digit runs, AWS access keys, API keys, bearer tokens and key=value secrets
(password=..., api_key: ...) are replaced by a tag.
User ids are logged as a short hash, not as the Cognito id itself.
"""

import hashlib
import json
import re
import sys
import time
from typing import Any

# Digit runs are bounded by "not a digit" rather than \b: Hangul counts as a word
# character, so "010-1234-5678입니다" has no word boundary after the 8.
_ND, _NA = r"(?<!\d)", r"(?!\d)"
PATTERNS = [
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "<email>"),
    (re.compile(_ND + r"\d{6}\s*-\s*[1-8]\d{6}" + _NA), "<rrn>"),  # 주민등록번호
    (
        re.compile(r"(?:\+82[-\s.]?|" + _ND + r"0)1[016789][-\s.]?\d{3,4}[-\s.]?\d{4}" + _NA),
        "<phone>",
    ),
    # landlines: 02-123-4567, 031-123-4567 (separators required: statute numbers are not)
    (
        re.compile(r"(?:\+82[-\s.]?|" + _ND + r"0)(?:2|[3-6][1-5])[-.)]\s?\d{3,4}[-.]\d{4}" + _NA),
        "<phone>",
    ),
    # cards: 4-digit groups with one separator style (a table row of single digits is not)
    (re.compile(_ND + r"\d{4}([ -]?)\d{4}\1\d{4}\1\d{1,7}" + _NA), "<card>"),
    (re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"), "<aws-key>"),
    (re.compile(r"(?i)bearer\s+[\w\-.~+/]+=*"), "Bearer <token>"),
    (re.compile(r"\beyJ[\w-]+\.[\w-]+\.[\w-]+"), "<jwt>"),
    (re.compile(r"\bsk-[A-Za-z0-9_-]{16,}"), "<api-key>"),
    # key=value secrets: password=..., "secret": "...", aws_secret_access_key = ...
    (
        re.compile(
            r"(?i)(?<![a-z])(password|passwd|pwd|secret|api[_-]?key|access[_-]?key|token|비밀번호)"
            r"(\w*[\"']?\s*[:=]\s*[\"']?)[^\s\"',}]+"
        ),
        r"\1\2<secret>",
    ),
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
