
### all=all

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 21 | 0.809 | 0.905 | 0.905 | 0.881 | 0.843 | 0.840 | 0.952 | 3386 | 4742 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 21 | 0.809 | 0.905 | 0.905 | 0.905 | 0.843 | 0.858 | 0.952 | 3412 | 4905 |
| bm25@chunks-fixed | 21 | 0.286 | 0.476 | 0.571 | 0.571 | 0.386 | 0.431 | 0.571 | 2 | 4 |
| bm25@chunks-structure | 21 | 0.333 | 0.476 | 0.571 | 0.571 | 0.414 | 0.448 | 0.571 | 2 | 2 |
| dense@chunks-fixed | 21 | 0.476 | 0.762 | 0.905 | 0.881 | 0.605 | 0.658 | 0.952 | 252 | 280 |
| dense@chunks-structure | 21 | 0.524 | 0.809 | 0.857 | 0.833 | 0.653 | 0.682 | 0.905 | 268 | 514 |
| hybrid@chunks-fixed | 21 | 0.476 | 0.667 | 0.809 | 0.786 | 0.573 | 0.602 | 0.905 | 262 | 426 |
| hybrid@chunks-structure | 21 | 0.429 | 0.857 | 0.857 | 0.833 | 0.604 | 0.656 | 0.905 | 261 | 327 |

### file_type=docx

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 3 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 3649 | 3649 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 3 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 3412 | 3412 |
| bm25@chunks-fixed | 3 | 0.667 | 0.667 | 1.000 | 1.000 | 0.708 | 0.772 | 1.000 | 2 | 2 |
| bm25@chunks-structure | 3 | 0.667 | 0.667 | 1.000 | 1.000 | 0.708 | 0.772 | 1.000 | 2 | 2 |
| dense@chunks-fixed | 3 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 246 | 246 |
| dense@chunks-structure | 3 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 270 | 270 |
| hybrid@chunks-fixed | 3 | 0.667 | 1.000 | 1.000 | 1.000 | 0.833 | 0.877 | 1.000 | 257 | 257 |
| hybrid@chunks-structure | 3 | 0.667 | 1.000 | 1.000 | 1.000 | 0.833 | 0.877 | 1.000 | 255 | 255 |

### file_type=docx+pdf

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 1 | 1.000 | 1.000 | 1.000 | 0.500 | 1.000 | 0.613 | 1.000 | 3586 | 3586 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 3229 | 3229 |
| bm25@chunks-fixed | 1 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 2 | 2 |
| bm25@chunks-structure | 1 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 2 | 2 |
| dense@chunks-fixed | 1 | 1.000 | 1.000 | 1.000 | 0.500 | 1.000 | 0.613 | 1.000 | 262 | 262 |
| dense@chunks-structure | 1 | 1.000 | 1.000 | 1.000 | 0.500 | 1.000 | 0.613 | 1.000 | 249 | 249 |
| hybrid@chunks-fixed | 1 | 1.000 | 1.000 | 1.000 | 0.500 | 1.000 | 0.613 | 1.000 | 303 | 303 |
| hybrid@chunks-structure | 1 | 0.000 | 1.000 | 1.000 | 0.500 | 0.333 | 0.307 | 1.000 | 488 | 488 |

### file_type=hwpx

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 5 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 3443 | 4515 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 5 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 3942 | 4600 |
| bm25@chunks-fixed | 5 | 0.200 | 0.200 | 0.200 | 0.200 | 0.200 | 0.200 | 0.200 | 2 | 4 |
| bm25@chunks-structure | 5 | 0.200 | 0.200 | 0.200 | 0.200 | 0.218 | 0.200 | 0.200 | 2 | 2 |
| dense@chunks-fixed | 5 | 0.400 | 0.800 | 0.800 | 0.800 | 0.550 | 0.612 | 1.000 | 252 | 256 |
| dense@chunks-structure | 5 | 0.800 | 0.800 | 0.800 | 0.800 | 0.817 | 0.800 | 1.000 | 273 | 288 |
| hybrid@chunks-fixed | 5 | 0.200 | 0.200 | 0.800 | 0.800 | 0.302 | 0.400 | 1.000 | 262 | 323 |
| hybrid@chunks-structure | 5 | 0.000 | 1.000 | 1.000 | 1.000 | 0.417 | 0.565 | 1.000 | 272 | 296 |

### file_type=pdf

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 7 | 0.571 | 0.857 | 0.857 | 0.857 | 0.671 | 0.717 | 1.000 | 3346 | 3561 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 7 | 0.571 | 0.857 | 0.857 | 0.857 | 0.671 | 0.717 | 1.000 | 3297 | 3611 |
| bm25@chunks-fixed | 7 | 0.286 | 0.429 | 0.571 | 0.571 | 0.378 | 0.423 | 0.571 | 2 | 3 |
| bm25@chunks-structure | 7 | 0.286 | 0.429 | 0.571 | 0.571 | 0.378 | 0.423 | 0.571 | 2 | 2 |
| dense@chunks-fixed | 7 | 0.286 | 0.571 | 1.000 | 1.000 | 0.488 | 0.607 | 1.000 | 252 | 280 |
| dense@chunks-structure | 7 | 0.286 | 0.714 | 0.857 | 0.857 | 0.446 | 0.544 | 0.857 | 277 | 514 |
| hybrid@chunks-fixed | 7 | 0.286 | 0.714 | 0.714 | 0.714 | 0.431 | 0.484 | 0.857 | 271 | 290 |
| hybrid@chunks-structure | 7 | 0.429 | 0.714 | 0.714 | 0.714 | 0.538 | 0.574 | 0.857 | 257 | 290 |

