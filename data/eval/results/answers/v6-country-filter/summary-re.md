# Answer quality (served pipeline: translation union + rerank + GLM-4.7 answers)

Real-estate test sample: 82 items spread over language and file type; unanswerable: 0 real questions the corpus does not answer. Judge: deepseek.v3.2 (prompts in eval/answers.py).

| Measure | Result |
|---|---|
| correctness (vs reference) | correct 74%, partial 22%, wrong 4% |
| groundedness (vs cited sources) | supported 90%, unsupported 6%, partly 4% |
| a citation overlaps the gold | 95% |
| unanswerable: declined | - |
| latency p50 | 12.2 s |
