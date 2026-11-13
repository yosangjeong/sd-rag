# Answer quality (served pipeline: translation union + rerank + GLM-4.7 answers)

Test sample: 100 items spread over language and file type; unanswerable: 27 real questions the corpus does not answer. Judge: deepseek.v3.2 (prompts in eval/answers.py).

| Measure | Result |
|---|---|
| correctness (vs reference) | correct 72%, partial 20%, wrong 8% |
| groundedness (vs cited sources) | supported 86%, partly 9%, unsupported 5% |
| a citation overlaps the gold | 91% |
| unanswerable: declined | declined 67%, answered 33% |
| latency p50 | 11.3 s |
