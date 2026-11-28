# sd-rag: retrieval-augmented search over Korean and US labor and real-estate law

> **한국어 요약 (평가자용, 5분)**
>
> - **무엇**: PDF·DOCX·HWPX(스캔 포함) 여러 개를 올리고 한국어나 영어로 물으면, 문서와 위치(조문·쪽)를
>   인용해 답하는 RAG 서비스입니다. 공개 코퍼스는 한국·미국 노동·부동산 법령 70건입니다. 업로드는 올린
>   사람만 검색합니다. AWS 한 리전(ap-southeast-2), ECS Fargate, OpenSearch, Bedrock으로 구성했습니다.
> - **접속**: 아래 "For evaluators"의 URL로 접속합니다. 계정은 제출 메일에 있습니다(평가자 2개는 로그 보기
>   가능, 일반 1개는 불가).
> - **써 보기**: 예시 질문 클릭 → 답의 `[n]`을 누르면 원문이 열립니다 → 영어로 한국 법을 묻기(교차 언어)
>   → 파일 여러 개 올리고 "이 문서에 질문" → 에이전트 모드 → 다른 계정으로 로그인해 격리 확인.
> - **핵심 숫자** (아래 표): 서비스 검색 hit@10 / MRR, 노동 시험 0.96 / 0.90, 실제 질문 0.98 / 0.90
>   (일반 hybrid 0.78 / 0.54). 11/14에 따로 모은 실제 질문 97개: 0.91 / 0.81 (두 번 쓰였고
>   일부는 개발셋과 정답 조문이 겹침, 본문 참조). 답변 정확도 (자동 채점, 하한, 11/14 답변 버전) 노동 87%, 부동산 89%. 파일 하나 기준 같은 20문항에서 Claude·ChatGPT와 같은 수준.
> - **어디를 읽나**: 설계·보안·한계 `docs/design.md` → 결정과 근거(측정 포함) `docs/decisions.md` →
>   평가 방법·채점 모델과 프롬프트 `data/eval/README.md` → 문항별 결과 `data/eval/results/`.
>   로그 조회 방법은 `docs/operations.md`.

A RAG system on AWS: upload many PDF / DOCX / HWPX files (scans included), then ask
questions in Korean or English and get answers that cite the document and the place
(article, section, page) they come from. The public corpus is 70 statutes and
regulations (Korean labor and real-estate acts with their decrees and rules; US Code,
CFR, Federal Register), and each user's uploads are searched only for that user.

