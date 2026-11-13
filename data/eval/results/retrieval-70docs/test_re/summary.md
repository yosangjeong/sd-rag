
### all=all

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| agent+rerank@chunks-structure~glm-4.7 | 82 | 0.817 | 0.988 | 0.988 | 0.976 | 0.894 | 0.932 | 1.000 | 5040 | 11055 |
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 82 | 0.866 | 0.963 | 0.976 | 0.976 | 0.908 | 0.947 | 0.988 | 5806 | 7699 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 82 | 0.866 | 0.939 | 0.963 | 0.963 | 0.901 | 0.932 | 0.988 | 3176 | 3761 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 82 | 0.866 | 0.976 | 0.976 | 0.976 | 0.913 | 0.951 | 0.988 | 5168 | 6871 |
| bilingual_union+rerank@chunks-structure~glm-4.7~labor-prompts | 82 | 0.854 | 0.976 | 0.976 | 0.976 | 0.904 | 0.944 | 0.988 | 3065 | 3696 |
| bm25@chunks-fixed | 82 | 0.354 | 0.549 | 0.634 | 0.634 | 0.443 | 0.492 | 0.720 | 2 | 3 |
| bm25@chunks-structure | 82 | 0.342 | 0.598 | 0.658 | 0.652 | 0.447 | 0.507 | 0.720 | 2 | 2 |
| dense@chunks-fixed | 82 | 0.488 | 0.756 | 0.854 | 0.854 | 0.616 | 0.682 | 0.939 | 254 | 310 |
| dense@chunks-structure | 82 | 0.488 | 0.744 | 0.866 | 0.860 | 0.606 | 0.676 | 0.951 | 259 | 307 |
| hybrid+rerank@chunks-structure~glm-4.7 | 82 | 0.793 | 0.902 | 0.902 | 0.902 | 0.840 | 0.878 | 0.951 | 1478 | 2082 |
| hybrid@chunks-fixed | 82 | 0.463 | 0.756 | 0.829 | 0.829 | 0.583 | 0.646 | 0.927 | 260 | 306 |
| hybrid@chunks-structure | 82 | 0.427 | 0.780 | 0.842 | 0.835 | 0.570 | 0.645 | 0.915 | 261 | 322 |

### file_type=docx

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| agent+rerank@chunks-structure~glm-4.7 | 13 | 0.769 | 1.000 | 1.000 | 1.000 | 0.872 | 0.905 | 1.000 | 6248 | 9142 |
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 13 | 0.692 | 0.846 | 0.923 | 0.923 | 0.767 | 0.805 | 1.000 | 5578 | 6121 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 13 | 0.692 | 0.769 | 0.923 | 0.923 | 0.756 | 0.796 | 1.000 | 3473 | 3656 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 13 | 0.692 | 0.923 | 0.923 | 0.923 | 0.772 | 0.809 | 1.000 | 5072 | 6564 |
| bilingual_union+rerank@chunks-structure~glm-4.7~labor-prompts | 13 | 0.692 | 0.923 | 0.923 | 0.923 | 0.772 | 0.809 | 1.000 | 3268 | 3688 |
| bm25@chunks-fixed | 13 | 0.385 | 0.615 | 0.769 | 0.769 | 0.484 | 0.550 | 0.846 | 2 | 2 |
| bm25@chunks-structure | 13 | 0.462 | 0.615 | 0.692 | 0.692 | 0.533 | 0.571 | 0.846 | 2 | 2 |
| dense@chunks-fixed | 13 | 0.385 | 0.692 | 0.846 | 0.846 | 0.507 | 0.582 | 0.923 | 264 | 296 |
| dense@chunks-structure | 13 | 0.462 | 0.615 | 0.846 | 0.846 | 0.546 | 0.606 | 1.000 | 243 | 282 |
| hybrid+rerank@chunks-structure~glm-4.7 | 13 | 0.692 | 0.923 | 0.923 | 0.923 | 0.785 | 0.819 | 1.000 | 1467 | 2082 |
| hybrid@chunks-fixed | 13 | 0.308 | 0.769 | 0.846 | 0.846 | 0.479 | 0.564 | 1.000 | 278 | 311 |
| hybrid@chunks-structure | 13 | 0.385 | 0.615 | 0.846 | 0.846 | 0.523 | 0.595 | 1.000 | 265 | 306 |

