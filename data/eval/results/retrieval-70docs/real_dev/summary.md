
### all=all

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 31 | 0.839 | 0.871 | 0.871 | 0.871 | 0.847 | 0.853 | 0.968 | 3692 | 4739 |
| bm25@chunks-d2q | 31 | 0.355 | 0.645 | 0.742 | 0.742 | 0.484 | 0.540 | 0.935 | 4 | 6 |
| bm25@chunks-structure | 31 | 0.323 | 0.645 | 0.710 | 0.710 | 0.450 | 0.510 | 0.871 | 2 | 3 |
| hybrid@chunks-d2q | 31 | 0.355 | 0.677 | 0.839 | 0.839 | 0.521 | 0.596 | 0.968 | 266 | 344 |
| hybrid@chunks-structure | 31 | 0.194 | 0.677 | 0.839 | 0.839 | 0.430 | 0.527 | 0.968 | 314 | 493 |
| wide+rerank+jur@chunks-d2q~glm-4.7 | 31 | 0.806 | 0.903 | 0.935 | 0.935 | 0.852 | 0.873 | 1.000 | 6320 | 7393 |
| wide+rerank+jur@chunks-structure~glm-4.7 | 31 | 0.806 | 0.903 | 0.903 | 0.903 | 0.840 | 0.855 | 1.000 | 6832 | 7856 |
| wide_fused+rerank+jur@chunks-structure~glm-4.7 | 31 | 0.774 | 0.839 | 0.871 | 0.871 | 0.805 | 0.821 | 0.968 | 6130 | 7339 |

### file_type=docx

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 14 | 0.857 | 0.929 | 0.929 | 0.929 | 0.875 | 0.888 | 0.929 | 3912 | 4739 |
| bm25@chunks-d2q | 14 | 0.500 | 0.714 | 0.786 | 0.786 | 0.591 | 0.632 | 1.000 | 4 | 5 |
| bm25@chunks-structure | 14 | 0.429 | 0.714 | 0.786 | 0.786 | 0.505 | 0.571 | 0.857 | 2 | 2 |
| hybrid@chunks-d2q | 14 | 0.429 | 0.643 | 0.929 | 0.929 | 0.544 | 0.632 | 1.000 | 264 | 403 |
| hybrid@chunks-structure | 14 | 0.143 | 0.643 | 0.857 | 0.857 | 0.388 | 0.496 | 1.000 | 345 | 493 |
| wide+rerank+jur@chunks-d2q~glm-4.7 | 14 | 0.714 | 0.857 | 0.929 | 0.929 | 0.798 | 0.830 | 1.000 | 6402 | 7606 |
| wide+rerank+jur@chunks-structure~glm-4.7 | 14 | 0.786 | 1.000 | 1.000 | 1.000 | 0.860 | 0.894 | 1.000 | 6861 | 7780 |
| wide_fused+rerank+jur@chunks-structure~glm-4.7 | 14 | 0.714 | 0.857 | 0.929 | 0.929 | 0.783 | 0.818 | 0.929 | 6510 | 7770 |

### file_type=hwpx

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 4 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 3517 | 3560 |
| bm25@chunks-d2q | 4 | 0.000 | 0.500 | 0.750 | 0.750 | 0.244 | 0.366 | 1.000 | 5 | 6 |
| bm25@chunks-structure | 4 | 0.000 | 0.750 | 0.750 | 0.750 | 0.351 | 0.441 | 1.000 | 3 | 3 |
| hybrid@chunks-d2q | 4 | 0.250 | 0.750 | 0.750 | 0.750 | 0.518 | 0.566 | 1.000 | 257 | 258 |
| hybrid@chunks-structure | 4 | 0.500 | 1.000 | 1.000 | 1.000 | 0.750 | 0.816 | 1.000 | 319 | 325 |
| wide+rerank+jur@chunks-d2q~glm-4.7 | 4 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 5378 | 5890 |
| wide+rerank+jur@chunks-structure~glm-4.7 | 4 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 5088 | 5469 |
| wide_fused+rerank+jur@chunks-structure~glm-4.7 | 4 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 5475 | 6020 |

