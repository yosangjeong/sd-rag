# Key decisions and their evidence

Each entry: what was decided, what else was considered, and the measurement behind it.
Scripts named here are in the repository; their raw outputs are kept under
`data/raw/` (not committed).

## Data

**Two fields of law, Korean and US: labor and employment first, real estate added.**
70 documents. Labor (the first corpus, 53): 42 Korean statutes (14 acts x act /
enforcement decree / enforcement rule) and 11 US documents (US Code, CFR, Federal
Register). Real estate (added 2026-11-13, 17): 13 Korean (공인중개사법, 부동산
거래신고법, 부동산 가격공시법 with decrees and rules, 주택·상가건물 임대차보호법 with
decrees) and 4 US (Fair Housing Act, RESPA, 24 CFR 100, Regulation X); see "Real-estate
statutes" below. One field at first gave hard distractors (the same topic in several
statutes and in both languages) and kept evaluation authoring tractable; the second
field checks that nothing was tuned to labor law and that unrelated documents do not
crowd out the answers. The labor evaluation sets stay frozen; the real-estate ones
are separate (`data/eval/README.md`). Licenses: Korean statutes are not protected (Copyright Act art. 7); US
federal works are public domain (17 U.S.C. 105). Rejected: employer documents (the
brief forbids real company data) and KLRI English translations (redistribution
forbidden). See `data/SOURCES.md`.

**File formats rotate across statutes** (`data/kr_families.csv`): each statute is
served as PDF, HWPX or DOCX, so every format is exercised on the same kind of text.
law.go.kr gives annexes as separate HWP files; `data/scripts/build_kr.py` converts
them (hwp2hwpx), merges them into one HWPX and generates the DOCX, verifying that the
text and table count survive.

**Hashes pin the downloaded file, not derived ones.** Merged HWPX and generated DOCX
differ byte-wise on every build (zip timestamps); they are verified by content
instead. Source integrity and conversion correctness are separate checks.

**Scanned PDFs are synthetic.** The brief requires scanned PDFs; seven corpus documents
(four labor, 34 pages; three real-estate, 44 pages; Korean and English, with tables)
are served only as image-only scans made
by `data/scripts/make_scans.py` (skew, blur, noise, JPEG), so the source text is the
OCR ground truth and no statute is indexed twice. One real English scan
(Federal Register 1938) is kept. A real Korean scan (the 1953 gazette) was dropped:
not required, and an extreme case (vertical text, hanja). Limitation: no real Korean
scan.

## Parsing (`backend/src/sdrag/ingest/parse.py`)

**Structure, not pages, is the citation unit for HWPX/DOCX**, which have no fixed
pages: every block carries the article / annex / section heading (제23조(...),
[별표 3], § 541.100 ...), and PDFs also carry the page.

**PDF text from pypdf, PDF tables from pdfplumber.** pypdf keeps the reading order of
two-column pages; pdfplumber finds ruled tables but reads two-column text across the
columns. Pages with tables use pdfplumber, cut into columns at detected gutters.
Against the HWPX edition of two annex-heavy statutes (`eval/pdf_tables.py`): table
content inside table blocks 0% -> 95.7% / 67.1%, characters kept 100%.

**Running headers are removed by position and frequency**, with a stricter rule at
the page bottom: body text repeats there (fine-table cells, "[전문개정 ...]"),
which a looser rule deleted in testing.

**Korean PDF line wraps are re-joined from the document's own words.** 36% of
Hangul-Hangul wraps were spaces in the original (HWPX ground truth), so neither
"always space" nor "always join" works; a vocabulary of line-interior words decides.
Break accuracy 88% / 85%; Korean word match 92.5% -> 96.3% and 90.6% -> 95.2%
(`eval/pdf_spacing.py`).

## Chunking (`backend/src/sdrag/ingest/chunk.py`)

**Two strategies for the ablation**: `structure` (one chunk per article / annex /
section, long ones split at paragraph > item > line > sentence, tables by rows with
header rows repeated) and `fixed` (sliding windows). Both record character spans in
one canonical text, so evaluation answers are written once as (document, span) and
scored against either strategy.