### file_type=docx+hwpx

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| agent+rerank@chunks-structure~glm-4.7 | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 8197 | 8197 |
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 6703 | 6703 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.920 | 1.000 | 3897 | 3897 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 7003 | 7003 |
| bilingual_union+rerank@chunks-structure~glm-4.7~labor-prompts | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 3091 | 3091 |
| bm25@chunks-fixed | 1 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 2 | 2 |
| bm25@chunks-structure | 1 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 2 | 2 |
| dense@chunks-fixed | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.850 | 1.000 | 232 | 232 |
| dense@chunks-structure | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 224 | 224 |
| hybrid+rerank@chunks-structure~glm-4.7 | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1444 | 1444 |
| hybrid@chunks-fixed | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.798 | 1.000 | 239 | 239 |
| hybrid@chunks-structure | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.920 | 1.000 | 248 | 248 |

### file_type=hwpx

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| agent+rerank@chunks-structure~glm-4.7 | 17 | 0.882 | 0.941 | 0.941 | 0.941 | 0.912 | 1.022 | 1.000 | 6754 | 11331 |
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 17 | 0.941 | 0.941 | 0.941 | 0.941 | 0.941 | 1.044 | 0.941 | 5870 | 6644 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 17 | 0.824 | 0.882 | 0.882 | 0.882 | 0.843 | 0.942 | 0.941 | 2921 | 3491 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 17 | 0.882 | 0.941 | 0.941 | 0.941 | 0.912 | 1.022 | 0.941 | 5494 | 7280 |
| bilingual_union+rerank@chunks-structure~glm-4.7~labor-prompts | 17 | 0.882 | 0.941 | 0.941 | 0.941 | 0.912 | 1.022 | 0.941 | 2984 | 3403 |
| bm25@chunks-fixed | 17 | 0.294 | 0.529 | 0.706 | 0.706 | 0.414 | 0.509 | 0.765 | 2 | 3 |
| bm25@chunks-structure | 17 | 0.235 | 0.647 | 0.765 | 0.765 | 0.379 | 0.537 | 0.765 | 2 | 2 |
| dense@chunks-fixed | 17 | 0.471 | 0.647 | 0.882 | 0.882 | 0.573 | 0.715 | 0.882 | 239 | 282 |
| dense@chunks-structure | 17 | 0.471 | 0.706 | 0.882 | 0.882 | 0.594 | 0.726 | 0.941 | 255 | 308 |
| hybrid+rerank@chunks-structure~glm-4.7 | 17 | 0.824 | 0.882 | 0.882 | 0.882 | 0.853 | 0.963 | 0.941 | 1510 | 1878 |
| hybrid@chunks-fixed | 17 | 0.353 | 0.765 | 0.765 | 0.765 | 0.533 | 0.643 | 0.882 | 248 | 285 |
| hybrid@chunks-structure | 17 | 0.412 | 0.824 | 0.824 | 0.824 | 0.590 | 0.725 | 0.882 | 244 | 280 |

### file_type=hwpx+pdf

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| agent+rerank@chunks-structure~glm-4.7 | 2 | 0.500 | 1.000 | 1.000 | 0.500 | 0.750 | 0.500 | 1.000 | 5187 | 4856 |
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 2 | 0.500 | 1.000 | 1.000 | 1.000 | 0.750 | 0.847 | 1.000 | 5547 | 5341 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 2 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.920 | 1.000 | 3275 | 2870 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 2 | 0.500 | 1.000 | 1.000 | 1.000 | 0.750 | 0.847 | 1.000 | 4839 | 4298 |
| bilingual_union+rerank@chunks-structure~glm-4.7~labor-prompts | 2 | 0.500 | 1.000 | 1.000 | 1.000 | 0.750 | 0.847 | 1.000 | 2927 | 2563 |
| bm25@chunks-fixed | 2 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.960 | 1.000 | 2 | 2 |
| bm25@chunks-structure | 2 | 1.000 | 1.000 | 1.000 | 0.750 | 1.000 | 0.807 | 1.000 | 2 | 2 |
| dense@chunks-fixed | 2 | 0.500 | 0.500 | 0.500 | 0.500 | 0.542 | 0.460 | 1.000 | 259 | 245 |
| dense@chunks-structure | 2 | 0.500 | 0.500 | 1.000 | 0.750 | 0.550 | 0.589 | 1.000 | 229 | 226 |
| hybrid+rerank@chunks-structure~glm-4.7 | 2 | 0.500 | 1.000 | 1.000 | 1.000 | 0.750 | 0.847 | 1.000 | 1230 | 922 |
| hybrid@chunks-fixed | 2 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.916 | 1.000 | 257 | 255 |
| hybrid@chunks-structure | 2 | 0.500 | 1.000 | 1.000 | 0.750 | 0.750 | 0.693 | 1.000 | 261 | 260 |

