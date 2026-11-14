
### all=all

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 85 | 0.882 | 0.953 | 0.953 | 0.941 | 0.911 | 0.915 | 0.977 | 3660 | 6323 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 85 | 0.824 | 0.929 | 0.953 | 0.929 | 0.873 | 0.879 | 0.977 | 3340 | 3760 |
| bm25@chunks-fixed | 85 | 0.353 | 0.459 | 0.529 | 0.523 | 0.402 | 0.428 | 0.600 | 2 | 3 |
| bm25@chunks-structure | 85 | 0.353 | 0.447 | 0.494 | 0.488 | 0.398 | 0.417 | 0.624 | 2 | 2 |
| dense@chunks-fixed | 85 | 0.412 | 0.659 | 0.788 | 0.776 | 0.530 | 0.579 | 0.906 | 257 | 308 |
| dense@chunks-structure | 85 | 0.459 | 0.682 | 0.859 | 0.835 | 0.566 | 0.620 | 0.918 | 256 | 308 |
| hybrid@chunks-fixed | 85 | 0.341 | 0.635 | 0.776 | 0.765 | 0.478 | 0.537 | 0.871 | 261 | 321 |
| hybrid@chunks-structure | 85 | 0.353 | 0.682 | 0.788 | 0.771 | 0.504 | 0.560 | 0.906 | 261 | 308 |
| wide+rerank+jur@chunks-structure~glm-4.7 | 85 | 0.929 | 1.000 | 1.000 | 0.994 | 0.956 | 0.963 | 1.000 | 4676 | 5842 |

### file_type=docx

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 15 | 0.933 | 1.000 | 1.000 | 1.000 | 0.956 | 0.967 | 1.000 | 3514 | 6323 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 15 | 0.800 | 0.933 | 0.933 | 0.933 | 0.856 | 0.875 | 0.933 | 3386 | 4064 |
| bm25@chunks-fixed | 15 | 0.400 | 0.600 | 0.667 | 0.667 | 0.491 | 0.533 | 0.733 | 2 | 3 |
| bm25@chunks-structure | 15 | 0.533 | 0.667 | 0.667 | 0.667 | 0.589 | 0.609 | 0.733 | 2 | 2 |
| dense@chunks-fixed | 15 | 0.200 | 0.333 | 0.600 | 0.600 | 0.285 | 0.344 | 0.733 | 246 | 304 |
| dense@chunks-structure | 15 | 0.267 | 0.467 | 0.800 | 0.800 | 0.380 | 0.471 | 0.867 | 270 | 345 |
| hybrid@chunks-fixed | 15 | 0.333 | 0.600 | 0.667 | 0.667 | 0.461 | 0.503 | 0.733 | 256 | 307 |
| hybrid@chunks-structure | 15 | 0.267 | 0.667 | 0.667 | 0.667 | 0.428 | 0.476 | 0.733 | 250 | 294 |
| wide+rerank+jur@chunks-structure~glm-4.7 | 15 | 0.867 | 1.000 | 1.000 | 1.000 | 0.922 | 0.942 | 1.000 | 4905 | 5469 |

### file_type=docx+hwpx

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 1 | 1.000 | 1.000 | 1.000 | 0.500 | 1.000 | 0.613 | 1.000 | 3471 | 3471 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 1 | 1.000 | 1.000 | 1.000 | 0.500 | 1.000 | 0.613 | 1.000 | 3158 | 3158 |
| bm25@chunks-fixed | 1 | 1.000 | 1.000 | 1.000 | 0.500 | 1.000 | 0.613 | 1.000 | 2 | 2 |
| bm25@chunks-structure | 1 | 1.000 | 1.000 | 1.000 | 0.500 | 1.000 | 0.613 | 1.000 | 2 | 2 |
| dense@chunks-fixed | 1 | 0.000 | 1.000 | 1.000 | 0.500 | 0.250 | 0.264 | 1.000 | 251 | 251 |
| dense@chunks-structure | 1 | 0.000 | 0.000 | 1.000 | 0.500 | 0.167 | 0.218 | 1.000 | 233 | 233 |
| hybrid@chunks-fixed | 1 | 1.000 | 1.000 | 1.000 | 0.500 | 1.000 | 0.613 | 1.000 | 277 | 277 |
| hybrid@chunks-structure | 1 | 0.000 | 1.000 | 1.000 | 0.500 | 0.500 | 0.387 | 1.000 | 342 | 342 |
| wide+rerank+jur@chunks-structure~glm-4.7 | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.832 | 1.000 | 6104 | 6104 |