The focus is retrieval accuracy (`data/eval/`). Choices were made on the dev sets; the
test sets below were kept apart from them, but they are not untouched: their results were
read and their errors analysed after each measurement, a few decisions were checked on
them too, and the answer versions were compared on a fixed sample of the labor test set
(`docs/decisions.md`). A set made after the last retrieval change, 374 questions over articles no other set uses, is
scored once on the final deploy (`data/eval/fresh_test.jsonl`, rules in `docs/decisions.md`).
Until then, the closest to held-out is the set of real questions collected on 11-14 after the
retrieval changes of that day (below: hit@10 0.91, MRR 0.81). It is not clean: it was used
twice (the second time to reject doc2query), 5 of its questions were re-run after the 11/27
OCR clean-up, retrieval changed after it (11-16 to 11-28), and 9 of its 33 answerable
questions have a gold passage that a tuning-set question also has (served 1.00 / 1.00 on
those 9, 0.875 / 0.74 on the other 24). hit@10 / MRR of
the served system against plain hybrid search (gold spans pooled from every reported
system's top 5, TREC-style, `eval/repool.py`):

| Set | Questions | Served | Hybrid (BM25 + vectors) |
|---|---|---|---|
| Labor, generated (test) | 338 | **0.96 / 0.90** | 0.78 / 0.54 |
| Labor, real user questions (government FAQs) | 137 | **0.98 / 0.90** | 0.89 / 0.60 |
| Real estate, generated (test) | 82 | **0.99 / 0.94** | 0.85 / 0.58 |
| Real estate, real user questions | 83 | **0.95 / 0.93** (agent mode 0.99 / 0.93) | 0.76 / 0.52 |

On documents it was never built or tuned on (press releases incl. HWPX and a scan, a NIST
framework, an IRS guide; uploaded as a user, 35 questions): hit@5 1.00, MRR 0.87, against
hybrid 0.63 / 0.54 (`eval/unseen.py`). Among 35 look-alike press releases of one ministry
(60 questions) it put the right release first 59 times (hybrid 48), MRR 0.88 against 0.65.

On 97 real questions collected on 11-14 (easylaw topics no other set uses, the HUD/DOJ
accommodations statement; used twice, and 9 share a gold passage with tuning questions, above): on the 33 the
corpus answers, hit@10 0.91, MRR 0.81, against hybrid 0.73 / 0.53; of the 64 it cannot
answer, 78% were declined.

Answers (automatic judge, a lower bound; answer version v11 of 11-14, before the later
answer-prompt changes: scope rule, dates and digits, yes/no; re-measured at the final deploy):
87% correct on labor, 89% on real estate (judge v3,
which also reads the cited sources; the stricter v2 gave 78% / 77%); 96% / 98% cite the gold
passage; questions the corpus cannot answer declined 67% / 90%; on the 27 unanswerable labor
questions where answers used to cite the other country's law (9 before the country filter),
0 do. Every period, ratio and amount with a unit in an answer is checked against the cited
sources before it is shown (bare numbers and dates are not). By slice (judge v3,
`data/eval/results/answers/v11-final/slices.md`): Korean questions 90% / 90% (labor / real
estate), English 84% / 88%; by file type the lowest is labor scans, 74% (23 questions).

Uploads (`data/eval/results/upload/upload.md`): 53 files in one request were done in 154 s
locally (20.7 files/min) and 429 s on AWS (7.4 files/min, the worker starting from zero);
a run with 70 files finished 63, the other 7 failed on a busy search node, which led to
retries and two workers at most; with those, the second rehearsal (2026-11-26) finished all
70 in 830 s (5.1 files/min, 78 scanned pages OCR'd). It is measured again on the final deployment.

On one uploaded file, against Claude (Sonnet 5.5) and ChatGPT (GPT-6) on the same 20
questions (2026-11-16, references checked against the statutes, every non-correct grade
re-read against the statutes by Claude Code, not blind, each change with its rule): ours 19 correct and 1 partial (served code), Claude 20, ChatGPT 19 and 1 wrong;
with 20 questions these are level (`data/eval/single_file/README.md`). How far the judge can be
trusted, and every choice behind these numbers: `docs/decisions.md`.

### Ablations (the brief's comparisons)

Labor test set (338 generated questions, choices made on dev; pooled gold), retrieval only.
Latency p50 and LLM cost per query (query embeddings, about $0.00001, not counted):

| Chunking | Search | hit@1 | hit@10 | MRR | nDCG@10 | p50 | $/query |
|---|---|---|---|---|---|---|---|
| fixed windows | BM25 | 0.37 | 0.57 | 0.44 | 0.47 | <0.1 s | 0 |
| fixed windows | dense | 0.41 | 0.76 | 0.53 | 0.58 | 0.3 s | 0 |
| fixed windows | hybrid | 0.42 | 0.76 | 0.54 | 0.58 | 0.3 s | 0 |
| per article | BM25 | 0.34 | 0.57 | 0.42 | 0.46 | <0.1 s | 0 |
| per article | dense | 0.46 | 0.79 | 0.58 | 0.63 | 0.3 s | 0 |
| per article | hybrid | 0.42 | 0.78 | 0.54 | 0.59 | 0.3 s | 0 |
| per article | hybrid + reranker | 0.78 | 0.85 | 0.81 | 0.82 | 1.5 s | 0.004 |
| per article | + translation candidates | 0.85 | 0.93 | 0.89 | 0.90 | 3.0 s | 0.006 |
| per article | **served** (+ wider pool, jurisdiction) | **0.85** | **0.96** | **0.90** | **0.91** | 5.7 s | 0.012 |

Fixed windows are 400 tokens with a 60-token overlap, per-article chunks at most 500, so the
two rows differ in size as well as in where they cut. The gold spans added by re-pooling
(`eval/repool.py`) came from four systems (served now and before, hybrid, agent), not from
the fixed windows, which favors the pooled systems slightly; the first pool included them.

Agent against the basic (served) search, real-estate sets (the agent was measured there):

| Set | System | hit@1 | hit@10 | MRR | p50 | $/query |
|---|---|---|---|---|---|---|
| test_re (82) | basic | 0.91 | 0.99 | 0.94 | 5.6 s | 0.012 |
| | agent + reranker (until 2026-11-16) | 0.87 | 0.99 | 0.92 | 5.0 s | 0.016 |
| | **agent on the wide pool** (served agent mode) | 0.90 | 0.99 | 0.94 | 8.8 s | 0.026 |
| real_re (83 real questions) | basic | 0.92 | 0.95 | 0.93 | 5.7 s | 0.012 |
| | agent + reranker (until 2026-11-16) | 0.86 | 0.95 | 0.88 | 9.6 s | 0.023 |
| | **agent on the wide pool** (served agent mode) | 0.90 | **0.99** | 0.93 | 12.4 s | 0.032 |

The agent mode now starts from the basic mode's candidate pool and adds what its own
searches find (`agent/search.with_pool`): it finds more on real questions, ranks about the
same, at twice the time, so the basic mode is the default (`docs/decisions.md`, Overnight 2026-11-16).

The agent is kept as a mode, not the default: it costs more and ranks no better.

### By language and file type (labor test set, hit@10 / MRR)

| Slice | n | hybrid | served |
|---|---|---|---|
| Korean question -> Korean document | 155 | 0.91 / 0.69 | 0.97 / 0.92 |
| Korean -> English | 49 | 0.47 / 0.12 | 0.94 / 0.87 |
| English -> English | 68 | 0.97 / 0.79 | 0.99 / 0.91 |
| English -> Korean | 66 | 0.53 / 0.23 | 0.94 / 0.88 |
| text PDF | 160 | 0.78 / 0.54 | 0.97 / 0.91 |
| HWPX | 58 | 0.78 / 0.54 | 0.93 / 0.91 |
| DOCX | 57 | 0.82 / 0.60 | 1.00 / 0.90 |
| scanned PDF (OCR) | 54 | 0.72 / 0.44 | 0.93 / 0.83 |
| answer in a table | 36 | 0.75 / 0.43 | 0.94 / 0.88 |

Every set and slice: `data/eval/results/retrieval-70docs/<set>/summary.md`.

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
         -> BM25 + vector search (RRF), top 20; same for its translation, +10 more;
            each list's own top 5; decree / rule articles citing the law articles found;
            the question in statute terms; definition articles
         -> LLM rerank -> answer with [n] citations
         (or: an agent chooses keyword / vector / filtered searches itself)
```

| Part | Choice | Why (details in `docs/decisions.md`) |
|---|---|---|
| Parsing | pypdf + pdfplumber (tables, columns), HWPX/DOCX XML | measured against HWPX ground truth |
| OCR | Qwen3-VL 235B on Bedrock, checked by Amazon Textract | CER 0.4-2.3% Korean on synthetic office-quality scans (2.8% body text on the poor profile); 1.1% on a real iPhone scan (2.8% before the `<br>` it writes in table cells was cleaned) |
| Chunks | one per article / section, split at paragraph > item > line | ahead of fixed windows with vectors and in the served system (hit@10 0.94 vs 0.92); level with BM25 alone; citations name one article |
| Embeddings | Titan Text Embeddings v2 | far ahead across languages |
| Search | OpenSearch (nori + English analyzers, HNSW) | hybrid BM25 + dense |
| Cross-lingual | query translation, candidates added | test ko->en hit@10 0.47 (hybrid) -> 0.94 (served) |
| Reranker | GLM-4.7 listwise | test MRR 0.54 -> 0.81 on hybrid |
| Answers / agent | GLM-4.7 (in-Region, tool use) | fast; 6 other in-Region models no clearly better (decisions.md) |

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
AWS_PROFILE=<profile> npx cdk deploy SdRag-Network SdRag-Data SdRag-App   # about 30 min the first time
cd .. && AWS_PROFILE=<profile> infra/scripts/after_deploy.sh corpus   # index the corpus inside the VPC
AWS_PROFILE=<profile> infra/scripts/after_deploy.sh user <email> evaluator   # an evaluator account
```

The scripts read the stack outputs from CloudFormation, so they work the same after a
deploy by CI/CD. `SdRag-CiCd` (GitHub OIDC roles) is deployed by hand (it also deploys
the network and data stacks it depends on: the eval role reads the corpus bucket); its
outputs and the bucket name go to the repository variables `DEPLOY_ROLE_ARN`,
`EVAL_ROLE_ARN` and `CORPUS_BUCKET`, after which pushes to `main` deploy, and a change to
parsing, chunking or retrieval is scored on the dev sets (`.github/workflows/eval.yml`,
`eval/gate.py`): on a pull request before it is merged, and on a push to `main` after it
(the deploy does not wait for that run; a red run means a revert). The roles trust GitHub's immutable subject for this
repository (`repo:<owner>@<id>/<repo>@<id>:...`, see `gh api
repos/<owner>/<repo>/actions/oidc/customization/sub`). Behind a TLS-inspecting proxy, set
`SDRAG_BUILD_CA` to its CA for the image build.

## Evaluate

```bash
cd backend
AWS_PROFILE=<profile> uv run python ../eval/run_retrieval.py --set ../data/eval/test.jsonl \
  --systems hybrid@chunks-structure wide+rerank+jur@chunks-structure agent+rerank@chunks-structure
```

Results per question and summaries by language and file type: `data/eval/results/`
(layout in `data/eval/results/README.md`).
How the set was built and scored: `data/eval/README.md`.
