
### all=all

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| agent+rerank@chunks-structure~glm-4.7 | 338 | 0.784 | 0.893 | 0.911 | 0.904 | 0.831 | 0.846 | 0.956 | 5958 | 13333 |
| agent@chunks-structure~glm-4.7 | 338 | 0.663 | 0.837 | 0.890 | 0.883 | 0.743 | 0.772 | 0.944 | 6088 | 19544 |
| bilingual+rerank@chunks-fixed~glm-4.7 | 338 | 0.811 | 0.885 | 0.896 | 0.890 | 0.845 | 0.853 | 0.959 | 2632 | 3422 |
| bilingual+rerank@chunks-structure~glm-4.7 | 338 | 0.820 | 0.911 | 0.911 | 0.905 | 0.861 | 0.870 | 0.968 | 2403 | 2810 |
| bilingual@chunks-structure~glm-4.7 | 338 | 0.441 | 0.728 | 0.834 | 0.827 | 0.570 | 0.624 | 0.941 | 1205 | 1506 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 338 | 0.823 | 0.920 | 0.920 | 0.916 | 0.865 | 0.875 | 0.973 | 3250 | 5788 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 338 | 0.831 | 0.926 | 0.938 | 0.936 | 0.875 | 0.890 | 0.979 | 4011 | 6718 |
| bm25@chunks-fixed | 338 | 0.361 | 0.530 | 0.577 | 0.574 | 0.433 | 0.464 | 0.639 | 1 | 2 |
| bm25@chunks-structure | 338 | 0.343 | 0.515 | 0.577 | 0.575 | 0.422 | 0.456 | 0.636 | 1 | 2 |
| dense@chunks-fixed | 338 | 0.408 | 0.680 | 0.763 | 0.753 | 0.531 | 0.576 | 0.920 | 253 | 324 |
| dense@chunks-structure | 338 | 0.462 | 0.737 | 0.793 | 0.788 | 0.583 | 0.629 | 0.929 | 255 | 327 |
| hybrid+rerank@chunks-structure~glm-4.7 | 338 | 0.766 | 0.834 | 0.840 | 0.839 | 0.798 | 0.808 | 0.926 | 1442 | 1630 |
| hybrid@chunks-fixed | 338 | 0.405 | 0.672 | 0.754 | 0.750 | 0.526 | 0.574 | 0.867 | 265 | 330 |
| hybrid@chunks-structure | 338 | 0.414 | 0.692 | 0.781 | 0.777 | 0.534 | 0.589 | 0.876 | 270 | 346 |
| per_language@chunks-fixed | 338 | 0.278 | 0.648 | 0.746 | 0.738 | 0.440 | 0.506 | 0.882 | 272 | 334 |
| per_language@chunks-structure | 338 | 0.314 | 0.675 | 0.775 | 0.769 | 0.469 | 0.536 | 0.890 | 278 | 352 |

### file_type=docx

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| agent+rerank@chunks-structure~glm-4.7 | 57 | 0.789 | 0.877 | 0.895 | 0.895 | 0.830 | 0.856 | 0.947 | 5331 | 13989 |
| agent@chunks-structure~glm-4.7 | 57 | 0.614 | 0.842 | 0.860 | 0.860 | 0.719 | 0.760 | 0.930 | 6681 | 18843 |
| bilingual+rerank@chunks-fixed~glm-4.7 | 57 | 0.754 | 0.912 | 0.912 | 0.912 | 0.822 | 0.855 | 0.947 | 2528 | 3916 |
| bilingual+rerank@chunks-structure~glm-4.7 | 57 | 0.860 | 0.947 | 0.947 | 0.947 | 0.903 | 0.925 | 0.983 | 2346 | 2703 |
| bilingual@chunks-structure~glm-4.7 | 57 | 0.509 | 0.754 | 0.895 | 0.895 | 0.617 | 0.690 | 0.947 | 1200 | 1399 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 57 | 0.842 | 0.965 | 0.965 | 0.965 | 0.886 | 0.915 | 0.983 | 3016 | 5534 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 57 | 0.860 | 0.965 | 0.965 | 0.965 | 0.908 | 0.932 | 0.983 | 3738 | 6006 |
| bm25@chunks-fixed | 57 | 0.404 | 0.649 | 0.702 | 0.702 | 0.503 | 0.556 | 0.754 | 1 | 2 |
| bm25@chunks-structure | 57 | 0.368 | 0.649 | 0.667 | 0.667 | 0.488 | 0.535 | 0.719 | 1 | 2 |
| dense@chunks-fixed | 57 | 0.333 | 0.632 | 0.737 | 0.737 | 0.467 | 0.530 | 0.912 | 255 | 348 |
| dense@chunks-structure | 57 | 0.456 | 0.772 | 0.877 | 0.877 | 0.601 | 0.676 | 0.947 | 252 | 314 |
| hybrid+rerank@chunks-structure~glm-4.7 | 57 | 0.807 | 0.877 | 0.877 | 0.877 | 0.838 | 0.858 | 0.930 | 1437 | 1716 |
| hybrid@chunks-fixed | 57 | 0.386 | 0.737 | 0.807 | 0.807 | 0.543 | 0.609 | 0.895 | 260 | 314 |
| hybrid@chunks-structure | 57 | 0.491 | 0.772 | 0.825 | 0.825 | 0.614 | 0.673 | 0.930 | 270 | 337 |
| per_language@chunks-fixed | 57 | 0.404 | 0.702 | 0.772 | 0.772 | 0.507 | 0.571 | 0.860 | 279 | 338 |
| per_language@chunks-structure | 57 | 0.526 | 0.754 | 0.825 | 0.825 | 0.601 | 0.662 | 0.895 | 284 | 378 |

