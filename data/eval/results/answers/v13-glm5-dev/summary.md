# Answer quality (served pipeline: translation union + rerank + zai.glm-5 answers)

Test sample: 50 items spread over language and file type; unanswerable: 27 real questions the corpus does not answer. Judge: deepseek.v3.2 (prompts in eval/answers.py).

| Measure | Result |
|---|---|
| correctness (vs reference) | correct 90%, wrong 8%, partial 2% |
| groundedness (vs cited sources) | supported 88%, partly 8%, unsupported 4% |
| a citation overlaps the gold | 94% |
| unanswerable: declined | declined 81%, answered 19% |
| latency p50 | 12.5 s |