### file_type=scan

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 5 | 0.800 | 0.800 | 0.800 | 0.800 | 0.800 | 0.800 | 0.800 | 3386 | 3685 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 5 | 0.800 | 0.800 | 0.800 | 0.800 | 0.800 | 0.800 | 0.800 | 3394 | 3523 |
| bm25@chunks-fixed | 5 | 0.200 | 0.800 | 0.800 | 0.800 | 0.467 | 0.552 | 0.800 | 2 | 2 |
| bm25@chunks-structure | 5 | 0.400 | 0.800 | 0.800 | 0.800 | 0.567 | 0.626 | 0.800 | 2 | 2 |
| dense@chunks-fixed | 5 | 0.400 | 0.800 | 0.800 | 0.800 | 0.507 | 0.577 | 0.800 | 265 | 273 |
| dense@chunks-structure | 5 | 0.200 | 0.800 | 0.800 | 0.800 | 0.500 | 0.579 | 0.800 | 254 | 256 |
| hybrid@chunks-fixed | 5 | 0.800 | 0.800 | 0.800 | 0.800 | 0.800 | 0.800 | 0.800 | 258 | 258 |
| hybrid@chunks-structure | 5 | 0.800 | 0.800 | 0.800 | 0.800 | 0.800 | 0.800 | 0.800 | 262 | 269 |

### kind=fact

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 18 | 0.833 | 0.944 | 0.944 | 0.944 | 0.872 | 0.890 | 0.944 | 3373 | 4742 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 18 | 0.833 | 0.944 | 0.944 | 0.944 | 0.872 | 0.890 | 0.944 | 3403 | 4905 |
| bm25@chunks-fixed | 18 | 0.333 | 0.500 | 0.611 | 0.611 | 0.422 | 0.467 | 0.611 | 2 | 4 |
| bm25@chunks-structure | 18 | 0.333 | 0.500 | 0.611 | 0.611 | 0.427 | 0.467 | 0.611 | 2 | 2 |
| dense@chunks-fixed | 18 | 0.500 | 0.778 | 0.889 | 0.889 | 0.632 | 0.694 | 0.944 | 252 | 278 |
| dense@chunks-structure | 18 | 0.556 | 0.833 | 0.889 | 0.889 | 0.678 | 0.726 | 0.944 | 272 | 514 |
| hybrid@chunks-fixed | 18 | 0.444 | 0.667 | 0.833 | 0.833 | 0.554 | 0.612 | 0.944 | 264 | 426 |
| hybrid@chunks-structure | 18 | 0.444 | 0.889 | 0.889 | 0.889 | 0.631 | 0.693 | 0.944 | 261 | 304 |

### kind=multi

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 1 | 1.000 | 1.000 | 1.000 | 0.500 | 1.000 | 0.613 | 1.000 | 3586 | 3586 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 3229 | 3229 |
| bm25@chunks-fixed | 1 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 2 | 2 |
| bm25@chunks-structure | 1 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 2 | 2 |
| dense@chunks-fixed | 1 | 1.000 | 1.000 | 1.000 | 0.500 | 1.000 | 0.613 | 1.000 | 262 | 262 |
| dense@chunks-structure | 1 | 1.000 | 1.000 | 1.000 | 0.500 | 1.000 | 0.613 | 1.000 | 249 | 249 |
| hybrid@chunks-fixed | 1 | 1.000 | 1.000 | 1.000 | 0.500 | 1.000 | 0.613 | 1.000 | 303 | 303 |
| hybrid@chunks-structure | 1 | 0.000 | 1.000 | 1.000 | 0.500 | 0.333 | 0.307 | 1.000 | 488 | 488 |

### kind=table

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 2 | 0.500 | 0.500 | 0.500 | 0.500 | 0.500 | 0.500 | 1.000 | 3185 | 2484 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 2 | 0.500 | 0.500 | 0.500 | 0.500 | 0.500 | 0.500 | 1.000 | 3815 | 3611 |
| bm25@chunks-fixed | 2 | 0.000 | 0.500 | 0.500 | 0.500 | 0.250 | 0.316 | 0.500 | 2 | 2 |
| bm25@chunks-structure | 2 | 0.500 | 0.500 | 0.500 | 0.500 | 0.500 | 0.500 | 0.500 | 1 | 1 |
| dense@chunks-fixed | 2 | 0.000 | 0.500 | 1.000 | 1.000 | 0.163 | 0.351 | 1.000 | 290 | 234 |
| dense@chunks-structure | 2 | 0.000 | 0.500 | 0.500 | 0.500 | 0.250 | 0.316 | 0.500 | 261 | 256 |
| hybrid@chunks-fixed | 2 | 0.500 | 0.500 | 0.500 | 0.500 | 0.531 | 0.500 | 0.500 | 252 | 247 |
| hybrid@chunks-structure | 2 | 0.500 | 0.500 | 0.500 | 0.500 | 0.500 | 0.500 | 0.500 | 238 | 237 |

