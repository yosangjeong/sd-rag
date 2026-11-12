# sd-rag: retrieval-augmented search over Korean and US labor law

A RAG system on AWS: upload many PDF / DOCX / HWPX files (scans included), then ask
questions in Korean or English and get answers that cite the document and the place
(article, section, page) they come from. The public corpus is 53 statutes and
regulations (Korean labor acts with their decrees and rules; US Code, CFR, Federal
Register), and each user's uploads are searched only for that user.

The focus is retrieval accuracy, measured on a 338-question held-out set plus 137
real user questions (`data/eval/`).

## How it works

```
upload -> S3 -> SQS -> worker: parse (OCR for scans) -> chunk -> embed -> OpenSearch
question -> translate to the other language -> BM25 + vector search for both
         -> fuse (RRF) -> LLM rerank -> answer with [n] citations
         (or: an agent chooses keyword / vector / filtered searches itself)
```

| Part | Choice | Why (details in `docs/decisions.md`) |
|---|---|---|
| Parsing | pypdf + pdfplumber (tables, columns), HWPX/DOCX XML | measured against HWPX ground truth |
| OCR | Qwen3-VL 235B on Bedrock | CER 0.4-2.3% Korean on synthetic scans |
| Chunks | one per article / section, split at paragraph > item > line | beats fixed windows on every slice |
| Embeddings | Titan Text Embeddings v2 | far ahead across languages |
| Search | OpenSearch (nori + English analyzers, HNSW) | hybrid BM25 + dense |
| Cross-lingual | query translation | ko->en hit@10 0.62 -> 0.85 (dev) |
| Reranker | GLM-4.7 listwise | MRR 0.51 -> 0.81 (dev) |
| Answers / agent | GLM-4.7 (in-Region, tool use) | fast; no cross-Region inference |

## Repository

| Path | What |
|---|---|
| `backend/src/sdrag/` | API (FastAPI), worker, ingestion, retrieval, agent |
| `frontend/` | React (Vite) single page |
| `infra/` | AWS CDK (Python): network, data, app, CI/CD stacks |
| `eval/` | evaluation set builder, retrieval runner, benchmarks |
| `data/` | manifest, sources and licenses, evaluation set and results |
| `docs/` | decisions, design, operations (logs) |

## Run locally

```bash
infra/local/opensearch/up.sh                       # OpenSearch 3.7 with nori on :9200
cd backend && uv sync
AWS_PROFILE=<profile> SDRAG_OCR_CACHE_DIR=../data/raw/ocr-cache SDRAG_EMBED_CACHE_DIR=../data/raw/embed-cache \
  uv run python -m sdrag.ingest.pipeline --strategy structure --recreate   # index the corpus
AWS_PROFILE=<profile> uv run uvicorn sdrag.api.main:app --port 8000      # API (auth_mode=dev)
cd ../frontend && npm ci && npm run dev                                  # http://localhost:5173
```

The corpus files are downloaded by `data/scripts/fetch.py` (sources and licenses:
`data/SOURCES.md`).

## Evaluate

```bash
cd backend
AWS_PROFILE=<profile> uv run python ../eval/run_retrieval.py --set ../data/eval/test.jsonl \
  --systems hybrid@chunks-structure bilingual+rerank@chunks-structure agent+rerank@chunks-structure
```

Results per question and summaries by language and file type: `data/eval/results/`.
How the set was built and scored: `data/eval/README.md`.
