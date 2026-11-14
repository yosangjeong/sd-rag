
### all=all

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 31 | 0.839 | 0.871 | 0.871 | 0.871 | 0.847 | 0.853 | 0.968 | 3692 | 4739 |
| hybrid@chunks-structure | 31 | 0.194 | 0.677 | 0.839 | 0.839 | 0.430 | 0.527 | 0.968 | 314 | 493 |
| wide+rerank+jur@chunks-structure~glm-4.7 | 31 | 0.806 | 0.903 | 0.903 | 0.903 | 0.840 | 0.855 | 1.000 | 6832 | 7856 |
| wide_fused+rerank+jur@chunks-structure~glm-4.7 | 31 | 0.774 | 0.839 | 0.871 | 0.871 | 0.805 | 0.821 | 0.968 | 6130 | 7339 |

### file_type=docx

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 14 | 0.857 | 0.929 | 0.929 | 0.929 | 0.875 | 0.888 | 0.929 | 3912 | 4739 |
| hybrid@chunks-structure | 14 | 0.143 | 0.643 | 0.857 | 0.857 | 0.388 | 0.496 | 1.000 | 345 | 493 |
| wide+rerank+jur@chunks-structure~glm-4.7 | 14 | 0.786 | 1.000 | 1.000 | 1.000 | 0.860 | 0.894 | 1.000 | 6861 | 7780 |
| wide_fused+rerank+jur@chunks-structure~glm-4.7 | 14 | 0.714 | 0.857 | 0.929 | 0.929 | 0.783 | 0.818 | 0.929 | 6510 | 7770 |

### file_type=hwpx

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 4 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 3517 | 3560 |
| hybrid@chunks-structure | 4 | 0.500 | 1.000 | 1.000 | 1.000 | 0.750 | 0.816 | 1.000 | 319 | 325 |
| wide+rerank+jur@chunks-structure~glm-4.7 | 4 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 5088 | 5469 |
| wide_fused+rerank+jur@chunks-structure~glm-4.7 | 4 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 5475 | 6020 |

### file_type=pdf

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 13 | 0.769 | 0.769 | 0.769 | 0.769 | 0.769 | 0.769 | 1.000 | 3569 | 3823 |
| hybrid@chunks-structure | 13 | 0.154 | 0.615 | 0.769 | 0.769 | 0.377 | 0.472 | 0.923 | 303 | 460 |
| wide+rerank+jur@chunks-structure~glm-4.7 | 13 | 0.769 | 0.769 | 0.769 | 0.769 | 0.769 | 0.769 | 1.000 | 6814 | 7856 |
| wide_fused+rerank+jur@chunks-structure~glm-4.7 | 13 | 0.769 | 0.769 | 0.769 | 0.769 | 0.769 | 0.769 | 1.000 | 6049 | 7060 |

### kind=real

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 31 | 0.839 | 0.871 | 0.871 | 0.871 | 0.847 | 0.853 | 0.968 | 3692 | 4739 |
| hybrid@chunks-structure | 31 | 0.194 | 0.677 | 0.839 | 0.839 | 0.430 | 0.527 | 0.968 | 314 | 493 |
| wide+rerank+jur@chunks-structure~glm-4.7 | 31 | 0.806 | 0.903 | 0.903 | 0.903 | 0.840 | 0.855 | 1.000 | 6832 | 7856 |
| wide_fused+rerank+jur@chunks-structure~glm-4.7 | 31 | 0.774 | 0.839 | 0.871 | 0.871 | 0.805 | 0.821 | 0.968 | 6130 | 7339 |

### lang=ko->ko

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 31 | 0.839 | 0.871 | 0.871 | 0.871 | 0.847 | 0.853 | 0.968 | 3692 | 4739 |
| hybrid@chunks-structure | 31 | 0.194 | 0.677 | 0.839 | 0.839 | 0.430 | 0.527 | 0.968 | 314 | 493 |
| wide+rerank+jur@chunks-structure~glm-4.7 | 31 | 0.806 | 0.903 | 0.903 | 0.903 | 0.840 | 0.855 | 1.000 | 6832 | 7856 |
| wide_fused+rerank+jur@chunks-structure~glm-4.7 | 31 | 0.774 | 0.839 | 0.871 | 0.871 | 0.805 | 0.821 | 0.968 | 6130 | 7339 |
