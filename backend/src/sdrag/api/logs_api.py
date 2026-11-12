"""Log viewer for evaluators: fixed CloudWatch Logs Insights queries, nothing free-form.

The brief asks that evaluators can check the logs; they have no access to our AWS
project, so the app runs the queries for members of the "evaluators" group. Only the
presets below run (a request id is the only parameter, checked as hex), over the
last `minutes`, on the API and worker log groups. Records are already masked
(common/logs.py); users appear as hashes.

Locally (no log groups configured) the same presets run over the JSON lines in
settings.local_log_file.
"""

import json
import re
import statistics
import time
from collections import Counter, defaultdict
from pathlib import Path

import boto3

from sdrag.common.config import settings

PRESETS = {
    "recent": "fields @timestamp, event, request_id, mode, status, path, latency_ms, question, error"
              " | filter event in ['request', 'question', 'answer', 'error'] | sort @timestamp desc | limit 100",
    "latency_cost": "filter event = 'answer' | stats count() as n, avg(latency_ms) as avg_ms,"
                    " pct(latency_ms, 95) as p95_ms, avg(llm_input_tokens) as input_tokens,"
                    " avg(llm_output_tokens) as output_tokens by mode",
    "tool_calls": "filter event = 'tool_call' | stats count() as n by tool",
    "errors": "fields @timestamp, request_id, path, status, error"
              " | filter event = 'error' or status >= 500 | sort @timestamp desc | limit 50",
    "audit": "fields @timestamp, user, action, document, documents, chunk"
             " | filter event = 'audit' | sort @timestamp desc | limit 100",
    "ingest": "fields @timestamp, doc_id, status, chunks, file_type, ocr_pages, parse_s, embed_s, index_s, error"
              " | filter event = 'ingest' | sort @timestamp desc | limit 100",
    "request": "fields @timestamp, event, mode, tool, input.query, input.method, results.0.doc_id, latency_ms, error"
               " | filter request_id = '{rid}' | sort @timestamp asc",
}  # fmt: skip
RE_RID = re.compile(r"^[0-9a-f]{6,32}$")


def query(preset: str, minutes: int = 60, rid: str = "") -> list[dict]:
    if preset not in PRESETS:
        raise ValueError("unknown preset")
    if preset == "request" and not RE_RID.match(rid):
        raise ValueError("request id must be hex")
    minutes = max(1, min(minutes, 7 * 24 * 60))
    if not settings.log_groups:
        return _local(preset, minutes, rid)
    logs = boto3.client("logs", region_name=settings.aws_region)
    end = int(time.time())
    q = logs.start_query(logGroupNames=settings.log_groups.split(","), startTime=end - 60 * minutes,
                         endTime=end, queryString=PRESETS[preset].format(rid=rid), limit=200)  # fmt: skip
    for _ in range(60):  # Insights queries finish in seconds at this volume
        r = logs.get_query_results(queryId=q["queryId"])
        if r["status"] in ("Complete", "Failed", "Cancelled", "Timeout"):
            break
        time.sleep(0.5)
    return [
        {f["field"]: f["value"] for f in row if f["field"] != "@ptr"}
        for row in r.get("results", [])
    ]


def _local(preset: str, minutes: int, rid: str) -> list[dict]:
    """The presets over the local log file (the API's stdout redirected to it)."""
    path = Path(settings.local_log_file)
    since = time.time() - 60 * minutes
    recs = []
    for line in path.read_text("utf-8").splitlines() if path.exists() else []:
        if line.startswith("{"):
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("ts", 0) >= since:
                recs.append(r)
    pick = {"recent": lambda r: r["event"] in ("request", "question", "answer", "error"),
            "errors": lambda r: r["event"] == "error" or r.get("status", 0) >= 500,
            "audit": lambda r: r["event"] == "audit", "ingest": lambda r: r["event"] == "ingest",
            "request": lambda r: r.get("request_id") == rid}  # fmt: skip
    if preset in pick:
        out = [r for r in recs if pick[preset](r)]
        return out if preset == "request" else out[::-1][:100]
    if preset == "tool_calls":
        return [
            {"tool": k, "n": v}
            for k, v in Counter(r["tool"] for r in recs if r["event"] == "tool_call").items()
        ]
    by = defaultdict(list)
    for r in recs:
        if r["event"] == "answer":
            by[r["mode"]].append(r)
    return [{"mode": m, "n": len(rs), "avg_ms": round(statistics.mean(r["latency_ms"] for r in rs)),
             "input_tokens": round(statistics.mean(r["llm_input_tokens"] for r in rs)),
             "output_tokens": round(statistics.mean(r["llm_output_tokens"] for r in rs))}
            for m, rs in by.items()]  # fmt: skip