### file_type=pdf

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| agent+rerank@chunks-structure~glm-4.7 | 32 | 0.812 | 1.000 | 1.000 | 1.000 | 0.901 | 0.927 | 1.000 | 4353 | 11055 |
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 32 | 0.875 | 1.000 | 1.000 | 1.000 | 0.930 | 0.948 | 1.000 | 5680 | 7342 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 32 | 0.875 | 1.000 | 1.000 | 1.000 | 0.930 | 0.948 | 1.000 | 3034 | 3617 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 32 | 0.906 | 1.000 | 1.000 | 1.000 | 0.953 | 0.965 | 1.000 | 5118 | 6320 |
| bilingual_union+rerank@chunks-structure~glm-4.7~labor-prompts | 32 | 0.875 | 1.000 | 1.000 | 1.000 | 0.930 | 0.948 | 1.000 | 3093 | 3779 |
| bm25@chunks-fixed | 32 | 0.312 | 0.531 | 0.562 | 0.562 | 0.408 | 0.445 | 0.656 | 2 | 3 |
| bm25@chunks-structure | 32 | 0.312 | 0.594 | 0.625 | 0.625 | 0.443 | 0.489 | 0.656 | 2 | 2 |
| dense@chunks-fixed | 32 | 0.500 | 0.781 | 0.812 | 0.812 | 0.622 | 0.667 | 0.938 | 264 | 323 |
| dense@chunks-structure | 32 | 0.438 | 0.750 | 0.812 | 0.812 | 0.576 | 0.629 | 0.938 | 277 | 297 |
| hybrid+rerank@chunks-structure~glm-4.7 | 32 | 0.781 | 0.875 | 0.875 | 0.875 | 0.823 | 0.836 | 0.938 | 1475 | 1962 |
| hybrid@chunks-fixed | 32 | 0.562 | 0.719 | 0.812 | 0.812 | 0.628 | 0.668 | 0.906 | 261 | 289 |
| hybrid@chunks-structure | 32 | 0.469 | 0.812 | 0.844 | 0.844 | 0.581 | 0.643 | 0.875 | 251 | 323 |

### file_type=scan

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| agent+rerank@chunks-structure~glm-4.7 | 17 | 0.824 | 1.000 | 1.000 | 1.000 | 0.892 | 0.919 | 1.000 | 4878 | 8613 |
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 17 | 0.941 | 1.000 | 1.000 | 1.000 | 0.956 | 0.967 | 1.000 | 6593 | 8219 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 17 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 3361 | 3761 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 17 | 0.941 | 1.000 | 1.000 | 1.000 | 0.961 | 0.971 | 1.000 | 5347 | 6838 |
| bilingual_union+rerank@chunks-structure~glm-4.7~labor-prompts | 17 | 0.941 | 1.000 | 1.000 | 1.000 | 0.961 | 0.971 | 1.000 | 3190 | 3455 |
| bm25@chunks-fixed | 17 | 0.412 | 0.529 | 0.588 | 0.588 | 0.467 | 0.495 | 0.706 | 2 | 2 |
| bm25@chunks-structure | 17 | 0.353 | 0.529 | 0.588 | 0.588 | 0.418 | 0.458 | 0.706 | 2 | 2 |
| dense@chunks-fixed | 17 | 0.529 | 0.882 | 0.941 | 0.941 | 0.717 | 0.771 | 1.000 | 267 | 290 |
| dense@chunks-structure | 17 | 0.588 | 0.882 | 0.941 | 0.941 | 0.705 | 0.758 | 0.941 | 257 | 311 |
| hybrid+rerank@chunks-structure~glm-4.7 | 17 | 0.882 | 0.941 | 0.941 | 0.941 | 0.902 | 0.912 | 0.941 | 1497 | 2178 |
| hybrid@chunks-fixed | 17 | 0.412 | 0.765 | 0.882 | 0.882 | 0.555 | 0.627 | 0.941 | 260 | 293 |
| hybrid@chunks-structure | 17 | 0.353 | 0.765 | 0.824 | 0.824 | 0.519 | 0.587 | 0.941 | 273 | 322 |

