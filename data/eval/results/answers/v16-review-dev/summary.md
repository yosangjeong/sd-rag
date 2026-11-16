# Answer quality (served pipeline: wide pool + rerank + GLM-4.7 answers)

Test sample: 50 items spread over language and file type; unanswerable: 27 real questions the corpus does not answer. Judge: deepseek.v3.2 (prompts in eval/answers.py).

| Measure | Result |
|---|---|
| correctness (vs reference) | correct 86%, wrong 8%, partial 4%, no_answer 2% |
| correctness, judge v4 (whole articles) | correct 72%, partial 18%, wrong 10% |
| groundedness (vs cited sources) | supported 88%, partly 8%, unsupported 4% |
| a citation overlaps the gold | 94% |
| unanswerable: declined | declined 74%, answered 26% |
| latency p50 | 7.1 s |
