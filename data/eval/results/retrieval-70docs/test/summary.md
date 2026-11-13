
### all=all

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 338 | 0.840 | 0.935 | 0.947 | 0.945 | 0.884 | 0.898 | 0.976 | 3529 | 4717 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 338 | 0.820 | 0.920 | 0.920 | 0.916 | 0.862 | 0.873 | 0.976 | 3220 | 6037 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 338 | 0.834 | 0.920 | 0.926 | 0.923 | 0.874 | 0.885 | 0.973 | 2966 | 3729 |
| bilingual_union+rerank@chunks-structure~glm-4.7~labor-prompts | 338 | 0.825 | 0.929 | 0.938 | 0.936 | 0.872 | 0.888 | 0.979 | 3137 | 3883 |
| bm25@chunks-fixed | 338 | 0.364 | 0.530 | 0.571 | 0.568 | 0.433 | 0.463 | 0.636 | 2 | 2 |
| bm25@chunks-structure | 338 | 0.328 | 0.515 | 0.568 | 0.567 | 0.413 | 0.448 | 0.636 | 2 | 3 |
| dense@chunks-fixed | 338 | 0.402 | 0.680 | 0.763 | 0.753 | 0.528 | 0.573 | 0.920 | 229 | 252 |
| dense@chunks-structure | 338 | 0.459 | 0.734 | 0.787 | 0.782 | 0.581 | 0.625 | 0.926 | 244 | 282 |
| hybrid+rerank@chunks-structure~glm-4.7 | 338 | 0.766 | 0.837 | 0.840 | 0.839 | 0.798 | 0.807 | 0.926 | 1455 | 2006 |
| hybrid@chunks-fixed | 338 | 0.405 | 0.672 | 0.757 | 0.753 | 0.525 | 0.574 | 0.870 | 247 | 273 |
| hybrid@chunks-structure | 338 | 0.411 | 0.698 | 0.781 | 0.777 | 0.533 | 0.588 | 0.885 | 237 | 264 |

### file_type=docx

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 57 | 0.842 | 0.947 | 0.965 | 0.965 | 0.895 | 0.922 | 0.965 | 3592 | 5733 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 57 | 0.842 | 0.965 | 0.965 | 0.965 | 0.883 | 0.913 | 0.983 | 3235 | 5901 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 57 | 0.842 | 0.930 | 0.930 | 0.930 | 0.880 | 0.903 | 0.965 | 2950 | 3706 |
| bilingual_union+rerank@chunks-structure~glm-4.7~labor-prompts | 57 | 0.842 | 0.965 | 0.965 | 0.965 | 0.899 | 0.926 | 0.983 | 3069 | 3692 |
| bm25@chunks-fixed | 57 | 0.404 | 0.649 | 0.702 | 0.702 | 0.503 | 0.555 | 0.754 | 2 | 2 |
| bm25@chunks-structure | 57 | 0.351 | 0.649 | 0.667 | 0.667 | 0.480 | 0.530 | 0.719 | 2 | 3 |
| dense@chunks-fixed | 57 | 0.316 | 0.632 | 0.737 | 0.737 | 0.459 | 0.523 | 0.912 | 229 | 244 |
| dense@chunks-structure | 57 | 0.439 | 0.772 | 0.877 | 0.877 | 0.589 | 0.667 | 0.947 | 244 | 290 |
| hybrid+rerank@chunks-structure~glm-4.7 | 57 | 0.807 | 0.877 | 0.877 | 0.877 | 0.835 | 0.855 | 0.930 | 1454 | 2055 |
| hybrid@chunks-fixed | 57 | 0.386 | 0.719 | 0.807 | 0.807 | 0.538 | 0.606 | 0.895 | 243 | 270 |
| hybrid@chunks-structure | 57 | 0.474 | 0.789 | 0.825 | 0.825 | 0.599 | 0.661 | 0.930 | 238 | 256 |

