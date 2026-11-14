
### all=all

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| agent+rerank@chunks-structure~glm-4.7 | 83 | 0.855 | 0.916 | 0.952 | 0.952 | 0.884 | 0.900 | 1.000 | 9601 | 18156 |
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 83 | 0.843 | 0.879 | 0.892 | 0.892 | 0.859 | 0.866 | 1.000 | 3615 | 4138 |
| bm25@chunks-fixed | 83 | 0.349 | 0.615 | 0.771 | 0.771 | 0.463 | 0.529 | 0.964 | 2 | 3 |
| bm25@chunks-structure | 83 | 0.325 | 0.542 | 0.711 | 0.711 | 0.440 | 0.497 | 0.964 | 2 | 2 |
| dense@chunks-fixed | 83 | 0.410 | 0.711 | 0.795 | 0.795 | 0.529 | 0.592 | 0.952 | 258 | 297 |
| dense@chunks-structure | 83 | 0.337 | 0.723 | 0.723 | 0.723 | 0.486 | 0.542 | 0.952 | 258 | 313 |
| hybrid+rerank@chunks-structure~glm-4.7 | 83 | 0.855 | 0.868 | 0.904 | 0.904 | 0.867 | 0.875 | 1.000 | 1614 | 2444 |
| hybrid@chunks-fixed | 83 | 0.446 | 0.687 | 0.807 | 0.807 | 0.560 | 0.614 | 0.976 | 259 | 292 |
| hybrid@chunks-structure | 83 | 0.410 | 0.651 | 0.759 | 0.759 | 0.520 | 0.572 | 0.976 | 258 | 300 |
| wide+rerank+jur@chunks-structure~glm-4.7 | 83 | 0.928 | 0.964 | 0.964 | 0.964 | 0.941 | 0.945 | 1.000 | 5690 | 6811 |
| wide_no_terms+rerank+jur@chunks-structure~glm-4.7 | 83 | 0.904 | 0.940 | 0.952 | 0.952 | 0.920 | 0.926 | 1.000 | 4693 | 5481 |

### file_type=docx

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| agent+rerank@chunks-structure~glm-4.7 | 17 | 0.882 | 1.000 | 1.000 | 1.000 | 0.922 | 0.941 | 1.000 | 8892 | 10458 |
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 17 | 0.824 | 0.824 | 0.824 | 0.824 | 0.828 | 0.824 | 1.000 | 3685 | 4058 |
| bm25@chunks-fixed | 17 | 0.471 | 0.706 | 0.765 | 0.765 | 0.560 | 0.601 | 1.000 | 2 | 2 |
| bm25@chunks-structure | 17 | 0.412 | 0.529 | 0.588 | 0.588 | 0.474 | 0.495 | 1.000 | 2 | 2 |
| dense@chunks-fixed | 17 | 0.471 | 0.824 | 0.941 | 0.941 | 0.622 | 0.699 | 1.000 | 255 | 282 |
| dense@chunks-structure | 17 | 0.235 | 0.765 | 0.765 | 0.765 | 0.457 | 0.528 | 1.000 | 259 | 315 |
| hybrid+rerank@chunks-structure~glm-4.7 | 17 | 0.824 | 0.824 | 0.882 | 0.882 | 0.833 | 0.845 | 1.000 | 1571 | 1995 |
| hybrid@chunks-fixed | 17 | 0.706 | 0.824 | 0.882 | 0.882 | 0.768 | 0.793 | 1.000 | 268 | 287 |
| hybrid@chunks-structure | 17 | 0.529 | 0.647 | 0.765 | 0.765 | 0.590 | 0.625 | 1.000 | 276 | 341 |
| wide+rerank+jur@chunks-structure~glm-4.7 | 17 | 0.882 | 0.882 | 0.882 | 0.882 | 0.888 | 0.882 | 1.000 | 6365 | 6811 |
| wide_no_terms+rerank+jur@chunks-structure~glm-4.7 | 17 | 0.824 | 0.882 | 0.941 | 0.941 | 0.849 | 0.870 | 1.000 | 4887 | 5427 |

