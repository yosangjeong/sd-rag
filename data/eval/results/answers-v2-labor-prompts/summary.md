# Answer quality (served pipeline: translation union + rerank + GLM-4.7 answers)

Test sample: 100 items spread over language and file type; unanswerable: 27 real questions the corpus does not answer. Judge: deepseek.v3.2 (prompts in eval/answers.py).

| Measure | Result |
|---|---|
| correctness (vs reference) | correct 71%, partial 23%, wrong 5%, no_answer 1% |
| groundedness (vs cited sources) | supported 86%, partly 9%, unsupported 5% |
| a citation overlaps the gold | 93% |
| unanswerable: declined | declined 59%, answered 41% |
| latency p50 | 7.6 s |
