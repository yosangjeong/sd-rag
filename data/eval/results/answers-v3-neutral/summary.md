# Answer quality (served pipeline: translation union + rerank + GLM-4.7 answers)

Test sample: 100 items spread over language and file type; unanswerable: 27 real questions the corpus does not answer. Judge: deepseek.v3.2 (prompts in eval/answers.py).

| Measure | Result |
|---|---|
| correctness (vs reference) | correct 74%, partial 18%, wrong 6%, no_answer 2% |
| groundedness (vs cited sources) | supported 89%, partly 7%, unsupported 4% |
| a citation overlaps the gold | 89% |
| unanswerable: declined | answered 59%, declined 41% |
| latency p50 | 4.7 s |
