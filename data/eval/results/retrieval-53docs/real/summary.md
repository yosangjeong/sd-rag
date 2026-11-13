
### all=all

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| agent+rerank@chunks-structure~glm-4.7 | 137 | 0.810 | 0.964 | 0.964 | 0.964 | 0.875 | 0.897 | 0.985 | 7128 | 13756 |
| agent@chunks-structure~glm-4.7 | 137 | 0.635 | 0.869 | 0.927 | 0.927 | 0.743 | 0.786 | 0.949 | 8607 | 21998 |
| bilingual+rerank@chunks-fixed~glm-4.7 | 137 | 0.737 | 0.869 | 0.876 | 0.876 | 0.797 | 0.817 | 0.978 | 2771 | 3469 |
| bilingual+rerank@chunks-structure~glm-4.7 | 137 | 0.737 | 0.861 | 0.876 | 0.876 | 0.798 | 0.817 | 0.964 | 2721 | 3419 |
| bilingual@chunks-structure~glm-4.7 | 137 | 0.343 | 0.613 | 0.781 | 0.781 | 0.469 | 0.536 | 0.934 | 1294 | 1833 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 137 | 0.810 | 0.934 | 0.942 | 0.942 | 0.864 | 0.883 | 0.985 | 4376 | 7895 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 137 | 0.832 | 0.942 | 0.949 | 0.949 | 0.877 | 0.895 | 0.985 | 3624 | 4594 |
| bm25@chunks-fixed | 137 | 0.321 | 0.642 | 0.730 | 0.730 | 0.472 | 0.528 | 0.942 | 1 | 2 |
| bm25@chunks-structure | 137 | 0.343 | 0.664 | 0.774 | 0.774 | 0.485 | 0.550 | 0.934 | 1 | 2 |
| dense@chunks-fixed | 137 | 0.358 | 0.657 | 0.839 | 0.839 | 0.502 | 0.580 | 0.978 | 251 | 324 |
| dense@chunks-structure | 137 | 0.474 | 0.715 | 0.832 | 0.832 | 0.589 | 0.643 | 0.971 | 243 | 324 |
| hybrid+rerank@chunks-structure~glm-4.7 | 137 | 0.847 | 0.942 | 0.949 | 0.949 | 0.888 | 0.903 | 0.985 | 1748 | 2467 |
| hybrid@chunks-fixed | 137 | 0.380 | 0.745 | 0.861 | 0.861 | 0.531 | 0.606 | 0.985 | 261 | 343 |
| hybrid@chunks-structure | 137 | 0.460 | 0.752 | 0.876 | 0.876 | 0.592 | 0.655 | 0.971 | 261 | 355 |
| per_language@chunks-fixed | 137 | 0.204 | 0.577 | 0.752 | 0.752 | 0.375 | 0.459 | 0.942 | 261 | 336 |
| per_language@chunks-structure | 137 | 0.226 | 0.642 | 0.752 | 0.752 | 0.417 | 0.492 | 0.942 | 259 | 325 |