### file_type=docx+pdf

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 3722 | 3722 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 3752 | 3752 |
| bm25@chunks-fixed | 1 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 2 | 2 |
| bm25@chunks-structure | 1 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 2 | 2 |
| dense@chunks-fixed | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 285 | 285 |
| dense@chunks-structure | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.832 | 1.000 | 300 | 300 |
| hybrid@chunks-fixed | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.920 | 1.000 | 292 | 292 |
| hybrid@chunks-structure | 1 | 1.000 | 1.000 | 1.000 | 0.500 | 1.000 | 0.613 | 1.000 | 257 | 257 |
| wide+rerank+jur@chunks-structure~glm-4.7 | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 3799 | 3799 |

### file_type=hwpx

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 14 | 0.786 | 0.929 | 0.929 | 0.929 | 0.845 | 0.867 | 0.929 | 3918 | 6020 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 14 | 0.714 | 0.929 | 0.929 | 0.929 | 0.809 | 0.840 | 1.000 | 3137 | 3465 |
| bm25@chunks-fixed | 14 | 0.500 | 0.500 | 0.571 | 0.571 | 0.516 | 0.525 | 0.643 | 2 | 2 |
| bm25@chunks-structure | 14 | 0.429 | 0.429 | 0.643 | 0.643 | 0.457 | 0.497 | 0.643 | 2 | 2 |
| dense@chunks-fixed | 14 | 0.571 | 0.714 | 0.857 | 0.857 | 0.622 | 0.671 | 0.929 | 280 | 317 |
| dense@chunks-structure | 14 | 0.571 | 0.786 | 0.857 | 0.857 | 0.668 | 0.711 | 0.929 | 243 | 282 |
| hybrid@chunks-fixed | 14 | 0.571 | 0.714 | 0.857 | 0.857 | 0.666 | 0.707 | 0.929 | 254 | 281 |
| hybrid@chunks-structure | 14 | 0.500 | 0.857 | 0.929 | 0.929 | 0.689 | 0.749 | 0.929 | 262 | 284 |
| wide+rerank+jur@chunks-structure~glm-4.7 | 14 | 0.857 | 1.000 | 1.000 | 1.000 | 0.899 | 0.924 | 1.000 | 4876 | 5993 |

### file_type=hwpx+pdf

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 1 | 1.000 | 1.000 | 1.000 | 0.500 | 1.000 | 0.613 | 1.000 | 3487 | 3487 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 1 | 1.000 | 1.000 | 1.000 | 0.500 | 1.000 | 0.613 | 1.000 | 3536 | 3536 |
| bm25@chunks-fixed | 1 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 2 | 2 |
| bm25@chunks-structure | 1 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 2 | 2 |
| dense@chunks-fixed | 1 | 1.000 | 1.000 | 1.000 | 0.500 | 1.000 | 0.613 | 1.000 | 272 | 272 |
| dense@chunks-structure | 1 | 0.000 | 1.000 | 1.000 | 0.500 | 0.500 | 0.387 | 1.000 | 243 | 243 |
| hybrid@chunks-fixed | 1 | 0.000 | 1.000 | 1.000 | 0.500 | 0.333 | 0.307 | 1.000 | 405 | 405 |
| hybrid@chunks-structure | 1 | 0.000 | 0.000 | 1.000 | 0.500 | 0.143 | 0.204 | 1.000 | 259 | 259 |
| wide+rerank+jur@chunks-structure~glm-4.7 | 1 | 1.000 | 1.000 | 1.000 | 0.500 | 1.000 | 0.613 | 1.000 | 4920 | 4920 |

