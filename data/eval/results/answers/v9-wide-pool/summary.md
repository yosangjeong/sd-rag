# Answer quality (served pipeline: translation union + rerank + GLM-4.7 answers)

Test sample: 100 items spread over language and file type; unanswerable: 27 real questions the corpus does not answer. Judge: deepseek.v3.2 (prompts in eval/answers.py).

| Measure | Result |
|---|---|
| correctness (vs reference) | correct 85%, partial 8%, wrong 7% |
| groundedness (vs cited sources) | supported 82%, partly 9%, unsupported 9% |
| a citation overlaps the gold | 94% |
| unanswerable: declined | declined 74%, answered 26% |
| latency p50 | 6.4 s |