### file_type=hwpx

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| agent+rerank@chunks-structure~glm-4.7 | 19 | 0.737 | 0.842 | 0.842 | 0.842 | 0.789 | 0.803 | 1.000 | 8294 | 13782 |
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 19 | 0.895 | 0.895 | 0.895 | 0.895 | 0.895 | 0.895 | 1.000 | 3668 | 4138 |
| bm25@chunks-fixed | 19 | 0.368 | 0.526 | 0.684 | 0.684 | 0.430 | 0.485 | 0.842 | 2 | 4 |
| bm25@chunks-structure | 19 | 0.263 | 0.526 | 0.632 | 0.632 | 0.372 | 0.430 | 0.842 | 2 | 2 |
| dense@chunks-fixed | 19 | 0.316 | 0.684 | 0.789 | 0.789 | 0.470 | 0.546 | 0.895 | 268 | 311 |
| dense@chunks-structure | 19 | 0.263 | 0.684 | 0.684 | 0.684 | 0.418 | 0.481 | 0.842 | 268 | 342 |
| hybrid+rerank@chunks-structure~glm-4.7 | 19 | 0.895 | 0.895 | 0.895 | 0.895 | 0.895 | 0.895 | 1.000 | 1567 | 1739 |
| hybrid@chunks-fixed | 19 | 0.368 | 0.684 | 0.684 | 0.684 | 0.504 | 0.536 | 0.895 | 259 | 276 |
| hybrid@chunks-structure | 19 | 0.316 | 0.579 | 0.684 | 0.684 | 0.434 | 0.489 | 0.895 | 261 | 288 |
| wide+rerank+jur@chunks-structure~glm-4.7 | 19 | 0.947 | 1.000 | 1.000 | 1.000 | 0.958 | 0.968 | 1.000 | 6294 | 7265 |
| wide_no_terms+rerank+jur@chunks-structure~glm-4.7 | 19 | 0.895 | 0.895 | 0.895 | 0.895 | 0.899 | 0.895 | 1.000 | 4893 | 5495 |

### file_type=pdf

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| agent+rerank@chunks-structure~glm-4.7 | 36 | 0.889 | 0.917 | 0.972 | 0.972 | 0.904 | 0.920 | 1.000 | 11797 | 19307 |
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 36 | 0.806 | 0.861 | 0.889 | 0.889 | 0.825 | 0.840 | 1.000 | 3498 | 3994 |
| bm25@chunks-fixed | 36 | 0.250 | 0.583 | 0.806 | 0.806 | 0.405 | 0.491 | 1.000 | 2 | 2 |
| bm25@chunks-structure | 36 | 0.250 | 0.528 | 0.750 | 0.750 | 0.401 | 0.473 | 1.000 | 2 | 2 |
| dense@chunks-fixed | 36 | 0.389 | 0.583 | 0.667 | 0.667 | 0.468 | 0.514 | 0.944 | 255 | 295 |
| dense@chunks-structure | 36 | 0.306 | 0.639 | 0.639 | 0.639 | 0.419 | 0.471 | 0.972 | 255 | 307 |
| hybrid+rerank@chunks-structure~glm-4.7 | 36 | 0.833 | 0.861 | 0.889 | 0.889 | 0.851 | 0.860 | 1.000 | 1809 | 2647 |
| hybrid@chunks-fixed | 36 | 0.361 | 0.556 | 0.806 | 0.806 | 0.467 | 0.545 | 1.000 | 261 | 297 |
| hybrid@chunks-structure | 36 | 0.333 | 0.611 | 0.722 | 0.722 | 0.457 | 0.513 | 1.000 | 256 | 287 |
| wide+rerank+jur@chunks-structure~glm-4.7 | 36 | 0.944 | 0.972 | 0.972 | 0.972 | 0.954 | 0.956 | 1.000 | 5362 | 6286 |
| wide_no_terms+rerank+jur@chunks-structure~glm-4.7 | 36 | 0.944 | 0.972 | 0.972 | 0.972 | 0.954 | 0.956 | 1.000 | 4525 | 5481 |