### file_type=pdf

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 39 | 0.872 | 0.923 | 0.923 | 0.923 | 0.892 | 0.905 | 0.974 | 3660 | 6565 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 39 | 0.821 | 0.897 | 0.949 | 0.923 | 0.861 | 0.871 | 0.974 | 3310 | 3746 |
| bm25@chunks-fixed | 39 | 0.256 | 0.410 | 0.487 | 0.487 | 0.319 | 0.363 | 0.590 | 2 | 2 |
| bm25@chunks-structure | 39 | 0.256 | 0.385 | 0.410 | 0.410 | 0.308 | 0.336 | 0.615 | 2 | 2 |
| dense@chunks-fixed | 39 | 0.436 | 0.667 | 0.769 | 0.769 | 0.548 | 0.596 | 0.949 | 256 | 308 |
| dense@chunks-structure | 39 | 0.487 | 0.692 | 0.846 | 0.821 | 0.581 | 0.629 | 0.923 | 266 | 323 |
| hybrid@chunks-fixed | 39 | 0.205 | 0.564 | 0.718 | 0.718 | 0.372 | 0.450 | 0.872 | 258 | 324 |
| hybrid@chunks-structure | 39 | 0.333 | 0.667 | 0.744 | 0.744 | 0.477 | 0.538 | 0.949 | 264 | 325 |
| wide+rerank+jur@chunks-structure~glm-4.7 | 39 | 0.974 | 1.000 | 1.000 | 1.000 | 0.983 | 0.993 | 1.000 | 4480 | 5565 |

### file_type=scan

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 14 | 0.929 | 1.000 | 1.000 | 1.000 | 0.964 | 0.974 | 1.000 | 3766 | 6259 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 14 | 0.929 | 1.000 | 1.000 | 1.000 | 0.964 | 0.974 | 1.000 | 3558 | 3760 |
| bm25@chunks-fixed | 14 | 0.429 | 0.429 | 0.500 | 0.500 | 0.436 | 0.450 | 0.500 | 2 | 3 |
| bm25@chunks-structure | 14 | 0.357 | 0.429 | 0.429 | 0.429 | 0.397 | 0.402 | 0.571 | 2 | 2 |
| dense@chunks-fixed | 14 | 0.357 | 0.857 | 0.929 | 0.929 | 0.601 | 0.684 | 0.929 | 252 | 301 |
| dense@chunks-structure | 14 | 0.500 | 0.786 | 0.929 | 0.929 | 0.625 | 0.694 | 0.929 | 255 | 283 |
| hybrid@chunks-fixed | 14 | 0.429 | 0.714 | 0.929 | 0.929 | 0.541 | 0.631 | 0.929 | 268 | 304 |
| hybrid@chunks-structure | 14 | 0.357 | 0.571 | 0.857 | 0.857 | 0.464 | 0.553 | 0.929 | 254 | 302 |
| wide+rerank+jur@chunks-structure~glm-4.7 | 14 | 0.929 | 1.000 | 1.000 | 1.000 | 0.964 | 0.974 | 1.000 | 4851 | 5471 |

### kind=fact

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 75 | 0.867 | 0.947 | 0.947 | 0.947 | 0.900 | 0.914 | 0.973 | 3665 | 6565 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 75 | 0.800 | 0.920 | 0.947 | 0.933 | 0.856 | 0.873 | 0.973 | 3345 | 3803 |
| bm25@chunks-fixed | 75 | 0.320 | 0.440 | 0.507 | 0.507 | 0.373 | 0.407 | 0.573 | 2 | 3 |
| bm25@chunks-structure | 75 | 0.333 | 0.427 | 0.480 | 0.480 | 0.377 | 0.403 | 0.600 | 2 | 2 |
| dense@chunks-fixed | 75 | 0.413 | 0.653 | 0.787 | 0.787 | 0.531 | 0.587 | 0.907 | 256 | 317 |
| dense@chunks-structure | 75 | 0.467 | 0.680 | 0.840 | 0.827 | 0.566 | 0.621 | 0.907 | 261 | 323 |
| hybrid@chunks-fixed | 75 | 0.320 | 0.600 | 0.760 | 0.760 | 0.454 | 0.523 | 0.867 | 258 | 313 |
| hybrid@chunks-structure | 75 | 0.347 | 0.653 | 0.760 | 0.760 | 0.492 | 0.553 | 0.893 | 261 | 308 |
| wide+rerank+jur@chunks-structure~glm-4.7 | 75 | 0.920 | 1.000 | 1.000 | 1.000 | 0.950 | 0.966 | 1.000 | 4666 | 5842 |