### lang=en->en

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 5 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 3561 | 3685 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 5 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 3430 | 3523 |
| bm25@chunks-fixed | 5 | 0.400 | 1.000 | 1.000 | 1.000 | 0.667 | 0.752 | 1.000 | 2 | 3 |
| bm25@chunks-structure | 5 | 0.400 | 1.000 | 1.000 | 1.000 | 0.667 | 0.752 | 1.000 | 2 | 2 |
| dense@chunks-fixed | 5 | 0.600 | 0.800 | 1.000 | 1.000 | 0.692 | 0.763 | 1.000 | 263 | 265 |
| dense@chunks-structure | 5 | 0.400 | 1.000 | 1.000 | 1.000 | 0.650 | 0.739 | 1.000 | 254 | 277 |
| hybrid@chunks-fixed | 5 | 0.800 | 1.000 | 1.000 | 1.000 | 0.867 | 0.900 | 1.000 | 258 | 275 |
| hybrid@chunks-structure | 5 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 265 | 290 |

### lang=en->ko

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 7 | 0.571 | 0.714 | 0.714 | 0.643 | 0.600 | 0.571 | 0.857 | 3443 | 4515 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 7 | 0.571 | 0.714 | 0.714 | 0.714 | 0.600 | 0.627 | 0.857 | 3611 | 4600 |
| bm25@chunks-fixed | 7 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 2 | 4 |
| bm25@chunks-structure | 7 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 2 | 2 |
| dense@chunks-fixed | 7 | 0.286 | 0.571 | 0.857 | 0.786 | 0.434 | 0.478 | 0.857 | 262 | 278 |
| dense@chunks-structure | 7 | 0.571 | 0.571 | 0.714 | 0.643 | 0.589 | 0.561 | 0.714 | 267 | 306 |
| hybrid@chunks-fixed | 7 | 0.286 | 0.286 | 0.571 | 0.500 | 0.348 | 0.326 | 0.714 | 265 | 426 |
| hybrid@chunks-structure | 7 | 0.000 | 0.571 | 0.571 | 0.500 | 0.236 | 0.286 | 0.714 | 272 | 327 |

### lang=ko->en

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 2 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 2757 | 2513 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 2 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 2740 | 2509 |
| bm25@chunks-fixed | 2 | 0.000 | 0.000 | 0.500 | 0.500 | 0.071 | 0.167 | 0.500 | 2 | 2 |
| bm25@chunks-structure | 2 | 0.000 | 0.000 | 0.500 | 0.500 | 0.071 | 0.167 | 0.500 | 2 | 2 |
| dense@chunks-fixed | 2 | 0.500 | 1.000 | 1.000 | 1.000 | 0.750 | 0.816 | 1.000 | 261 | 242 |
| dense@chunks-structure | 2 | 0.500 | 1.000 | 1.000 | 1.000 | 0.750 | 0.816 | 1.000 | 271 | 254 |
| hybrid@chunks-fixed | 2 | 0.000 | 1.000 | 1.000 | 1.000 | 0.267 | 0.443 | 1.000 | 261 | 251 |
| hybrid@chunks-structure | 2 | 0.000 | 1.000 | 1.000 | 1.000 | 0.350 | 0.509 | 1.000 | 278 | 252 |

### lang=ko->ko

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 7 | 0.857 | 1.000 | 1.000 | 1.000 | 0.929 | 0.947 | 1.000 | 3346 | 3886 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 7 | 0.857 | 1.000 | 1.000 | 1.000 | 0.929 | 0.947 | 1.000 | 3412 | 4019 |
| bm25@chunks-fixed | 7 | 0.571 | 0.714 | 0.857 | 0.857 | 0.661 | 0.707 | 0.857 | 2 | 2 |
| bm25@chunks-structure | 7 | 0.714 | 0.714 | 0.857 | 0.857 | 0.745 | 0.759 | 0.857 | 2 | 2 |
| dense@chunks-fixed | 7 | 0.571 | 0.857 | 0.857 | 0.857 | 0.671 | 0.717 | 1.000 | 247 | 252 |
| dense@chunks-structure | 7 | 0.571 | 0.857 | 0.857 | 0.857 | 0.691 | 0.723 | 1.000 | 273 | 285 |
| hybrid@chunks-fixed | 7 | 0.571 | 0.714 | 0.857 | 0.857 | 0.675 | 0.709 | 1.000 | 262 | 301 |
| hybrid@chunks-structure | 7 | 0.571 | 1.000 | 1.000 | 1.000 | 0.762 | 0.823 | 1.000 | 252 | 256 |
