# Evaluation scripts

Run from `backend/` (`uv run python ../eval/<script>.py`) with `AWS_PROFILE` set when
the script calls Bedrock; results go to `data/eval/results/` (layout in its README).
The decisions they support are in `docs/decisions.md`.

## The evaluation set (built once, then frozen: `data/eval/SHA256SUMS`)

| Script | Does |
|---|---|
| `sample_passages.py` | stage 1: choose the passages questions are written from (per language x file type) |
| `generate_qa.py` | stage 2: a question per passage (Qwen3-Next), checked by another family (DeepSeek) |
| `finalize_qa.py` | stage 3: pool 8 systems for more gold spans, confirm (gpt-oss), annotate real questions, split dev / test |
| `describe_sets.py` | rewrite the composition table of `data/eval/README.md` from the set files |
| `evalset.py` | shared: corpus texts, gold spans, scoring (hit@k, recall, MRR, nDCG, doc hit) |

## Measuring the system

| Script | Measures |
|---|---|
| `run_retrieval.py` | retrieval systems on a set: `<mode>[+rerank][+jur]@<index>` |
| `answers.py` | answer quality of the served pipeline: correct (judge v3, v2, v4), grounded, citing the gold, declining (`--set labor | re | heldout`); references corrected in `data/eval/reference_fixes.json` take precedence |
| `jurisdiction_check.py` | answers citing the other country's law, per answer version |
| `judges.py` | the correctness judge's prompts (v1, v2, v3) and judge v4's passage (`wide_passage`: gold chunks widened to split tables and the next article), shared by the answer scripts |
| `rejudge.py` | re-grades every stored answer version with the current judge |
| `run_retrieval.py --rerank-llm <model> --cache-aux` | compares rerankers on the same pools (translation, jurisdiction and statute terms cached) |
| `unseen.py` | retrieval on public documents unrelated to the corpus, uploaded as a user (prepare, ingest, generate, measure; `--suite similar`: 35 look-alike press releases) |
| `doc2query.py` | everyday-word questions per chunk appended to BM25 text in an index copy (tried, not adopted: docs/decisions.md) |
| `repool.py` | adds the reported systems' top results to the gold spans after judging them (TREC-style pooling; `--sets` to pool some sets) |
| `rejudge_v3.py` | re-grades one stored answer run with judge v3 (cited sources and the run's date) |
| `check_items.py` | checks every graded item's reference answer and question (third model family) |
| `real_re.py` | the real-estate real questions: gold by the same pooling as the labor ones |
| `ocr_corpus.py` | OCR accuracy on every scanned corpus page (cached results, no calls) |
| `single_file.py` | the brief's one-file comparison with Claude and ChatGPT (`ours-now`: served code path scoped to the file; `grade-full [--wide] [--skip-fix q]`: the 20 compared rows with checked references) |
| `answer_slices.py` | answer accuracy of a stored run by question language and file type (no model calls) |
| `yesno.py` | re-asks every stored answer that opens with yes/no, old and new side by side for reading |
| `real_scan.py` | OCR on 9 printed pages scanned with a phone (plan in data/raw/bench/real-scan/) |
| `answer_models.py` | answer models compared on the same sources (single-file questions, judge v2) |
| `upload_bench.py` | upload throughput through the API |
| `gate.py` | CI: fail when dev retrieval falls below `data/eval/baseline-dev.json` |
| `search_smoke.py` | a few questions through every retrieval mode (local index works) |
| `spend.py` | Bedrock spend since a time, from CloudWatch token metrics |

## Component choices

| Script | Chose |
|---|---|
| `ocr_bench.py` | the OCR model (Qwen3-VL), on synthetic scans of our own pages |
| `embed_bench.py` | the embedding model (Titan v2), within and across languages |
| `pdf_tables.py`, `pdf_spacing.py` | PDF table and Korean line-wrap parsing, against the HWPX (Korean) or govinfo XML (CFR) edition |
| `robustness_files.py`, `robustness.py` | awkward inputs (damaged, encrypted, rotated ...) and how parsing copes |