### kind=fact

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| agent+rerank@chunks-structure~glm-4.7 | 69 | 0.826 | 1.000 | 1.000 | 1.000 | 0.906 | 0.955 | 1.000 | 5015 | 11055 |
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 69 | 0.884 | 0.986 | 0.986 | 0.986 | 0.925 | 0.966 | 1.000 | 5779 | 8034 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 69 | 0.884 | 0.971 | 0.986 | 0.986 | 0.924 | 0.961 | 1.000 | 3151 | 3722 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 69 | 0.884 | 0.986 | 0.986 | 0.986 | 0.930 | 0.970 | 1.000 | 5140 | 6838 |
| bilingual_union+rerank@chunks-structure~glm-4.7~labor-prompts | 69 | 0.870 | 0.986 | 0.986 | 0.986 | 0.919 | 0.961 | 1.000 | 3085 | 3779 |
| bm25@chunks-fixed | 69 | 0.348 | 0.536 | 0.623 | 0.623 | 0.438 | 0.488 | 0.725 | 2 | 3 |
| bm25@chunks-structure | 69 | 0.333 | 0.580 | 0.652 | 0.652 | 0.437 | 0.505 | 0.725 | 2 | 2 |
| dense@chunks-fixed | 69 | 0.507 | 0.826 | 0.899 | 0.899 | 0.649 | 0.727 | 0.971 | 255 | 317 |
| dense@chunks-structure | 69 | 0.522 | 0.797 | 0.884 | 0.884 | 0.644 | 0.715 | 0.957 | 261 | 307 |
| hybrid+rerank@chunks-structure~glm-4.7 | 69 | 0.797 | 0.899 | 0.899 | 0.899 | 0.843 | 0.882 | 0.957 | 1500 | 2130 |
| hybrid@chunks-fixed | 69 | 0.464 | 0.768 | 0.841 | 0.841 | 0.588 | 0.659 | 0.942 | 262 | 306 |
| hybrid@chunks-structure | 69 | 0.435 | 0.783 | 0.841 | 0.841 | 0.569 | 0.650 | 0.927 | 263 | 323 |

### kind=multi

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| agent+rerank@chunks-structure~glm-4.7 | 3 | 0.667 | 1.000 | 1.000 | 0.667 | 0.833 | 0.667 | 1.000 | 5517 | 5517 |
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 3 | 0.667 | 1.000 | 1.000 | 1.000 | 0.833 | 0.898 | 1.000 | 5753 | 5753 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 3 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.920 | 1.000 | 3679 | 3679 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 3 | 0.667 | 1.000 | 1.000 | 1.000 | 0.833 | 0.898 | 1.000 | 5380 | 5380 |
| bilingual_union+rerank@chunks-structure~glm-4.7~labor-prompts | 3 | 0.667 | 1.000 | 1.000 | 1.000 | 0.833 | 0.898 | 1.000 | 3091 | 3091 |
| bm25@chunks-fixed | 3 | 0.667 | 0.667 | 0.667 | 0.667 | 0.667 | 0.640 | 0.667 | 2 | 2 |
| bm25@chunks-structure | 3 | 0.667 | 0.667 | 0.667 | 0.500 | 0.667 | 0.538 | 0.667 | 2 | 2 |
| dense@chunks-fixed | 3 | 0.667 | 0.667 | 0.667 | 0.667 | 0.694 | 0.590 | 1.000 | 245 | 245 |
| dense@chunks-structure | 3 | 0.667 | 0.667 | 1.000 | 0.833 | 0.700 | 0.726 | 1.000 | 226 | 226 |
| hybrid+rerank@chunks-structure~glm-4.7 | 3 | 0.667 | 1.000 | 1.000 | 1.000 | 0.833 | 0.898 | 1.000 | 1444 | 1444 |
| hybrid@chunks-fixed | 3 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.876 | 1.000 | 255 | 255 |
| hybrid@chunks-structure | 3 | 0.667 | 1.000 | 1.000 | 0.833 | 0.833 | 0.769 | 1.000 | 260 | 260 |