### file_type=docx

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| agent+rerank@chunks-structure~glm-4.7 | 22 | 0.727 | 0.864 | 0.864 | 0.864 | 0.788 | 0.807 | 0.955 | 11001 | 15062 |
| agent@chunks-structure~glm-4.7 | 22 | 0.545 | 0.727 | 0.818 | 0.818 | 0.643 | 0.683 | 0.909 | 9497 | 17318 |
| bilingual+rerank@chunks-fixed~glm-4.7 | 22 | 0.727 | 0.818 | 0.818 | 0.818 | 0.761 | 0.775 | 1.000 | 2759 | 3171 |
| bilingual+rerank@chunks-structure~glm-4.7 | 22 | 0.727 | 0.818 | 0.818 | 0.818 | 0.773 | 0.785 | 0.909 | 2650 | 3102 |
| bilingual@chunks-structure~glm-4.7 | 22 | 0.364 | 0.636 | 0.727 | 0.727 | 0.475 | 0.531 | 0.864 | 1425 | 1600 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 22 | 0.773 | 0.864 | 0.864 | 0.864 | 0.807 | 0.821 | 1.000 | 3612 | 4376 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 22 | 0.818 | 0.909 | 0.909 | 0.909 | 0.856 | 0.870 | 0.955 | 3313 | 4292 |
| bm25@chunks-fixed | 22 | 0.136 | 0.545 | 0.636 | 0.636 | 0.318 | 0.388 | 0.909 | 1 | 2 |
| bm25@chunks-structure | 22 | 0.091 | 0.636 | 0.727 | 0.727 | 0.305 | 0.401 | 0.864 | 1 | 2 |
| dense@chunks-fixed | 22 | 0.227 | 0.591 | 0.727 | 0.727 | 0.394 | 0.473 | 0.955 | 248 | 299 |
| dense@chunks-structure | 22 | 0.409 | 0.727 | 0.818 | 0.818 | 0.542 | 0.604 | 0.955 | 245 | 275 |
| hybrid+rerank@chunks-structure~glm-4.7 | 22 | 0.818 | 0.909 | 0.909 | 0.909 | 0.864 | 0.875 | 0.955 | 1835 | 3032 |
| hybrid@chunks-fixed | 22 | 0.318 | 0.727 | 0.818 | 0.818 | 0.493 | 0.570 | 1.000 | 260 | 305 |
| hybrid@chunks-structure | 22 | 0.409 | 0.727 | 0.818 | 0.818 | 0.580 | 0.632 | 0.955 | 270 | 355 |
| per_language@chunks-fixed | 22 | 0.318 | 0.636 | 0.727 | 0.727 | 0.426 | 0.492 | 0.909 | 244 | 328 |
| per_language@chunks-structure | 22 | 0.409 | 0.727 | 0.727 | 0.727 | 0.515 | 0.563 | 0.864 | 261 | 287 |

### file_type=hwpx

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| agent+rerank@chunks-structure~glm-4.7 | 17 | 0.824 | 0.941 | 0.941 | 0.941 | 0.873 | 0.890 | 1.000 | 9298 | 14919 |
| agent@chunks-structure~glm-4.7 | 17 | 0.647 | 0.765 | 0.882 | 0.882 | 0.716 | 0.752 | 0.882 | 11123 | 22112 |
| bilingual+rerank@chunks-fixed~glm-4.7 | 17 | 0.765 | 1.000 | 1.000 | 1.000 | 0.873 | 0.905 | 1.000 | 2675 | 3136 |
| bilingual+rerank@chunks-structure~glm-4.7 | 17 | 0.824 | 0.941 | 0.941 | 0.941 | 0.882 | 0.898 | 1.000 | 2503 | 2664 |
| bilingual@chunks-structure~glm-4.7 | 17 | 0.353 | 0.647 | 0.824 | 0.824 | 0.499 | 0.570 | 1.000 | 1382 | 1846 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 17 | 0.765 | 1.000 | 1.000 | 1.000 | 0.882 | 0.913 | 1.000 | 3428 | 4226 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 17 | 0.941 | 0.941 | 0.941 | 0.941 | 0.941 | 0.941 | 1.000 | 3702 | 4235 |
| bm25@chunks-fixed | 17 | 0.471 | 0.765 | 0.765 | 0.765 | 0.603 | 0.641 | 0.941 | 2 | 2 |
| bm25@chunks-structure | 17 | 0.471 | 0.765 | 0.824 | 0.824 | 0.605 | 0.655 | 0.941 | 1 | 1 |
| dense@chunks-fixed | 17 | 0.412 | 0.824 | 0.882 | 0.882 | 0.575 | 0.647 | 1.000 | 238 | 307 |
| dense@chunks-structure | 17 | 0.294 | 0.647 | 0.824 | 0.824 | 0.455 | 0.537 | 1.000 | 244 | 283 |
| hybrid+rerank@chunks-structure~glm-4.7 | 17 | 0.941 | 0.941 | 0.941 | 0.941 | 0.941 | 0.941 | 1.000 | 1826 | 2460 |
| hybrid@chunks-fixed | 17 | 0.471 | 0.765 | 0.941 | 0.941 | 0.614 | 0.691 | 1.000 | 261 | 295 |
| hybrid@chunks-structure | 17 | 0.412 | 0.765 | 0.941 | 0.941 | 0.575 | 0.661 | 1.000 | 257 | 335 |
| per_language@chunks-fixed | 17 | 0.471 | 0.706 | 0.765 | 0.765 | 0.560 | 0.601 | 0.882 | 254 | 290 |
| per_language@chunks-structure | 17 | 0.412 | 0.647 | 0.765 | 0.765 | 0.516 | 0.567 | 0.941 | 257 | 300 |

