
### all=all

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| agent+rerank@chunks-structure~glm-4.7 | 83 | 0.807 | 0.916 | 0.952 | 0.952 | 0.856 | 0.879 | 1.000 | 9601 | 18156 |
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 83 | 0.807 | 0.855 | 0.868 | 0.868 | 0.829 | 0.837 | 0.976 | 3615 | 4138 |
| bm25@chunks-fixed | 83 | 0.301 | 0.590 | 0.723 | 0.723 | 0.418 | 0.483 | 0.940 | 2 | 3 |
| bm25@chunks-structure | 83 | 0.301 | 0.518 | 0.699 | 0.699 | 0.417 | 0.478 | 0.940 | 2 | 2 |
| dense@chunks-fixed | 83 | 0.349 | 0.699 | 0.771 | 0.771 | 0.485 | 0.553 | 0.928 | 258 | 297 |
| dense@chunks-structure | 83 | 0.301 | 0.711 | 0.723 | 0.723 | 0.463 | 0.525 | 0.928 | 258 | 313 |
| hybrid+rerank@chunks-structure~glm-4.7 | 83 | 0.819 | 0.843 | 0.879 | 0.879 | 0.836 | 0.846 | 0.976 | 1614 | 2444 |
| hybrid@chunks-fixed | 83 | 0.373 | 0.675 | 0.783 | 0.783 | 0.506 | 0.568 | 0.952 | 259 | 292 |
| hybrid@chunks-structure | 83 | 0.398 | 0.639 | 0.735 | 0.735 | 0.505 | 0.554 | 0.952 | 258 | 300 |

### file_type=docx

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| agent+rerank@chunks-structure~glm-4.7 | 17 | 0.882 | 1.000 | 1.000 | 1.000 | 0.922 | 0.941 | 1.000 | 8892 | 10458 |
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 17 | 0.824 | 0.824 | 0.824 | 0.824 | 0.828 | 0.824 | 1.000 | 3685 | 4058 |
| bm25@chunks-fixed | 17 | 0.412 | 0.647 | 0.706 | 0.706 | 0.501 | 0.542 | 1.000 | 2 | 2 |
| bm25@chunks-structure | 17 | 0.412 | 0.471 | 0.529 | 0.529 | 0.454 | 0.466 | 1.000 | 2 | 2 |
| dense@chunks-fixed | 17 | 0.412 | 0.765 | 0.824 | 0.824 | 0.562 | 0.623 | 1.000 | 255 | 282 |
| dense@chunks-structure | 17 | 0.176 | 0.765 | 0.765 | 0.765 | 0.427 | 0.506 | 1.000 | 259 | 315 |
| hybrid+rerank@chunks-structure~glm-4.7 | 17 | 0.824 | 0.824 | 0.882 | 0.882 | 0.833 | 0.845 | 1.000 | 1571 | 1995 |
| hybrid@chunks-fixed | 17 | 0.647 | 0.765 | 0.824 | 0.824 | 0.709 | 0.735 | 1.000 | 268 | 287 |
| hybrid@chunks-structure | 17 | 0.471 | 0.588 | 0.706 | 0.706 | 0.536 | 0.566 | 1.000 | 276 | 341 |

### file_type=hwpx

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| agent+rerank@chunks-structure~glm-4.7 | 19 | 0.737 | 0.842 | 0.842 | 0.842 | 0.789 | 0.803 | 1.000 | 8294 | 13782 |
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 19 | 0.895 | 0.895 | 0.895 | 0.895 | 0.895 | 0.895 | 1.000 | 3668 | 4138 |
| bm25@chunks-fixed | 19 | 0.316 | 0.526 | 0.684 | 0.684 | 0.403 | 0.466 | 0.842 | 2 | 4 |
| bm25@chunks-structure | 19 | 0.263 | 0.526 | 0.632 | 0.632 | 0.372 | 0.430 | 0.842 | 2 | 2 |
| dense@chunks-fixed | 19 | 0.263 | 0.684 | 0.789 | 0.789 | 0.443 | 0.527 | 0.895 | 268 | 311 |
| dense@chunks-structure | 19 | 0.210 | 0.684 | 0.684 | 0.684 | 0.392 | 0.462 | 0.842 | 268 | 342 |
| hybrid+rerank@chunks-structure~glm-4.7 | 19 | 0.895 | 0.895 | 0.895 | 0.895 | 0.895 | 0.895 | 1.000 | 1567 | 1739 |
| hybrid@chunks-fixed | 19 | 0.316 | 0.684 | 0.684 | 0.684 | 0.478 | 0.517 | 0.895 | 259 | 276 |
| hybrid@chunks-structure | 19 | 0.316 | 0.579 | 0.684 | 0.684 | 0.434 | 0.489 | 0.895 | 261 | 288 |

