# Answer quality (served pipeline: translation union + rerank + GLM-4.7 answers)

Test sample: 100 items spread over language and file type; unanswerable: 27 real questions the corpus does not answer. Judge: deepseek.v3.2 (prompts in eval/answers.py).

| Measure | Result |
|---|---|
| correctness (vs reference) | correct 74%, partial 14%, wrong 12% |
| groundedness (vs cited sources) | supported 84%, partly 9%, unsupported 7% |
| a citation overlaps the gold | 89% |
| unanswerable: declined | declined 70%, answered 30% |
| latency p50 | 5.4 s |
