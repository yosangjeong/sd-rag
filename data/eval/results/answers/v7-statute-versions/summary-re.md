# Answer quality (served pipeline: translation union + rerank + GLM-4.7 answers)

Real-estate test sample: 82 items spread over language and file type; unanswerable: 30 real questions the corpus does not answer. Judge: deepseek.v3.2 (prompts in eval/answers.py).

| Measure | Result |
|---|---|
| correctness (vs reference) | correct 76%, partial 18%, wrong 6% |
| groundedness (vs cited sources) | supported 90%, unsupported 5%, partly 5% |
| a citation overlaps the gold | 93% |
| unanswerable: declined | declined 93%, answered 7% |
| latency p50 | 5.4 s |