### file_type=pdf

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| agent+rerank@chunks-structure~glm-4.7 | 98 | 0.827 | 0.990 | 0.990 | 0.990 | 0.895 | 0.919 | 0.990 | 6096 | 11441 |
| agent@chunks-structure~glm-4.7 | 98 | 0.653 | 0.918 | 0.959 | 0.959 | 0.770 | 0.816 | 0.969 | 8016 | 21001 |
| bilingual+rerank@chunks-fixed~glm-4.7 | 98 | 0.735 | 0.857 | 0.867 | 0.867 | 0.792 | 0.811 | 0.969 | 2805 | 3593 |
| bilingual+rerank@chunks-structure~glm-4.7 | 98 | 0.725 | 0.857 | 0.878 | 0.878 | 0.789 | 0.811 | 0.969 | 2843 | 3561 |
| bilingual@chunks-structure~glm-4.7 | 98 | 0.337 | 0.602 | 0.786 | 0.786 | 0.462 | 0.531 | 0.939 | 1276 | 1813 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 98 | 0.827 | 0.939 | 0.949 | 0.949 | 0.874 | 0.892 | 0.980 | 5355 | 8185 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 98 | 0.816 | 0.949 | 0.959 | 0.959 | 0.871 | 0.892 | 0.990 | 3645 | 4773 |
| bm25@chunks-fixed | 98 | 0.337 | 0.643 | 0.745 | 0.745 | 0.484 | 0.540 | 0.949 | 1 | 2 |
| bm25@chunks-structure | 98 | 0.378 | 0.653 | 0.775 | 0.775 | 0.505 | 0.565 | 0.949 | 1 | 1 |
| dense@chunks-fixed | 98 | 0.378 | 0.643 | 0.857 | 0.857 | 0.514 | 0.593 | 0.980 | 258 | 328 |
| dense@chunks-structure | 98 | 0.520 | 0.725 | 0.837 | 0.837 | 0.623 | 0.670 | 0.969 | 242 | 332 |
| hybrid+rerank@chunks-structure~glm-4.7 | 98 | 0.837 | 0.949 | 0.959 | 0.959 | 0.885 | 0.903 | 0.990 | 1732 | 2265 |
| hybrid@chunks-fixed | 98 | 0.378 | 0.745 | 0.857 | 0.857 | 0.526 | 0.600 | 0.980 | 261 | 345 |
| hybrid@chunks-structure | 98 | 0.480 | 0.755 | 0.878 | 0.878 | 0.598 | 0.659 | 0.969 | 261 | 345 |
| per_language@chunks-fixed | 98 | 0.133 | 0.541 | 0.755 | 0.755 | 0.332 | 0.427 | 0.959 | 265 | 346 |
| per_language@chunks-structure | 98 | 0.153 | 0.622 | 0.755 | 0.755 | 0.378 | 0.463 | 0.959 | 260 | 328 |