### file_type=pdf

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 13 | 0.769 | 0.769 | 0.769 | 0.769 | 0.769 | 0.769 | 1.000 | 3569 | 3823 |
| bm25@chunks-d2q | 13 | 0.308 | 0.615 | 0.692 | 0.692 | 0.443 | 0.495 | 0.846 | 4 | 7 |
| bm25@chunks-structure | 13 | 0.308 | 0.538 | 0.615 | 0.615 | 0.421 | 0.465 | 0.846 | 2 | 3 |
| hybrid@chunks-d2q | 13 | 0.308 | 0.692 | 0.769 | 0.769 | 0.498 | 0.566 | 0.923 | 269 | 278 |
| hybrid@chunks-structure | 13 | 0.154 | 0.615 | 0.769 | 0.769 | 0.377 | 0.472 | 0.923 | 303 | 460 |
| wide+rerank+jur@chunks-d2q~glm-4.7 | 13 | 0.846 | 0.923 | 0.923 | 0.923 | 0.865 | 0.879 | 1.000 | 6177 | 6596 |
| wide+rerank+jur@chunks-structure~glm-4.7 | 13 | 0.769 | 0.769 | 0.769 | 0.769 | 0.769 | 0.769 | 1.000 | 6814 | 7856 |
| wide_fused+rerank+jur@chunks-structure~glm-4.7 | 13 | 0.769 | 0.769 | 0.769 | 0.769 | 0.769 | 0.769 | 1.000 | 6049 | 7060 |

### kind=real

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 31 | 0.839 | 0.871 | 0.871 | 0.871 | 0.847 | 0.853 | 0.968 | 3692 | 4739 |
| bm25@chunks-d2q | 31 | 0.355 | 0.645 | 0.742 | 0.742 | 0.484 | 0.540 | 0.935 | 4 | 6 |
| bm25@chunks-structure | 31 | 0.323 | 0.645 | 0.710 | 0.710 | 0.450 | 0.510 | 0.871 | 2 | 3 |
| hybrid@chunks-d2q | 31 | 0.355 | 0.677 | 0.839 | 0.839 | 0.521 | 0.596 | 0.968 | 266 | 344 |
| hybrid@chunks-structure | 31 | 0.194 | 0.677 | 0.839 | 0.839 | 0.430 | 0.527 | 0.968 | 314 | 493 |
| wide+rerank+jur@chunks-d2q~glm-4.7 | 31 | 0.806 | 0.903 | 0.935 | 0.935 | 0.852 | 0.873 | 1.000 | 6320 | 7393 |
| wide+rerank+jur@chunks-structure~glm-4.7 | 31 | 0.806 | 0.903 | 0.903 | 0.903 | 0.840 | 0.855 | 1.000 | 6832 | 7856 |
| wide_fused+rerank+jur@chunks-structure~glm-4.7 | 31 | 0.774 | 0.839 | 0.871 | 0.871 | 0.805 | 0.821 | 0.968 | 6130 | 7339 |

### lang=ko->ko

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 31 | 0.839 | 0.871 | 0.871 | 0.871 | 0.847 | 0.853 | 0.968 | 3692 | 4739 |
| bm25@chunks-d2q | 31 | 0.355 | 0.645 | 0.742 | 0.742 | 0.484 | 0.540 | 0.935 | 4 | 6 |
| bm25@chunks-structure | 31 | 0.323 | 0.645 | 0.710 | 0.710 | 0.450 | 0.510 | 0.871 | 2 | 3 |
| hybrid@chunks-d2q | 31 | 0.355 | 0.677 | 0.839 | 0.839 | 0.521 | 0.596 | 0.968 | 266 | 344 |
| hybrid@chunks-structure | 31 | 0.194 | 0.677 | 0.839 | 0.839 | 0.430 | 0.527 | 0.968 | 314 | 493 |
| wide+rerank+jur@chunks-d2q~glm-4.7 | 31 | 0.806 | 0.903 | 0.935 | 0.935 | 0.852 | 0.873 | 1.000 | 6320 | 7393 |
| wide+rerank+jur@chunks-structure~glm-4.7 | 31 | 0.806 | 0.903 | 0.903 | 0.903 | 0.840 | 0.855 | 1.000 | 6832 | 7856 |
| wide_fused+rerank+jur@chunks-structure~glm-4.7 | 31 | 0.774 | 0.839 | 0.871 | 0.871 | 0.805 | 0.821 | 0.968 | 6130 | 7339 |