**Sizes in estimated tokens, fitted to the embedding model's tokenizer.** A first
guess of 1 token per Hangul syllable undercounted Korean by a third (28% of Korean
chunks exceeded 512 real tokens). A least-squares fit of Titan v2's own counts gives
1.41 per syllable and 0.25 per other character; now actual/estimate is 0.99 at the
median.

## OCR (`backend/src/sdrag/ingest/ocr.py`)

**Qwen3-VL 235B on Bedrock**, in-region. Benchmark on 12 synthetic-scan pages at two
quality levels (`eval/ocr_bench.py`): CER Korean body 2.3%, Korean tables 0.4%,
English 2-column 3.9%, 3-column 7.1%, tables 9.0%; invented characters under 1%;
about 14 s and $0.005 per page. Nova Pro was rejected (repetition loops, content
filter). Textract (supports Korean, but needs the paid plan) and Claude (needs the
Anthropic use-case form) were not available to test; the engine sits behind one
interface (`OcrEngine`) and can be swapped.

**Two guards found by the benchmark**: the prompt asks for leader dots as "...",
since the model otherwise repeated dots until the token limit and lost the rest of
the page; and an answer cut by the token limit is re-read as two halves cut at the
blankest row. Measured on the corpus scans: Korean CER 1.2-2.6% against the digital
text. Known errors: 융자 read as 용자 throughout one statute; "·" where law.go.kr has
"ㆍ" (to be unified in search normalization).

## Embeddings

**Amazon Titan Text Embeddings v2 (1024 dims)**, decided 2026-11-12. Only models
callable in the project Region without cross-Region inference were compared (Cohere
Embed v4 is offered here only through a global profile). Development set
(`eval/embed_bench.py`, separate from the held-out evaluation set): 160 article and
section titles as queries, translated literally for the cross-lingual sets; 8,588
chunks of at most 350 tokens so that Cohere v3's 512-token input is not truncated.

| R@10 | ko->ko | ko->en | en->ko | en->en |
|---|---|---|---|---|
| Cohere Embed Multilingual v3 | 83.8% | 5.0% | 51.2% | 81.2% |
| Titan Text Embeddings v2 | 81.2% | 38.8% | 63.7% | 78.8% |
| ... searching only the answer language: Cohere | 83.8% | 61.3% | 65.0% | 81.2% |
| ... searching only the answer language: Titan | 81.2% | 62.5% | 67.5% | 80.0% |

Titan is far ahead across languages on the whole corpus and level within a language;
it takes 8,192 tokens (no constraint on chunk size), costs $0.026 per million tokens
(about a quarter of Cohere v3) and reports its token counts.

**Both models favor the query's language**: a Korean query puts Korean chunks in 74%
(Titan) to 97% (Cohere) of its top 10, and the corpus holds 4.5x more Korean than
English chunks. Restricting the search to the answer's language lifts ko->en from
38.8% to 62.5%. Retrieval will therefore search per language and merge the results
(to be compared in the ablation).

## Index and retrieval (`backend/src/sdrag/retrieval/`)

**OpenSearch, one document per chunk**, developed against a local OpenSearch 3.7
(the newest version AWS OpenSearch Service offers; `infra/local/opensearch/up.sh`).
BM25 runs on the embedding input (statute title > heading + text) through two
analyzers: Korean nori (morphemes, hanja read as hangul, particles dropped) and
English (stemmed); middle dots ㆍ · • become spaces, which also absorbs the OCR's
· for ㆍ. nori splits words our PDF clean-up wrongly joined
("동거하는친족만을" -> 동거/하/는/친족/만/을), which is why the spacing heuristic leans
to joining. Vectors: Lucene HNSW, cosine.

**Fusion by Reciprocal Rank Fusion, in application code**: ranks, not scores, so BM25
and cosine need no normalization, and the same code can merge per-language lists.

**Ingestion throughput (local, 2026-11-12)**: 53 documents, 6,499 chunks in 242 s
(13 documents per minute), 2.2M embedding tokens (about $0.06). Embedding calls take
most of the time; HWPX/DOCX parse in under 0.1 s, the 210-page PDF in 8 s.

