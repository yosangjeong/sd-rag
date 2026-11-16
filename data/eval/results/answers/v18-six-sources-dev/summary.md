# Answer quality (served pipeline: wide pool + rerank + GLM-4.7 answers)

Test sample: 50 items spread over language and file type; unanswerable: 27 real questions the corpus does not answer. Judge: deepseek.v3.2 (prompts in eval/answers.py).

| Measure | Result |
|---|---|
| correctness (vs reference) | correct 84%, partial 12%, wrong 2%, no_answer 2% |
| correctness, judge v4 (whole articles) | correct 70%, partial 24%, wrong 6% |
| groundedness (vs cited sources) | supported 90%, unsupported 8%, partly 2% |
| a citation overlaps the gold | 94% |
| unanswerable: declined | declined 81%, answered 19% |
| latency p50 | 7.2 s |