### file_type=docx+hwpx

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 3 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.932 | 1.000 | 3336 | 3336 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 3 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.932 | 1.000 | 3311 | 3311 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 3 | 0.667 | 1.000 | 1.000 | 1.000 | 0.833 | 0.857 | 1.000 | 2804 | 2804 |
| bilingual_union+rerank@chunks-structure~glm-4.7~labor-prompts | 3 | 0.667 | 1.000 | 1.000 | 1.000 | 0.833 | 0.857 | 1.000 | 3064 | 3064 |
| bm25@chunks-fixed | 3 | 0.667 | 0.667 | 0.667 | 0.667 | 0.667 | 0.602 | 0.667 | 2 | 2 |
| bm25@chunks-structure | 3 | 0.667 | 0.667 | 0.667 | 0.667 | 0.667 | 0.602 | 0.667 | 2 | 2 |
| dense@chunks-fixed | 3 | 0.667 | 1.000 | 1.000 | 0.667 | 0.833 | 0.640 | 1.000 | 225 | 225 |
| dense@chunks-structure | 3 | 0.333 | 0.667 | 1.000 | 1.000 | 0.492 | 0.633 | 1.000 | 247 | 247 |
| hybrid+rerank@chunks-structure~glm-4.7 | 3 | 0.667 | 1.000 | 1.000 | 1.000 | 0.833 | 0.857 | 1.000 | 1429 | 1429 |
| hybrid@chunks-fixed | 3 | 0.333 | 1.000 | 1.000 | 1.000 | 0.556 | 0.655 | 1.000 | 245 | 245 |
| hybrid@chunks-structure | 3 | 0.333 | 0.667 | 1.000 | 0.833 | 0.486 | 0.565 | 1.000 | 237 | 237 |

### file_type=docx+pdf

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 4 | 1.000 | 1.000 | 1.000 | 0.875 | 1.000 | 0.866 | 1.000 | 3320 | 3458 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 4 | 1.000 | 1.000 | 1.000 | 0.750 | 1.000 | 0.732 | 1.000 | 3044 | 3119 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 4 | 1.000 | 1.000 | 1.000 | 0.875 | 1.000 | 0.873 | 1.000 | 3092 | 3108 |
| bilingual_union+rerank@chunks-structure~glm-4.7~labor-prompts | 4 | 1.000 | 1.000 | 1.000 | 0.875 | 1.000 | 0.873 | 1.000 | 3270 | 3430 |
| bm25@chunks-fixed | 4 | 0.500 | 0.750 | 0.750 | 0.500 | 0.625 | 0.480 | 0.750 | 2 | 2 |
| bm25@chunks-structure | 4 | 0.750 | 0.750 | 0.750 | 0.625 | 0.750 | 0.623 | 0.750 | 2 | 2 |
| dense@chunks-fixed | 4 | 0.750 | 1.000 | 1.000 | 0.625 | 0.875 | 0.616 | 1.000 | 229 | 235 |
| dense@chunks-structure | 4 | 0.500 | 1.000 | 1.000 | 0.750 | 0.688 | 0.594 | 1.000 | 242 | 243 |
| hybrid+rerank@chunks-structure~glm-4.7 | 4 | 1.000 | 1.000 | 1.000 | 0.875 | 1.000 | 0.866 | 1.000 | 1502 | 1514 |
| hybrid@chunks-fixed | 4 | 0.500 | 1.000 | 1.000 | 0.750 | 0.750 | 0.621 | 1.000 | 254 | 258 |
| hybrid@chunks-structure | 4 | 0.500 | 1.000 | 1.000 | 0.750 | 0.667 | 0.623 | 1.000 | 242 | 243 |

