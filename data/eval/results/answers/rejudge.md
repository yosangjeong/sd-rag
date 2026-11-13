# Answer correctness re-graded (`eval/rejudge.py`)

correct / partial / wrong; judge v1 and v2 in `eval/judges.py`; flagged items in `data/eval/item_flags.json`.

| version | set | n | judge v1 | judge v2 | v2 without flagged |
|---|---|---|---|---|---|
| v1 | labor | 100 | 71% / 23% / 6% | 77% / 17% / 6% | 80% / 15% / 5% (n=95) |
| v2-labor-prompts | labor | 100 | 71% / 23% / 5% | 75% / 19% / 5% | 78% / 17% / 4% (n=95) |
| v3-neutral | labor | 100 | 74% / 18% / 6% | 77% / 13% / 10% | 80% / 13% / 7% (n=95) |
| v4-prompt-rule | labor | 100 | 73% / 17% / 7% | 76% / 11% / 12% | 79% / 11% / 9% (n=95) |
| v5-labels-rejected | labor | 100 | 72% / 16% / 9% | 75% / 13% / 12% | 78% / 14% / 8% (n=95) |
| v6-country-filter | labor | 100 | 77% / 15% / 5% | 82% / 10% / 7% | 85% / 9% / 4% (n=95) |
| v6-country-filter | real-estate | 82 | 74% / 22% / 4% | 72% / 23% / 5% | 74% / 22% / 4% (n=80) |