### file_type=scan

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| agent+rerank@chunks-structure~glm-4.7 | 11 | 0.909 | 0.909 | 1.000 | 1.000 | 0.922 | 0.939 | 1.000 | 12650 | 13819 |
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 11 | 0.909 | 1.000 | 1.000 | 1.000 | 0.955 | 0.966 | 1.000 | 3577 | 4172 |
| bm25@chunks-fixed | 11 | 0.455 | 0.727 | 0.818 | 0.818 | 0.558 | 0.615 | 1.000 | 2 | 2 |
| bm25@chunks-structure | 11 | 0.545 | 0.636 | 0.909 | 0.909 | 0.631 | 0.695 | 1.000 | 2 | 2 |
| dense@chunks-fixed | 11 | 0.545 | 1.000 | 1.000 | 1.000 | 0.685 | 0.762 | 1.000 | 268 | 287 |
| dense@chunks-structure | 11 | 0.727 | 1.000 | 1.000 | 1.000 | 0.864 | 0.899 | 1.000 | 252 | 288 |
| hybrid+rerank@chunks-structure~glm-4.7 | 11 | 0.909 | 0.909 | 1.000 | 1.000 | 0.920 | 0.938 | 1.000 | 1602 | 1954 |
| hybrid@chunks-fixed | 11 | 0.455 | 0.909 | 0.909 | 0.909 | 0.636 | 0.699 | 1.000 | 248 | 275 |
| hybrid@chunks-structure | 11 | 0.636 | 0.909 | 1.000 | 1.000 | 0.767 | 0.823 | 1.000 | 252 | 271 |
| wide+rerank+jur@chunks-structure~glm-4.7 | 11 | 0.909 | 1.000 | 1.000 | 1.000 | 0.955 | 0.966 | 1.000 | 5350 | 5690 |
| wide_no_terms+rerank+jur@chunks-structure~glm-4.7 | 11 | 0.909 | 1.000 | 1.000 | 1.000 | 0.955 | 0.966 | 1.000 | 4201 | 4523 |

### kind=real

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| agent+rerank@chunks-structure~glm-4.7 | 83 | 0.855 | 0.916 | 0.952 | 0.952 | 0.884 | 0.900 | 1.000 | 9601 | 18156 |
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 83 | 0.843 | 0.879 | 0.892 | 0.892 | 0.859 | 0.866 | 1.000 | 3615 | 4138 |
| bm25@chunks-fixed | 83 | 0.349 | 0.615 | 0.771 | 0.771 | 0.463 | 0.529 | 0.964 | 2 | 3 |
| bm25@chunks-structure | 83 | 0.325 | 0.542 | 0.711 | 0.711 | 0.440 | 0.497 | 0.964 | 2 | 2 |
| dense@chunks-fixed | 83 | 0.410 | 0.711 | 0.795 | 0.795 | 0.529 | 0.592 | 0.952 | 258 | 297 |
| dense@chunks-structure | 83 | 0.337 | 0.723 | 0.723 | 0.723 | 0.486 | 0.542 | 0.952 | 258 | 313 |
| hybrid+rerank@chunks-structure~glm-4.7 | 83 | 0.855 | 0.868 | 0.904 | 0.904 | 0.867 | 0.875 | 1.000 | 1614 | 2444 |
| hybrid@chunks-fixed | 83 | 0.446 | 0.687 | 0.807 | 0.807 | 0.560 | 0.614 | 0.976 | 259 | 292 |
| hybrid@chunks-structure | 83 | 0.410 | 0.651 | 0.759 | 0.759 | 0.520 | 0.572 | 0.976 | 258 | 300 |
| wide+rerank+jur@chunks-structure~glm-4.7 | 83 | 0.928 | 0.964 | 0.964 | 0.964 | 0.941 | 0.945 | 1.000 | 5690 | 6811 |
| wide_no_terms+rerank+jur@chunks-structure~glm-4.7 | 83 | 0.904 | 0.940 | 0.952 | 0.952 | 0.920 | 0.926 | 1.000 | 4693 | 5481 |