### file_type=hwpx

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 58 | 0.862 | 0.914 | 0.914 | 0.914 | 0.888 | 0.895 | 0.983 | 3514 | 4237 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 58 | 0.810 | 0.914 | 0.914 | 0.914 | 0.858 | 0.872 | 0.983 | 3153 | 5965 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 58 | 0.828 | 0.914 | 0.914 | 0.914 | 0.871 | 0.882 | 0.983 | 3005 | 3511 |
| bilingual_union+rerank@chunks-structure~glm-4.7~labor-prompts | 58 | 0.828 | 0.914 | 0.914 | 0.914 | 0.868 | 0.880 | 0.983 | 3110 | 3694 |
| bm25@chunks-fixed | 58 | 0.397 | 0.466 | 0.517 | 0.517 | 0.423 | 0.443 | 0.638 | 2 | 2 |
| bm25@chunks-structure | 58 | 0.293 | 0.483 | 0.534 | 0.534 | 0.378 | 0.415 | 0.638 | 2 | 3 |
| dense@chunks-fixed | 58 | 0.345 | 0.707 | 0.776 | 0.776 | 0.499 | 0.563 | 0.966 | 232 | 250 |
| dense@chunks-structure | 58 | 0.431 | 0.741 | 0.759 | 0.759 | 0.555 | 0.601 | 0.914 | 242 | 272 |
| hybrid+rerank@chunks-structure~glm-4.7 | 58 | 0.810 | 0.879 | 0.879 | 0.879 | 0.842 | 0.852 | 0.966 | 1454 | 2006 |
| hybrid@chunks-fixed | 58 | 0.448 | 0.672 | 0.793 | 0.793 | 0.557 | 0.609 | 0.966 | 246 | 264 |
| hybrid@chunks-structure | 58 | 0.448 | 0.690 | 0.776 | 0.776 | 0.550 | 0.598 | 0.914 | 238 | 264 |

### file_type=hwpx+pdf

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 2 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.855 | 1.000 | 3553 | 3427 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 2 | 1.000 | 1.000 | 1.000 | 0.750 | 1.000 | 0.807 | 1.000 | 2832 | 2765 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 2 | 1.000 | 1.000 | 1.000 | 0.750 | 1.000 | 0.766 | 1.000 | 2921 | 2708 |
| bilingual_union+rerank@chunks-structure~glm-4.7~labor-prompts | 2 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.876 | 1.000 | 2815 | 2655 |
| bm25@chunks-fixed | 2 | 0.000 | 1.000 | 1.000 | 1.000 | 0.417 | 0.567 | 1.000 | 2 | 1 |
| bm25@chunks-structure | 2 | 0.000 | 1.000 | 1.000 | 1.000 | 0.417 | 0.568 | 1.000 | 2 | 2 |
| dense@chunks-fixed | 2 | 0.500 | 1.000 | 1.000 | 0.500 | 0.750 | 0.387 | 1.000 | 224 | 224 |
| dense@chunks-structure | 2 | 1.000 | 1.000 | 1.000 | 0.750 | 1.000 | 0.653 | 1.000 | 251 | 241 |
| hybrid+rerank@chunks-structure~glm-4.7 | 2 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.855 | 1.000 | 1405 | 1382 |
| hybrid@chunks-fixed | 2 | 0.000 | 1.000 | 1.000 | 0.750 | 0.500 | 0.489 | 1.000 | 239 | 236 |
| hybrid@chunks-structure | 2 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.782 | 1.000 | 249 | 237 |

