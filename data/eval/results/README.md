# Evaluation results

| Folder | What | Written by |
|---|---|---|
| `retrieval-53docs/{dev,test,real}/` | the retrieval systems compared on the first corpus (53 labor documents); every choice was made on dev | `eval/run_retrieval.py` |
| `retrieval-70docs/{test,real,test_re,real_re,dev,dev_re}/` | the same sets and the real-estate set after the 17 real-estate documents were added (70 documents), including the served system with the jurisdiction filter (`+jur`) | `eval/run_retrieval.py` (default output) |
| `retrieval-70docs/real_dev/`, `real_heldout/` | real questions for tuning decisions (31) and the held-out real questions collected after the last change, measured once (97) | `eval/run_retrieval.py` |
| `unseen/`, `similar/` | documents unrelated to the corpus uploaded as a user (35 questions), and 35 look-alike press releases of one ministry (60 questions) | `eval/unseen.py` (`--suite similar`) |
| `repool.json` | candidates judged and gold spans added per set by the pooling | `eval/repool.py` |
| `injection.md`, `injection.jsonl` | uploaded documents with planted instructions, asked in basic and agent mode | `eval/injection.py` |
| `ann-recall.md` | the HNSW index's recall against exact search | `eval/ann_recall.py` |
| `ocr-real-scan.md`, `ocr-real-scan.json` | OCR on 9 printed pages scanned with a phone (CER 2.8%, before the `<br>` clean-up of 11-27; 1.1% after it: `ocr-textract.md`) | `eval/real_scan.py` |
| `answers/yesno-check.json` | every stored yes/no answer re-asked after the yes/no rule, old and new side by side | `eval/yesno.py` |
| `answers/<version>/` | answer quality per prompt or pipeline version: `test_sample.jsonl`, `unanswerable.jsonl`, `summary.md` | `eval/answers.py --version ...` |
| `answers/rejudge.md`, `answers/judge-agreement.md` | every version re-graded with judge v2; the judge against a reference grading (Claude Code) | `eval/rejudge.py`, Claude Code |
| `item-check.jsonl` | the item check's verdict on every graded item | `eval/check_items.py` |
| `upload/` | upload throughput, local and on AWS | `eval/upload_bench.py` |
| `robustness.md` | parsing of damaged, encrypted, rotated and unusual files | `eval/robustness.py` |
| `ocr-corpus.md` | OCR accuracy on every scanned corpus page, labor and real estate | `eval/ocr_corpus.py` |

In each retrieval folder, `<system>.jsonl` holds one line per question (top 20 chunks,
scores, latency, tokens, cost) and `summary.md` / `summary.json` the scores of every
system run on that set, broken down by language, file type and question kind.
System names: `<mode>[+rerank][+jur]@<index>[~<llm>]` (`eval/run_retrieval.py`).

Answer versions (`docs/decisions.md`, Answers): v1, v2-labor-prompts, v3-neutral,
v4-prompt-rule, v5-labels-rejected (tried, not kept), v6-country-filter,
v7-statute-versions (and a rerun of the same system), v8-figure-check, v9 / v10-wide-pool,
v11-final (the README's numbers), v12-scope (and its dev check), v13 (answer models GLM-5
and gpt-oss on dev, not adopted), v14-dates-digits-dev, v15-yesno-dev. Versions ending in
`-dev` are quick checks of one change on the same 50 + 27 items: 50 of the labor *test*
sample (not the dev set, despite the name) and the 27 unanswerable questions; the others
ran on the labor test sample (100) and the real-estate test set (82).
