# Answer quality (served pipeline: translation union + rerank + GLM-4.7 answers)

Test sample: 100 items spread over language and file type; unanswerable: 27 real questions the corpus does not answer. Judge: deepseek.v3.2 (prompts in eval/answers.py).

| Measure | Result |
|---|---|
| correctness (vs reference) | correct 87%, wrong 7%, partial 6% |
| groundedness (vs cited sources) | supported 83%, partly 9%, unsupported 8% |
| a citation overlaps the gold | 96% |
| unanswerable: declined | declined 67%, answered 33% |
| latency p50 | 8.1 s |
