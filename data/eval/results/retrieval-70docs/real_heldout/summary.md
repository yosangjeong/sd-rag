
### all=all

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| hybrid@chunks-structure | 33 | 0.424 | 0.576 | 0.727 | 0.727 | 0.526 | 0.569 | 0.970 | 267 | 338 |
| wide+rerank+jur@chunks-structure~glm-4.7 | 33 | 0.758 | 0.909 | 0.909 | 0.909 | 0.816 | 0.839 | 1.000 | 6591 | 8070 |

### file_type=docx

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| hybrid@chunks-structure | 11 | 0.455 | 0.727 | 0.727 | 0.727 | 0.583 | 0.615 | 0.909 | 265 | 303 |
| wide+rerank+jur@chunks-structure~glm-4.7 | 11 | 0.818 | 0.909 | 0.909 | 0.909 | 0.849 | 0.864 | 1.000 | 7273 | 8070 |

### file_type=hwpx

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| hybrid@chunks-structure | 6 | 0.333 | 0.500 | 1.000 | 1.000 | 0.496 | 0.613 | 1.000 | 264 | 269 |
| wide+rerank+jur@chunks-structure~glm-4.7 | 6 | 0.667 | 1.000 | 1.000 | 1.000 | 0.806 | 0.855 | 1.000 | 6316 | 6764 |

### file_type=pdf

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| hybrid@chunks-structure | 14 | 0.357 | 0.429 | 0.571 | 0.571 | 0.425 | 0.453 | 1.000 | 269 | 372 |
| wide+rerank+jur@chunks-structure~glm-4.7 | 14 | 0.714 | 0.857 | 0.857 | 0.857 | 0.768 | 0.790 | 1.000 | 6132 | 7160 |

### file_type=scan

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| hybrid@chunks-structure | 2 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 320 | 302 |
| wide+rerank+jur@chunks-structure~glm-4.7 | 2 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 6906 | 6854 |

### kind=real

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| hybrid@chunks-structure | 33 | 0.424 | 0.576 | 0.727 | 0.727 | 0.526 | 0.569 | 0.970 | 267 | 338 |
| wide+rerank+jur@chunks-structure~glm-4.7 | 33 | 0.758 | 0.909 | 0.909 | 0.909 | 0.816 | 0.839 | 1.000 | 6591 | 8070 |

### lang=en->en

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| hybrid@chunks-structure | 4 | 0.750 | 0.750 | 1.000 | 1.000 | 0.792 | 0.839 | 1.000 | 286 | 302 |
| wide+rerank+jur@chunks-structure~glm-4.7 | 4 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 6408 | 6854 |

### lang=ko->ko

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| hybrid@chunks-structure | 29 | 0.379 | 0.552 | 0.690 | 0.690 | 0.489 | 0.532 | 0.966 | 266 | 306 |
| wide+rerank+jur@chunks-structure~glm-4.7 | 29 | 0.724 | 0.897 | 0.897 | 0.897 | 0.790 | 0.817 | 1.000 | 6591 | 8070 |
