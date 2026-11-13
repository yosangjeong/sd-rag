# Answer quality (served pipeline: translation union + rerank + GLM-4.7 answers)

Test sample: 100 items spread over language and file type; unanswerable: 27 real questions the corpus does not answer. Judge: deepseek.v3.2 (prompts in eval/answers.py).

| Measure | Result |
|---|---|
| correctness (vs reference) | correct 72%, partial 16%, wrong 9%, no_answer 3% |
| groundedness (vs cited sources) | supported 85%, unsupported 8%, partly 7% |
| a citation overlaps the gold | 91% |
| unanswerable: declined | declined 52%, answered 48% |
| latency p50 | 9.1 s |