**Retrieval as served: the question's hybrid top 20, plus up to 10 more from its
translation, reranked by GLM-4.7** (`Searcher.bilingual_union`, `service.py`).
Every choice was made on the dev set; the test and real sets were each scored once
per system (`data/eval/results/retrieval-53docs/`). hit@10 / MRR, span level:

| System | dev | test (338) | real (137) | test ko->en | test en->ko | p50 | $/query |
|---|---|---|---|---|---|---|---|
| BM25 | 0.51 / 0.39 | 0.58 / 0.42 | 0.77 / 0.49 | 0.00 | 0.02 | 0.0 s | 0 |
| dense | 0.82 / 0.56 | 0.79 / 0.58 | 0.83 / 0.59 | 0.59 | 0.64 | 0.3 s | 0 |
| hybrid (BM25 + dense, RRF) | 0.76 / 0.51 | 0.78 / 0.53 | 0.88 / 0.59 | 0.47 | 0.53 | 0.3 s | 0 |
| hybrid, fixed-size chunks | 0.78 / 0.47 | 0.75 / 0.53 | 0.86 / 0.53 | 0.41 | 0.44 | 0.3 s | 0 |
| per-language hybrid, fused | 0.76 / 0.45 | 0.78 / 0.47 | 0.75 / 0.42 | 0.53 | 0.58 | 0.3 s | 0 |
| hybrid + rerank | 0.85 / 0.81 | 0.84 / 0.80 | 0.95 / 0.89 | 0.59 | 0.64 | 1.4 s | 0.004 |
| translation, fused (bilingual) | 0.85 / 0.56 | 0.83 / 0.57 | 0.78 / 0.47 | 0.80 | 0.77 | 1.2 s | 0.0001 |
| translation, fused + rerank | 0.93 / 0.85 | 0.91 / 0.86 | 0.88 / 0.80 | 0.88 | 0.89 | 2.4 s | 0.004 |
| **translation, union + rerank** | **0.95 / 0.88** | **0.94 / 0.88** | **0.95 / 0.88** | **0.90** | **0.91** | 4.0 s | 0.006 |
| same, fixed-size chunks | | 0.92 / 0.86 | 0.94 / 0.86 | 0.82 | 0.86 | 3.3 s | 0.006 |
| agent | 0.92 / 0.81 | 0.89 / 0.74 | 0.93 / 0.74 | 0.88 | 0.82 | 6.1 s | 0.016 |
| agent + rerank | 0.92 / 0.86 | 0.91 / 0.83 | 0.96 / 0.87 | 0.92 | 0.85 | 6.0 s | 0.019 |

How the served configuration was reached:

- **Chunking**: structure chunks beat fixed windows in every configuration measured
  (hybrid test MRR equal, hit@10 0.78 vs 0.75; final system 0.94 vs 0.92).
- **Dense vs hybrid**: hybrid is best within a language (test en->en 0.97, ko->ko
  0.90), dense across languages, where BM25 scores 0: the cross-lingual problem.
- **Per-language fusion** (the earlier candidate) forces the other language into the
  results even when it holds no answer: worst of all on the real set (0.75); dropped.
- **Query translation** fixes BM25 across languages (test ko->en 0.47 -> 0.80).
- **Reranker**: GLM-4.7 listwise over the candidates, MRR 0.53 -> 0.80 on hybrid.
  gpt-oss-120b was tried and returned no ranking within 400 output tokens (its
  reasoning used them), so its order fell back to the first stage's. Bedrock's
  rerank models are not offered in ap-southeast-2.
- **Union instead of fusion.** Fusing the question's and the translation's lists
  scored well on test (0.91 / 0.86) but lost on the real set (0.88 vs 0.95 for hybrid
  + rerank alone): real questions are all in the language of their law, and the
  translation's results took candidate slots from the question's own. Weighting the
  translation down (0.3, 0.5) was tried on dev and was within noise. Keeping the
  question's top 20 whole and adding up to 10 of the translation's removes the cause:
  same-language results match hybrid + rerank, cross-lingual ones are the best
  measured. Disclosure: this change came after seeing the real set's scores of the
  fused version; it was chosen on dev, and the real set was then scored once.