### file_type=pdf

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 160 | 0.844 | 0.956 | 0.975 | 0.975 | 0.896 | 0.915 | 1.000 | 3526 | 4735 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 160 | 0.806 | 0.919 | 0.919 | 0.919 | 0.855 | 0.871 | 0.988 | 3273 | 6092 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 160 | 0.863 | 0.950 | 0.956 | 0.956 | 0.901 | 0.914 | 0.994 | 2969 | 3743 |
| bilingual_union+rerank@chunks-structure~glm-4.7~labor-prompts | 160 | 0.831 | 0.938 | 0.950 | 0.950 | 0.877 | 0.895 | 0.988 | 3221 | 3955 |
| bm25@chunks-fixed | 160 | 0.362 | 0.500 | 0.544 | 0.544 | 0.424 | 0.451 | 0.600 | 2 | 2 |
| bm25@chunks-structure | 160 | 0.338 | 0.469 | 0.537 | 0.537 | 0.403 | 0.433 | 0.606 | 2 | 3 |
| dense@chunks-fixed | 160 | 0.456 | 0.669 | 0.769 | 0.769 | 0.559 | 0.607 | 0.931 | 230 | 257 |
| dense@chunks-structure | 160 | 0.519 | 0.738 | 0.762 | 0.762 | 0.616 | 0.648 | 0.931 | 244 | 280 |
| hybrid+rerank@chunks-structure~glm-4.7 | 160 | 0.750 | 0.825 | 0.825 | 0.825 | 0.782 | 0.793 | 0.925 | 1484 | 2024 |
| hybrid@chunks-fixed | 160 | 0.419 | 0.675 | 0.744 | 0.744 | 0.527 | 0.574 | 0.863 | 247 | 276 |
| hybrid@chunks-structure | 160 | 0.412 | 0.694 | 0.775 | 0.775 | 0.535 | 0.590 | 0.881 | 237 | 266 |

### file_type=scan

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 54 | 0.778 | 0.870 | 0.870 | 0.870 | 0.813 | 0.827 | 0.907 | 3573 | 4542 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 54 | 0.815 | 0.870 | 0.870 | 0.870 | 0.841 | 0.847 | 0.926 | 3210 | 5037 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 54 | 0.741 | 0.815 | 0.833 | 0.833 | 0.778 | 0.791 | 0.907 | 2965 | 3690 |
| bilingual_union+rerank@chunks-structure~glm-4.7~labor-prompts | 54 | 0.778 | 0.870 | 0.889 | 0.889 | 0.820 | 0.837 | 0.944 | 2984 | 3823 |
| bm25@chunks-fixed | 54 | 0.278 | 0.518 | 0.537 | 0.537 | 0.370 | 0.409 | 0.593 | 2 | 2 |
| bm25@chunks-structure | 54 | 0.278 | 0.500 | 0.556 | 0.556 | 0.372 | 0.415 | 0.611 | 2 | 3 |
| dense@chunks-fixed | 54 | 0.352 | 0.685 | 0.722 | 0.722 | 0.488 | 0.539 | 0.833 | 228 | 246 |
| dense@chunks-structure | 54 | 0.315 | 0.648 | 0.759 | 0.759 | 0.474 | 0.540 | 0.889 | 244 | 288 |
| hybrid+rerank@chunks-structure~glm-4.7 | 54 | 0.704 | 0.759 | 0.778 | 0.778 | 0.732 | 0.742 | 0.870 | 1426 | 1934 |
| hybrid@chunks-fixed | 54 | 0.352 | 0.556 | 0.667 | 0.667 | 0.453 | 0.497 | 0.741 | 247 | 270 |
| hybrid@chunks-structure | 54 | 0.278 | 0.593 | 0.722 | 0.722 | 0.415 | 0.484 | 0.796 | 234 | 262 |

### kind=fact

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 293 | 0.833 | 0.932 | 0.945 | 0.945 | 0.879 | 0.898 | 0.976 | 3521 | 4586 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 293 | 0.829 | 0.932 | 0.932 | 0.932 | 0.872 | 0.888 | 0.983 | 3224 | 5901 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 293 | 0.833 | 0.925 | 0.928 | 0.928 | 0.874 | 0.890 | 0.973 | 2964 | 3686 |
| bilingual_union+rerank@chunks-structure~glm-4.7~labor-prompts | 293 | 0.823 | 0.932 | 0.939 | 0.939 | 0.871 | 0.890 | 0.980 | 3121 | 3900 |
| bm25@chunks-fixed | 293 | 0.365 | 0.529 | 0.567 | 0.567 | 0.433 | 0.465 | 0.621 | 2 | 2 |
| bm25@chunks-structure | 293 | 0.317 | 0.512 | 0.560 | 0.560 | 0.404 | 0.441 | 0.621 | 2 | 3 |
| dense@chunks-fixed | 293 | 0.423 | 0.710 | 0.795 | 0.795 | 0.550 | 0.608 | 0.928 | 230 | 255 |
| dense@chunks-structure | 293 | 0.488 | 0.754 | 0.792 | 0.792 | 0.607 | 0.651 | 0.932 | 244 | 280 |
| hybrid+rerank@chunks-structure~glm-4.7 | 293 | 0.761 | 0.836 | 0.836 | 0.836 | 0.794 | 0.807 | 0.928 | 1443 | 2003 |
| hybrid@chunks-fixed | 293 | 0.430 | 0.689 | 0.768 | 0.768 | 0.545 | 0.595 | 0.867 | 247 | 273 |
| hybrid@chunks-structure | 293 | 0.420 | 0.707 | 0.778 | 0.778 | 0.541 | 0.597 | 0.884 | 237 | 264 |

