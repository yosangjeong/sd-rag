# sd-rag: retrieval-augmented search over Korean and US labor and real-estate law

A RAG system on AWS: upload many PDF / DOCX / HWPX files (scans included), then ask
questions in Korean or English and get answers that cite the document and the place
(article, section, page) they come from. The public corpus is 70 statutes and
regulations (Korean labor and real-estate acts with their decrees and rules; US Code,
CFR, Federal Register), and each user's uploads are searched only for that user.

The focus is retrieval accuracy, measured on held-out sets that were never used for
tuning (`data/eval/`). hit@10 / MRR of the served system against plain hybrid search:

| Set | Questions | Served | Hybrid (BM25 + vectors) |
|---|---|---|---|
| Labor, generated (test) | 338 | **0.95 / 0.88** | 0.78 / 0.53 |
| Labor, real user questions (government FAQs) | 137 | **0.95 / 0.89** | 0.89 / 0.60 |
| Real estate, generated (test) | 82 | **0.98 / 0.91** | 0.84 / 0.57 |
| Real estate, real user questions | 83 | **0.87 / 0.83** (agent mode 0.95 / 0.86) | 0.75 / 0.51 |

Answers (automatic judge, a lower bound): 72-77% correct over two runs of the same system,
91% cite the gold passage (real estate 76%, 93%); unanswerable questions declined 67%
(real estate 93%); the other country's law cited 0 times. How far the judge can be
trusted, and every choice behind these numbers: `docs/decisions.md`.

## For evaluators

- **Service**: <URL, filled in at deployment> - up from submission to 2026-12-07 and on
  the interview day. **Accounts** are in the submission e-mail: two evaluator accounts
  (with the log viewer) and one regular account (without it), so isolation between
  users and the log permission can both be checked.
- **Five minutes to try**:
  1. Sign in, click an example question; the answer cites its sources by number, and
     clicking `[n]` opens the passage (statute > article, page).
  2. Ask in English about Korean law, or in Korean about US law (cross-lingual search).
  3. Upload several PDF / DOCX / HWPX files at once (scans are OCR'd; progress is shown),
     then ask about them or pick "이 문서에 질문" to search one file only.
  4. Switch to **에이전트** (agent mode): the model rewrites the query and picks keyword,
     vector or filtered searches itself; the number of searches is shown.
  5. Sign in with the other account: the first account's uploads and conversations are
     not there.
- **Logs** (`docs/operations.md`): evaluator accounts see **로그 보기 (평가자)** in the
  sidebar: fixed queries over the service logs (requests, questions, retrieval results,
  tool calls, errors, latency and tokens, uploads, the audit trail of searches and
  opened sources), or every step of one request by its `x-request-id`. Personal data
  and secrets are masked before anything is written.
- **Reading order**: `docs/design.md` (architecture, security incl. prompt injection,
  logging, limitations), `docs/decisions.md` (every decision with its measurement),
  `data/eval/README.md` (how the evaluation sets were built and scored, judge models
  and prompts), `eval/README.md` (what each evaluation script does), results per
  question in `data/eval/results/`.

## How it works

```
upload -> S3 -> SQS -> worker: parse (OCR for scans) -> chunk -> embed -> OpenSearch
question -> which country's law (KR / US / none): the other country's statutes are left out
         -> BM25 + vector search (RRF), top 20; same for its translation, +10 more
         -> LLM rerank -> answer with [n] citations
         (or: an agent chooses keyword / vector / filtered searches itself)
```

| Part | Choice | Why (details in `docs/decisions.md`) |
|---|---|---|
| Parsing | pypdf + pdfplumber (tables, columns), HWPX/DOCX XML | measured against HWPX ground truth |
| OCR | Qwen3-VL 235B on Bedrock | CER 0.4-2.3% Korean on synthetic scans |
| Chunks | one per article / section, split at paragraph > item > line | beats fixed windows on every slice |
| Embeddings | Titan Text Embeddings v2 | far ahead across languages |
| Search | OpenSearch (nori + English analyzers, HNSW) | hybrid BM25 + dense |
| Cross-lingual | query translation, candidates added | test ko->en hit@10 0.47 -> 0.90 |
| Reranker | GLM-4.7 listwise | test MRR 0.53 -> 0.80 on hybrid |
| Answers / agent | GLM-4.7 (in-Region, tool use) | fast; no cross-Region inference |

## Repository

| Path | What |
|---|---|
| `backend/src/sdrag/` | API (FastAPI), worker, ingestion, retrieval, agent |
| `frontend/` | React (Vite) single page |
| `infra/` | AWS CDK (Python): network, data, app, CI/CD stacks |
| `eval/` | evaluation set builder, retrieval and answer runners, benchmarks (`eval/README.md`) |
| `data/` | manifest, sources and licenses, the corpus (`data/corpus/`), evaluation set and results; downloads and caches in `data/raw/` (not committed, layout in `backend/src/sdrag/ingest/layout.py`) |
| `docs/` | decisions, design, operations (logs) |

## Run locally

```bash
infra/local/opensearch/up.sh                       # OpenSearch 3.7 with nori on :9200
cd backend && uv sync
AWS_PROFILE=<profile> SDRAG_OCR_CACHE_DIR=../data/raw/cache/ocr SDRAG_EMBED_CACHE_DIR=../data/raw/cache/embed \
  uv run python -m sdrag.ingest.pipeline --strategy structure --recreate   # index the corpus
AWS_PROFILE=<profile> uv run uvicorn sdrag.api.main:app --port 8000      # API (auth_mode=dev)
cd ../frontend && npm ci && npm run dev                                  # http://localhost:5173
```

The corpus files are downloaded by `data/scripts/fetch.py` (sources and licenses:
`data/SOURCES.md`).

## Deploy (AWS, one Region: ap-southeast-2)

```bash
cd frontend && npm ci && npm run build && cd ../infra && npm ci && uv sync
AWS_PROFILE=<profile> npx cdk deploy SdRag-Network SdRag-Data SdRag-App \
  --outputs-file ../data/raw/deploy/cdk-outputs.json        # about 30 min the first time
cd .. && AWS_PROFILE=<profile> infra/scripts/after_deploy.sh corpus   # index the corpus inside the VPC
AWS_PROFILE=<profile> infra/scripts/after_deploy.sh user <email> evaluator   # an evaluator account
```

`SdRag-CiCd` (GitHub OIDC roles) is deployed once by hand; its outputs go to the
repository variables `DEPLOY_ROLE_ARN`, `EVAL_ROLE_ARN` and `CORPUS_BUCKET`, after which
pushes to `main` deploy and retrieval changes are gated on the dev sets. Behind a
TLS-inspecting proxy, set `SDRAG_BUILD_CA` to its CA for the image build.

## Evaluate

```bash
cd backend
AWS_PROFILE=<profile> uv run python ../eval/run_retrieval.py --set ../data/eval/test.jsonl \
  --systems hybrid@chunks-structure bilingual_union+rerank+jur@chunks-structure agent+rerank@chunks-structure
```

Results per question and summaries by language and file type: `data/eval/results/`
(layout in `data/eval/results/README.md`).
How the set was built and scored: `data/eval/README.md`.