### kind=real

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| agent+rerank@chunks-structure~glm-4.7 | 137 | 0.810 | 0.964 | 0.964 | 0.964 | 0.875 | 0.897 | 0.985 | 7128 | 13756 |
| agent@chunks-structure~glm-4.7 | 137 | 0.635 | 0.869 | 0.927 | 0.927 | 0.743 | 0.786 | 0.949 | 8607 | 21998 |
| bilingual+rerank@chunks-fixed~glm-4.7 | 137 | 0.737 | 0.869 | 0.876 | 0.876 | 0.797 | 0.817 | 0.978 | 2771 | 3469 |
| bilingual+rerank@chunks-structure~glm-4.7 | 137 | 0.737 | 0.861 | 0.876 | 0.876 | 0.798 | 0.817 | 0.964 | 2721 | 3419 |
| bilingual@chunks-structure~glm-4.7 | 137 | 0.343 | 0.613 | 0.781 | 0.781 | 0.469 | 0.536 | 0.934 | 1294 | 1833 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 137 | 0.810 | 0.934 | 0.942 | 0.942 | 0.864 | 0.883 | 0.985 | 4376 | 7895 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 137 | 0.832 | 0.942 | 0.949 | 0.949 | 0.877 | 0.895 | 0.985 | 3624 | 4594 |
| bm25@chunks-fixed | 137 | 0.321 | 0.642 | 0.730 | 0.730 | 0.472 | 0.528 | 0.942 | 1 | 2 |
| bm25@chunks-structure | 137 | 0.343 | 0.664 | 0.774 | 0.774 | 0.485 | 0.550 | 0.934 | 1 | 2 |
| dense@chunks-fixed | 137 | 0.358 | 0.657 | 0.839 | 0.839 | 0.502 | 0.580 | 0.978 | 251 | 324 |
| dense@chunks-structure | 137 | 0.474 | 0.715 | 0.832 | 0.832 | 0.589 | 0.643 | 0.971 | 243 | 324 |
| hybrid+rerank@chunks-structure~glm-4.7 | 137 | 0.847 | 0.942 | 0.949 | 0.949 | 0.888 | 0.903 | 0.985 | 1748 | 2467 |
| hybrid@chunks-fixed | 137 | 0.380 | 0.745 | 0.861 | 0.861 | 0.531 | 0.606 | 0.985 | 261 | 343 |
| hybrid@chunks-structure | 137 | 0.460 | 0.752 | 0.876 | 0.876 | 0.592 | 0.655 | 0.971 | 261 | 355 |
| per_language@chunks-fixed | 137 | 0.204 | 0.577 | 0.752 | 0.752 | 0.375 | 0.459 | 0.942 | 261 | 336 |
| per_language@chunks-structure | 137 | 0.226 | 0.642 | 0.752 | 0.752 | 0.417 | 0.492 | 0.942 | 259 | 325 |

### lang=en->en

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| agent+rerank@chunks-structure~glm-4.7 | 60 | 0.833 | 0.983 | 0.983 | 0.983 | 0.896 | 0.918 | 0.983 | 4895 | 8716 |
| agent@chunks-structure~glm-4.7 | 60 | 0.650 | 0.967 | 0.983 | 0.983 | 0.781 | 0.832 | 0.983 | 6868 | 15825 |
| bilingual+rerank@chunks-fixed~glm-4.7 | 60 | 0.783 | 0.900 | 0.917 | 0.917 | 0.839 | 0.858 | 0.967 | 2955 | 3665 |
| bilingual+rerank@chunks-structure~glm-4.7 | 60 | 0.717 | 0.883 | 0.917 | 0.917 | 0.796 | 0.826 | 0.967 | 2964 | 3701 |
| bilingual@chunks-structure~glm-4.7 | 60 | 0.383 | 0.667 | 0.800 | 0.800 | 0.510 | 0.571 | 0.950 | 1297 | 1813 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 60 | 0.833 | 0.983 | 0.983 | 0.983 | 0.896 | 0.917 | 0.983 | 6197 | 8261 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 60 | 0.817 | 0.983 | 0.983 | 0.983 | 0.889 | 0.912 | 1.000 | 3667 | 4842 |
| bm25@chunks-fixed | 60 | 0.350 | 0.650 | 0.733 | 0.733 | 0.499 | 0.546 | 0.983 | 1 | 1 |
| bm25@chunks-structure | 60 | 0.417 | 0.717 | 0.817 | 0.817 | 0.549 | 0.608 | 0.983 | 1 | 1 |
| dense@chunks-fixed | 60 | 0.400 | 0.750 | 0.933 | 0.933 | 0.567 | 0.652 | 0.983 | 262 | 320 |
| dense@chunks-structure | 60 | 0.567 | 0.833 | 0.917 | 0.917 | 0.686 | 0.740 | 0.983 | 242 | 326 |
| hybrid+rerank@chunks-structure~glm-4.7 | 60 | 0.850 | 0.983 | 0.983 | 0.983 | 0.911 | 0.929 | 1.000 | 1700 | 2265 |
| hybrid@chunks-fixed | 60 | 0.400 | 0.800 | 0.933 | 0.933 | 0.557 | 0.643 | 0.983 | 264 | 351 |
| hybrid@chunks-structure | 60 | 0.533 | 0.750 | 0.917 | 0.917 | 0.638 | 0.698 | 0.967 | 265 | 407 |
| per_language@chunks-fixed | 60 | 0.000 | 0.517 | 0.817 | 0.817 | 0.277 | 0.399 | 0.983 | 269 | 356 |
| per_language@chunks-structure | 60 | 0.000 | 0.617 | 0.750 | 0.750 | 0.317 | 0.415 | 0.967 | 262 | 328 |