### kind=multi

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 9 | 1.000 | 1.000 | 1.000 | 0.944 | 1.000 | 0.886 | 1.000 | 3427 | 3678 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 9 | 1.000 | 1.000 | 1.000 | 0.833 | 1.000 | 0.815 | 1.000 | 2969 | 4469 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 9 | 0.889 | 1.000 | 1.000 | 0.889 | 0.944 | 0.844 | 1.000 | 2990 | 3133 |
| bilingual_union+rerank@chunks-structure~glm-4.7~labor-prompts | 9 | 0.889 | 1.000 | 1.000 | 0.944 | 0.944 | 0.868 | 1.000 | 3064 | 3551 |
| bm25@chunks-fixed | 9 | 0.444 | 0.778 | 0.778 | 0.667 | 0.593 | 0.540 | 0.778 | 2 | 2 |
| bm25@chunks-structure | 9 | 0.556 | 0.778 | 0.778 | 0.722 | 0.648 | 0.604 | 0.778 | 2 | 2 |
| dense@chunks-fixed | 9 | 0.667 | 1.000 | 1.000 | 0.611 | 0.833 | 0.573 | 1.000 | 225 | 240 |
| dense@chunks-structure | 9 | 0.556 | 0.889 | 1.000 | 0.833 | 0.692 | 0.620 | 1.000 | 243 | 261 |
| hybrid+rerank@chunks-structure~glm-4.7 | 9 | 0.889 | 1.000 | 1.000 | 0.944 | 0.944 | 0.861 | 1.000 | 1429 | 1514 |
| hybrid@chunks-fixed | 9 | 0.333 | 1.000 | 1.000 | 0.833 | 0.630 | 0.603 | 1.000 | 245 | 258 |
| hybrid@chunks-structure | 9 | 0.556 | 0.889 | 1.000 | 0.833 | 0.681 | 0.639 | 1.000 | 242 | 261 |

### kind=table

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 36 | 0.861 | 0.944 | 0.944 | 0.944 | 0.890 | 0.903 | 0.972 | 3659 | 5451 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 36 | 0.694 | 0.806 | 0.806 | 0.806 | 0.748 | 0.761 | 0.917 | 3214 | 6412 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 36 | 0.833 | 0.861 | 0.889 | 0.889 | 0.851 | 0.860 | 0.972 | 3032 | 3775 |
| bilingual_union+rerank@chunks-structure~glm-4.7~labor-prompts | 36 | 0.833 | 0.889 | 0.917 | 0.917 | 0.860 | 0.874 | 0.972 | 3213 | 3672 |
| bm25@chunks-fixed | 36 | 0.333 | 0.472 | 0.556 | 0.556 | 0.393 | 0.429 | 0.722 | 2 | 2 |
| bm25@chunks-structure | 36 | 0.361 | 0.472 | 0.583 | 0.583 | 0.429 | 0.462 | 0.722 | 2 | 3 |
| dense@chunks-fixed | 36 | 0.167 | 0.361 | 0.444 | 0.444 | 0.265 | 0.294 | 0.833 | 227 | 248 |
| dense@chunks-structure | 36 | 0.194 | 0.528 | 0.694 | 0.694 | 0.337 | 0.417 | 0.861 | 242 | 283 |
| hybrid+rerank@chunks-structure~glm-4.7 | 36 | 0.778 | 0.806 | 0.833 | 0.833 | 0.790 | 0.800 | 0.889 | 1550 | 2132 |
| hybrid@chunks-fixed | 36 | 0.222 | 0.444 | 0.611 | 0.611 | 0.339 | 0.397 | 0.861 | 244 | 270 |
| hybrid@chunks-structure | 36 | 0.306 | 0.583 | 0.750 | 0.750 | 0.431 | 0.501 | 0.861 | 237 | 267 |

