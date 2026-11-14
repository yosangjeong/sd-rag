# Answer quality (served pipeline: translation union + rerank + GLM-4.7 answers)

Real-estate test sample: 0 items spread over language and file type; unanswerable: 64 real questions the corpus does not answer. Judge: deepseek.v3.2 (prompts in eval/answers.py).

| Measure | Result |
|---|---|
| correctness (vs reference) | - |
| groundedness (vs cited sources) | - |
| a citation overlaps the gold | 0% |
| unanswerable: declined | declined 78%, answered 22% |
| latency p50 | 8.4 s |