### kind=table

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| agent+rerank@chunks-structure~glm-4.7 | 10 | 0.800 | 0.900 | 0.900 | 0.900 | 0.833 | 0.850 | 1.000 | 5143 | 8348 |
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 10 | 0.800 | 0.800 | 0.900 | 0.900 | 0.814 | 0.833 | 0.900 | 6088 | 6806 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 10 | 0.700 | 0.700 | 0.800 | 0.800 | 0.717 | 0.736 | 0.900 | 3238 | 3766 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 10 | 0.800 | 0.900 | 0.900 | 0.900 | 0.820 | 0.839 | 0.900 | 5364 | 6247 |
| bilingual_union+rerank@chunks-structure~glm-4.7~labor-prompts | 10 | 0.800 | 0.900 | 0.900 | 0.900 | 0.820 | 0.839 | 0.900 | 2984 | 3403 |
| bm25@chunks-fixed | 10 | 0.300 | 0.600 | 0.700 | 0.700 | 0.414 | 0.482 | 0.700 | 2 | 3 |
| bm25@chunks-structure | 10 | 0.300 | 0.700 | 0.700 | 0.700 | 0.450 | 0.513 | 0.700 | 1 | 2 |
| dense@chunks-fixed | 10 | 0.300 | 0.300 | 0.600 | 0.600 | 0.366 | 0.399 | 0.700 | 266 | 292 |
| dense@chunks-structure | 10 | 0.200 | 0.400 | 0.700 | 0.700 | 0.320 | 0.392 | 0.900 | 270 | 299 |
| hybrid+rerank@chunks-structure~glm-4.7 | 10 | 0.800 | 0.900 | 0.900 | 0.900 | 0.820 | 0.839 | 0.900 | 1454 | 1622 |
| hybrid@chunks-fixed | 10 | 0.300 | 0.600 | 0.700 | 0.700 | 0.423 | 0.483 | 0.800 | 256 | 285 |
| hybrid@chunks-structure | 10 | 0.300 | 0.700 | 0.800 | 0.800 | 0.500 | 0.575 | 0.800 | 245 | 269 |

### lang=en->en

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| agent+rerank@chunks-structure~glm-4.7 | 18 | 0.944 | 1.000 | 1.000 | 1.000 | 0.972 | 0.980 | 1.000 | 4937 | 8461 |
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 18 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 6688 | 8171 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 18 | 0.889 | 1.000 | 1.000 | 1.000 | 0.944 | 0.959 | 1.000 | 3468 | 3801 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 18 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 5010 | 6358 |
| bilingual_union+rerank@chunks-structure~glm-4.7~labor-prompts | 18 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 3271 | 3806 |
| bm25@chunks-fixed | 18 | 0.500 | 0.722 | 0.778 | 0.778 | 0.598 | 0.638 | 1.000 | 2 | 2 |
| bm25@chunks-structure | 18 | 0.500 | 0.778 | 0.889 | 0.889 | 0.613 | 0.678 | 1.000 | 2 | 2 |
| dense@chunks-fixed | 18 | 0.722 | 0.944 | 0.944 | 0.944 | 0.817 | 0.849 | 1.000 | 257 | 308 |
| dense@chunks-structure | 18 | 0.667 | 0.944 | 1.000 | 1.000 | 0.789 | 0.841 | 1.000 | 271 | 295 |
| hybrid+rerank@chunks-structure~glm-4.7 | 18 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1445 | 2229 |
| hybrid@chunks-fixed | 18 | 0.667 | 0.833 | 0.833 | 0.833 | 0.760 | 0.772 | 1.000 | 271 | 306 |
| hybrid@chunks-structure | 18 | 0.556 | 0.889 | 0.889 | 0.889 | 0.675 | 0.723 | 1.000 | 259 | 300 |

### lang=en->ko

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| agent+rerank@chunks-structure~glm-4.7 | 15 | 0.800 | 0.933 | 0.933 | 0.933 | 0.867 | 0.884 | 1.000 | 4717 | 6754 |
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 15 | 0.867 | 0.933 | 0.933 | 0.933 | 0.889 | 0.900 | 0.933 | 5704 | 6703 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 15 | 0.800 | 0.867 | 0.867 | 0.867 | 0.833 | 0.837 | 0.933 | 3233 | 3766 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 15 | 0.867 | 0.933 | 0.933 | 0.933 | 0.889 | 0.900 | 0.933 | 5565 | 7280 |
| bilingual_union+rerank@chunks-structure~glm-4.7~labor-prompts | 15 | 0.867 | 0.933 | 0.933 | 0.933 | 0.889 | 0.900 | 0.933 | 3122 | 3467 |
| bm25@chunks-fixed | 15 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 2 | 3 |
| bm25@chunks-structure | 15 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 2 | 2 |
| dense@chunks-fixed | 15 | 0.400 | 0.533 | 0.733 | 0.733 | 0.490 | 0.532 | 0.867 | 271 | 299 |
| dense@chunks-structure | 15 | 0.467 | 0.533 | 0.667 | 0.667 | 0.512 | 0.540 | 0.867 | 271 | 311 |
| hybrid+rerank@chunks-structure~glm-4.7 | 15 | 0.600 | 0.667 | 0.667 | 0.667 | 0.633 | 0.642 | 0.867 | 1610 | 1880 |
| hybrid@chunks-fixed | 15 | 0.267 | 0.533 | 0.533 | 0.533 | 0.366 | 0.383 | 0.733 | 262 | 285 |
| hybrid@chunks-structure | 15 | 0.200 | 0.467 | 0.533 | 0.533 | 0.318 | 0.362 | 0.667 | 262 | 328 |

