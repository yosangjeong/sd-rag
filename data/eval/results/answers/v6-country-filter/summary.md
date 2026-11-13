# Answer quality (served pipeline: translation union + rerank + GLM-4.7 answers)

Test sample: 100 items spread over language and file type; unanswerable: 27 real questions the corpus does not answer. Judge: deepseek.v3.2 (prompts in eval/answers.py).

| Measure | Result |
|---|---|
| correctness (vs reference) | correct 77%, partial 15%, wrong 5%, no_answer 3% |
| groundedness (vs cited sources) | supported 85%, unsupported 10%, partly 5% |
| a citation overlaps the gold | 92% |
| unanswerable: declined | declined 63%, answered 37% |
| latency p50 | 5.7 s |