### lang=ko->ko

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| agent+rerank@chunks-structure~glm-4.7 | 77 | 0.792 | 0.948 | 0.948 | 0.948 | 0.858 | 0.881 | 0.987 | 9298 | 15062 |
| agent@chunks-structure~glm-4.7 | 77 | 0.623 | 0.792 | 0.883 | 0.883 | 0.713 | 0.751 | 0.922 | 10361 | 22449 |
| bilingual+rerank@chunks-fixed~glm-4.7 | 77 | 0.701 | 0.844 | 0.844 | 0.844 | 0.765 | 0.785 | 0.987 | 2658 | 3171 |
| bilingual+rerank@chunks-structure~glm-4.7 | 77 | 0.753 | 0.844 | 0.844 | 0.844 | 0.799 | 0.811 | 0.961 | 2521 | 3080 |
| bilingual@chunks-structure~glm-4.7 | 77 | 0.312 | 0.571 | 0.766 | 0.766 | 0.436 | 0.509 | 0.922 | 1294 | 1846 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 77 | 0.792 | 0.896 | 0.909 | 0.909 | 0.840 | 0.857 | 0.987 | 3449 | 4996 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 77 | 0.844 | 0.909 | 0.922 | 0.922 | 0.868 | 0.881 | 0.974 | 3536 | 4477 |
| bm25@chunks-fixed | 77 | 0.299 | 0.636 | 0.727 | 0.727 | 0.451 | 0.514 | 0.909 | 1 | 2 |
| bm25@chunks-structure | 77 | 0.286 | 0.623 | 0.740 | 0.740 | 0.436 | 0.505 | 0.896 | 1 | 2 |
| dense@chunks-fixed | 77 | 0.325 | 0.584 | 0.766 | 0.766 | 0.452 | 0.524 | 0.974 | 249 | 324 |
| dense@chunks-structure | 77 | 0.403 | 0.623 | 0.766 | 0.766 | 0.513 | 0.567 | 0.961 | 243 | 297 |
| hybrid+rerank@chunks-structure~glm-4.7 | 77 | 0.844 | 0.909 | 0.922 | 0.922 | 0.871 | 0.883 | 0.974 | 1808 | 3032 |
| hybrid@chunks-fixed | 77 | 0.364 | 0.701 | 0.805 | 0.805 | 0.512 | 0.578 | 0.987 | 259 | 325 |
| hybrid@chunks-structure | 77 | 0.403 | 0.753 | 0.844 | 0.844 | 0.557 | 0.621 | 0.974 | 257 | 345 |
| per_language@chunks-fixed | 77 | 0.364 | 0.623 | 0.701 | 0.701 | 0.452 | 0.506 | 0.909 | 254 | 330 |
| per_language@chunks-structure | 77 | 0.403 | 0.662 | 0.753 | 0.753 | 0.496 | 0.552 | 0.922 | 258 | 300 |
