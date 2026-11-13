# Answer quality (served pipeline: translation union + rerank + GLM-4.7 answers)

Test sample: 100 items spread over language and file type; unanswerable: 27 real questions the corpus does not answer. Judge: deepseek.v3.2 (prompts in eval/answers.py).

| Measure | Result |
|---|---|
| correctness (vs reference) | correct 77%, partial 13%, wrong 10% |
| groundedness (vs cited sources) | supported 88%, partly 7%, unsupported 5% |
| a citation overlaps the gold | 90% |
| unanswerable: declined | declined 67%, answered 33% |
| latency p50 | 5.8 s |
