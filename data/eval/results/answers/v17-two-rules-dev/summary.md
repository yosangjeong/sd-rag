# Answer quality (served pipeline: wide pool + rerank + GLM-4.7 answers)

Test sample: 50 items spread over language and file type; unanswerable: 27 real questions the corpus does not answer. Judge: deepseek.v3.2 (prompts in eval/answers.py).

| Measure | Result |
|---|---|
| correctness (vs reference) | correct 90%, partial 6%, wrong 2%, no_answer 2% |
| correctness, judge v4 (whole articles) | correct 70%, partial 24%, wrong 6% |
| groundedness (vs cited sources) | supported 78%, partly 14%, unsupported 8% |
| a citation overlaps the gold | 92% |
| unanswerable: declined | declined 59%, answered 41% |
| latency p50 | 7.8 s |