### file_type=pdf

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| agent+rerank@chunks-structure~glm-4.7 | 36 | 0.778 | 0.917 | 0.972 | 0.972 | 0.839 | 0.871 | 1.000 | 11797 | 19307 |
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 36 | 0.722 | 0.806 | 0.833 | 0.833 | 0.756 | 0.774 | 0.944 | 3498 | 3994 |
| bm25@chunks-fixed | 36 | 0.250 | 0.583 | 0.750 | 0.750 | 0.395 | 0.472 | 0.944 | 2 | 2 |
| bm25@chunks-structure | 36 | 0.250 | 0.500 | 0.750 | 0.750 | 0.393 | 0.470 | 0.944 | 2 | 2 |
| dense@chunks-fixed | 36 | 0.389 | 0.583 | 0.667 | 0.667 | 0.468 | 0.514 | 0.889 | 255 | 295 |
| dense@chunks-structure | 36 | 0.306 | 0.611 | 0.639 | 0.639 | 0.410 | 0.463 | 0.917 | 255 | 307 |
| hybrid+rerank@chunks-structure~glm-4.7 | 36 | 0.750 | 0.806 | 0.833 | 0.833 | 0.781 | 0.794 | 0.944 | 1809 | 2647 |
| hybrid@chunks-fixed | 36 | 0.361 | 0.556 | 0.778 | 0.778 | 0.465 | 0.535 | 0.944 | 261 | 297 |
| hybrid@chunks-structure | 36 | 0.333 | 0.611 | 0.694 | 0.694 | 0.448 | 0.501 | 0.944 | 256 | 287 |

### file_type=scan

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| agent+rerank@chunks-structure~glm-4.7 | 11 | 0.909 | 0.909 | 1.000 | 1.000 | 0.922 | 0.939 | 1.000 | 12650 | 13819 |
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 11 | 0.909 | 1.000 | 1.000 | 1.000 | 0.955 | 0.966 | 1.000 | 3577 | 4172 |
| bm25@chunks-fixed | 11 | 0.273 | 0.636 | 0.727 | 0.727 | 0.390 | 0.460 | 1.000 | 2 | 2 |
| bm25@chunks-structure | 11 | 0.364 | 0.636 | 0.909 | 0.909 | 0.518 | 0.610 | 1.000 | 2 | 2 |
| dense@chunks-fixed | 11 | 0.273 | 1.000 | 1.000 | 1.000 | 0.495 | 0.620 | 1.000 | 268 | 287 |
| dense@chunks-structure | 11 | 0.636 | 1.000 | 1.000 | 1.000 | 0.818 | 0.866 | 1.000 | 252 | 288 |
| hybrid+rerank@chunks-structure~glm-4.7 | 11 | 0.909 | 0.909 | 1.000 | 1.000 | 0.920 | 0.938 | 1.000 | 1602 | 1954 |
| hybrid@chunks-fixed | 11 | 0.091 | 0.909 | 0.909 | 0.909 | 0.379 | 0.505 | 1.000 | 248 | 275 |
| hybrid@chunks-structure | 11 | 0.636 | 0.909 | 1.000 | 1.000 | 0.767 | 0.823 | 1.000 | 252 | 271 |

