
### all=all

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 21 | 0.809 | 0.905 | 0.905 | 0.881 | 0.843 | 0.840 | 0.952 | 3386 | 4742 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 21 | 0.809 | 0.905 | 0.905 | 0.905 | 0.843 | 0.858 | 0.952 | 3412 | 4905 |

### file_type=docx

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 3 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 3649 | 3649 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 3 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 3412 | 3412 |

### file_type=docx+pdf

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 1 | 1.000 | 1.000 | 1.000 | 0.500 | 1.000 | 0.613 | 1.000 | 3586 | 3586 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 3229 | 3229 |

### file_type=hwpx

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 5 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 3443 | 4515 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 5 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 3942 | 4600 |

### file_type=pdf

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 7 | 0.571 | 0.857 | 0.857 | 0.857 | 0.671 | 0.717 | 1.000 | 3346 | 3561 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 7 | 0.571 | 0.857 | 0.857 | 0.857 | 0.671 | 0.717 | 1.000 | 3297 | 3611 |

### file_type=scan

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 5 | 0.800 | 0.800 | 0.800 | 0.800 | 0.800 | 0.800 | 0.800 | 3386 | 3685 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 5 | 0.800 | 0.800 | 0.800 | 0.800 | 0.800 | 0.800 | 0.800 | 3394 | 3523 |

### kind=fact

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 18 | 0.833 | 0.944 | 0.944 | 0.944 | 0.872 | 0.890 | 0.944 | 3373 | 4742 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 18 | 0.833 | 0.944 | 0.944 | 0.944 | 0.872 | 0.890 | 0.944 | 3403 | 4905 |

### kind=multi

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 1 | 1.000 | 1.000 | 1.000 | 0.500 | 1.000 | 0.613 | 1.000 | 3586 | 3586 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 3229 | 3229 |

### kind=table

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 2 | 0.500 | 0.500 | 0.500 | 0.500 | 0.500 | 0.500 | 1.000 | 3185 | 2484 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 2 | 0.500 | 0.500 | 0.500 | 0.500 | 0.500 | 0.500 | 1.000 | 3815 | 3611 |

### lang=en->en

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 5 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 3561 | 3685 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 5 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 3430 | 3523 |

### lang=en->ko

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 7 | 0.571 | 0.714 | 0.714 | 0.643 | 0.600 | 0.571 | 0.857 | 3443 | 4515 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 7 | 0.571 | 0.714 | 0.714 | 0.714 | 0.600 | 0.627 | 0.857 | 3611 | 4600 |

### lang=ko->en

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 2 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 2757 | 2513 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 2 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 2740 | 2509 |

### lang=ko->ko

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 7 | 0.857 | 1.000 | 1.000 | 1.000 | 0.929 | 0.947 | 1.000 | 3346 | 3886 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 7 | 0.857 | 1.000 | 1.000 | 1.000 | 0.929 | 0.947 | 1.000 | 3412 | 4019 |
