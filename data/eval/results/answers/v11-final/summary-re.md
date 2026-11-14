# Answer quality (served pipeline: translation union + rerank + GLM-4.7 answers)

Real-estate test sample: 82 items spread over language and file type; unanswerable: 30 real questions the corpus does not answer. Judge: deepseek.v3.2 (prompts in eval/answers.py).

| Measure | Result |
|---|---|
| correctness (vs reference) | correct 89%, partial 7%, wrong 4% |
| groundedness (vs cited sources) | supported 94%, partly 5%, unsupported 1% |
| a citation overlaps the gold | 98% |
| unanswerable: declined | declined 90%, answered 10% |
| latency p50 | 7.7 s |