### lang=en->en

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 68 | 0.853 | 0.971 | 1.000 | 1.000 | 0.909 | 0.932 | 1.000 | 3604 | 4670 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 68 | 0.868 | 0.985 | 0.985 | 0.985 | 0.909 | 0.928 | 1.000 | 3383 | 6100 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 68 | 0.838 | 0.971 | 0.985 | 0.985 | 0.895 | 0.917 | 1.000 | 3178 | 3874 |
| bilingual_union+rerank@chunks-structure~glm-4.7~labor-prompts | 68 | 0.838 | 0.971 | 0.985 | 0.985 | 0.894 | 0.917 | 1.000 | 3264 | 3993 |
| bm25@chunks-fixed | 68 | 0.574 | 0.794 | 0.868 | 0.868 | 0.669 | 0.715 | 0.971 | 2 | 2 |
| bm25@chunks-structure | 68 | 0.500 | 0.721 | 0.838 | 0.838 | 0.605 | 0.656 | 0.985 | 2 | 3 |
| dense@chunks-fixed | 68 | 0.632 | 0.853 | 0.926 | 0.926 | 0.745 | 0.787 | 1.000 | 229 | 251 |
| dense@chunks-structure | 68 | 0.662 | 0.912 | 0.941 | 0.941 | 0.780 | 0.818 | 1.000 | 245 | 280 |
| hybrid+rerank@chunks-structure~glm-4.7 | 68 | 0.838 | 0.985 | 0.985 | 0.985 | 0.897 | 0.920 | 1.000 | 1566 | 1977 |
| hybrid@chunks-fixed | 68 | 0.647 | 0.956 | 0.985 | 0.985 | 0.761 | 0.816 | 1.000 | 245 | 261 |
| hybrid@chunks-structure | 68 | 0.632 | 0.941 | 0.971 | 0.971 | 0.768 | 0.818 | 1.000 | 238 | 263 |

### lang=en->ko

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 66 | 0.758 | 0.879 | 0.879 | 0.871 | 0.812 | 0.821 | 0.894 | 3693 | 4510 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 66 | 0.742 | 0.864 | 0.864 | 0.856 | 0.798 | 0.807 | 0.924 | 3225 | 5901 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 66 | 0.742 | 0.833 | 0.833 | 0.826 | 0.782 | 0.789 | 0.894 | 3075 | 3690 |
| bilingual_union+rerank@chunks-structure~glm-4.7~labor-prompts | 66 | 0.773 | 0.909 | 0.909 | 0.901 | 0.836 | 0.849 | 0.939 | 3213 | 3951 |
| bm25@chunks-fixed | 66 | 0.000 | 0.015 | 0.015 | 0.015 | 0.004 | 0.006 | 0.015 | 2 | 2 |
| bm25@chunks-structure | 66 | 0.000 | 0.000 | 0.015 | 0.015 | 0.002 | 0.005 | 0.015 | 2 | 3 |
| dense@chunks-fixed | 66 | 0.227 | 0.470 | 0.591 | 0.583 | 0.346 | 0.395 | 0.742 | 227 | 257 |
| dense@chunks-structure | 66 | 0.258 | 0.576 | 0.636 | 0.629 | 0.404 | 0.454 | 0.788 | 242 | 271 |
| hybrid+rerank@chunks-structure~glm-4.7 | 66 | 0.591 | 0.636 | 0.636 | 0.629 | 0.614 | 0.614 | 0.773 | 1433 | 1907 |
| hybrid@chunks-fixed | 66 | 0.167 | 0.348 | 0.455 | 0.447 | 0.253 | 0.287 | 0.636 | 250 | 270 |
| hybrid@chunks-structure | 66 | 0.106 | 0.409 | 0.530 | 0.515 | 0.231 | 0.291 | 0.636 | 237 | 264 |

