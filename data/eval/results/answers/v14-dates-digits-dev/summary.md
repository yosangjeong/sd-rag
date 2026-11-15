# Answer quality (served pipeline: translation union + rerank + GLM-4.7 answers)

Test sample: 50 items spread over language and file type; unanswerable: 27 real questions the corpus does not answer. Judge: deepseek.v3.2 (prompts in eval/answers.py).

| Measure | Result |
|---|---|
| correctness (vs reference) | correct 90%, partial 8%, wrong 2% |
| groundedness (vs cited sources) | supported 92%, unsupported 6%, partly 2% |
| a citation overlaps the gold | 96% |
| unanswerable: declined | declined 74%, answered 26% |
| latency p50 | 8.3 s |