### file_type=docx+hwpx

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| agent+rerank@chunks-structure~glm-4.7 | 3 | 1.000 | 1.000 | 1.000 | 0.833 | 1.000 | 0.844 | 1.000 | 7972 | 7972 |
| agent@chunks-structure~glm-4.7 | 3 | 0.667 | 0.667 | 1.000 | 0.833 | 0.700 | 0.699 | 1.000 | 5861 | 5861 |
| bilingual+rerank@chunks-fixed~glm-4.7 | 3 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.923 | 1.000 | 2454 | 2454 |
| bilingual+rerank@chunks-structure~glm-4.7 | 3 | 0.667 | 1.000 | 1.000 | 0.833 | 0.833 | 0.769 | 1.000 | 2468 | 2468 |
| bilingual@chunks-structure~glm-4.7 | 3 | 0.333 | 1.000 | 1.000 | 0.667 | 0.611 | 0.565 | 1.000 | 1165 | 1165 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 3 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.932 | 1.000 | 3073 | 3073 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 3 | 0.667 | 1.000 | 1.000 | 1.000 | 0.833 | 0.857 | 1.000 | 3488 | 3488 |
| bm25@chunks-fixed | 3 | 0.667 | 0.667 | 0.667 | 0.667 | 0.667 | 0.602 | 0.667 | 2 | 2 |
| bm25@chunks-structure | 3 | 0.667 | 0.667 | 0.667 | 0.667 | 0.667 | 0.602 | 0.667 | 1 | 1 |
| dense@chunks-fixed | 3 | 0.667 | 1.000 | 1.000 | 0.667 | 0.833 | 0.640 | 1.000 | 238 | 238 |
| dense@chunks-structure | 3 | 0.333 | 0.667 | 1.000 | 1.000 | 0.492 | 0.633 | 1.000 | 246 | 246 |
| hybrid+rerank@chunks-structure~glm-4.7 | 3 | 0.667 | 1.000 | 1.000 | 1.000 | 0.833 | 0.857 | 1.000 | 1412 | 1412 |
| hybrid@chunks-fixed | 3 | 0.333 | 1.000 | 1.000 | 1.000 | 0.556 | 0.655 | 1.000 | 247 | 247 |
| hybrid@chunks-structure | 3 | 0.333 | 0.667 | 1.000 | 0.833 | 0.486 | 0.565 | 1.000 | 280 | 280 |
| per_language@chunks-fixed | 3 | 0.333 | 1.000 | 1.000 | 1.000 | 0.467 | 0.554 | 1.000 | 258 | 258 |
| per_language@chunks-structure | 3 | 0.333 | 0.667 | 0.667 | 0.500 | 0.430 | 0.386 | 1.000 | 268 | 268 |

### file_type=docx+pdf

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| agent+rerank@chunks-structure~glm-4.7 | 4 | 1.000 | 1.000 | 1.000 | 0.750 | 1.000 | 0.776 | 1.000 | 9642 | 9847 |
| agent@chunks-structure~glm-4.7 | 4 | 1.000 | 1.000 | 1.000 | 0.750 | 1.000 | 0.786 | 1.000 | 6167 | 6742 |
| bilingual+rerank@chunks-fixed~glm-4.7 | 4 | 1.000 | 1.000 | 1.000 | 0.750 | 1.000 | 0.724 | 1.000 | 2421 | 2476 |
| bilingual+rerank@chunks-structure~glm-4.7 | 4 | 1.000 | 1.000 | 1.000 | 0.750 | 1.000 | 0.776 | 1.000 | 2489 | 2558 |
| bilingual@chunks-structure~glm-4.7 | 4 | 0.500 | 1.000 | 1.000 | 0.750 | 0.708 | 0.585 | 1.000 | 1168 | 1203 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 4 | 1.000 | 1.000 | 1.000 | 0.750 | 1.000 | 0.732 | 1.000 | 3090 | 3091 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 4 | 1.000 | 1.000 | 1.000 | 0.875 | 1.000 | 0.873 | 1.000 | 3405 | 3543 |
| bm25@chunks-fixed | 4 | 0.500 | 0.750 | 0.750 | 0.500 | 0.625 | 0.480 | 0.750 | 1 | 1 |
| bm25@chunks-structure | 4 | 0.750 | 0.750 | 0.750 | 0.625 | 0.750 | 0.623 | 0.750 | 2 | 2 |
| dense@chunks-fixed | 4 | 0.750 | 1.000 | 1.000 | 0.625 | 0.875 | 0.616 | 1.000 | 243 | 244 |
| dense@chunks-structure | 4 | 0.500 | 1.000 | 1.000 | 0.750 | 0.688 | 0.594 | 1.000 | 237 | 239 |
| hybrid+rerank@chunks-structure~glm-4.7 | 4 | 1.000 | 1.000 | 1.000 | 0.875 | 1.000 | 0.873 | 1.000 | 1450 | 1463 |
| hybrid@chunks-fixed | 4 | 0.500 | 1.000 | 1.000 | 0.750 | 0.750 | 0.621 | 1.000 | 284 | 299 |
| hybrid@chunks-structure | 4 | 0.500 | 1.000 | 1.000 | 0.750 | 0.667 | 0.623 | 1.000 | 280 | 287 |
| per_language@chunks-fixed | 4 | 0.500 | 1.000 | 1.000 | 0.625 | 0.667 | 0.511 | 1.000 | 264 | 269 |
| per_language@chunks-structure | 4 | 0.500 | 1.000 | 1.000 | 0.750 | 0.600 | 0.553 | 1.000 | 276 | 277 |

