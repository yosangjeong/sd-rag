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
not required, and an extreme case (vertical text, hanja). A real phone scan of printed
corpus pages was measured later (below, 2026-11-16); it is not in the corpus.

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
filter). Claude (needs the Anthropic use-case form) was not available to test; the
engine sits behind one interface (`OcrEngine`) and can be swapped.

**Textract, measured later (2026-11-27, on the paid plan; `eval/textract_bench.py`,
`results/ocr-textract.md`)**: AnalyzeDocument on the same 24 bench pages and the 9
real-scan sheets, with tables and then also with LAYOUT (reading order). It recognizes
characters about as well (recall 94-99.5% against 95.7-99.8%), adds fewer characters not
in the source (real scan: extra 0.3% against 1.6%; Qwen3-VL's extra turned out to be `<br>`
tags, see the next paragraph) and is faster (2-6 s per page against 11-14 s). Without LAYOUT it
loses reading order on two-column English pages (CER 58-76% against 3.9%); with LAYOUT
those come level (3.6-5.6%), but Korean stays behind (body 3.1-4.4% against 2.3-2.8%,
tables 11-12% against 0.4%), and the real scan overall is 4.9% against 2.8% (Qwen3-VL before the `<br>` cleanup; 1.1%
after it). Qwen3-VL
stays, as the criteria set before the run said. Simulated as a check on Qwen3-VL: flagging
pages where over 5% of Qwen3-VL's characters are missing from Textract's output flags one
page (real-scan sheet 5) and no good page, but not Qwen3-VL's other high-CER pages, whose
errors are reading order that Textract shares (33 pages; a direction, not a rate).