- **Agent vs no agent** (the brief's comparison): the agent rewrites queries, searches
  4.4 times on average, chooses methods and filters; with the same reranker it is
  level on accuracy (test 0.91 / 0.83 vs 0.94 / 0.88; real 0.96 / 0.87 vs 0.95 / 0.88)
  at 1.5x the latency and 3x the cost. It is offered as a mode in the UI; the
  default is the pipeline. The agent model is GLM-4.7 (tool use in-region; Claude
  is reachable here only through cross-Region inference).
- **Answers**: GLM-4.7, fast (about 1 s) and in-region; the same model reranks.

Latency is end to end from the local machine to Bedrock in Sydney; cost counts the
tokens sent at US list prices (`eval/run_retrieval.py` `PRICES`).

## Answers (`agent/answer.py`, `eval/answers.py`)

Answers are judged on 100 test items (spread over language and file type) and the 27
real questions the corpus cannot answer, by DeepSeek V3.2 (another family than the
GLM answers and the Qwen questions; prompts in the script). Four prompt versions,
each measured once (`data/eval/results/answers/v1/`, `v2-labor-prompts/`,
`v3-neutral/`, `v4-prompt-rule/`):

| | v1 | v2 language + jurisdiction fixed | v3 domain-neutral | v4 prompt rule | **v6 country filter (served)** |
|---|---|---|---|---|---|
| corpus | 53 docs | 53 docs | 70 docs | 70 docs | 70 docs |
| correct / partial / wrong | 71 / 23 / 6% | 71 / 23 / 5% | 74 / 18 / 6% | 73 / 17 / 7% | 77 / 15 / 5% |
| unsupported by the cited sources | 10% | 5% | 4% | 5% | 10% |
| a citation overlaps the gold | 93% | 93% | 89% | 89% | 92% |
| unanswerable questions declined | 63% | 59% | 41% | 48% | 63% |
| unanswerable answers citing the other country's law | | | 9 / 27 | 8 / 27 | 0 / 27 |
| one file (30 items) correct | | 80% | 83% | 77% | (scoped: no filter) |

- v1 -> v2: English questions were answered in Korean when the sources were Korean
  (the language is now fixed by code, `is_korean`), and country-less questions got
  the other country's law as the answer (a question without a country is now taken
  to be about its language's country).
- v2 -> v3: the prompts stopped saying "labor law" (unknown uploads at the live test);
  the jurisdiction rule was limited to legal questions, and declining fell: a Korean
  question on tips got US tip-credit rules, an English one on evaluations Korean law.
- v3 -> v4: the rule now says what makes a question legal (what a law requires or
  allows: wages, leave, leases, penalties ...), never to present the other country's
  law as the answer, and that other documents have no jurisdiction rule. Declining
  recovered to 48%; then stopped, as the 27-item set is small and noisy (some of it
  is partly answerable) and further rounds would tune to it.
- v4 left a limit: an English legal question naming no country could still get Korean law
  first ("Are pay stubs required?"). Tried and not kept (v5, measured once): every
  source labelled jurisdiction="KR" / "US" and the rule told to answer from the
  question's jurisdiction. The answers citing the other country's law stayed at 8 of
  27, unsupported statements went 5% -> 8%, declining 48% -> 52%: no gain, so the
  change was reverted (`data/eval/results/answers/v5-labels-rejected/`). The fix
  that would hold is in retrieval, not the prompt: for a legal question naming no
  country, pass only that country's statutes (and the user's documents) to the
  answer step.