### file_type=hwpx

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| agent+rerank@chunks-structure~glm-4.7 | 58 | 0.776 | 0.845 | 0.862 | 0.862 | 0.807 | 0.821 | 0.948 | 5426 | 12392 |
| agent@chunks-structure~glm-4.7 | 58 | 0.672 | 0.810 | 0.897 | 0.897 | 0.747 | 0.780 | 0.948 | 5508 | 21283 |
| bilingual+rerank@chunks-fixed~glm-4.7 | 58 | 0.862 | 0.897 | 0.897 | 0.897 | 0.876 | 0.882 | 0.983 | 2643 | 3422 |
| bilingual+rerank@chunks-structure~glm-4.7 | 58 | 0.810 | 0.862 | 0.862 | 0.862 | 0.833 | 0.841 | 0.966 | 2378 | 2640 |
| bilingual@chunks-structure~glm-4.7 | 58 | 0.466 | 0.759 | 0.845 | 0.845 | 0.593 | 0.652 | 0.948 | 1154 | 1350 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 58 | 0.828 | 0.914 | 0.914 | 0.914 | 0.866 | 0.878 | 0.983 | 3327 | 5079 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 58 | 0.828 | 0.897 | 0.897 | 0.897 | 0.859 | 0.869 | 0.966 | 4023 | 6904 |
| bm25@chunks-fixed | 58 | 0.397 | 0.466 | 0.534 | 0.534 | 0.423 | 0.449 | 0.638 | 1 | 2 |
| bm25@chunks-structure | 58 | 0.328 | 0.483 | 0.552 | 0.552 | 0.404 | 0.440 | 0.638 | 1 | 2 |
| dense@chunks-fixed | 58 | 0.345 | 0.707 | 0.776 | 0.776 | 0.502 | 0.565 | 0.966 | 248 | 300 |
| dense@chunks-structure | 58 | 0.431 | 0.741 | 0.776 | 0.776 | 0.556 | 0.607 | 0.914 | 258 | 319 |
| hybrid+rerank@chunks-structure~glm-4.7 | 58 | 0.793 | 0.862 | 0.862 | 0.862 | 0.828 | 0.837 | 0.948 | 1447 | 1582 |
| hybrid@chunks-fixed | 58 | 0.466 | 0.690 | 0.793 | 0.793 | 0.566 | 0.616 | 0.966 | 262 | 312 |
| hybrid@chunks-structure | 58 | 0.448 | 0.690 | 0.776 | 0.776 | 0.552 | 0.601 | 0.897 | 273 | 330 |
| per_language@chunks-fixed | 58 | 0.466 | 0.690 | 0.759 | 0.759 | 0.537 | 0.586 | 0.914 | 269 | 318 |
| per_language@chunks-structure | 58 | 0.517 | 0.690 | 0.724 | 0.724 | 0.573 | 0.603 | 0.862 | 280 | 351 |

### file_type=hwpx+pdf

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| agent+rerank@chunks-structure~glm-4.7 | 2 | 1.000 | 1.000 | 1.000 | 0.500 | 1.000 | 0.460 | 1.000 | 3293 | 2083 |
| agent@chunks-structure~glm-4.7 | 2 | 1.000 | 1.000 | 1.000 | 0.500 | 1.000 | 0.439 | 1.000 | 5210 | 1370 |
| bilingual+rerank@chunks-fixed~glm-4.7 | 2 | 1.000 | 1.000 | 1.000 | 0.500 | 1.000 | 0.613 | 1.000 | 2518 | 2498 |
| bilingual+rerank@chunks-structure~glm-4.7 | 2 | 1.000 | 1.000 | 1.000 | 0.750 | 1.000 | 0.766 | 1.000 | 2215 | 2183 |
| bilingual@chunks-structure~glm-4.7 | 2 | 1.000 | 1.000 | 1.000 | 0.750 | 1.000 | 0.693 | 1.000 | 1475 | 1243 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 2 | 1.000 | 1.000 | 1.000 | 0.750 | 1.000 | 0.807 | 1.000 | 2822 | 2774 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 2 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.869 | 1.000 | 3512 | 3494 |
| bm25@chunks-fixed | 2 | 0.000 | 1.000 | 1.000 | 1.000 | 0.417 | 0.567 | 1.000 | 1 | 1 |
| bm25@chunks-structure | 2 | 0.500 | 1.000 | 1.000 | 1.000 | 0.667 | 0.694 | 1.000 | 1 | 1 |
| dense@chunks-fixed | 2 | 0.500 | 1.000 | 1.000 | 0.500 | 0.750 | 0.387 | 1.000 | 247 | 228 |
| dense@chunks-structure | 2 | 1.000 | 1.000 | 1.000 | 0.750 | 1.000 | 0.653 | 1.000 | 285 | 241 |
| hybrid+rerank@chunks-structure~glm-4.7 | 2 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.855 | 1.000 | 1375 | 1372 |
| hybrid@chunks-fixed | 2 | 0.000 | 1.000 | 1.000 | 0.750 | 0.500 | 0.489 | 1.000 | 271 | 241 |
| hybrid@chunks-structure | 2 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.782 | 1.000 | 246 | 241 |
| per_language@chunks-fixed | 2 | 0.000 | 1.000 | 1.000 | 0.500 | 0.333 | 0.307 | 1.000 | 272 | 239 |
| per_language@chunks-structure | 2 | 1.000 | 1.000 | 1.000 | 0.750 | 1.000 | 0.613 | 1.000 | 277 | 266 |

