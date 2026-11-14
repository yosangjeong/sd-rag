# Answer quality (served pipeline: translation union + rerank + GLM-4.7 answers)

Real-estate test sample: 82 items spread over language and file type; unanswerable: 30 real questions the corpus does not answer. Judge: deepseek.v3.2 (prompts in eval/answers.py).

| Measure | Result |
|---|---|
| correctness (vs reference) | correct 79%, partial 18%, wrong 2% |
| groundedness (vs cited sources) | supported 93%, partly 5%, unsupported 2% |
| a citation overlaps the gold | 96% |
| unanswerable: declined | declined 97%, answered 3% |
| latency p50 | 5.0 s |