### lang=en->en

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| agent+rerank@chunks-structure~glm-4.7 | 40 | 0.875 | 0.900 | 0.975 | 0.975 | 0.893 | 0.911 | 1.000 | 12072 | 17927 |
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 40 | 0.850 | 0.900 | 0.925 | 0.925 | 0.874 | 0.886 | 1.000 | 3498 | 4046 |
| bm25@chunks-fixed | 40 | 0.325 | 0.625 | 0.825 | 0.825 | 0.456 | 0.536 | 1.000 | 2 | 2 |
| bm25@chunks-structure | 40 | 0.350 | 0.550 | 0.775 | 0.775 | 0.468 | 0.532 | 1.000 | 2 | 2 |
| dense@chunks-fixed | 40 | 0.400 | 0.650 | 0.700 | 0.700 | 0.489 | 0.538 | 0.950 | 253 | 302 |
| dense@chunks-structure | 40 | 0.450 | 0.700 | 0.700 | 0.700 | 0.552 | 0.587 | 0.975 | 256 | 297 |
| hybrid+rerank@chunks-structure~glm-4.7 | 40 | 0.850 | 0.875 | 0.925 | 0.925 | 0.869 | 0.881 | 1.000 | 1878 | 2647 |
| hybrid@chunks-fixed | 40 | 0.325 | 0.600 | 0.800 | 0.800 | 0.458 | 0.537 | 1.000 | 260 | 315 |
| hybrid@chunks-structure | 40 | 0.375 | 0.650 | 0.775 | 0.775 | 0.497 | 0.557 | 1.000 | 256 | 294 |
| wide+rerank+jur@chunks-structure~glm-4.7 | 40 | 0.950 | 0.975 | 0.975 | 0.975 | 0.965 | 0.966 | 1.000 | 5206 | 5690 |
| wide_no_terms+rerank+jur@chunks-structure~glm-4.7 | 40 | 0.950 | 0.975 | 0.975 | 0.975 | 0.965 | 0.966 | 1.000 | 4332 | 4871 |

### lang=ko->ko

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| agent+rerank@chunks-structure~glm-4.7 | 43 | 0.837 | 0.930 | 0.930 | 0.930 | 0.876 | 0.890 | 1.000 | 8892 | 18853 |
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 43 | 0.837 | 0.861 | 0.861 | 0.861 | 0.845 | 0.847 | 1.000 | 3674 | 4138 |
| bm25@chunks-fixed | 43 | 0.372 | 0.605 | 0.721 | 0.721 | 0.469 | 0.521 | 0.930 | 2 | 4 |
| bm25@chunks-structure | 43 | 0.302 | 0.535 | 0.651 | 0.651 | 0.414 | 0.466 | 0.930 | 2 | 2 |
| dense@chunks-fixed | 43 | 0.419 | 0.767 | 0.884 | 0.884 | 0.566 | 0.642 | 0.954 | 258 | 295 |
| dense@chunks-structure | 43 | 0.233 | 0.744 | 0.744 | 0.744 | 0.424 | 0.500 | 0.930 | 259 | 315 |
| hybrid+rerank@chunks-structure~glm-4.7 | 43 | 0.861 | 0.861 | 0.884 | 0.884 | 0.864 | 0.869 | 1.000 | 1569 | 1880 |
| hybrid@chunks-fixed | 43 | 0.558 | 0.767 | 0.814 | 0.814 | 0.654 | 0.686 | 0.954 | 259 | 286 |
| hybrid@chunks-structure | 43 | 0.442 | 0.651 | 0.744 | 0.744 | 0.541 | 0.585 | 0.954 | 264 | 300 |
| wide+rerank+jur@chunks-structure~glm-4.7 | 43 | 0.907 | 0.954 | 0.954 | 0.954 | 0.920 | 0.926 | 1.000 | 6294 | 6857 |
| wide_no_terms+rerank+jur@chunks-structure~glm-4.7 | 43 | 0.861 | 0.907 | 0.930 | 0.930 | 0.878 | 0.889 | 1.000 | 4932 | 5597 |