### file_type=pdf

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| agent+rerank@chunks-structure~glm-4.7 | 160 | 0.806 | 0.931 | 0.956 | 0.956 | 0.861 | 0.884 | 0.975 | 6238 | 12096 |
| agent@chunks-structure~glm-4.7 | 160 | 0.669 | 0.856 | 0.925 | 0.925 | 0.753 | 0.793 | 0.969 | 6178 | 17576 |
| bilingual+rerank@chunks-fixed~glm-4.7 | 160 | 0.812 | 0.875 | 0.900 | 0.900 | 0.846 | 0.859 | 0.975 | 2666 | 3373 |
| bilingual+rerank@chunks-structure~glm-4.7 | 160 | 0.819 | 0.931 | 0.931 | 0.931 | 0.869 | 0.884 | 0.981 | 2448 | 2844 |
| bilingual@chunks-structure~glm-4.7 | 160 | 0.419 | 0.731 | 0.831 | 0.831 | 0.562 | 0.620 | 0.963 | 1232 | 1528 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 160 | 0.812 | 0.919 | 0.919 | 0.919 | 0.860 | 0.875 | 0.988 | 3357 | 5877 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 160 | 0.844 | 0.938 | 0.956 | 0.956 | 0.889 | 0.906 | 0.994 | 4246 | 7156 |
| bm25@chunks-fixed | 160 | 0.356 | 0.500 | 0.550 | 0.550 | 0.424 | 0.452 | 0.606 | 2 | 2 |
| bm25@chunks-structure | 160 | 0.344 | 0.469 | 0.550 | 0.550 | 0.406 | 0.438 | 0.606 | 1 | 2 |
| dense@chunks-fixed | 160 | 0.463 | 0.669 | 0.769 | 0.769 | 0.563 | 0.610 | 0.931 | 253 | 334 |
| dense@chunks-structure | 160 | 0.519 | 0.744 | 0.769 | 0.769 | 0.617 | 0.651 | 0.938 | 257 | 312 |
| hybrid+rerank@chunks-structure~glm-4.7 | 160 | 0.750 | 0.819 | 0.825 | 0.825 | 0.781 | 0.792 | 0.938 | 1436 | 1628 |
| hybrid@chunks-fixed | 160 | 0.412 | 0.662 | 0.744 | 0.744 | 0.524 | 0.572 | 0.856 | 266 | 336 |
| hybrid@chunks-structure | 160 | 0.412 | 0.688 | 0.775 | 0.775 | 0.531 | 0.586 | 0.875 | 270 | 346 |
| per_language@chunks-fixed | 160 | 0.138 | 0.619 | 0.750 | 0.750 | 0.374 | 0.461 | 0.925 | 272 | 339 |
| per_language@chunks-structure | 160 | 0.163 | 0.650 | 0.794 | 0.794 | 0.396 | 0.490 | 0.931 | 277 | 336 |

### file_type=scan

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| agent+rerank@chunks-structure~glm-4.7 | 54 | 0.685 | 0.833 | 0.833 | 0.833 | 0.743 | 0.766 | 0.907 | 6427 | 14475 |
| agent@chunks-structure~glm-4.7 | 54 | 0.648 | 0.796 | 0.796 | 0.796 | 0.711 | 0.730 | 0.870 | 5587 | 21203 |
| bilingual+rerank@chunks-fixed~glm-4.7 | 54 | 0.778 | 0.852 | 0.852 | 0.852 | 0.809 | 0.820 | 0.889 | 2608 | 3329 |
| bilingual+rerank@chunks-structure~glm-4.7 | 54 | 0.778 | 0.852 | 0.852 | 0.852 | 0.807 | 0.818 | 0.907 | 2379 | 2739 |
| bilingual@chunks-structure~glm-4.7 | 54 | 0.389 | 0.611 | 0.741 | 0.741 | 0.490 | 0.542 | 0.852 | 1168 | 1493 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 54 | 0.796 | 0.870 | 0.870 | 0.870 | 0.832 | 0.841 | 0.907 | 3202 | 5476 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 54 | 0.759 | 0.870 | 0.889 | 0.889 | 0.808 | 0.828 | 0.944 | 3986 | 6620 |
| bm25@chunks-fixed | 54 | 0.278 | 0.518 | 0.537 | 0.537 | 0.368 | 0.407 | 0.593 | 1 | 2 |
| bm25@chunks-structure | 54 | 0.278 | 0.500 | 0.556 | 0.556 | 0.372 | 0.415 | 0.611 | 1 | 2 |
| dense@chunks-fixed | 54 | 0.352 | 0.685 | 0.722 | 0.722 | 0.488 | 0.539 | 0.833 | 262 | 309 |
| dense@chunks-structure | 54 | 0.315 | 0.648 | 0.759 | 0.759 | 0.474 | 0.540 | 0.889 | 255 | 323 |
| hybrid+rerank@chunks-structure~glm-4.7 | 54 | 0.722 | 0.778 | 0.796 | 0.796 | 0.750 | 0.761 | 0.852 | 1449 | 1623 |
| hybrid@chunks-fixed | 54 | 0.352 | 0.556 | 0.648 | 0.648 | 0.453 | 0.491 | 0.741 | 266 | 355 |
| hybrid@chunks-structure | 54 | 0.278 | 0.593 | 0.722 | 0.722 | 0.415 | 0.484 | 0.778 | 269 | 355 |
| per_language@chunks-fixed | 54 | 0.352 | 0.574 | 0.648 | 0.648 | 0.450 | 0.491 | 0.722 | 271 | 309 |
| per_language@chunks-structure | 54 | 0.278 | 0.611 | 0.704 | 0.704 | 0.407 | 0.473 | 0.778 | 278 | 371 |