### lang=ko->en

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 49 | 0.755 | 0.918 | 0.939 | 0.939 | 0.828 | 0.855 | 1.000 | 3465 | 4542 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 49 | 0.694 | 0.816 | 0.816 | 0.816 | 0.757 | 0.771 | 1.000 | 3190 | 5839 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 49 | 0.816 | 0.898 | 0.898 | 0.898 | 0.854 | 0.864 | 1.000 | 2861 | 3372 |
| bilingual_union+rerank@chunks-structure~glm-4.7~labor-prompts | 49 | 0.694 | 0.857 | 0.878 | 0.878 | 0.766 | 0.792 | 0.980 | 2982 | 3748 |
| bm25@chunks-fixed | 49 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 2 | 2 |
| bm25@chunks-structure | 49 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 2 | 3 |
| dense@chunks-fixed | 49 | 0.327 | 0.551 | 0.653 | 0.653 | 0.417 | 0.471 | 0.898 | 229 | 258 |
| dense@chunks-structure | 49 | 0.327 | 0.551 | 0.592 | 0.592 | 0.428 | 0.463 | 0.878 | 245 | 270 |
| hybrid+rerank@chunks-structure~glm-4.7 | 49 | 0.531 | 0.571 | 0.571 | 0.571 | 0.552 | 0.556 | 0.837 | 1418 | 1914 |
| hybrid@chunks-fixed | 49 | 0.000 | 0.245 | 0.408 | 0.408 | 0.126 | 0.179 | 0.694 | 246 | 278 |
| hybrid@chunks-structure | 49 | 0.000 | 0.265 | 0.469 | 0.469 | 0.123 | 0.196 | 0.714 | 236 | 261 |

### lang=ko->ko

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 155 | 0.897 | 0.948 | 0.955 | 0.955 | 0.921 | 0.929 | 0.994 | 3467 | 4467 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 155 | 0.871 | 0.948 | 0.948 | 0.942 | 0.902 | 0.909 | 0.981 | 3095 | 5866 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 155 | 0.877 | 0.942 | 0.948 | 0.945 | 0.909 | 0.919 | 0.987 | 2871 | 3562 |
| bilingual_union+rerank@chunks-structure~glm-4.7~labor-prompts | 155 | 0.884 | 0.942 | 0.948 | 0.948 | 0.911 | 0.921 | 0.987 | 3001 | 3620 |
| bm25@chunks-fixed | 155 | 0.542 | 0.800 | 0.858 | 0.852 | 0.650 | 0.693 | 0.955 | 2 | 2 |
| bm25@chunks-structure | 155 | 0.497 | 0.806 | 0.865 | 0.861 | 0.635 | 0.687 | 0.948 | 2 | 3 |
| dense@chunks-fixed | 155 | 0.400 | 0.736 | 0.800 | 0.781 | 0.544 | 0.588 | 0.968 | 230 | 249 |
| dense@chunks-structure | 155 | 0.497 | 0.781 | 0.845 | 0.839 | 0.617 | 0.665 | 0.968 | 244 | 288 |
| hybrid+rerank@chunks-structure~glm-4.7 | 155 | 0.884 | 0.942 | 0.948 | 0.948 | 0.910 | 0.920 | 0.987 | 1467 | 2024 |
| hybrid@chunks-fixed | 155 | 0.529 | 0.819 | 0.897 | 0.890 | 0.664 | 0.715 | 0.968 | 246 | 274 |
| hybrid@chunks-structure | 155 | 0.574 | 0.852 | 0.903 | 0.900 | 0.689 | 0.737 | 0.994 | 237 | 264 |