### kind=real

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| agent+rerank@chunks-structure~glm-4.7 | 83 | 0.807 | 0.916 | 0.952 | 0.952 | 0.856 | 0.879 | 1.000 | 9601 | 18156 |
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 83 | 0.807 | 0.855 | 0.868 | 0.868 | 0.829 | 0.837 | 0.976 | 3615 | 4138 |
| bm25@chunks-fixed | 83 | 0.301 | 0.590 | 0.723 | 0.723 | 0.418 | 0.483 | 0.940 | 2 | 3 |
| bm25@chunks-structure | 83 | 0.301 | 0.518 | 0.699 | 0.699 | 0.417 | 0.478 | 0.940 | 2 | 2 |
| dense@chunks-fixed | 83 | 0.349 | 0.699 | 0.771 | 0.771 | 0.485 | 0.553 | 0.928 | 258 | 297 |
| dense@chunks-structure | 83 | 0.301 | 0.711 | 0.723 | 0.723 | 0.463 | 0.525 | 0.928 | 258 | 313 |
| hybrid+rerank@chunks-structure~glm-4.7 | 83 | 0.819 | 0.843 | 0.879 | 0.879 | 0.836 | 0.846 | 0.976 | 1614 | 2444 |
| hybrid@chunks-fixed | 83 | 0.373 | 0.675 | 0.783 | 0.783 | 0.506 | 0.568 | 0.952 | 259 | 292 |
| hybrid@chunks-structure | 83 | 0.398 | 0.639 | 0.735 | 0.735 | 0.505 | 0.554 | 0.952 | 258 | 300 |

### lang=en->en

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| agent+rerank@chunks-structure~glm-4.7 | 40 | 0.775 | 0.900 | 0.975 | 0.975 | 0.834 | 0.867 | 1.000 | 12072 | 17927 |
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 40 | 0.775 | 0.850 | 0.875 | 0.875 | 0.811 | 0.827 | 0.950 | 3498 | 4046 |
| bm25@chunks-fixed | 40 | 0.275 | 0.600 | 0.750 | 0.750 | 0.401 | 0.477 | 0.950 | 2 | 2 |
| bm25@chunks-structure | 40 | 0.300 | 0.525 | 0.775 | 0.775 | 0.429 | 0.505 | 0.950 | 2 | 2 |
| dense@chunks-fixed | 40 | 0.325 | 0.650 | 0.700 | 0.700 | 0.436 | 0.499 | 0.900 | 253 | 302 |
| dense@chunks-structure | 40 | 0.425 | 0.675 | 0.700 | 0.700 | 0.530 | 0.570 | 0.925 | 256 | 297 |
| hybrid+rerank@chunks-structure~glm-4.7 | 40 | 0.775 | 0.825 | 0.875 | 0.875 | 0.806 | 0.822 | 0.950 | 1878 | 2647 |
| hybrid@chunks-fixed | 40 | 0.225 | 0.600 | 0.775 | 0.775 | 0.386 | 0.475 | 0.950 | 260 | 315 |
| hybrid@chunks-structure | 40 | 0.375 | 0.650 | 0.750 | 0.750 | 0.489 | 0.545 | 0.950 | 256 | 294 |

### lang=ko->ko

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| agent+rerank@chunks-structure~glm-4.7 | 43 | 0.837 | 0.930 | 0.930 | 0.930 | 0.876 | 0.890 | 1.000 | 8892 | 18853 |
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 43 | 0.837 | 0.861 | 0.861 | 0.861 | 0.845 | 0.847 | 1.000 | 3674 | 4138 |
| bm25@chunks-fixed | 43 | 0.326 | 0.581 | 0.698 | 0.698 | 0.434 | 0.490 | 0.930 | 2 | 4 |
| bm25@chunks-structure | 43 | 0.302 | 0.512 | 0.628 | 0.628 | 0.406 | 0.454 | 0.930 | 2 | 2 |
| dense@chunks-fixed | 43 | 0.372 | 0.744 | 0.837 | 0.837 | 0.531 | 0.603 | 0.954 | 258 | 295 |
| dense@chunks-structure | 43 | 0.186 | 0.744 | 0.744 | 0.744 | 0.401 | 0.483 | 0.930 | 259 | 315 |
| hybrid+rerank@chunks-structure~glm-4.7 | 43 | 0.861 | 0.861 | 0.884 | 0.884 | 0.864 | 0.869 | 1.000 | 1569 | 1880 |
| hybrid@chunks-fixed | 43 | 0.512 | 0.744 | 0.791 | 0.791 | 0.619 | 0.654 | 0.954 | 259 | 286 |
| hybrid@chunks-structure | 43 | 0.419 | 0.628 | 0.721 | 0.721 | 0.520 | 0.562 | 0.954 | 264 | 300 |