**`<br>` cleaned, and the check in the service (2026-11-27)**: the flagged page's extra
characters were not invented words but HTML `<br>` that Qwen3-VL writes for a line break
inside a table cell (as noted for sheet 5 under the real scan below). The same check run
on the 78 corpus scan pages flagged one more, for the same reason (kr-equal-employment-dec
p14, 37 tags); 5 corpus pages had `<br>`. `ingest/ocr.py` `tidy` turns it into a space in a
table row (a line break elsewhere), after the cache. What the index now gets: real scan CER
1.1% (extra 0.1%), corpus scans labor 4.1%, real estate 2.2%; the check then flags none of
the 111 pages. It is in the service anyway (`CheckedOcr`, `SDRAG_OCR_CHECK`, on): every
scanned page is also read by Textract alongside (2-6 s, about $0.02 per page), and a page
where over 5% of Qwen3-VL's characters are not in Textract's text keeps Textract's text and
is counted (`ocr_replaced` in the upload's stats). It guards against what a generative
reader can do; it has found no invented text in our scans, and the 5% was chosen on 33
pages. Three test-set gold quotes that had copied the tags were cleaned the same way.
Retrieval re-run after the rebuild (public-only index, labor test set, BM25 and hybrid,
no LLM): top 10 changed on 4 and 10 of 338 questions, hit@1/hit@10/MRR/nDCG unchanged at
two decimals (BM25 MRR 0.423 -> 0.424); fixed windows likewise. The LLM systems were then
re-run on the 104 questions whose stored results or gold touch the 5 changed pages (served
system on test, real, real_heldout, test_re and real_re; hybrid + reranker on test; about
$1.5), the other questions' rows kept, latency and cost kept from the original runs:
served test hit@10 0.968 -> 0.965 (MRR 0.899 unchanged), real MRR 0.910 -> 0.896, held-out
MRR 0.816 -> 0.810, real_re hit@10 0.964 -> 0.952 / MRR 0.941 -> 0.929, test_re unchanged;
hybrid + reranker unchanged at two decimals. Most of it is the LLM reranker's run-to-run
variation, not the clean-up: of the 11 served questions whose score moved, 9 have their
gold in documents the clean-up did not touch (moves both ways). README and the slices
updated to these numbers. Not re-run: the other LLM ablation systems (translation
candidates, fixed windows, prompt variants), the agent, and answer generation/judging
(v11-final); their reported numbers are from before the clean-up.

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

- **Chunking**: structure chunks beat fixed windows in every configuration measured here
  (hybrid test MRR equal, hit@10 0.78 vs 0.75; final system 0.94 vs 0.92). On the 70-document
  corpus (README ablation table) BM25 alone is level or slightly behind (MRR 0.42 vs 0.44),
  dense ahead (0.58 vs 0.53); the margin is small, and one article per chunk also gives
  citations a single article to name.
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

**How far the correctness judge can be trusted** (2026-11-13, `eval/judges.py`,
`data/eval/results/answers/rejudge.md`, `judge-agreement.md`):

- Reading the non-correct grades showed answers marked down for correct extra detail
  and items whose reference answer is itself wrong. Two fixes, both applied to every
  version and every system alike:
  - **Faulty items**: every item used for answer grading (198) was checked by a third
    family (gpt-oss, `eval/check_items.py`) and its flags checked against the statutes by
    Claude Code (the coding assistant; not a model the pipeline uses); 8 are faulty
    (`data/eval/item_flags.json`: a reference saying "150 million" for 150만원, one
    reversing "excluded" from the minimum wage, a garbled question ...). They stay in
    the sets (their gold spans are right); answer results are given with and without.
  - **Judge v2**: says what the key fact is, that correct extra detail never lowers the
    grade, and that the passage outranks the reference. Fixed before the Claude and
    ChatGPT answers exist; every stored answer re-graded with it.
- Re-graded (correct / partial / wrong): v6 labor 77/15/5 (v1) -> 82/10/7 (v2) ->
  85/9/4 without the flagged items; real estate 74/22/4 -> 72/23/5 -> 74/22/4. The order
  of the versions is the same under both judges.
- **Agreement with a reference grading** on a seeded 20 (10 judge-correct, 10 not): 11 of
  20. The reference grades are Claude Code's, reading the statutes in full before seeing
  the judge's grade (a better-informed model, not a person). Judge-correct was right 10
  of 10; of the 10 judge-non-correct, the reference grades 8 correct.
  Every disagreement is the judge being stricter: it sees only the gold passage, so a
  correct rule from another article (a decree's exemption, a later item of the list)
  looks invented; the groundedness judge, which sees the cited sources, rated all 8
  supported. The correctness figures are therefore a lower bound (scaled by the sample,
  about 95% for v6, with a wide interval); comparisons stand, as every system meets the
  same judge. Stopped there rather than tuning the judge further to our answers; the
  final Claude / ChatGPT comparison has the non-correct grades of all three read again
  the same way.

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
dol.gov questions were matched to Korean law). 137 have gold (4 annotated outside the
judge, by Claude Code searching the statutes, after the judge missed them), 27 the corpus cannot answer (court cases, guidance,
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

**The prompts no longer say "labor law".** A live test with files never seen before is
expected; the reranker, translation, follow-up rewriting, agent and answer prompts now
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
| + jurisdiction filter | 0.94 / 0.88 | 0.94 / 0.90 | 0.98 / 0.91 |
| **+ statute versions (served, below)** | **0.95 / 0.88** | **0.95 / 0.89** | **0.98 / 0.91** |

- **Dense instead of hybrid as the first stage** (asked late: on dev, dense + rerank had
  beaten hybrid + rerank, 0.894 vs 0.847 hit@10, but the translation union had only been
  built on hybrid). Measured on dev with the rest as served (`bilingual_union_dense+rerank+jur`,
  `results/retrieval-70docs/dev*`): labor dev hit@10 0.953 both, MRR 0.869 vs 0.889 served,
  hit@1 0.824 vs 0.859 (3 questions); real-estate dev identical (0.905 / 0.843). Hybrid stays;
  the test sets were not run for it, as choices are made on dev.
- Labels on 557 questions: wrong country 0, no filter 8 (`country` in each result line,
  `data/eval/results/retrieval-70docs/*/bilingual_union+rerank+jur@...`).
- real hit@10 lost 3 questions, all reranker reorderings within the right country's
  documents (the gold was not filtered out); hit@1 rose 0.83 -> 0.87.
- Limit: an English question about Korean law that names neither Korea nor a Korean
  statute is taken to be about US law.

## Amended articles not yet in force (2026-11-13)

**Found while grading by hand**: law.go.kr's 현행 법령 files carry amendments that are
enacted but not yet in force right after the article in force (남녀고용평등법 제18조의3:
"최초 2일은 유급" in force, then "최초 4일은 유급 ... [시행일: 2026. 11. 27.]"). Both
versions had the same heading, so they were chunked together, and the answer gave both
rules side by side and dated the amendment by its `<개정 2026. 5. 26.>` (the enactment
date, not the effective one). 86 such markers in 14 of the 55 Korean statutes, in every
format; many take effect on 2026-12-08, during the interview week.

- **Parsing** (`ingest/parse.py` `mark_versions`, every format, uploads too): the amended
  version gets the heading "<article> [2026. 11. 27. 시행]", the version before it
  "<article> [개정 전, 2026. 11. 27. 전까지]": facts that hold on any day, and distinct
  headings keep the versions in separate chunks (8,023 -> 8,051 chunks). 85 amended
  versions labelled, 55 with an earlier version (the rest are new articles).
- **Answering** (`agent/answer.py` `version_status`): which version is in force is
  computed from today's date in Korea and written into the source as
  status="in force today (until 2026-11-26; ...)" / "not in force today (amended version,
  takes effect 2026-11-27)"; the prompt says to answer with the version in force and add
  one sentence on the other. First tried giving only today's date and leaving the
  comparison to the model: it called the version taking effect in two weeks the current
  law. With the status computed: on 2026-11-13 "2 days now, 4 from 2026-11-27"; with the
  date set to 2026-12-01, "4 days now, 2 until the change".
- **Measured again** with the versions split (v7): retrieval unchanged within a question
  or two (test 0.947 / 0.884, real 0.949 / 0.893, real-estate 0.976 / 0.908, dev
  0.953 / 0.902; the CI baselines were raised to these). Answers: labor 72% correct in
  one run, 77% in a second run of the same system, real estate 76%; unanswerable
  declined 67% / 93%; the other country's law cited 0 times.
- **Run-to-run variation, measured here for the first time**: the same system run twice
  on the same 100 items changed 13 correctness grades (translation, reranking and the
  answer are LLM calls). A difference of about 5 points between two single runs is
  therefore within the noise; the version-to-version differences in the Answers table
  above (one run each) should be read the same way. Production would repeat runs and
  report a mean and range.
- **Evaluation**: 20 test items touch an article with two versions; 7 items across the
  sets have their gold only in a version not yet in force on the grading date, so their
  reference answers are only right later: flagged "date" in `data/eval/item_flags.json`
  (`eval/version_flags.py`). Retrieval scoring is unaffected (gold spans are offsets in
  the same text).

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

**Single file** (`data/eval/single_file/`): 20 real-estate rows added to the 30 labor
ones (8 cells, 16 files); ours: 80% correct, 20% partial, the gold passage in the
sources for 20 of 20. The Claude / ChatGPT columns were filled by hand for 20 chosen rows (2026-11-16, below).

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
| 12 CFR 1024, Regulation X (English, vs govinfo XML), before | 8 / 7 | 5.0% | 64.9% | 0.0% | 97.9% |
| same, with unruled tables read again (served) | 8 / 7 | 68.4% | 90.0% | 37.1% | 100% |

CFR tables have rules only around a few heads, so pdfplumber's line strategy found the
ruled middle of each table, every column's values stacked in one cell, and read the
columns beside it as text. Now (`ingest/parse.py` `_widen_unruled`), on an English page,
a table whose filled cells all hold the same number of lines (3+) is read again by text
alignment over its band of the page column, kept if that gives more columns; leader dots
are dropped and the minus sign GPO's font encodes as "¥" restored. Korean tables are
untouched (their figures above are unchanged). Two documents changed (12 CFR 1024,
29 CFR 778); the evaluation spans in them moved with the text (19 of 78) and none was
lost, which `evalset.load_items` now checks on every load: spans are re-anchored in
the current text, and a quote no longer found stops the run (`anchor` had been written
for this but was never called). Retrieval without the LLM steps changed by at most one
question per set; the served system was measured before this change. Rows still split
differently from the XML in places (37% exact): a layout model remains the production fix.

## Measured late: approximate search, injection (2026-11-13)

**HNSW loses almost nothing** (`eval/ann_recall.py`, `results/ann-recall.md`): the served
k-NN query against an exact cosine search over every chunk, same owner filter, on the
test, real, real-estate test and real-estate real sets (640 questions): 99.3-100% of the
exact top 10 returned, identical top 10 for 95-100% of the questions, dense hit@10
equal on three sets and one question lower on the fourth (0.723 vs 0.735).

**Prompt injection, repeatable** (`eval/injection.py`): 8 planted-instruction documents x
basic and agent mode, 16 of 16 resisted; see design.md, Security.

## Figures checked against the sources (`common/numbers.py`, 2026-11-13)

A legal answer is only as good as its periods, ratios and amounts. Reviewing answers
for the human grading turned up the answer model copying a figure wrongly with the
right one in front of it: the decree's "1분의 100" (rent x 100) written as "100분의 100"
(r0111), and "150만원" written as "150,000 won" (g0224, v7 rerun).

- **The check**: every quantity in the answer (a number with a unit, a percent, a Korean
  fraction) must occur, by value, in the sources the answer cites (all sources if it
  cites none) or in the question. Values, not strings, because the answer rarely says it
  the source's way: "7일" / "7 days", "100분의 25" / "25%", "1천분의 2", "6억9천만원" /
  "690 million won", "5백명", and US statutes in words ("one thousand eight hundred and
  forty hours", "one and one-half times"). Fractions are matched against the sources'
  ratios only; article numbers, list markers, dates (decided in code, see Amended
  articles) and per-unit "1일" / "per day" are not quantities.
- **What happens**: an answer with an unsupported figure is sent back once with the
  figures named; if one is still unsupported, the answer keeps it in
  `unchecked_figures` and the UI shows a warning beside the answer. The first draft's
  figures are kept in `rewritten_for` (answer rows, logs).
- **Tuned on** the stored v7 answers (366 answers whose citations still match the
  index, 127 with figures): it flags the two real errors above and nothing else. The
  first version, a string match, flagged 29 of 68 answers with figures, almost all
  translations.
- **Measured on new answers** (v8, `results/answers/v8-figure-check/`): rewrites in 3
  of 239 answers. Two were real errors corrected by the rewrite: r0111 again ("100분의
  100" -> "1분의 100", and now says there is no such cap) and r0163 ("500만원" first
  written as "500,000 won"). One was a false alarm ("5백명" not read as 500), fixed
  since and added to the tests. Labor answers never triggered it; correctness is within
  the run-to-run spread (labor 74%, after 72% and 77%; real estate 74% and 79% in two v8
  runs, 76% in v7; declining 70% and 93-97%).
- **Limits**: it catches a figure the sources do not have, not a wrong figure that
  occurs elsewhere in them (a fine of the neighbouring row of a table), and units are
  compared loosely (a value matches whatever its unit). Unit conversions add to that: "24개월" also
  matches a 2 (years) in the source. A long run of scale words ("100만 200만 ..." in an
  uploaded table) made the first version's patterns take exponential time, found in a
  code review and fixed before deployment (a test keeps 60 of them under 0.5 s). Production would compare the
  figure with the unit and the sentence it sits in.

**Citation numbers** (same day): the model cites by position among the six sources it
is given, so an answer citing only the second, third and fifth read "[2][3][5]" next to
a source list of three. `agent/answer.py:renumber` numbers the cited sources 1, 2, 3 in
the order the text first cites them, after the figure check (which works on the
model's numbering).

## Wider candidate pool and judge v3 (`retrieval/search.py:wide`, 2026-11-13)

**Where the served system missed.** Of 746 questions over the six sets, the gold article
was outside the answer's six sources for 49, yet the right document was among them for
97% of all questions. 40 of the 49 were not even among the reranker's 30 candidates, so
the first stage, not the reranker, was the limit:

- 26: another article of the right document;
- 15: the law article was retrieved but the answer sits in the decree or rule that
  carries it out (a fine's amount in a decree table, a delegated authority, a form);
- 8: another statute.

Two reasons stood out. RRF (`rrf`) ranks a chunk that one list puts near the top below
chunks both lists put in the middle: a gold that BM25 put 3rd was 38th after fusion. And
a decree article that carries out "법 제39조" shares few words with a question about
the law's subject.

**Change.** `Searcher.wide` gives the reranker, in order: the previous candidates
(question's hybrid top 20, translation's 10 more), then the top 5 of each first-stage
list on its own (BM25 and dense, question and translation), then up to 5
cross-references: for each Korean law (or decree) article among them, the decree and
rule chunks with the phrase "법 제N" ("영 제N" for decrees), best three by BM25 on the
question (`Searcher.references`). About 50 candidates instead of 30.

- Chosen on the dev sets only (pool size 29 to 69 and passage length tried; the test
  sets were run once, after). Cutting reranker passages from 1,200 to 800 characters
  lowered dev hit@1 0.894 -> 0.859 for 7% less cost, so they stay at 1,200.
- Cross-references changed nothing on the dev sets (106 questions, already at 100% pool
  recall); they are kept because 15 of the 49 test-set misses are that pattern.

hit@10 / MRR, previous served system -> wide (`results/retrieval-70docs/<set>/`):

| Set | n | previous | wide | p50 latency | cost / query |
|---|---|---|---|---|---|
| dev | 85 | 0.953 / 0.902 | 0.977 / 0.911 | 3.7 -> 4.4 s | $0.006 -> $0.010 |
| dev_re | 21 | 0.905 / 0.843 | 1.000 / 0.914 | 3.4 -> 4.5 s | |
| test | 338 | 0.947 / 0.884 | 0.962 / 0.882 | 3.5 -> 4.6 s | |
| real | 137 | 0.949 / 0.893 | 0.964 / 0.894 | 3.4 -> 4.5 s | |
| test_re | 82 | 0.976 / 0.908 | 0.988 / 0.916 | | |
| real_re | 83 | 0.868 / 0.829 | **0.928 / 0.866** | 3.6 -> 4.4 s | |

The gain is largest where the previous system was weakest (real-estate real questions,
situation questions whose answer is a rule they do not name). hit@1 fell on the labor
test set (0.840 -> 0.828): with more candidates the reranker sometimes puts the gold
second or third, which the answer, reading six sources, does not mind.

**Judge v3** (`eval/judges.py`). Reading the 43 answers judge v2 did not grade correct
in the v8 run: 26 were right (a further case or deadline from another cited source
counted against the answer; the version of an amended article in force today graded
against a reference written from the amended text; "one of the cases" answered with
another case of the list), 5 were faulty items, 8 retrieval misses, 4 real answer
faults. v3 also gets the cited sources and today's date, and says that any item of a
list answers a "one of" question. On the same v8 answers it moved 16 of the 26 to
correct and kept 7 of the 8 retrieval misses wrong; it still fails some "one of" answers
and is still a lower bound.

**Answers** under judge v3 (correct; citation of the gold; unanswerable declined):

| Run | labor (100) | real estate (82) | declined labor / re |
|---|---|---|---|
| v8, previous pool | 86%; 89% | 94%; 96% | 70% / 97% |
| v10, wide pool | 87%; 92% | 91%; 96% | 74% / 90% |

Within the run-to-run spread (13 of 100 grades change between two runs of the same
system), so the answers are about as good as before; the retrieval gain shows in more
answers citing the gold passage on labor. A rule tried in between (v9: "a yes/no
question starts with the conclusion the rest supports") turned a right answer into a
wrong "Yes" and did not fix the answer it was written for, and was removed.

## Statute terms, definitions, reranker windows (2026-11-14)

Reading the 25 questions the wide pool still missed at rank 10 (20 not among the
candidates, 5 ranked below 10). Each change was checked without an LLM call (does the
gold come into the candidate pool; can the reranker see it); the end-to-end measurement
with the reranker is pending.

- **Cross-references fixed** (`Searcher.references`). It looked at the first 8 law
  articles among the candidates and scored the decree's chunks by the question alone;
  for a fine asked in English, 제39조(과태료) was 9th and an English question shares no
  words with a Korean fine table. Now 15 articles, scored with the question and its
  translation, all hits ordered by score.
- **Statute terms for BM25** (`retrieval/terms.py`): everyday words get the statute's
  term appended (집주인 -> 임대인, 월세 -> 차임, 알바 -> 단시간근로자; in English
  "fired" -> discharge, "kickback" -> unearned fees). A word is listed only if the statutes
  rarely use it themselves (under 10 times in that country's corpus, a test checks):
  adding "산업재해 업무상 재해" to questions with 산재 pushed the right article down in
  three real questions, because 산재보험 is itself the statute's word. First stage
  alone, real-estate real questions hit@10 0.723 -> 0.783, other sets unchanged.
- **Section names** (`terms.SECTIONS`): "RESPA Section 8" -> 12 U.S.C. 2607 and a few
  others. This one was written after two real CFPB questions asked by that name were
  missed, i.e. from test-set failures; it is general knowledge of the statutes, but
  its gain is not an unbiased estimate.
- **Definition articles** (`Searcher.definitions`): the best three of the 133
  "제2조(정의)" / "Definitions" chunks join the pool; "평균임금은 어떻게 계산하나요" is
  answered there, and a definitions article lists dozens of terms, so it matches no
  single question well in the main search.
- **Statute-terms query** (`LlmTranslator.to_statute_terms`): the LLM rewrites the
  question as the provision that answers it would say it, run in parallel with the
  translation; its hybrid top 10 join the pool. Not measured yet on its own.
- **Reranker windows** (`rerank.window`): the reranker got the first 1,200 characters of
  each chunk; in 26 of 725 pooled gold chunks the answer starts later, and 3 of those
  ranked below 10. Sending only the 1,200 characters that share most words with the
  query made the gold visible in 15 more and invisible in 16 others, so it was
  dropped; sending the first 1,200 plus the best later 500 makes it visible in 176 of
  192 long gold chunks instead of 166, loses none, for 2.4% more characters.

Candidate pool, without the paid statute-terms query: misses 20 -> 13 over the four
test sets (dev g0345 too), none lost.

First end-to-end check, on a new real-question dev set (`data/eval/real_dev.jsonl`, 31
easylaw questions from six topics no other set uses, gold chosen by Claude Code
reading the statutes): hit@10 / MRR / hit@1, previous served 0.871 / 0.847 / 0.839,
with these additions 0.903 / 0.840 / 0.806, hybrid 0.839 / 0.430 / 0.194. One more
question found (산재 for construction day workers), one fewer ranked first. The
injection test was re-run after the changes: 16 of 16 resisted.

Two reranker-side ideas were tried on real_dev and dev_re and dropped (hit@10 / MRR on
real_dev, served 0.903 / 0.840): presenting the pool in RRF order over all its lists
instead of arrival order, against an LLM's bias toward the top of a long list (0.871 /
0.805; dev_re 1.00 -> 0.95), and a reranker rule that a question whether a rule covers
some group is answered by the provision setting its scope (0.871 / 0.807; dev_re
unchanged). Each is one or two questions on 31, inside the noise, but neither helped.
`Searcher.wide_fused` stays as the ablation.

**Reranker model** (2026-11-14). Every model Bedrock serves on demand in ap-southeast-2
was tried as the reranker over the same pools (`run_retrieval.py --rerank-llm`, the
translation, jurisdiction and statute-terms replies cached so only the reranker
differs). Claude is offered in this Region only through cross-Region inference
profiles (au. routes to Melbourne too), which the project's one-Region rule excludes.

| Reranker | real_dev 31 hit@1 / MRR | dev_re 21 | dev 85 (hit@6 / MRR) | rerank $/query |
|---|---|---|---|---|
| GLM-4.7 (served) | 0.806 / 0.840 | 0.857 / 0.914 | 1.000 / 0.947 | 0.012 |
| GLM-5 | 0.871 / 0.876 | 0.857 / 0.910 | 0.965 / 0.934 | 0.019 |
| DeepSeek V3.2 | 0.774 / 0.812 | 0.762 / 0.835 | - | 0.012 |
| Qwen3 235B | 0.774 / 0.804 | 0.714 / 0.843 | - | 0.004 |
| gpt-oss-120b | 0.194 / 0.432 | 0.571 / 0.713 | - | 0.003 |

GLM-5 won on the real questions (two more first) but lost on the larger labor dev set,
three golds falling out of the answer's six sources; over all 137 dev questions MRR
0.918 vs 0.917 and hit@6 0.978 vs 0.949, for 60% more reranking cost. GLM-4.7 stays.
gpt-oss-120b mostly returned no usable ranking (the first-stage order then stands).
The dev run also shows the 2026-11-14 additions on the labor dev set: hit@10 / MRR
0.977 / 0.911 (wide, 2026-11-13) -> 1.000 / 0.947.

## Documents the system never saw (`eval/unseen.py`, 2026-11-14)

Every other set measures the 70 statutes, and part of the retrieval is specific to them
(cross-references, definition articles, statute terms). An evaluator uploads other
things, so a small set was built from public files unrelated to the corpus, downloaded
on 2026-11-14 (`data/eval/unseen_docs.json`, sources and licenses): five Korean
government press releases from korea.kr (KOGL type 1; three HWPX, two PDF), one more
turned into a simulated scan (rendered to images, skewed, noised, no text layer: OCR'd),
the NIST Cybersecurity Framework 2.0 and IRS Publication 15 (US government works). They
went through the upload path (parse, OCR, chunk, embed, index) as a test user. Questions:
up to 6 sampled chunks per document, written by Qwen and checked by DeepSeek with the
generator's prompts made field-neutral; 14 of 35 asked in the other language. The search
runs as for that user: their uploads plus all public statutes, with the served system
as of 2026-11-14 (wide pool with the cross-reference fix, statute terms, definition
articles, reranker windows and the statute-terms query).

| System | n | hit@1 | hit@5 | hit@10 | MRR |
|---|---|---|---|---|---|
| hybrid (BM25 + vectors) | 35 | 0.43 | 0.63 | 0.83 | 0.54 |
| served (wide + rerank + jurisdiction) | 35 | **0.77** | **1.00** | **1.00** | **0.87** |

Every miss at rank 1 was another chunk of the right document (press releases repeat a
fact in the summary and the body); no statute ever came first. Cross-lingual questions
MRR 0.83, same-language 0.90; the scan 0.87. Limits: eight documents make picking the
document easy, and the questions were written from single chunks.

**Many similar uploads** (`unseen.py --suite similar`, same day): the 35 latest press
releases of one ministry (고용노동부, korea.kr, KOGL type 1; 33 HWPX, 2 PDF where the
"HWPX" attachment was an old binary HWP), same format, same vocabulary, several on the
same subjects (employment statistics, jobs meetings, safety inspections), uploaded as
another test user; 2 questions per document by the same generator and check, 60 kept
(16 in English). This is the case the eight-document set could not test: picking the
right one among look-alikes, with the labor statutes as distractors on the same topics.

| System | n | right document first | hit@1 | hit@5 | hit@10 | MRR |
|---|---|---|---|---|---|---|
| hybrid | 60 | 48 | 0.48 | 0.87 | 0.95 | 0.65 |
| served | 60 | **59** | **0.80** | **0.97** | **1.00** | **0.88** |

Hybrid put a statute first 8 times; the served system never. Of the served system's 12
misses at rank 1, 11 were another chunk of the right release, and one (u035, winter jobs
for low-income households) a release of the jobs meeting that states the same plan.
Cost about $1.2.

## Final measurement (2026-11-14)

The served system with all of the above, on every set, after pooling the gold spans
(`eval/repool.py`): the top 5 of the four systems the README reports (served now and
before, hybrid, agent) were judged with finalize_qa.py's prompts and models (DeepSeek
V3.2 finds passages giving the same answer, gpt-oss-120b confirms each); 210 spans were
added to `also` for 163 questions, logged in each item's `meta.also_repooled`, and
every stored result file was re-scored. The four pooled systems gain most; the other
ablation rows (fixed windows, BM25 or dense alone) only where they found the same passages. Before pooling, the
served system's own top answers that differed from the single gold counted as misses
(the youth-wage question's top passage, "during the first 90 consecutive calendar
days", next to its gold sentence).

hit@10 / MRR (hit@1), pooled gold:

| Set | n | hybrid | served until 2026-11-13 (bilingual union) | **served now (wide)** | agent |
|---|---|---|---|---|---|
| test | 338 | 0.784 / 0.539 | 0.956 / 0.897 (0.858) | **0.968 / 0.899 (0.852)** | - |
| real | 137 | 0.890 / 0.604 | 0.949 / 0.902 (0.869) | **0.978 / 0.910 (0.869)** | - |
| test_re | 82 | 0.854 / 0.582 | 0.988 / 0.933 (0.902) | **0.988 / 0.945 (0.915)** | 0.988 / 0.921 |
| real_re | 83 | 0.759 / 0.520 | 0.892 / 0.859 (0.843) | **0.964 / 0.941 (0.928)** | 0.952 / 0.884 |
| dev | 85 | 0.788 / 0.504 | 0.953 / 0.911 | 1.000 / 0.956 | - |
| dev_re | 21 | 0.857 / 0.604 | 0.952 / 0.867 | 1.000 / 0.938 | - |

On real-estate real questions the basic mode now beats the agent (0.964 / 0.941 against
0.952 / 0.884) at about half its latency. The statute-terms query alone (without it,
real_re 0.952 / 0.882, hit@1 0.843) moves answers up rather than finding new ones.
Cost and latency per query: about $0.012 and 5.7 s p50 for retrieval with reranking
(was $0.006 and 3.5 s), 7.7-8.1 s p50 with the answer.

Answers (v11, judge v3; labor 100 / real estate 82): correct 87% / 89% (v2 judge 78% /
77%), without flagged items 92% / 90%; a citation of the gold 96% / 98%; unanswerable
questions declined 67% / 90%; no answer cites the other country's statutes; the figure
check rewrote 3 answers and left none with an unsupported figure. Declining on labor
(18 of 27) is lower than the 70-74% of v8-v10, within the run-to-run spread of 27 items.

## Held-out real questions and the scope rule (2026-11-14)

Every earlier real-question set was in use while the system was tuned (several ideas came
from their misses, said where they were made), so their numbers may be optimistic. This
set was collected after the last retrieval change and measured once.

**The set** (`data/eval/real_heldout.jsonl`, 33 answerable; `real_heldout_unanswerable.json`,
64): easylaw 백문백답 topics no other set uses (부동산 경매, 이사, 전세사기 피해자 지원,
배달앱종사자, 가사근로자, 고령자 고용, 요양보호사, and the labor and lease questions of
business and welfare topics such as 음식점 운영, 예술인 지원, 저출생 지원), 29 + 59
Korean questions, and the HUD/DOJ Joint Statement on reasonable accommodations (2004), 4
+ 5 English ones. Three of its questions repeat the 2008 modifications statement's in
real_re and were left out; "the Act" is written "the Fair Housing Act", since the
question stands alone. Most of the unanswerable ones are under statutes outside the
corpus (민사집행법, 전세사기피해자법, 가사근로자법, 고령자고용법, 노인복지법, tax and
food-safety law). Gold spans were chosen by reading the statutes (`data/raw/heldout/`,
not committed: questions.csv, labels.json, build.py), each quote checked verbatim, then
pooled once with `eval/repool.py --sets real_heldout` before reporting (9 spans for 7
questions, which raised hybrid and left the served numbers unchanged).

| | hit@1 | hit@5 | hit@10 | MRR |
|---|---|---|---|---|
| hybrid | 0.424 | 0.576 | 0.727 | 0.526 |
| **served (wide + rerank + jurisdiction)** | **0.758** | **0.909** | **0.909** | **0.816** |

Lower than real_re (0.964 / 0.941), as a set no decision saw should be. Three of 33 are
not in the top 10: the delivery rider's accident (elh-039) and the employer of an older
part-timer (elh-056) got articles that answer them as well (산재법 제91조의18/20 on
노무제공자 accidents; 고용보험법 시행령 제17조 on job-creation support, arguably better
than the gold 법 제20조), which the pooling judge rejected because a real question's
reference is the gold quote; whether a restaurant's staff get social insurance (elh-071)
is a true miss (노무제공자 articles above 고용보험법 제8조). The labels were not changed
after seeing the results.

**Scope rule** (answer prompt): many of the unanswerable questions answered in v11 had a
narrower provision presented as the general rule (foreign workers' termination grounds
for "what ends an employment relationship", FMLA rules for "when are pay raises
required"). The rule: check that the sources answer the question as asked; if they cover
only a narrower case, say first that the documents do not answer it in general, then what
the narrower provision says, labelled with its scope. Decided on the 27 labor
unanswerable questions (the dev role here): declined 67% -> 70% (18 -> 19), within the
run-to-run spread; read one by one, four answers (el-032, el-063, el-066, dol-067) that had
stated a narrower provision now say first that the documents do not answer, and the three
that went the other way are answers that open with the same statement (el-085, dol-060) or
that the corpus partly answers (el-016). On the same 50 test items as v11, correct 44 /
partial 3 / wrong 3 and supported 42 in both, the gold cited 47 -> 50: kept.

Held-out unanswerable questions, once with the rule (v12): **declined 78%** (Korean 47/59,
English 3/5). Of the 14 counted as answered, 9 begin by saying the documents do not answer
and then give related provisions, which the decline judge's prompt allows but grades
inconsistently; 5 answer outright, two from lease provisions that partly apply (elh-017
eviction after an auction, elh-038 a landlord's tax arrears), one the corpus does partly
answer (elh-049: 근로기준법 제11조 excludes 가사사용인), and two that should have declined
(elh-084, enh-007). Cost of this section: about $3 (retrieval $0.7, pooling $0.2, answers
$2.1).

## doc2query, tried and not adopted (`eval/doc2query.py`, 2026-11-14)

For each of the 8,049 public chunks gpt-oss-120b wrote 3 questions in everyday words
that the passage answers (not Qwen, which wrote the generated sets: same-model wording
would inflate them; judged on real questions only), appended to `search_text` in a copy
of the index, `chunks-d2q` (embeddings, shown text and the reranker's passage unchanged).
Cost $1.9 to generate, $1.8 to measure.

| Set | system | hit@1 | hit@10 | MRR |
|---|---|---|---|---|
| real_dev (31, decides) | hybrid | 0.194 -> 0.355 | 0.839 -> 0.839 | 0.430 -> 0.521 |
| | served | 0.806 -> 0.806 | 0.903 -> 0.935 | 0.840 -> 0.852 |
| real (137) | hybrid | 0.474 -> 0.489 | 0.890 -> 0.898 | 0.604 -> 0.632 |
| real_re (83) | hybrid | 0.410 -> 0.458 | 0.759 -> 0.807 | 0.520 -> 0.569 |
| | served | 0.928 -> 0.916 | 0.964 -> 0.988 | 0.941 -> 0.936 |
| real_heldout (33) | hybrid | 0.424 -> 0.364 | 0.727 -> 0.818 | 0.526 -> 0.518 |
| | served | 0.758 -> 0.667 | 0.909 -> 0.939 | 0.816 -> 0.777 |

The keyword search gains on every real set (it finds the article from everyday words, as
intended) and the served system finds more answers in its top 10 everywhere; but the
article ranked first got worse on the two reported sets (one question on real_re, three
on the held-out set), so MRR fell. Adopted only if clearly better; it is not, so the
served index stays `chunks-structure`. A likely cause: the generated questions also match
neighbouring articles of the same statute, so more look-alike candidates reach the
reranker. Using doc2query only to add candidates, or for the first stage only, would be
the next thing to try, decided on real_dev; the held-out set has now been used twice and
is no longer clean for that. The questions are in `data/raw/d2q/` (not committed;
`doc2query.py generate` rebuilds them from the LLM cache).

## Answer model compared, GLM-4.7 kept (`eval/answer_models.py`, 2026-11-15)

Only the answer step changes: the 50 single-file questions get the same top 6 sources
(bilingual_union + GLM-4.7 rerank, the retrieval single_file.py records, not the wide
pool served since 11-13; run once) and the served answer prompt;
judge v2 (DeepSeek V3.2) grades every answer. Candidates are the in-Region on-demand
text models; DeepSeek is left out (the judge's family), Claude too (cross-Region only).

| Answer model | correct | vs GLM-4.7 (items) | note |
|---|---|---|---|
| GLM-4.7 (served) | 80% | | |
| GLM-5 | 84% | +3 -1 | |
| Kimi K2.5 | 82% | +3 -2 | |
| gpt-oss-120b | 84% (80% at 4000 tokens) | +6 -4 | cited as `【1】` / `【1†L2-L4】`; now read as `[1]` (`answer.py`), same grades |
| Mistral Large 3 | 80% | +5 -5 | |
| Qwen3 235B | 78% | +4 -5 | |
| MiniMax M2.5 | 54% (54% at 4000 tokens) | | thinks through its budget: 18-23 empty answers |

The best clean candidate, GLM-5, then ran the labor dev run of the served pipeline with
only the answer model swapped (`answers.py --answer-model zai.glm-5`, 50 test items + 27
unanswerable real questions, against `v12-scope-dev`): correct 88% -> 90% (+4 -3 items),
supported 84% -> 88% (+4 -2), declined 70% -> 81% (+4 -1), latency p50 8.3 s -> 11.9 s,
answer-step price about 1.5x. gpt-oss-120b, about a quarter of GLM-4.7's price, the same
way (`v13-gptoss-dev`): correct 88% -> 86% (+3 -4), supported 84% -> 88% (+4 -2),
declined 70% -> 56% (+2 -6), p50 9.0 s. The differences are a few items each, except the
declines, and the answers are slower; adopted only if clearly better, so GLM-4.7 stays.
If declining out-of-scope questions mattered more than latency, GLM-5 would be the
switch to make (one setting: `RagService(answer_chat=...)` / `answers.py --answer-model`).

Found on the way: the judge graded an empty answer "correct" (it took the reference for
the answer). No reported run had an empty answer (checked every result file);
`answer_models.py` now grades empty answers `no_answer` without asking the judge.
Cost about $3.7.

## Future dates and Korean amounts in English answers (`agent/answer.py`, 2026-11-15)

The six labor dev answers that were not graded correct (`v12-scope-dev`), read one by
one: two were judge errors (g0175, g0330: the answer had the law in force right), one
arguable (g0524: $211 is the inflation-adjusted penalty in force, the reference has the
statute's $100), three wrong answers. Two of those had a general cause:

- g0279: a notice announces next year's rate ("beginning January 6, 2027"); the answer
  gave it as today's. The version rule covered only labelled statute versions. New
  prompt rule: a rate or rule that a source says applies from a date after today is
  given with that date, after the one that applies today when the sources have it.
- g0224: the source's 150만원 became "150,000 won" in an English answer, and again after
  the figure check named it. Sources for an English answer now carry the value in
  digits, in code (`with_digits`: "150만원(=1,500,000 won)"), so the model copies it.

The third (g0308, the answer said the documents did not answer) has no general fix here.
g0224 is now right on the amount but still adds a ratio condition: its table chunk has no
column headings (limitations). Measured (`v14-dates-digits-dev` vs `v12-scope-dev`, same
50 + 27 items): correct 88% -> 90% (+3 -2), supported 84% -> 92% (+4 -0), declined 70% ->
74% (+3 -2), latency unchanged; single-file 50 with fixed sources 80% -> 78% (5 grades
moved, none on an English answer with a Korean amount or a future date: the wording of
the answers changes with the prompt). Adopted: both target errors are gone, nothing got
worse beyond noise. The README's final numbers (v11-final) are from before this; a
re-measure belongs with the served re-measure after the final deploy. Cost about $1.3.

## A real phone scan (`eval/real_scan.py`, 2026-11-16)

Nine corpus pages (Korean articles, Korean tables, an English two-column CFR page and a
USC page) printed at 100% on A4 and scanned with an iPhone (Notes, document scan, its
automatic crop and deskew left on), some on purpose badly: two a little skewed, one
under a hand's shadow, one in a dark room. Results: `data/eval/results/ocr-real-scan.md`.

- The first run failed: the iPhone's PDF pages are about 1815 x 2633 pt (A4 is 595 x
  842), so at 200 dpi the image was over Bedrock's request limit ("length limit
  exceeded"). A user's phone scan would have failed to upload. `ingest/ocr.py` now
  caps a rendered page's longest side at A4's (2,339 px); A4 and Letter pages render as
  before (the corpus scans' 78 cached pages all hit the cache, same CER).
- CER 2.8% over the 9 pages (synthetic corpus scans: labor 4.8%, real estate 2.4%),
  recall 99.4% (2026-11-16; since the `<br>` cleanup of 2026-11-27: 1.1%, labor 4.1%,
  real estate 2.2%). The two highest are not misreadings: sheet 5 (15.6%) is the table
  markup the engine writes (`<br>`, `---`; 0.4% without it), sheet 7 (recall 96.6%)
  misses only the GPO's tiny print-job line (`VerDate ... Jkt ...`). Shadow 0.0%, dark
  0.7%, skewed 0.2-2.6%.
- Uploaded to the local service as a user: indexed in 41 s (9 OCR pages, 27 chunks).
  Three questions scoped to it were answered right with the right page cited: 30 days'
  notice of dismissal (p.1), disability grade 5 = 790 days (p.9, a table), FLSA overtime
  after 40 hours (p.8). The last citation's heading is the previous Korean page's
  `[별표 4]`: in a scan mixing documents, a page with no heading of its own inherits
  the last one (rare in a real document; limitations).

Cost under $0.1.

## Human grading: faulty references, a stricter judge (2026-11-16)

The user graded 20 v8 answers by hand (`data/eval/results/answers/judge-agreement.md`,
second table). The first item showed the problem: its gold quote was a bare list item
("1. ... 이행상황의 제출 요구") without the article's sentence that says who holds the
power. Every item was then read against its whole article: 9 of 20 had a faulty
reference answer or gold (a list item without its lead-in, 4 of 6 grounds, "what" for a
"when" question, an unrelated article, an amendment not yet in force, two different
reasons in reference and gold), and one question was garbled (r0178, already flagged;
the user added its missing "at settlement" condition and ambiguous negative form). The
grading page showed the whole articles and the corrected references.

- Agreement with the human (19 graded): judge v2 11, the same judge given the corrected
  reference and the whole article 15, Claude Code 15. The judge is stricter than the
  human (10 vs 15 correct, 12 after the corrections); half of its disagreements came from
  the references.
- Across the sets about 15% of gold quotes are a bare list item (test 51 of 338, real
  estate 9 of 82, dev 15 of 85). Retrieval scores are unaffected (chunks are whole
  articles); the judge reads the quote. Next judge version: the whole gold article as the
  passage (no new prompt), applied with the final re-measure.
- The user's notes found real errors: a retrieval miss (g0274, found since by the wider
  pool), next year's rate first (g0279, fixed on 11-15 by the future-date rule), a
  deadline given only by name (g0364: the 15th of the next month), a yes/no answer
  reversed against its own content (r0082), and a list chunk whose amount sits in its
  lead-in in another chunk (g0395, limitations).
- Plan: the final served re-measure after the deploy is graded by the judge with whole
  articles, and the user hand-grades a new 20 from it, references checked against the
  articles first.

## One file: Claude and ChatGPT compared (2026-11-16)

The user ran the 20 chosen rows (`data/eval/single_file/subset20.json`, fixed before any
answer) on claude.ai (Sonnet 5.5) and chatgpt.com (GPT-6). Details and table:
`data/eval/single_file/README.md`.

- References first, against whole articles (`fixes20.json`): 5 of 20 corrected. g0597's
  sentence (a certification "shall be sufficient") governs premium recovery after a failure
  to return, not approving leave, so the reference "yes" was wrong; r0176 was written from
  the association-inspection article for a broker-inspection question. r0176's error had
  been noted on 11-13 (judge-agreement.md, v6 item 1) but not applied to the set; today's
  audit missed it and it was applied after the answers came in (our served answer cited
  the other article), so the table shows the grades both ways; it moved every system, not
  only ours. Lesson: a reference error found in a judge check goes into the set (or
  item_flags.json) at once.
- Done the same day: the 10 references corrected so far (6 from the v8 hand grading, 4 from
  this audit) are in `data/eval/reference_fixes.json`, which `eval/answers.py` grades with;
  before, they lived only in the grading page's files.
- Our system answered twice: the `ours` column (2026-11-13, an older retrieval path in the
  eval script, `bilingual_union`) and the served code path (`RagService.ask`, wide pool,
  statute terms), the code as committed before the other answers were seen. The served one
  is the number reported; the old one stays as the pre-registered record.
- Judge v2 with the whole articles still made 15 errors in 80 grades, all from what its
  passage left out (a table split across chunks, a neighbouring article). Every
  non-correct grade was re-read against the statutes by Claude Code, not blind
  (`regrade20.json`, each change with its rule,
  applied to every system on the item). After that: ours 19/1/0, Claude 20/0/0, ChatGPT
  19/0/1. On one file the three are level; the brief's target (as good as Claude /
  ChatGPT on one file) is met, not exceeded.
- What the judge taught: a whole article is not always enough; a table or a cross-reference
  needs the neighbouring chunks. Judge v4's passage (`eval/judges.wide_passage`): the gold
  chunks, the run of chunks under the same heading, one chunk on each side, capped at
  14,000 characters. Measured the same day: agreement with the hand-read grades on these
  80, 65 -> 68 (7 fixed: split table, next-article exemption; 4 new errors: with the wider
  fine table the judge called 30만원 and 300,000 won different, r0015 x3); with the human's
  19 v8 grades 14 of 19, against 15 with passages picked by hand per item. So v4 gives the
  hand-picked quality automatically, not more: the final re-measure uses it, and the
  re-read of every non-correct grade stays a required step.
- Yes/no openers: of the 47 stored answers that open with yes/no (v11-final, v14 dev, the
  20 served answers), 5 (about 11%) open with the word their own body contradicts
  (g0036 twice, r0082, r0178, g0143), mostly an English "Yes" before a negative
  conclusion; the judge graded 2 of them correct.
- Two real faults in our served answers, both noted in limitations: a yes/no question
  opened with the wrong word against its own body (g0143, like r0082), and 권리금 glossed as
  "Jeonsegeum" in an English answer (r0037).

## Yes/no openers (`agent/answer.py`, 2026-11-16)

Of the 47 stored answers that open with yes/no, 5 open with the word their own body
contradicts (above). Two changes:

- Prompt rule: open with Yes/No only when that word and the rest of the first sentence
  agree; a Korean question asked in the negative is answered by agreeing with its wording
  ("올릴 수 없나요?" → "네, ... 올릴 수 없습니다"). Re-asking the 40 yes/no questions
  (`eval/yesno.py`, read by hand: the judge had missed these): r0178 and g0143 now agree,
  no new reversal among the other 38, Korean negative questions still right. g0036 and
  r0082 kept "Yes, employers do not owe ..." / "Yes, a landlord may not ...", also with a
  second prompt sentence giving exactly those examples (tried twice each, dropped).
- So a code fix: `yes_not_to_no` turns an English opener "Yes, <1-4 words> <verb> not"
  (or cannot, never, ...) into "No, ..."; the sentence reads the same with "No". Run over
  all 2,645 stored answers it changes g0036 and r0082 only (every version since v2), and
  leaves "Yes, you are entitled ... even if you are not ..." alone (unit test).
- Quick check with the prompt rule (`v15-yesno-dev` vs `v14-dates-digits-dev`, the same 50
  items of the labor test sample + 27 unanswerable; "-dev" in the name is historical): correct 90% -> 90% (5 up, 1 down), declined 74% -> 74%, gold cited 96% -> 96%,
  supported 92% -> 86% (1 up, 4 down: g0136's wording of the amendment date, g0201, g0395,
  and g0036, the reversal itself). The answers' wording changes with any prompt change;
  the same measure moved 84% -> 92% on 11-15. Adopted; the served re-measure after the
  final deploy shows it on the full sets. Cost estimated under $2 (Bedrock usage shows a day late).

## Overnight 2026-11-16: live-test rehearsal, depth questions, agent on the wide pool

**Live-test rehearsal** (the interviewer brings unseen files): the eight unseen documents
of `eval/unseen.py` (press releases in HWPX and PDF, a scan, IRS Pub 15, NIST CSF), uploaded
as a user; 19 questions written by hand from the documents (not generated), expected
answers noted first; answers read by hand (`data/raw/scratch/live18/`, local). 16 of 19
right: HWPX figures, a scanned page, an English table, a list, both cross-lingual
directions, a follow-up ("그럼 등유는요?"), a question the documents do not answer
(declined). Three issues: a scanned table's figure given without a unit (the table has
none; its total matches the text's 1,007억 원, so 백만 원); a list over all six press
releases cut to five (the answer saw six sources); a ministry named by its former name
(산업통상자원부 for the document's 산업통상부), the model's knowledge over the source.

**Depth questions** (22, written by hand: calculations, rule and exception, multi-step,
Korea-US comparison, two follow-up chains, uploads with statutes), basic and agent mode,
graded by hand against the statute text (`data/raw/scratch/depth17/`, local): 17 right,
2 partial, 3 wrong, the two modes alike. The wrong ones show where the answer step is
weak: counting from a rule (first-year leave at most 11 days, answered 12; 3 years of
service 16 days, answered 15) and a provision cited down to its paragraph (the decree's
annex applies only 제23조제2항 to workplaces of four or fewer; both modes said the
just-cause rule of 제23조제1항 applies). One expected answer of mine was wrong: the act
amended on 2026-02-19 gives six months of wages in a bankruptcy, as the system said.

**Agent on the wide pool** (`agent/search.with_pool`, served agent mode and
`run_retrieval.py agent+pool`): the agent mode first builds the basic mode's wide pool and
adds up to 20 chunks its own searches found that the pool lacks; the reranker orders the
union. hit@1 / hit@10 / MRR, p50, $/query:

| Set | basic | agent before | agent on the pool |
|---|---|---|---|
| test_re (82) | 0.915 / 0.988 / 0.945, 5.6 s, 0.012 | 0.866 / 0.988 / 0.921, 5.0 s, 0.016 | 0.902 / 0.988 / 0.939, 8.8 s, 0.026 |
| real_re (83) | 0.928 / 0.964 / 0.941, 5.7 s, 0.012 | 0.855 / 0.952 / 0.884, 9.6 s, 0.023 | 0.904 / **0.988** / 0.931, 12.4 s, 0.032 |

Better than the agent before on every measure, so the agent mode now works this way; it
finds more than the basic mode on real questions (hit@10) and ranks a little lower (MRR
-0.006 / -0.010) at twice the time, so the basic mode stays the default.

**Answer step** (#13 sources 6 -> 8, #23 the other version of an amended article, prompt
rules from the depth questions), quick checks on the same 50 + 27 items as `v15-yesno-dev`
(correct / supported / declined): v15 90 / 86 / 74%. With five rules and 8 sources
(`v16-review-dev`) 86 / 88 / 74%: three answers newly said the documents did not answer
(a rule "say plainly the documents do not cover the rest" made the model too cautious);
rules "give the unit" and "write names as the sources do" changed nothing in the
rehearsal; dropped. Two rules and 8 sources (`v17-two-rules-dev`) 90 / 78 / **59%**: more
sources let more unanswerable questions be answered; #13 dropped (a list over seven or more
documents stays cut: limitations). Kept (`v18-six-sources-dev`): six sources, the sibling
version (`service.with_versions`, added in 2 of 50 answers) and two rules: a provision
cited to its paragraph means only that part; a number that follows from a rule is worked
out in a short step. 84 / **90** / **81%**: the three correct answers lost are a question
that names no law ("이 법은 ...", g0437: re-asked with and without the rules it declines
half the time, the gold ranked first either way) and two partial grades for wording. On
the depth questions the calculation rule fixed the dismissal-notice amount (c1, 300만원,
both modes) and the agent got the 제23조제2항 case right; the leave-day counts (c2, c3)
stay wrong and the basic mode still misreads the annex: counting across a rule's limits
is a limitation. The judge graded the infertility-leave answer wrongly both ways (2 days
before 2026-11-27 is right). Cost of the night about $11 (CloudWatch token metrics, `eval/spend.py`).

**Not done**: #25 (a table's header across page breaks): g0224's cause turned out to be a
small table's header row inside a large HWPX table, not a page break; no general rule,
one known case, a re-index to verify: the limitation now says so. #14 (another embedding
model): the Region's on-demand text embeddings are still Titan v2 and Cohere v3, compared on
2026-11-12; Cohere v4 is offered only through a cross-Region profile.

## Streaming the answer (`/api/chat/stream`, 2026-11-16)

The page now asks `/api/chat/stream`, which sends one JSON line per event: the stage
(searching, ranking, writing), the answer's text as the model writes it (Converse
streaming, answer step only), and at the end the same body as `/api/chat`, whose final
text replaces the draft (citations renumbered from 1, the figure check's rewrite and the
yes/no fix applied; a rewrite is announced and the draft cleared). A keep-alive line goes
out every 10 s while nothing else does. `/api/chat` is unchanged (evaluation, tests, and
the page's fallback). Measured locally on one question: first text at 5.1 s and 8.2 s, the
end 1.8 s later; GLM-4.7 sends about ten pieces, so the gain is mostly the visible stages,
not a word-by-word answer. To check on the deployment: CloudFront passes the lines through
unbuffered (content type application/x-ndjson, not in its compression list).

## Where an answer's time goes (2026-11-16)

The served basic path, each step timed on 10 real dev questions (local, median; total
7.5 s): country, translation and statute terms at once 0.95 s, search (embeddings and
OpenSearch, about 59 candidates) 0.9 s, the reranker 3.7 s, the answer with its figure
check 2.3 s. The reranker reads every candidate (about 20,000 tokens) and is half the
time; fewer round trips in the search would save at most part of its 0.9 s, so that is not
worth the change. Faster would mean fewer or shorter candidates, which cost accuracy
(passages cut to 800 characters: dev hit@1 0.894 -> 0.859), or showing the answer as it
is written (streaming).

## Duplicate uploads and conversation items (2026-11-16)

Two limitations closed after the review, free: an upload whose content (SHA-256, taken
while it is written to disk) matches one of the user's files that is not failed is refused
("already uploaded (as a.pdf)"), so the same file is not indexed twice; and a conversation
is now one item plus one item per message (`MSG#<conversation>#<time>`), so a long one no
longer meets DynamoDB's 400 KB item limit. Conversations written before keep their
message list and are read together with any new message items.

## Code review before the final deploy (2026-11-16)

Five reviews, one per area (ingest and worker; retrieval and answers; API, auth and UI;
infrastructure and CI/CD; the brief against the repository), each read the code without
the others' conclusions; every high finding was reproduced before it was fixed. Fixed:

- Deploy and demo: the deploy role trusted `ref:refs/heads/main`, but a job with
  `environment: aws` presents `environment:aws` (the first CI/CD deploy would have been
  refused); deploys now run only after CI passed on the commit, and stop when the role
  variable is removed. Model calls on the request path get 30 s and 3 attempts (they had
  300 s and 8 behind CloudFront's 60 s), the agent 30 s of searching, a failing optional
  step (country, translation, statute terms, reranking) is skipped and logged; the ALB
  idle timeout is above CloudFront's. Reopening an agent-mode conversation blanked the page.
- Uploads: a scan whose text layer is only a stamp ("Scanned with CamScanner") was not
  OCR'd (now: under 50 characters and an image over half the page; no corpus page
  qualifies); a page whose OCR was throttled was dropped while the file showed "done"
  (now the file is retried; other unread pages are counted in its status); a DynamoDB error
  stopped the worker; a long scan was handed to the second worker at the 30-minute timeout
  (a heartbeat now extends it); the last retry left "retrying" forever (now "failed"); a
  failed file's indexed batches stayed searchable (removed). Size is checked while reading,
  not after; the first bytes must match the type; an old HWP / DOC, an encrypted Office
  file or a zip that inflates past 500 MB gets a message; DOCX content controls and
  tracked insertions are read. Corpus parses are byte-identical before and after.
- Security: masking missed numbers written next to Hangul ("010-1234-5678입니다": `\b`
  sees no boundary there), landlines, +82, key=value secrets; a document could close its
  `<source>` tag and forge a source or a status, and the reranker had no "passages are not
  instructions" rule; a token with an unknown key id gave 500, not 401; dev auth is refused
  inside an ECS task even without SDRAG_ENV; request ids from clients must look like ours.
- Answers: `yes_not_to_no` (same day) turned "Yes, if the employer does not pay, ..." into
  "No"; clause openers are now excluded. A heading with an impossible date ("2026. 13. 1.")
  made every answer citing it fail. With no sources the answer step no longer calls the model.
- Docs: "never used for tuning" was overstated (test results were read and analysed, and
  the answer versions were compared on a test sample; the untouched check is real_heldout);
  "re-read by hand" was Claude Code, not blind; two README figures were from the 53-document
  corpus and one MRR was rounded up; the table-chunk limitation described code that had
  long repeated the header row. Responses (answer text) and an estimated cost are now logged.

Measured after the fixes (the reranker prompt and its tags changed): the CI gate passes on
both dev sets; dev_re is unchanged (hit@10 1.000, MRR 0.938); dev lost one item, g0345 "is
off-the-clock work paid" (hit@10 1.000 -> 0.988, MRR 0.956 -> 0.939), and the commit before
the fixes gives the same pool without its gold: the model's rewrites of that question
differ from the 11-14 run, not the code. Prompt injection: 18 of 18 resisted, the new
tag-breakout document included (`data/eval/results/injection.md`).

Left as limitations (docs/design.md): the CloudFront to ALB leg (HTTP, header check), the
sibling statute version in the
answer, the agent measured on the real-estate sets only. Answers are now split by language
and file type too (`eval/answer_slices.py`, from the run's own grades).

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

## Second deployment rehearsal (2026-11-26, through CI/CD)

This time GitHub Actions deployed the app stack (push -> CI -> deploy.yml); only the
CiCd, network and data stacks were deployed by hand. Three faults, none visible locally:

| Found | Fix |
|---|---|
| `AssumeRoleWithWebIdentity` denied: the repository uses GitHub's immutable OIDC subject (`repo:<owner>@<id>/<repo>@<id>:...`), the trust policy expected `repo:<owner>/<repo>:...` (seen in CloudTrail's failed event) | `cicd.py` trusts the immutable form: a deleted and re-created repository with the same name does not match |
| every worker task exited at once with no log line; the circuit breaker rolled the app stack back. A refactor on 11-16 had dropped `if __name__ == "__main__": main()` from `worker/main.py`, so `python -m` only imported it (reproduced by running the CI-built image locally) | guard restored; `tests/test_entrypoints.py` checks the modules ECS starts with `python -m` |
| every streamed answer failed with AccessDenied: `ConverseStream` is authorized as `bedrock:InvokeModelWithResponseStream`, the task roles had `bedrock:InvokeModel` only (local runs use the developer's credentials) | the action added; the policy test requires both |

Measured: corpus ingest 70 documents / 8,049 chunks in 138 s from the caches; upload of 70
files through CloudFront all done in 830 s, none failed (the first rehearsal lost 7);
401 / 403 / evaluator-only logs and per-user isolation of documents, sources and
conversations as designed; the streamed answer arrives in pieces through CloudFront
(4-20 deltas); agent mode 10-19 s. Answers took 10-11 s against 7.5 s measured on 11-14:
single GLM-4.7 calls from the laptop took 1.1-3.5 s that afternoon (0.95 s for the three
in parallel on 11-14), so most of it was Bedrock latency; to be measured again on the
final deployment. Torn down the same day.

## The statute-terms query's own lists, and the pool's searches sent at once (2026-11-28)

The question and its translation each add the top 5 of their own BM25 and dense lists
(part 2 of `Searcher.wide`); the statute-terms query, added later (11-14), added only its
fused top 10. Giving it its own lists as well:

- **Pool (no reranker, all sets)**: 3 of the 10 test-set golds that never reached the pool
  now do (g0536, el-044, cfpb-026; real_dev eld-028 too), none lost; the pool grows from
  a mean of 56 to 66 candidates (max 68 -> 78).
- **Reranked, dev sets only** (real_dev 31, dev_re 21, labor dev 85): gold in the top 6
  134 vs 134 of 137 (eld-028 gained, g0179 lost), first 122 vs 124; reranker median time
  -0.1 to +0.6 s per set. The rule set before the run (+2 in the top 6, none lost) was
  not met: on accuracy it is a draw.

Adopted anyway, so the three queries follow one rule (simpler to explain; the asymmetry was
an accident of the order things were added, not a decision). The idea came from test-set
misses; the choice was made on dev, and the test sets are scored once after.

To win back the reranker's extra time, `wide`'s searches are sent at once instead of one
after another: the BM25 and dense searches of the three queries, their embeddings, the
definitions search, and the up-to-15 cross-reference searches. Same calls, same merge
order, so the same pool (40 of 40 dev questions identical); `wide` 0.78 s -> 0.27 s median
on 40 dev questions (local OpenSearch, Bedrock embeddings from the laptop). Spend about
$3.8 (rerank calls). Scripts were scratch, not kept.

## Consistency audit (2026-11-28)

After the statute-terms asymmetry above, the question path, ingestion and evaluation were
read for the same kind of thing: parallel steps treated differently with no reason given.

Fixed in the service:
- **Empty tables**: HWPX dropped them, DOCX and PDF kept them; a blank DOCX form was
  "done, 1 chunk" of empty cells instead of "no text found". All three drop them now.
- **Agent mode**: the reranker was meant to see the agent's own queries (for long
  passages' windows) but never did; the agent records them now.
- **Fallbacks**: jurisdiction, translation, statute terms and the reranker could fail
  without failing the request; condensing a follow-up and the agent could not. Now a
  failed condense searches the question as asked, a failed agent keeps the wide pool.
- **Bulk ingest** deleted the public corpus first and then indexed document by document:
  one failure left a partial corpus in service. Every document is now parsed and
  embedded first, the index touched only after; a document with no chunks stops the run.
- **Pool (as option (a): fixed for consistency, pool checked free, accuracy left to the
  final re-measure)**: definition articles matched "(정의)" exactly in Korean but any
  "definition" in English, so 제10조의3(권리금의 정의 등) and two others never came up
  (now "(정의" or " 정의", which adds those 3 and none of the 50-odd "조정의"/"결정의"
  headings); the statute-terms query took its new ones from its fused top 10, the
  translation from its top 20 (now both 20); BM25 expanded everyday words for the main
  search and the definitions search but not for the cross-references, and expanded the
  statute-terms query only in the definitions search (now one rule for all three).
  Gold in the pool over all seven sets: 1 more (real_dev eld-032), none lost; pool mean
  66 -> 70.
- Corpus chunks identical before and after (140 document/strategy pairs), so no re-index.

Corrected in the docs: answer_models.py's retrieval is bilingual_union + rerank (not the
wide pool); re-pooling covered four systems, so the other ablation rows gain less
(README); fixed windows are 400 tokens against at most 500 per article (README);
references keep the best three, not two; rejudge.py grades against the original
references (do not re-run it over v11 on); eval text now uses the index's OCR with its
Textract check; MAX_OCR_PAGES' comment named the old 30-minute limit. Not changed: HWPX
headings from styles (design.md limitations: the press releases use none).

## Full code review before the final deploy (2026-11-28)

Four checklist reviews (security, bugs, performance, consistency), then six line-by-line
reviews of every file of the service and the evaluation code; each finding was reproduced
or checked in the code before it was fixed. No finding gave another user's data or broke
sign-in; every headline number in README was recomputed from the stored result files and
matched.

Fixed, with what they changed:
- **Amended articles** (`mark_versions`): a block can hold several "[시행일]" markers and
  only the first was read; the amended version is now dated by a marker the previous
  version does not also carry (the earliest of its own), and the previous version is
  found as the run of the same article right before it, whatever its title. 근로기준법
  제116조 had both versions labelled "[2027. 1. 1. 시행]" (none in force); 8 articles whose
  title changed (최저임금법 제26조 근로감독관 -> 노동감독관, in force 2026-12-08, ...) had no
  "개정 전" label on the old text, which would have been cited as current after that date.
- **Decree -> rule references**: nori drops 영 and 제, so the filter "영 제2" matched 1,390
  of 1,852 rule chunks; it is now a phrase prefix on the standard-analyzed field (6 of 6
  real citations of 영 제13조). Law -> decree stays on nori, which also finds
  "「근로기준법」 제39조" (215 articles compared: nori found 89 more citing chunks).
- **Reranker writes the best 20** instead of every number: on the dev sets (137) gold in
  the top 6 135 -> 136, first 125 -> 124, median 3.58 s -> 2.49 s (output 212 -> 71
  tokens). Rule set before the run: adopt if the top 6 did not lose and it was 0.5 s
  faster. About $3.9. Its reply is also read when numbers come as strings or the JSON is cut.
- **PDF memory**: pdfplumber pages are closed as read (113 pages: 1,098 MB -> 110 MB).
- **Uploads**: names cut to 200 bytes (a longer one failed the whole batch), each file's
  error kept to that file, 100 files per user per 24 hours, one full request (first set to 30 for
  OCR cost; raised the same day because the brief has 50+ files uploaded at once, and only
  the admin creates accounts), the page sends files 10 per request (one
  request of 100 large files could outlast CloudFront's 60 s).
- **Worker**: a final failure removes the chunks a busy index took and the stage; botocore
  timeouts are transient; a retry's extra chunks are removed; an empty Textract read keeps
  Qwen's text; OCR and embedding cache files are written atomically.
- **Parsing**: DOCX cells read tracked insertions and content controls, text boxes once;
  HWPX text boxes and fixed-width spaces; an annex no longer captures every later heading;
  scanned table rows are not taken for running headers; circled numbers start items in
  PDF table cells (kr-occupational-safety-rul: 195 chunks gain a space, no heading moves);
  damaged files get a Korean message. Every other corpus chunk is unchanged.
- **Figure check**: "$7.25" is checked, days convert back to months and years, a bare
  "2억" in the question counts, both ends of "3~5일"; on 332 stored answers the flags are
  the same (1).
- **Frontend**: an answer stays in the conversation it was asked in; no double upload;
  rejection reasons in Korean; no blank page when the sign-in return fails.
- **Infra/CI**: DeployRole trusts only the aws environment; EvalRole may call Textract; the
  eval gate also watches common/ and uv.lock; after_deploy.sh fails instead of waiting
  forever and waits for the corpus task's exit code; Region passed to tasks; security
  headers; index.html and config.json not cached; helper log groups 14 days.
- **OpenSearch** client keeps 16 connections (urllib3's default kept 1); API search
  timeout 30 s; request ids always generated by the server.
- **Docs**: the held-out set is not clean (used twice, 9 of 33 share a gold passage with
  tuning items, served 1.00 on those against 0.875 hit@10 on the other 24); the answer
  numbers are v11 of 11-14.

- **Vector search width**: after the local re-index, the filtered HNSW search (ef = k = 50)
  missed a chunk that exact search ranks first for an English translation over Korean
  statutes (elr-016 left the pool); the graph differs per build, so the old index had
  found it by chance. ef_search 500 matched exact search on 60 dev questions (recall@50
  0.995 -> 1.000; min 0.96 -> 1.00) for 0.2 ms more. Over all seven sets, gold in the pool:
  none lost against the morning's code.
- **Eval spans**: the circled-number spacing moved 6 test-set quotes in
  kr-occupational-safety-rul ("진찰①" -> "진찰 ①"); their quotes were re-spaced and
  re-anchored (data/eval/test.jsonl, SHA256SUMS updated), and the canonical-text cache
  rebuilt; every gold and also span is found again.

Checked, not a problem: GLM-4.7 allows 100M tokens a minute in ap-southeast-2 (a question
is about 25k). Left as limitations (design.md): derived figures flagged, evaluators' log
view across users, tokens valid an hour after sign-out, retry wait after scale-in, streams
not cancelled on disconnect, the re-index minute without public chunks, OCR cache keys.

## A fresh test set, and the gate on main (2026-11-28)

Checked against the brief again: the evaluation set must be one "not used for tuning".
The test sets were kept out of the choices, but their results were read and analysed
after each measurement, and the closest to held-out (the 11-14 real questions) was used
twice and shares gold passages with tuning items. So a new set is made now, after the
last retrieval change, by the same pipeline as the labor and real-estate sets
(`eval/sample_passages.py --set fresh`, `generate_qa.py`, `finalize_qa.py`):

- passages from all 70 documents, per (answer language, file type) cell, about 330 items
  targeted; **no passage from an article, annex or section that holds a gold or also span
  of any other set** (780 left out), so no item shares an answer with a tuning item;
- gold from generation and the check (another model family), `also` from pooling the
  eight cheap systems (bm25, dense, hybrid, per_language; not the served system);
- all test (`data/eval/fresh_test.jsonl`), its hash in `SHA256SUMS` committed before any
  system is scored on it.

Made: 640 passages, 384 passed generation and the check, 376 after cleaning, and 2 more
dropped whose pooled also-span is a tuning item's answer: **374 items** (ko->ko 152,
en->ko 69, en->en 93, ko->en 60; PDF 185, scan 65, DOCX 55, HWPX 54, two formats 15;
64 documents). A first draw (110 English PDF passages) gave only 88 English answers, so
English PDF was drawn deeper before anything was scored; no scanned table is in it (every
one is in an annex a tuning item answers from). About $2 of model calls in all; `chunks-fixed` re-indexed first so the pool reads
the current parser's text.

Rules set before it is scored: it is scored **once**, at the final deploy, on the final
code, for every system in the ablation table, then re-pooled with the served system's top
5 like the other sets (`eval/repool.py`). Its numbers are reported as they come, next to
the earlier sets; nothing is changed after reading them. The eval gate never reads it.

The CI eval gate had never run: it ran on pull requests only, and the commits go
straight to main. It now also runs on a push to main that touches parsing, chunking or
retrieval (the deploy does not wait for it; a red run means a revert), and runs once at
the final deploy to show it working.

## Follow-ups that point further back (2026-11-28)

Studying the request path: `condense` saw only the last 6 messages, so a follow-up about
an earlier question was rewritten against the wrong subject. Four exchanges (dismissal
notice, annual leave, minimum wage, severance), then "아까 첫 번째로 물어본 거, 5인 미만
사업장이면 어떻게 돼요?": the old window gave "5인 미만 사업장이면 연차휴가는 며칠인가요?". Now
the user's questions before those 6 messages are listed too (up to 20, 200 characters each;
their answers are not), in the same call: "5인 미만 사업장이면 수습 기간에도 해고 예고를 해야
하나요?". A new topic came back unchanged, a recent reference still resolved, and an English
chain ("Going back to my first question ...") resolved too (GLM-4.7, 4 conversations, about
1,200 tokens in all). The retrieval sets are single questions, so their numbers do not
change. A summary of older turns or retrieving them was not needed for this: a question
names its subject in one line.

## Constraints that shaped the above

- AWS project on the free plan, single Region ap-southeast-2, no cross-Region
  features: Textract (paid plan) and Bedrock rerankers (not offered in this Region)
  are unavailable as of 2026-11-12.