### kind=multi

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 3 | 1.000 | 1.000 | 1.000 | 0.667 | 1.000 | 0.742 | 1.000 | 3487 | 3487 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 3 | 1.000 | 1.000 | 1.000 | 0.667 | 1.000 | 0.742 | 1.000 | 3536 | 3536 |
| bm25@chunks-fixed | 3 | 0.333 | 0.333 | 0.333 | 0.167 | 0.333 | 0.204 | 0.333 | 2 | 2 |
| bm25@chunks-structure | 3 | 0.333 | 0.333 | 0.333 | 0.167 | 0.333 | 0.204 | 0.333 | 2 | 2 |
| dense@chunks-fixed | 3 | 0.667 | 1.000 | 1.000 | 0.667 | 0.750 | 0.626 | 1.000 | 272 | 272 |
| dense@chunks-structure | 3 | 0.333 | 0.667 | 1.000 | 0.667 | 0.556 | 0.479 | 1.000 | 243 | 243 |
| hybrid@chunks-fixed | 3 | 0.667 | 1.000 | 1.000 | 0.667 | 0.778 | 0.613 | 1.000 | 292 | 292 |
| hybrid@chunks-structure | 3 | 0.333 | 0.667 | 1.000 | 0.500 | 0.548 | 0.402 | 1.000 | 259 | 259 |
| wide+rerank+jur@chunks-structure~glm-4.7 | 3 | 1.000 | 1.000 | 1.000 | 0.833 | 1.000 | 0.815 | 1.000 | 4920 | 4920 |

### kind=table

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 7 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 3318 | 4393 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 7 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 3297 | 3431 |
| bm25@chunks-fixed | 7 | 0.714 | 0.714 | 0.857 | 0.857 | 0.730 | 0.757 | 1.000 | 2 | 3 |
| bm25@chunks-structure | 7 | 0.571 | 0.714 | 0.714 | 0.714 | 0.651 | 0.662 | 1.000 | 2 | 2 |
| dense@chunks-fixed | 7 | 0.286 | 0.571 | 0.714 | 0.714 | 0.419 | 0.479 | 0.857 | 269 | 283 |
| dense@chunks-structure | 7 | 0.429 | 0.714 | 1.000 | 1.000 | 0.578 | 0.674 | 1.000 | 249 | 271 |
| hybrid@chunks-fixed | 7 | 0.429 | 0.857 | 0.857 | 0.857 | 0.606 | 0.662 | 0.857 | 253 | 294 |
| hybrid@chunks-structure | 7 | 0.429 | 1.000 | 1.000 | 1.000 | 0.607 | 0.703 | 1.000 | 277 | 279 |
| wide+rerank+jur@chunks-structure~glm-4.7 | 7 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 5082 | 5468 |

### lang=en->en

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 16 | 0.875 | 0.938 | 0.938 | 0.938 | 0.906 | 0.914 | 1.000 | 4789 | 6243 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 16 | 0.938 | 0.938 | 0.938 | 0.938 | 0.938 | 0.938 | 0.938 | 3458 | 3854 |
| bm25@chunks-fixed | 16 | 0.438 | 0.688 | 0.750 | 0.750 | 0.538 | 0.586 | 0.938 | 2 | 2 |
| bm25@chunks-structure | 16 | 0.375 | 0.562 | 0.625 | 0.625 | 0.444 | 0.484 | 1.000 | 2 | 2 |
| dense@chunks-fixed | 16 | 0.688 | 0.875 | 0.938 | 0.938 | 0.789 | 0.826 | 0.938 | 268 | 328 |
| dense@chunks-structure | 16 | 0.688 | 0.875 | 0.938 | 0.938 | 0.787 | 0.824 | 0.938 | 250 | 286 |
| hybrid@chunks-fixed | 16 | 0.438 | 0.875 | 0.938 | 0.938 | 0.653 | 0.724 | 0.938 | 259 | 286 |
| hybrid@chunks-structure | 16 | 0.562 | 0.812 | 0.812 | 0.812 | 0.667 | 0.697 | 1.000 | 264 | 325 |
| wide+rerank+jur@chunks-structure~glm-4.7 | 16 | 0.938 | 1.000 | 1.000 | 1.000 | 0.958 | 0.969 | 1.000 | 4412 | 5235 |