- v6 does that (`retrieval/jurisdiction.py`, below under "Jurisdiction filter"):
  answers citing the other country's law 8 -> 0 of 27, declining 48% -> 63%, correct
  73% -> 77%. Unsupported statements 5% -> 10%: of the 10, the judge's reasons are
  mostly fine points (a source "for a specific category", "a different regulatory
  context"), three of the flipped items became correct and one is a decline without
  citations; 5 items of 100 is within the noise of one judging run, so kept and noted
  (`eval/jurisdiction_check.py` counts the other-country citations).
- Real-estate test set, all 82 items, v6 (`answers.py --set re`, `summary-re.md`):
  correct / partial / wrong 74 / 22 / 4%, unsupported 6%, a citation overlaps the gold
  95%, the other country's law cited 0 of 82. The partial share is higher than on
  labor: answers to procedural questions (documents to submit, who handles a
  dispute) often give part of a list.
- The one-file numbers move by one or two items out of 30 between versions.

**One file, against Claude and ChatGPT** (`eval/single_file.py`): 30 single-document
questions over 28 files, search scoped to the file: the gold passage is among the
answer's 6 sources for 30 of 30; answers 77% correct, 17% partial, 7% wrong with the
served prompts (80% / 83% with earlier versions). The
Claude and ChatGPT columns are filled by hand (`data/eval/single_file/README.md`).

## Evaluation set (`data/eval/`, `eval/`)

**Gold answers are character ranges, written answer-first.** Passages are drawn from
the canonical text per (answer language, file type) cell before any question exists,
so neither chunking is favored, and a gold range scores both (a chunk is relevant
when it overlaps). The quote is stored with the range, so a parser change that
moves the text is caught (`evalset.anchor`).

**Generated by one model, checked by others.** Qwen3-Next 80B writes the questions
(Qwen3 235B was 55-66 s per call on demand, Qwen3-Next 2 s), DeepSeek V3.2 drops any
that are not fully answerable or are ambiguous (205 of 636 dropped: 96 passages with
nothing to ask, 98 only partly answerable, 11 quotes not in the passage). Rules that
keep it fair to keyword search: own words, no article numbers, country named only
when asking in the other language; a known OCR error copied into a question was
fixed (용자 -> 융자).

**Pooling for answers in other statutes.** The act, decree and rule repeat each other,
so a correct result can sit outside the gold. The top 5 of 8 systems are judged
(DeepSeek V3.2, with the reference answer) and each accepted span confirmed by a
third family (gpt-oss-120b), which rejected 163 of 311: the same clause about another
committee, form or table row. Without the confirmation a sample of 12 had 3 wrong.

**Real questions as a check on the generated ones.** 164 FAQ titles (easylaw.go.kr,
dol.gov), verbatim; the judge is told the source's jurisdiction (without it, three
dol.gov questions were matched to Korean law). 137 have gold (4 annotated by hand
after the judge missed them), 27 the corpus cannot answer (court cases, guidance,
laws not in the corpus) are kept for the agent's "I don't know".

Result: test 338 / dev 85 (split 80/20 per cell, seeded) / real 137; composition and
limits in `data/eval/README.md`. Cost: about 10M judge and 0.5M generator input tokens, an estimated $5-7 of Bedrock calls, all cached.

## Real-estate statutes and domain-neutral prompts (2026-11-13)

**17 real-estate documents were added** (13 Korean: 공인중개사법, 부동산 거래신고법,
부동산 가격공시법 with decrees and rules, 주택·상가건물 임대차보호법 with decrees; 4 US:
Fair Housing Act, RESPA, 24 CFR 100 as a synthetic scan, Regulation X), 70 documents in
all, formats rotated as for the labor statutes. The labor sets stay frozen (their
passages re-sample byte for byte); a real-estate set is built the same way from the
new documents only: 82 test, 21 dev (`data/eval/README.md`).

**The prompts no longer say "labor law".** The interview's live test brings unknown
files; the reranker, translation, follow-up rewriting, agent and answer prompts now
describe a collection of statutes and user uploads of any topic, and the
jurisdiction rule applies to legal questions only. Checked on dev (0.953 / 0.887
against 0.953 / 0.881) and on the unseen-document questions (8 of 8 as before).

Served system on the 70-document corpus (hit@10 / MRR), results in
`data/eval/results/retrieval-70docs/`:

| | test (338) | real (137) | real-estate test (82) |
|---|---|---|---|
| hybrid | 0.78 / 0.53 | 0.89 / 0.60 | 0.84 / 0.57 |
| hybrid + rerank | 0.84 / 0.80 | 0.96 / 0.89 | 0.90 / 0.84 |
| served, labor-specific prompts | 0.94 / 0.87 | 0.96 / 0.88 | 0.98 / 0.90 |
| served, domain-neutral prompts (before the jurisdiction filter, below) | 0.93 / 0.87 | 0.96 / 0.88 | 0.98 / 0.91 |
| same, fixed-size chunks (labor prompts) | 0.92 / 0.86 | 0.94 / 0.85 | 0.96 / 0.90 |
| agent + rerank (labor prompts) | | | 0.99 / 0.89 |

The extra documents changed nothing measurable on the labor sets; the 1.2-point
hit@10 difference on test between the two prompt versions is 4 questions.

## Jurisdiction filter (`retrieval/jurisdiction.py`, 2026-11-13)

**A legal question searches only its country's statutes; uploads are always searched.**
One short GLM-4.7 call answers KR / US / BOTH / NONE: a named country, agency or
statute decides; a legal question naming none takes its language's country (Korean
-> KR, English -> US, the corpus's two jurisdictions); comparisons (BOTH), non-legal
questions (NONE) and unreadable replies get no filter. `Searcher(country=...)` then
drops chunks that are public *and* from the other country's id prefix, in BM25 and
inside the k-NN search; a search scoped to chosen documents is not classified. It
runs alongside the translation (both only need the question), about 0.3 s added.

Why in retrieval: two answer-prompt versions (v4 rule, v5 source labels) left 8 of 27
answers citing the other country's law; what is not among the sources cannot be
cited. The risk is a wrong label removing the gold document, so unclear cases fall
back to no filter.

| | test (338) | real (137) | real-estate test (82) |
|---|---|---|---|
| served before (domain-neutral prompts) | 0.93 / 0.87 | 0.96 / 0.88 | 0.98 / 0.91 |
| **+ jurisdiction filter (served)** | **0.94 / 0.88** | **0.94 / 0.90** | **0.98 / 0.91** |

- Labels on 557 questions: wrong country 0, no filter 8 (`country` in each result line,
  `data/eval/results/retrieval-70docs/*/bilingual_union+rerank+jur@...`).
- real hit@10 lost 3 questions, all reranker reorderings within the right country's
  documents (the gold was not filtered out); hit@1 rose 0.83 -> 0.87.
- Limit: an English question about Korean law that names neither Korea nor a Korean
  statute is taken to be about US law.

## Real estate measured like labor (2026-11-13)

Everything measured on the labor statutes was repeated for the real-estate ones.

**Real questions** (`data/eval/real_re.jsonl`, `eval/real_re.py`, sources in
`data/eval/README.md`): 83 answerable (43 Korean easylaw, 40 English CFPB and HUD /
DOJ), 30 unanswerable. hit@10 / MRR (`results/retrieval-70docs/real_re/`):

| System | real-estate real (83) | labor real (137) | p50 | $/query |
|---|---|---|---|---|
| BM25 | 0.70 / 0.42 | 0.78 / 0.49 | 0.0 s | 0 |
| dense | 0.73 / 0.48 | 0.83 / 0.59 | 0.3 s | 0 |
| hybrid | 0.75 / 0.51 | 0.89 / 0.60 | 0.3 s | 0 |
| hybrid, fixed-size chunks | 0.78 / 0.50 | 0.86 / 0.54 | 0.3 s | 0 |
| hybrid + rerank | 0.88 / 0.84 | 0.96 / 0.89 | 1.6 s | 0.004 |
| **served** (translation union + rerank + jurisdiction) | **0.87 / 0.83** | **0.94 / 0.90** | 3.6 s | 0.006 |
| agent + rerank | 0.95 / 0.86 | 0.96 / 0.88 (53 docs) | 9.6 s | 0.022 |

