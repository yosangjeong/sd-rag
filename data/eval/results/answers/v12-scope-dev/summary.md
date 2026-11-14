# Answer quality (served pipeline: translation union + rerank + GLM-4.7 answers)

Test sample: 50 items spread over language and file type; unanswerable: 27 real questions the corpus does not answer. Judge: deepseek.v3.2 (prompts in eval/answers.py).

| Measure | Result |
|---|---|
| correctness (vs reference) | correct 88%, wrong 6%, partial 6% |
| groundedness (vs cited sources) | supported 84%, partly 10%, unsupported 6% |
| a citation overlaps the gold | 100% |
| unanswerable: declined | declined 70%, answered 30% |
| latency p50 | 8.4 s |
