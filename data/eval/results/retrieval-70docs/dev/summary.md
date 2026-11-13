
### all=all

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 85 | 0.871 | 0.953 | 0.953 | 0.941 | 0.902 | 0.908 | 0.965 | 3660 | 6323 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 85 | 0.824 | 0.918 | 0.953 | 0.929 | 0.869 | 0.876 | 0.965 | 3340 | 3760 |

### file_type=docx

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 15 | 0.933 | 1.000 | 1.000 | 1.000 | 0.956 | 0.967 | 1.000 | 3514 | 6323 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 15 | 0.800 | 0.933 | 0.933 | 0.933 | 0.856 | 0.875 | 0.933 | 3386 | 4064 |

### file_type=docx+hwpx

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 1 | 1.000 | 1.000 | 1.000 | 0.500 | 1.000 | 0.613 | 1.000 | 3471 | 3471 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 1 | 1.000 | 1.000 | 1.000 | 0.500 | 1.000 | 0.613 | 1.000 | 3158 | 3158 |

### file_type=docx+pdf

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 3722 | 3722 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 3752 | 3752 |

### file_type=hwpx

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 14 | 0.786 | 0.929 | 0.929 | 0.929 | 0.836 | 0.858 | 0.929 | 3918 | 6020 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 14 | 0.714 | 0.857 | 0.929 | 0.929 | 0.798 | 0.830 | 1.000 | 3137 | 3465 |

### file_type=hwpx+pdf

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 1 | 1.000 | 1.000 | 1.000 | 0.500 | 1.000 | 0.613 | 1.000 | 3487 | 3487 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 1 | 1.000 | 1.000 | 1.000 | 0.500 | 1.000 | 0.613 | 1.000 | 3536 | 3536 |

### file_type=pdf

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 39 | 0.846 | 0.923 | 0.923 | 0.923 | 0.880 | 0.895 | 0.949 | 3660 | 6565 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 39 | 0.821 | 0.897 | 0.949 | 0.923 | 0.861 | 0.871 | 0.949 | 3310 | 3746 |

### file_type=scan

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 14 | 0.929 | 1.000 | 1.000 | 1.000 | 0.952 | 0.964 | 1.000 | 3766 | 6259 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 14 | 0.929 | 1.000 | 1.000 | 1.000 | 0.952 | 0.964 | 1.000 | 3558 | 3760 |

### kind=fact

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 75 | 0.853 | 0.947 | 0.947 | 0.947 | 0.889 | 0.906 | 0.960 | 3665 | 6565 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 75 | 0.800 | 0.907 | 0.947 | 0.933 | 0.852 | 0.869 | 0.960 | 3345 | 3803 |

### kind=multi

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 3 | 1.000 | 1.000 | 1.000 | 0.667 | 1.000 | 0.742 | 1.000 | 3487 | 3487 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 3 | 1.000 | 1.000 | 1.000 | 0.667 | 1.000 | 0.742 | 1.000 | 3536 | 3536 |

### kind=table

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 7 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 3318 | 4393 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 7 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 3297 | 3431 |

### lang=en->en

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 16 | 0.875 | 0.938 | 0.938 | 0.938 | 0.906 | 0.914 | 1.000 | 4789 | 6243 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 16 | 0.938 | 0.938 | 0.938 | 0.938 | 0.938 | 0.938 | 0.938 | 3458 | 3854 |

### lang=en->ko

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 21 | 0.905 | 0.952 | 0.952 | 0.929 | 0.914 | 0.905 | 0.952 | 3887 | 6323 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 21 | 0.857 | 0.905 | 0.952 | 0.929 | 0.889 | 0.886 | 1.000 | 3491 | 4064 |

### lang=ko->en

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 13 | 0.692 | 0.923 | 0.923 | 0.923 | 0.780 | 0.812 | 0.923 | 3491 | 6565 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 13 | 0.692 | 0.846 | 1.000 | 1.000 | 0.780 | 0.832 | 1.000 | 3216 | 3458 |

### lang=ko->ko

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 35 | 0.914 | 0.971 | 0.971 | 0.957 | 0.938 | 0.942 | 0.971 | 3448 | 6020 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 35 | 0.800 | 0.943 | 0.943 | 0.900 | 0.860 | 0.857 | 0.943 | 3297 | 3676 |