### kind=fact

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| agent+rerank@chunks-structure~glm-4.7 | 293 | 0.792 | 0.908 | 0.925 | 0.925 | 0.842 | 0.864 | 0.963 | 5990 | 12860 |
| agent@chunks-structure~glm-4.7 | 293 | 0.669 | 0.857 | 0.901 | 0.901 | 0.752 | 0.788 | 0.952 | 6118 | 19649 |
| bilingual+rerank@chunks-fixed~glm-4.7 | 293 | 0.816 | 0.894 | 0.908 | 0.908 | 0.853 | 0.868 | 0.963 | 2629 | 3422 |
| bilingual+rerank@chunks-structure~glm-4.7 | 293 | 0.819 | 0.915 | 0.915 | 0.915 | 0.862 | 0.877 | 0.966 | 2404 | 2793 |
| bilingual@chunks-structure~glm-4.7 | 293 | 0.457 | 0.741 | 0.836 | 0.836 | 0.583 | 0.641 | 0.935 | 1202 | 1506 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 293 | 0.833 | 0.932 | 0.932 | 0.932 | 0.874 | 0.891 | 0.983 | 3280 | 5788 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 293 | 0.829 | 0.928 | 0.939 | 0.939 | 0.875 | 0.893 | 0.980 | 4027 | 6718 |
| bm25@chunks-fixed | 293 | 0.362 | 0.529 | 0.573 | 0.573 | 0.432 | 0.465 | 0.625 | 1 | 2 |
| bm25@chunks-structure | 293 | 0.331 | 0.512 | 0.570 | 0.570 | 0.412 | 0.450 | 0.621 | 1 | 2 |
| dense@chunks-fixed | 293 | 0.430 | 0.710 | 0.795 | 0.795 | 0.555 | 0.611 | 0.928 | 252 | 320 |
| dense@chunks-structure | 293 | 0.491 | 0.758 | 0.799 | 0.799 | 0.609 | 0.655 | 0.935 | 257 | 310 |
| hybrid+rerank@chunks-structure~glm-4.7 | 293 | 0.758 | 0.833 | 0.836 | 0.836 | 0.792 | 0.805 | 0.928 | 1438 | 1621 |
| hybrid@chunks-fixed | 293 | 0.430 | 0.686 | 0.764 | 0.764 | 0.545 | 0.594 | 0.864 | 265 | 336 |
| hybrid@chunks-structure | 293 | 0.423 | 0.700 | 0.778 | 0.778 | 0.542 | 0.598 | 0.874 | 271 | 341 |
| per_language@chunks-fixed | 293 | 0.283 | 0.665 | 0.764 | 0.764 | 0.455 | 0.527 | 0.891 | 273 | 334 |
| per_language@chunks-structure | 293 | 0.307 | 0.693 | 0.788 | 0.788 | 0.474 | 0.550 | 0.898 | 278 | 352 |

