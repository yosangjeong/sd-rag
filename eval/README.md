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
| `answers.py` | answer quality of the served pipeline: correct, grounded, citing the gold, declining |
| `jurisdiction_check.py` | answers citing the other country's law, per answer version |
| `single_file.py` | the brief's one-file comparison with Claude and ChatGPT |
| `upload_bench.py` | upload throughput through the API |
| `gate.py` | CI: fail when dev retrieval falls below `data/eval/baseline-dev.json` |
| `search_smoke.py` | a few questions through every retrieval mode (local index works) |
| `spend.py` | Bedrock spend since a time, from CloudWatch token metrics |

## Component choices

| Script | Chose |
|---|---|
| `ocr_bench.py` | the OCR model (Qwen3-VL), on synthetic scans of our own pages |
| `embed_bench.py` | the embedding model (Titan v2), within and across languages |
| `pdf_tables.py`, `pdf_spacing.py` | PDF table and Korean line-wrap parsing, against the HWPX edition |
| `robustness_files.py`, `robustness.py` | awkward inputs (damaged, encrypted, rotated ...) and how parsing copes |
