# Answer quality (served pipeline: translation union + rerank + GLM-4.7 answers)

Test sample: 100 items spread over language and file type; unanswerable: 27 real questions the corpus does not answer. Judge: deepseek.v3.2 (prompts in eval/answers.py).

| Measure | Result |
|---|---|
| correctness (vs reference) | correct 73%, partial 17%, wrong 7%, no_answer 3% |
| groundedness (vs cited sources) | supported 88%, partly 7%, unsupported 5% |
| a citation overlaps the gold | 89% |
| unanswerable: declined | answered 52%, declined 48% |
| latency p50 | 4.9 s |