### kind=multi

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| agent+rerank@chunks-structure~glm-4.7 | 9 | 1.000 | 1.000 | 1.000 | 0.722 | 1.000 | 0.729 | 1.000 | 7972 | 9847 |
| agent@chunks-structure~glm-4.7 | 9 | 0.889 | 0.889 | 1.000 | 0.722 | 0.900 | 0.680 | 1.000 | 5861 | 9051 |
| bilingual+rerank@chunks-fixed~glm-4.7 | 9 | 1.000 | 1.000 | 1.000 | 0.778 | 1.000 | 0.766 | 1.000 | 2476 | 2989 |
| bilingual+rerank@chunks-structure~glm-4.7 | 9 | 0.889 | 1.000 | 1.000 | 0.778 | 0.944 | 0.771 | 1.000 | 2420 | 2641 |
| bilingual@chunks-structure~glm-4.7 | 9 | 0.556 | 1.000 | 1.000 | 0.722 | 0.741 | 0.602 | 1.000 | 1203 | 1707 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 9 | 1.000 | 1.000 | 1.000 | 0.833 | 1.000 | 0.815 | 1.000 | 3073 | 5098 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 9 | 0.889 | 1.000 | 1.000 | 0.944 | 0.944 | 0.867 | 1.000 | 3494 | 3778 |
| bm25@chunks-fixed | 9 | 0.444 | 0.778 | 0.778 | 0.667 | 0.593 | 0.540 | 0.778 | 1 | 2 |
| bm25@chunks-structure | 9 | 0.667 | 0.778 | 0.778 | 0.722 | 0.704 | 0.632 | 0.778 | 1 | 5 |
| dense@chunks-fixed | 9 | 0.667 | 1.000 | 1.000 | 0.611 | 0.833 | 0.573 | 1.000 | 242 | 265 |
| dense@chunks-structure | 9 | 0.556 | 0.889 | 1.000 | 0.833 | 0.692 | 0.620 | 1.000 | 241 | 284 |
| hybrid+rerank@chunks-structure~glm-4.7 | 9 | 0.889 | 1.000 | 1.000 | 0.944 | 0.944 | 0.864 | 1.000 | 1412 | 1517 |
| hybrid@chunks-fixed | 9 | 0.333 | 1.000 | 1.000 | 0.833 | 0.630 | 0.603 | 1.000 | 270 | 301 |
| hybrid@chunks-structure | 9 | 0.556 | 0.889 | 1.000 | 0.833 | 0.681 | 0.639 | 1.000 | 273 | 287 |
| per_language@chunks-fixed | 9 | 0.333 | 1.000 | 1.000 | 0.722 | 0.526 | 0.480 | 1.000 | 258 | 305 |
| per_language@chunks-structure | 9 | 0.556 | 0.889 | 0.889 | 0.667 | 0.632 | 0.510 | 1.000 | 275 | 287 |

### kind=table

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| agent+rerank@chunks-structure~glm-4.7 | 36 | 0.667 | 0.750 | 0.778 | 0.778 | 0.704 | 0.722 | 0.889 | 5670 | 14475 |
| agent@chunks-structure~glm-4.7 | 36 | 0.556 | 0.667 | 0.778 | 0.778 | 0.631 | 0.662 | 0.861 | 5529 | 17715 |
| bilingual+rerank@chunks-fixed~glm-4.7 | 36 | 0.722 | 0.778 | 0.778 | 0.778 | 0.745 | 0.754 | 0.917 | 2724 | 3160 |
| bilingual+rerank@chunks-structure~glm-4.7 | 36 | 0.806 | 0.861 | 0.861 | 0.861 | 0.833 | 0.841 | 0.972 | 2377 | 2810 |
| bilingual@chunks-structure~glm-4.7 | 36 | 0.278 | 0.556 | 0.778 | 0.778 | 0.417 | 0.494 | 0.972 | 1212 | 1412 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 36 | 0.694 | 0.806 | 0.806 | 0.806 | 0.752 | 0.764 | 0.889 | 3172 | 5396 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 36 | 0.833 | 0.889 | 0.917 | 0.917 | 0.860 | 0.874 | 0.972 | 4021 | 6478 |
| bm25@chunks-fixed | 36 | 0.333 | 0.472 | 0.556 | 0.556 | 0.401 | 0.435 | 0.722 | 2 | 2 |
| bm25@chunks-structure | 36 | 0.361 | 0.472 | 0.583 | 0.583 | 0.429 | 0.462 | 0.722 | 1 | 2 |
| dense@chunks-fixed | 36 | 0.167 | 0.361 | 0.444 | 0.444 | 0.265 | 0.294 | 0.833 | 257 | 349 |
| dense@chunks-structure | 36 | 0.194 | 0.528 | 0.694 | 0.694 | 0.342 | 0.421 | 0.861 | 248 | 341 |
| hybrid+rerank@chunks-structure~glm-4.7 | 36 | 0.806 | 0.806 | 0.833 | 0.833 | 0.809 | 0.815 | 0.889 | 1466 | 1758 |
| hybrid@chunks-fixed | 36 | 0.222 | 0.472 | 0.611 | 0.611 | 0.344 | 0.402 | 0.861 | 263 | 312 |
| hybrid@chunks-structure | 36 | 0.306 | 0.583 | 0.750 | 0.750 | 0.432 | 0.502 | 0.861 | 262 | 361 |
| per_language@chunks-fixed | 36 | 0.222 | 0.417 | 0.528 | 0.528 | 0.300 | 0.344 | 0.778 | 263 | 316 |
| per_language@chunks-structure | 36 | 0.306 | 0.472 | 0.639 | 0.639 | 0.386 | 0.436 | 0.806 | 281 | 337 |