### lang=ko->en

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| agent+rerank@chunks-structure~glm-4.7 | 8 | 0.625 | 1.000 | 1.000 | 1.000 | 0.792 | 0.845 | 1.000 | 6860 | 10862 |
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 8 | 0.625 | 1.000 | 1.000 | 1.000 | 0.750 | 0.811 | 1.000 | 5842 | 7342 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 8 | 0.875 | 1.000 | 1.000 | 1.000 | 0.906 | 0.929 | 1.000 | 2942 | 3558 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 8 | 0.750 | 1.000 | 1.000 | 1.000 | 0.854 | 0.891 | 1.000 | 4926 | 5347 |
| bilingual_union+rerank@chunks-structure~glm-4.7~labor-prompts | 8 | 0.625 | 1.000 | 1.000 | 1.000 | 0.760 | 0.820 | 1.000 | 2845 | 3456 |
| bm25@chunks-fixed | 8 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 2 | 2 |
| bm25@chunks-structure | 8 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 2 | 2 |
| dense@chunks-fixed | 8 | 0.250 | 0.750 | 0.750 | 0.750 | 0.479 | 0.549 | 0.750 | 247 | 310 |
| dense@chunks-structure | 8 | 0.500 | 0.750 | 0.750 | 0.750 | 0.595 | 0.625 | 0.750 | 255 | 288 |
| hybrid+rerank@chunks-structure~glm-4.7 | 8 | 0.500 | 0.750 | 0.750 | 0.750 | 0.583 | 0.625 | 0.750 | 1452 | 1526 |
| hybrid@chunks-fixed | 8 | 0.000 | 0.250 | 0.750 | 0.750 | 0.132 | 0.272 | 0.750 | 253 | 260 |
| hybrid@chunks-structure | 8 | 0.000 | 0.500 | 0.750 | 0.750 | 0.159 | 0.296 | 0.750 | 268 | 309 |

### lang=ko->ko

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| agent+rerank@chunks-structure~glm-4.7 | 41 | 0.805 | 1.000 | 1.000 | 0.976 | 0.890 | 0.946 | 1.000 | 5812 | 11669 |
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 41 | 0.854 | 0.951 | 0.976 | 0.976 | 0.906 | 0.967 | 1.000 | 5753 | 7170 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 41 | 0.878 | 0.927 | 0.976 | 0.976 | 0.906 | 0.956 | 1.000 | 3019 | 3581 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 41 | 0.829 | 0.976 | 0.976 | 0.976 | 0.895 | 0.960 | 1.000 | 5186 | 6728 |
| bilingual_union+rerank@chunks-structure~glm-4.7~labor-prompts | 41 | 0.829 | 0.976 | 0.976 | 0.976 | 0.895 | 0.960 | 1.000 | 2906 | 3581 |
| bm25@chunks-fixed | 41 | 0.488 | 0.780 | 0.927 | 0.927 | 0.624 | 0.705 | 1.000 | 2 | 3 |
| bm25@chunks-structure | 41 | 0.463 | 0.854 | 0.927 | 0.915 | 0.625 | 0.717 | 1.000 | 2 | 2 |
| dense@chunks-fixed | 41 | 0.463 | 0.756 | 0.878 | 0.878 | 0.601 | 0.690 | 0.976 | 255 | 317 |
| dense@chunks-structure | 41 | 0.415 | 0.732 | 0.902 | 0.890 | 0.563 | 0.663 | 1.000 | 257 | 307 |
| hybrid+rerank@chunks-structure~glm-4.7 | 41 | 0.829 | 0.976 | 0.976 | 0.976 | 0.895 | 0.960 | 1.000 | 1500 | 2082 |
| hybrid@chunks-fixed | 41 | 0.537 | 0.902 | 0.951 | 0.951 | 0.673 | 0.759 | 1.000 | 256 | 306 |
| hybrid@chunks-structure | 41 | 0.537 | 0.902 | 0.951 | 0.939 | 0.696 | 0.783 | 1.000 | 260 | 306 |