- The served system finds the right document (doc hit@10 0.98) but misses the
  article on 11 of 83: situation questions ("주변에서 계약기간을 1년으로 하라고 합니다.
  어떻게 하는 것이 좋을까요?") whose answer is a rule the question does not name. The
  agent rewrites them into several searches and finds 8 of the 11. Three of the 11 are
  the hand-annotated gold (no pooled system found them by construction; the agent,
  not in the pool, found two).
- The agent stays an option, not the default: on labor it matches the served system,
  and it costs 4x and takes 2.7x as long. These situation questions are where
  agent mode is worth its cost; a user can switch to it per question.
- Fixed-size chunks beat structure chunks on hybrid hit@10 here (3 questions of 83),
  not on MRR; the other sets favor structure chunks.

**Answers** (`answers.py --set re`): unanswerable real-estate questions declined 93%
(28 of 30; labor 63%): most ask about laws outside the corpus (Civil Act, taxes), which
the answer step recognizes; none cites the other country's law.

**Single file** (`data/eval/single_file/`): 10 real-estate rows added to the 30 labor
ones (8 cells); ours: 80% correct, 20% partial, the gold passage in the sources for
10 of 10. The Claude / ChatGPT columns are filled by hand for all 40.

**OCR on every scanned page** (`eval/ocr_corpus.py`, `results/ocr-corpus.md`; cached
transcriptions the index holds, no new calls): real estate 44 pages, CER 2.4%, recall
99.5%; labor 34 pages, CER 4.8%, recall 99.0%. The worst page set is the short labor
English notice (CER 9.5%, a three-column table).

**Tables in PDFs** (`eval/pdf_tables.py`), against structured editions:

| Document | tables found | cell exact | cell in table | row match | chars kept |
|---|---|---|---|---|---|
| 산업안전보건법 시행규칙 (labor) | 44 / 33 | 65.6% | 95.7% | 58.1% | 100% |
| 산업재해보상보험법 시행령 (labor) | 9 / 10 | 61.8% | 67.1% | 52.1% | 100% |
| 주택임대차보호법 시행령 (real estate) | 2 / 2 | 94.6% | 94.6% | 89.3% | 100% |
| 12 CFR 1024, Regulation X (English, vs govinfo XML) | 8 / 7 | 5.0% | 64.9% | 0.0% | 97.9% |

The English figure measures the known limit: CFR tables have no ruling lines, so
pdfplumber's line-based detection returns fragments (a column's numbers in one cell);
the text is kept (97.9%) and searchable, the cell structure is not. A layout model for
borderless tables is the production fix (design.md, limitations).

## Deployment rehearsal (2026-11-12)

The whole stack was deployed once to AWS, checked, measured and torn down. What it
found, none of which a local run could show:

| Found | Fix |
|---|---|
| "Unknown tokenizer type [nori_tokenizer]": nori is an optional plugin on AWS OpenSearch Service, not built in | associate the analysis-nori package for the engine version (custom resource in data.py); a blue/green deployment, 20 min |
| the API died at start (index creation failed) and the circuit breaker rolled back, deleting the logs | a failed index creation is logged and the API starts; log groups are kept on rollback |
| a domain with no access policy refused the task roles | the domain policy defers to IAM in the account; only the task roles have identity policies |
| the first upload waited 4-5 min: the queue alarm behind the worker's scaling uses 5-minute periods | the API raises the worker service itself after an upload (one task per 10 files) |
| scale-in stopped a worker in the middle of the last file (the alarm counts waiting messages, not in-flight ones); the file waited 30 min for its retry | ECS task scale-in protection while a worker holds a job |
| on t3.small.search, four workers indexing at once got 429 Too Many Requests / 502 (7 of 70 files failed) | bulk writes retry with backoff, busy failures are redelivered after a minute, at most two workers |
| 13,000 cache files to S3 one by one: 13 min | three archives |
| health checks were logged every 15 s per target | not logged |

Measured on AWS: chat answers in 3-5 s (11 s for the first, cold request); 53 files
in 429 s before the fixes, the first done at 59 s after the worker wake-up; access
controls as designed (401 without a token or with the dev header, 403 on the ALB
directly and for non-evaluators on the log viewer).

## Constraints that shaped the above

- AWS project on the free plan, single Region ap-southeast-2, no cross-Region
  features: Textract (paid plan) and Bedrock rerankers (not offered in this Region)
  are unavailable as of 2026-11-12.