### lang=en->en

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| agent+rerank@chunks-structure~glm-4.7 | 68 | 0.794 | 0.971 | 0.971 | 0.971 | 0.866 | 0.892 | 0.985 | 5589 | 8797 |
| agent@chunks-structure~glm-4.7 | 68 | 0.647 | 0.926 | 0.971 | 0.971 | 0.763 | 0.813 | 0.985 | 4879 | 11644 |
| bilingual+rerank@chunks-fixed~glm-4.7 | 68 | 0.868 | 0.912 | 0.941 | 0.941 | 0.890 | 0.902 | 0.985 | 2706 | 3373 |
| bilingual+rerank@chunks-structure~glm-4.7 | 68 | 0.824 | 0.971 | 0.971 | 0.971 | 0.891 | 0.910 | 0.985 | 2575 | 2850 |
| bilingual@chunks-structure~glm-4.7 | 68 | 0.441 | 0.809 | 0.897 | 0.897 | 0.593 | 0.661 | 0.985 | 1392 | 1639 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 68 | 0.868 | 0.985 | 0.985 | 0.985 | 0.917 | 0.934 | 1.000 | 3486 | 5907 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 68 | 0.838 | 0.956 | 0.985 | 0.985 | 0.895 | 0.917 | 1.000 | 4302 | 6486 |
| bm25@chunks-fixed | 68 | 0.544 | 0.794 | 0.882 | 0.882 | 0.657 | 0.708 | 0.985 | 2 | 2 |
| bm25@chunks-structure | 68 | 0.515 | 0.721 | 0.868 | 0.868 | 0.612 | 0.667 | 0.985 | 2 | 2 |
| dense@chunks-fixed | 68 | 0.632 | 0.853 | 0.926 | 0.926 | 0.745 | 0.787 | 1.000 | 255 | 390 |
| dense@chunks-structure | 68 | 0.662 | 0.912 | 0.941 | 0.941 | 0.780 | 0.818 | 1.000 | 256 | 301 |
| hybrid+rerank@chunks-structure~glm-4.7 | 68 | 0.838 | 0.971 | 0.985 | 0.985 | 0.895 | 0.917 | 1.000 | 1464 | 1645 |
| hybrid@chunks-fixed | 68 | 0.647 | 0.941 | 0.985 | 0.985 | 0.761 | 0.816 | 1.000 | 264 | 323 |
| hybrid@chunks-structure | 68 | 0.632 | 0.941 | 0.971 | 0.971 | 0.762 | 0.813 | 1.000 | 271 | 341 |
| per_language@chunks-fixed | 68 | 0.000 | 0.750 | 0.941 | 0.941 | 0.379 | 0.515 | 1.000 | 268 | 334 |
| per_language@chunks-structure | 68 | 0.000 | 0.794 | 0.956 | 0.956 | 0.381 | 0.523 | 1.000 | 280 | 330 |

### lang=en->ko

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| agent+rerank@chunks-structure~glm-4.7 | 66 | 0.727 | 0.849 | 0.849 | 0.833 | 0.782 | 0.787 | 0.939 | 4851 | 9429 |
| agent@chunks-structure~glm-4.7 | 66 | 0.667 | 0.727 | 0.818 | 0.803 | 0.713 | 0.727 | 0.849 | 3769 | 13161 |
| bilingual+rerank@chunks-fixed~glm-4.7 | 66 | 0.742 | 0.833 | 0.833 | 0.826 | 0.780 | 0.786 | 0.909 | 2723 | 3422 |
| bilingual+rerank@chunks-structure~glm-4.7 | 66 | 0.788 | 0.894 | 0.894 | 0.879 | 0.838 | 0.843 | 0.924 | 2514 | 2810 |
| bilingual@chunks-structure~glm-4.7 | 66 | 0.439 | 0.697 | 0.773 | 0.758 | 0.561 | 0.596 | 0.864 | 1301 | 1493 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 66 | 0.712 | 0.864 | 0.864 | 0.856 | 0.780 | 0.794 | 0.909 | 3363 | 5969 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 66 | 0.758 | 0.909 | 0.909 | 0.901 | 0.826 | 0.842 | 0.939 | 4023 | 6475 |
| bm25@chunks-fixed | 66 | 0.000 | 0.015 | 0.015 | 0.015 | 0.004 | 0.006 | 0.015 | 2 | 2 |
| bm25@chunks-structure | 66 | 0.000 | 0.000 | 0.015 | 0.015 | 0.002 | 0.004 | 0.015 | 2 | 2 |
| dense@chunks-fixed | 66 | 0.242 | 0.470 | 0.591 | 0.583 | 0.354 | 0.400 | 0.742 | 256 | 319 |
| dense@chunks-structure | 66 | 0.273 | 0.576 | 0.636 | 0.629 | 0.411 | 0.459 | 0.788 | 261 | 310 |
| hybrid+rerank@chunks-structure~glm-4.7 | 66 | 0.591 | 0.636 | 0.636 | 0.629 | 0.614 | 0.614 | 0.758 | 1419 | 1556 |
| hybrid@chunks-fixed | 66 | 0.197 | 0.348 | 0.439 | 0.432 | 0.271 | 0.296 | 0.636 | 265 | 314 |
| hybrid@chunks-structure | 66 | 0.106 | 0.394 | 0.530 | 0.515 | 0.230 | 0.290 | 0.621 | 280 | 337 |
| per_language@chunks-fixed | 66 | 0.212 | 0.439 | 0.485 | 0.477 | 0.281 | 0.318 | 0.636 | 270 | 338 |
| per_language@chunks-structure | 66 | 0.242 | 0.485 | 0.576 | 0.568 | 0.322 | 0.375 | 0.651 | 275 | 324 |

