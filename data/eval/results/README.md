# Evaluation results

| Folder | What | Written by |
|---|---|---|
| `retrieval-53docs/{dev,test,real}/` | the retrieval systems compared on the first corpus (53 labor documents); every choice was made on dev | `eval/run_retrieval.py` |
| `retrieval-70docs/{test,real,test_re,real_re,dev,dev_re}/` | the same sets and the real-estate set after the 17 real-estate documents were added (70 documents), including the served system with the jurisdiction filter (`+jur`) | `eval/run_retrieval.py` (default output) |
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
v4-prompt-rule, v5-labels-rejected (tried, not kept), v6-country-filter.
