# sd-rag: retrieval-augmented search over Korean and US labor and real-estate law

A RAG system on AWS: upload many PDF / DOCX / HWPX files (scans included), then ask
questions in Korean or English and get answers that cite the document and the place
(article, section, page) they come from. The public corpus is 70 statutes and
regulations (Korean labor and real-estate acts with their decrees and rules; US Code,
CFR, Federal Register), and each user's uploads are searched only for that user.

The focus is retrieval accuracy, measured on held-out sets (`data/eval/`): 338
generated labor-law questions, 137 real labor questions, 82 generated and 83 real
real-estate questions (the last: hit@10 / MRR 0.87 / 0.83 served, 0.95 / 0.86 agent).
hit@10 / MRR: 0.94 / 0.88, 0.94 / 0.90 and 0.98 / 0.91, against 0.78 / 0.53,
0.89 / 0.60 and 0.84 / 0.57 for plain hybrid search (`docs/decisions.md`). Answers:
77% correct, 92% cite the gold passage (real estate: 74%, 95%), 63% of unanswerable
questions declined.

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
