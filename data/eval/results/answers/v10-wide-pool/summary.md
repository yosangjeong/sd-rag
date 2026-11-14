# Answer quality (served pipeline: translation union + rerank + GLM-4.7 answers)

Test sample: 100 items spread over language and file type; unanswerable: 27 real questions the corpus does not answer. Judge: deepseek.v3.2 (prompts in eval/answers.py).

| Measure | Result |
|---|---|
| correctness (vs reference) | correct 87%, wrong 7%, partial 6% |
| groundedness (vs cited sources) | supported 83%, partly 12%, unsupported 5% |
| a citation overlaps the gold | 92% |
| unanswerable: declined | declined 74%, answered 26% |
| latency p50 | 6.8 s |
