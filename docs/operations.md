# Operations: logs, costs, audit

## Where the logs are

Both services write one JSON object per line to stdout; ECS ships them to CloudWatch
Logs (14 days):

| Log group | What |
|---|---|
| `SdRag-App-ApiLogs...` (stack output `ApiLogGroup`) | API: requests, questions, retrieval, tool calls, answers, errors, audit |
| `SdRag-App-WorkerLogs...` (stack output `WorkerLogGroup`) | upload processing and the bulk corpus index |

**Evaluators: the app's log viewer.** Evaluator accounts are in the Cognito group
`evaluators`; for them the app shows "로그 보기 (평가자)", which runs fixed Logs
Insights queries (`backend/src/sdrag/api/logs_api.py`) over the API and worker logs:
recent requests, latency and tokens per mode, agent tool calls, errors, the audit
trail, upload processing, and every step of one request (by the `x-request-id` each
response carries). Nothing free-form is accepted. Opening the viewer is itself
audited. With console access, the same queries can be pasted into CloudWatch >
Logs Insights. Every record has `ts` and
`event`; records of one request share `request_id` (also returned to the browser in
the `x-request-id` header).

## Records (`backend/src/sdrag/common/logs.py`)

| event | fields |
|---|---|
| `request` | method, path, status, latency_ms |
| `question` | user (hash), mode, question (masked) |
| `tool_call` | tool, input (agent mode: each search the agent ran) |
| `retrieval` | mode, results (top 10 chunk and document ids) |
| `answer` | mode, latency_ms, llm_input_tokens, llm_output_tokens, cited |
| `error` | path, error |
| `upload`, `ingest` | accepted / rejected counts; per file: status, chunks, parse_s, embed_s, index_s |
| `audit` | action (search: documents an answer cited; view: a source opened), user, document |

**Masking.** Every string field is passed through `mask()` before it is written:
e-mail addresses, Korean resident registration numbers, phone numbers, card-like
digit runs, AWS access keys, bearer tokens and JWTs become tags (`<email>`, ...).
Users appear only as a 12-character hash of their Cognito id. Tokens, passwords and
document text are never logged.

## Logs Insights queries

Latency and cost per mode (LLM tokens; embedding tokens are ~20 per question):

```
filter event = "answer"
| stats count() as n, avg(latency_ms) as avg_ms, pct(latency_ms, 95) as p95_ms,
        avg(llm_input_tokens) as in_tok, avg(llm_output_tokens) as out_tok by mode
```

One request, every step:

```
filter request_id = "<id from the x-request-id header>"
| sort ts asc
| display ts, event, mode, tool, input.query, results.0.doc_id, latency_ms, error
```

What the agent did:

```
filter event = "tool_call" | stats count() by tool, input.method
```

Errors:

```
filter event = "error" or status >= 500 | sort ts desc | limit 50
```

Upload throughput (files per minute and seconds per stage):

```
filter event = "ingest"
| stats count() as files, sum(chunks) as chunks, avg(parse_s), avg(embed_s), avg(index_s),
        (max(ts) - min(ts)) / 60 as minutes by status
```

Audit trail (who searched or opened which document):

```
filter event = "audit" | sort ts desc | display ts, user, action, document, documents
```

## Cost per query

LLM prices are US list prices on demand (Sydney may be somewhat higher); see
`eval/run_retrieval.py` `PRICES`. The evaluation reports the measured cost per query
for every system (`data/eval/results/*/summary.md`).