### lang=en->ko

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 21 | 0.905 | 0.952 | 0.952 | 0.929 | 0.921 | 0.910 | 0.952 | 3887 | 6323 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 21 | 0.857 | 0.952 | 0.952 | 0.929 | 0.897 | 0.893 | 1.000 | 3491 | 4064 |
| bm25@chunks-fixed | 21 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 2 | 3 |
| bm25@chunks-structure | 21 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 2 | 2 |
| dense@chunks-fixed | 21 | 0.333 | 0.667 | 0.667 | 0.643 | 0.452 | 0.480 | 0.809 | 272 | 301 |
| dense@chunks-structure | 21 | 0.476 | 0.714 | 0.762 | 0.738 | 0.573 | 0.594 | 0.809 | 244 | 345 |
| hybrid@chunks-fixed | 21 | 0.143 | 0.333 | 0.524 | 0.500 | 0.237 | 0.283 | 0.714 | 266 | 304 |
| hybrid@chunks-structure | 21 | 0.286 | 0.381 | 0.667 | 0.619 | 0.377 | 0.413 | 0.714 | 274 | 300 |
| wide+rerank+jur@chunks-structure~glm-4.7 | 21 | 0.905 | 1.000 | 1.000 | 0.976 | 0.941 | 0.937 | 1.000 | 4673 | 5842 |

### lang=ko->en

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 13 | 0.769 | 0.923 | 0.923 | 0.923 | 0.831 | 0.851 | 0.923 | 3491 | 6565 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 13 | 0.692 | 0.846 | 1.000 | 1.000 | 0.793 | 0.842 | 1.000 | 3216 | 3458 |
| bm25@chunks-fixed | 13 | 0.000 | 0.000 | 0.077 | 0.077 | 0.009 | 0.023 | 0.077 | 2 | 3 |
| bm25@chunks-structure | 13 | 0.000 | 0.000 | 0.000 | 0.000 | 0.004 | 0.000 | 0.154 | 2 | 2 |
| dense@chunks-fixed | 13 | 0.462 | 0.692 | 0.846 | 0.846 | 0.568 | 0.629 | 1.000 | 257 | 301 |
| dense@chunks-structure | 13 | 0.385 | 0.615 | 0.769 | 0.769 | 0.467 | 0.534 | 0.923 | 278 | 308 |
| hybrid@chunks-fixed | 13 | 0.077 | 0.462 | 0.692 | 0.692 | 0.232 | 0.333 | 0.846 | 258 | 302 |
| hybrid@chunks-structure | 13 | 0.000 | 0.385 | 0.615 | 0.615 | 0.181 | 0.278 | 0.923 | 250 | 285 |
| wide+rerank+jur@chunks-structure~glm-4.7 | 13 | 0.923 | 1.000 | 1.000 | 1.000 | 0.962 | 0.972 | 1.000 | 4291 | 4831 |

### lang=ko->ko

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 35 | 0.914 | 0.971 | 0.971 | 0.957 | 0.938 | 0.942 | 1.000 | 3448 | 6020 |
| bilingual_union_dense+rerank+jur@chunks-structure~glm-4.7 | 35 | 0.800 | 0.943 | 0.943 | 0.900 | 0.860 | 0.857 | 0.971 | 3297 | 3676 |
| bm25@chunks-fixed | 35 | 0.657 | 0.800 | 0.914 | 0.900 | 0.726 | 0.764 | 1.000 | 2 | 2 |
| bm25@chunks-structure | 35 | 0.686 | 0.829 | 0.914 | 0.900 | 0.761 | 0.791 | 1.000 | 2 | 2 |
| dense@chunks-fixed | 35 | 0.314 | 0.543 | 0.771 | 0.757 | 0.444 | 0.507 | 0.914 | 252 | 304 |
| dense@chunks-structure | 35 | 0.371 | 0.600 | 0.914 | 0.871 | 0.499 | 0.574 | 0.971 | 256 | 296 |
| hybrid@chunks-fixed | 35 | 0.514 | 0.771 | 0.886 | 0.871 | 0.635 | 0.681 | 0.943 | 258 | 321 |
| hybrid@chunks-structure | 35 | 0.429 | 0.914 | 0.914 | 0.900 | 0.625 | 0.690 | 0.971 | 252 | 313 |
| wide+rerank+jur@chunks-structure~glm-4.7 | 35 | 0.943 | 1.000 | 1.000 | 1.000 | 0.962 | 0.973 | 1.000 | 5082 | 6047 |