### lang=ko->en

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| agent+rerank@chunks-structure~glm-4.7 | 49 | 0.714 | 0.837 | 0.918 | 0.918 | 0.776 | 0.809 | 0.959 | 7584 | 12177 |
| agent@chunks-structure~glm-4.7 | 49 | 0.551 | 0.816 | 0.878 | 0.878 | 0.667 | 0.716 | 0.980 | 7802 | 18466 |
| bilingual+rerank@chunks-fixed~glm-4.7 | 49 | 0.694 | 0.796 | 0.837 | 0.837 | 0.747 | 0.769 | 0.980 | 2511 | 3346 |
| bilingual+rerank@chunks-structure~glm-4.7 | 49 | 0.755 | 0.878 | 0.878 | 0.878 | 0.802 | 0.821 | 0.980 | 2387 | 2633 |
| bilingual@chunks-structure~glm-4.7 | 49 | 0.408 | 0.694 | 0.796 | 0.796 | 0.543 | 0.598 | 1.000 | 1171 | 1334 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 49 | 0.714 | 0.816 | 0.816 | 0.816 | 0.763 | 0.776 | 1.000 | 3122 | 5621 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 49 | 0.755 | 0.878 | 0.898 | 0.898 | 0.811 | 0.832 | 1.000 | 4019 | 7196 |
| bm25@chunks-fixed | 49 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1 | 2 |
| bm25@chunks-structure | 49 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1 | 2 |
| dense@chunks-fixed | 49 | 0.327 | 0.551 | 0.653 | 0.653 | 0.417 | 0.471 | 0.898 | 263 | 325 |
| dense@chunks-structure | 49 | 0.327 | 0.551 | 0.592 | 0.592 | 0.427 | 0.463 | 0.898 | 252 | 297 |
| hybrid+rerank@chunks-structure~glm-4.7 | 49 | 0.551 | 0.592 | 0.592 | 0.592 | 0.571 | 0.577 | 0.878 | 1416 | 1557 |
| hybrid@chunks-fixed | 49 | 0.000 | 0.245 | 0.408 | 0.408 | 0.126 | 0.179 | 0.694 | 268 | 322 |
| hybrid@chunks-structure | 49 | 0.000 | 0.225 | 0.469 | 0.469 | 0.119 | 0.192 | 0.714 | 267 | 307 |
| per_language@chunks-fixed | 49 | 0.000 | 0.429 | 0.571 | 0.571 | 0.222 | 0.301 | 0.959 | 280 | 316 |
| per_language@chunks-structure | 49 | 0.000 | 0.449 | 0.531 | 0.531 | 0.213 | 0.283 | 0.918 | 281 | 328 |

### lang=ko->ko

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| agent+rerank@chunks-structure~glm-4.7 | 155 | 0.826 | 0.897 | 0.910 | 0.900 | 0.855 | 0.861 | 0.948 | 6258 | 14513 |
| agent@chunks-structure~glm-4.7 | 155 | 0.703 | 0.852 | 0.890 | 0.881 | 0.771 | 0.791 | 0.955 | 6742 | 21283 |
| bilingual+rerank@chunks-fixed~glm-4.7 | 155 | 0.852 | 0.923 | 0.923 | 0.913 | 0.884 | 0.887 | 0.961 | 2528 | 3292 |
| bilingual+rerank@chunks-structure~glm-4.7 | 155 | 0.852 | 0.903 | 0.903 | 0.897 | 0.876 | 0.880 | 0.974 | 2339 | 2558 |
| bilingual@chunks-structure~glm-4.7 | 155 | 0.452 | 0.716 | 0.845 | 0.836 | 0.571 | 0.629 | 0.935 | 1136 | 1316 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 155 | 0.884 | 0.948 | 0.948 | 0.942 | 0.910 | 0.915 | 0.981 | 3072 | 5178 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 155 | 0.884 | 0.935 | 0.942 | 0.942 | 0.909 | 0.918 | 0.981 | 3867 | 6700 |
| bm25@chunks-fixed | 155 | 0.548 | 0.800 | 0.865 | 0.858 | 0.654 | 0.699 | 0.955 | 1 | 2 |
| bm25@chunks-structure | 155 | 0.523 | 0.806 | 0.871 | 0.868 | 0.651 | 0.700 | 0.948 | 1 | 2 |
| dense@chunks-fixed | 155 | 0.406 | 0.736 | 0.800 | 0.781 | 0.549 | 0.592 | 0.968 | 249 | 308 |
| dense@chunks-structure | 155 | 0.497 | 0.787 | 0.858 | 0.852 | 0.619 | 0.671 | 0.968 | 255 | 331 |
| hybrid+rerank@chunks-structure~glm-4.7 | 155 | 0.877 | 0.935 | 0.942 | 0.942 | 0.906 | 0.915 | 0.981 | 1450 | 1628 |
| hybrid@chunks-fixed | 155 | 0.516 | 0.826 | 0.897 | 0.890 | 0.658 | 0.711 | 0.961 | 263 | 330 |
| hybrid@chunks-structure | 155 | 0.581 | 0.858 | 0.903 | 0.900 | 0.695 | 0.742 | 0.981 | 270 | 355 |
| per_language@chunks-fixed | 155 | 0.516 | 0.761 | 0.826 | 0.813 | 0.604 | 0.648 | 0.910 | 271 | 331 |
| per_language@chunks-structure | 155 | 0.581 | 0.774 | 0.858 | 0.848 | 0.650 | 0.691 | 0.935 | 278 | 378 |
