# Key decisions and their evidence

Each entry: what was decided, what else was considered, and the measurement behind it.
Scripts named here are in the repository; their raw outputs are kept under
`data/raw/` (not committed).

## Data

**One domain: labor and employment law, Korean and US.** 53 documents: 42 Korean
statutes (14 acts x act / enforcement decree / enforcement rule) and 11 US documents
(US Code, CFR, Federal Register). A single domain gives hard distractors (the same
topic in several statutes and in both languages) and keeps evaluation authoring
tractable. Licenses: Korean statutes are not protected (Copyright Act art. 7); US
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

**Scanned PDFs are synthetic.** The brief requires scanned PDFs; four corpus documents
(34 pages, Korean and English, with tables) are served only as image-only scans made
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

**Open: how to search across languages.** In a smoke test (`eval/search_smoke.py`)
BM25 and hybrid answered an English question about Korean law with US FMLA sections,
while dense search found 근로기준법 제26조. Fusing one hybrid list per language fixes
that but forces the other language into the top results even when it holds no
answer (a Korean 포상금 article ranked first for "minimum wage for federal contracts
in 2027"). Translating the query and searching with both versions is the candidate
fix; to be decided on the evaluation set.

## Constraints that shaped the above

- AWS project on the free plan, single Region ap-southeast-2, no cross-Region
  features: Textract (paid plan) and Bedrock rerankers (not offered in this Region)
  are unavailable as of 2026-11-12.
