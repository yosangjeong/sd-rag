# Answer quality (served pipeline: translation union + rerank + GLM-4.7 answers)

Test sample: 100 items spread over language and file type; unanswerable: 27 real questions the corpus does not answer. Judge: deepseek.v3.2 (prompts in eval/answers.py).

| Measure | Result |
|---|---|
| correctness (vs reference) | correct 71%, partial 23%, wrong 6% |
| groundedness (vs cited sources) | supported 82%, unsupported 10%, partly 8% |
| a citation overlaps the gold | 93% |
| unanswerable: declined | declined 63%, answered 37% |
| latency p50 | 4.7 s |
