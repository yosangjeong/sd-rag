# Answer quality (served pipeline: translation union + rerank + openai.gpt-oss-120b-1:0 answers)

Test sample: 50 items spread over language and file type; unanswerable: 27 real questions the corpus does not answer. Judge: deepseek.v3.2 (prompts in eval/answers.py).

| Measure | Result |
|---|---|
| correctness (vs reference) | correct 86%, partial 8%, wrong 4%, no_answer 2% |
| groundedness (vs cited sources) | supported 88%, unsupported 8%, partly 4% |
| a citation overlaps the gold | 98% |
| unanswerable: declined | declined 56%, answered 44% |
| latency p50 | 9.0 s |
