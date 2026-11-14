
### all=all

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 137 | 0.869 | 0.942 | 0.949 | 0.949 | 0.902 | 0.914 | 0.985 | 3378 | 4371 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 137 | 0.832 | 0.934 | 0.942 | 0.942 | 0.874 | 0.890 | 0.985 | 3178 | 3832 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 137 | 0.847 | 0.956 | 0.964 | 0.964 | 0.890 | 0.908 | 0.985 | 2932 | 5393 |
| bilingual_union+rerank@chunks-structure~glm-4.7~labor-prompts | 137 | 0.832 | 0.949 | 0.956 | 0.956 | 0.882 | 0.900 | 0.985 | 3048 | 3742 |
| bm25@chunks-fixed | 137 | 0.321 | 0.650 | 0.774 | 0.774 | 0.473 | 0.541 | 0.942 | 2 | 2 |
| bm25@chunks-structure | 137 | 0.343 | 0.671 | 0.781 | 0.781 | 0.490 | 0.556 | 0.934 | 2 | 2 |
| dense@chunks-fixed | 137 | 0.402 | 0.671 | 0.839 | 0.839 | 0.534 | 0.604 | 0.978 | 253 | 304 |
| dense@chunks-structure | 137 | 0.474 | 0.723 | 0.839 | 0.839 | 0.592 | 0.647 | 0.971 | 257 | 308 |
| hybrid+rerank@chunks-structure~glm-4.7 | 137 | 0.847 | 0.949 | 0.956 | 0.956 | 0.891 | 0.907 | 0.985 | 1460 | 1923 |
| hybrid@chunks-fixed | 137 | 0.409 | 0.759 | 0.869 | 0.869 | 0.561 | 0.631 | 0.978 | 257 | 316 |
| hybrid@chunks-structure | 137 | 0.474 | 0.752 | 0.890 | 0.890 | 0.604 | 0.668 | 0.971 | 258 | 323 |
| wide+rerank+jur@chunks-structure~glm-4.7 | 137 | 0.869 | 0.964 | 0.978 | 0.978 | 0.910 | 0.926 | 0.993 | 5744 | 6925 |

### file_type=docx

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 22 | 0.864 | 0.909 | 0.909 | 0.909 | 0.886 | 0.892 | 0.955 | 3542 | 4540 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 22 | 0.682 | 0.864 | 0.864 | 0.864 | 0.754 | 0.781 | 1.000 | 3348 | 3598 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 22 | 0.864 | 0.955 | 0.955 | 0.955 | 0.898 | 0.912 | 0.955 | 2957 | 3421 |
| bilingual_union+rerank@chunks-structure~glm-4.7~labor-prompts | 22 | 0.818 | 0.955 | 0.955 | 0.955 | 0.875 | 0.895 | 0.955 | 3059 | 3370 |
| bm25@chunks-fixed | 22 | 0.136 | 0.545 | 0.636 | 0.636 | 0.318 | 0.388 | 0.909 | 2 | 3 |
| bm25@chunks-structure | 22 | 0.091 | 0.636 | 0.727 | 0.727 | 0.303 | 0.401 | 0.864 | 2 | 2 |
| dense@chunks-fixed | 22 | 0.227 | 0.591 | 0.727 | 0.727 | 0.394 | 0.473 | 0.955 | 257 | 287 |
| dense@chunks-structure | 22 | 0.409 | 0.682 | 0.818 | 0.818 | 0.540 | 0.602 | 0.955 | 280 | 307 |
| hybrid+rerank@chunks-structure~glm-4.7 | 22 | 0.818 | 0.955 | 0.955 | 0.955 | 0.875 | 0.895 | 0.955 | 1471 | 1563 |
| hybrid@chunks-fixed | 22 | 0.318 | 0.727 | 0.818 | 0.818 | 0.496 | 0.573 | 1.000 | 240 | 295 |
| hybrid@chunks-structure | 22 | 0.409 | 0.773 | 0.864 | 0.864 | 0.582 | 0.649 | 0.955 | 249 | 286 |
| wide+rerank+jur@chunks-structure~glm-4.7 | 22 | 0.864 | 0.955 | 1.000 | 1.000 | 0.905 | 0.928 | 1.000 | 6149 | 7103 |

### file_type=hwpx

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 17 | 0.941 | 0.941 | 0.941 | 0.941 | 0.941 | 0.941 | 1.000 | 3419 | 3788 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 17 | 0.941 | 1.000 | 1.000 | 1.000 | 0.971 | 0.978 | 1.000 | 3038 | 3787 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 17 | 0.941 | 0.941 | 0.941 | 0.941 | 0.941 | 0.941 | 1.000 | 2882 | 3471 |
| bilingual_union+rerank@chunks-structure~glm-4.7~labor-prompts | 17 | 0.882 | 0.941 | 0.941 | 0.941 | 0.912 | 0.919 | 1.000 | 2798 | 3341 |
| bm25@chunks-fixed | 17 | 0.471 | 0.765 | 0.824 | 0.824 | 0.609 | 0.658 | 0.941 | 2 | 2 |
| bm25@chunks-structure | 17 | 0.412 | 0.706 | 0.824 | 0.824 | 0.574 | 0.631 | 0.941 | 2 | 2 |
| dense@chunks-fixed | 17 | 0.529 | 0.824 | 0.882 | 0.882 | 0.658 | 0.710 | 1.000 | 248 | 296 |
| dense@chunks-structure | 17 | 0.294 | 0.706 | 0.824 | 0.824 | 0.456 | 0.539 | 1.000 | 247 | 304 |
| hybrid+rerank@chunks-structure~glm-4.7 | 17 | 0.941 | 0.941 | 0.941 | 0.941 | 0.941 | 0.941 | 1.000 | 1415 | 1471 |
| hybrid@chunks-fixed | 17 | 0.529 | 0.765 | 0.941 | 0.941 | 0.645 | 0.715 | 1.000 | 266 | 322 |
| hybrid@chunks-structure | 17 | 0.412 | 0.706 | 0.941 | 0.941 | 0.577 | 0.663 | 1.000 | 272 | 299 |
| wide+rerank+jur@chunks-structure~glm-4.7 | 17 | 0.882 | 0.941 | 1.000 | 1.000 | 0.919 | 0.938 | 1.000 | 6006 | 6485 |

### file_type=pdf

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 98 | 0.857 | 0.949 | 0.959 | 0.959 | 0.899 | 0.914 | 0.990 | 3343 | 3784 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 98 | 0.847 | 0.939 | 0.949 | 0.949 | 0.884 | 0.900 | 0.980 | 3164 | 3836 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 98 | 0.827 | 0.959 | 0.969 | 0.969 | 0.879 | 0.902 | 0.990 | 2929 | 5630 |
| bilingual_union+rerank@chunks-structure~glm-4.7~labor-prompts | 98 | 0.827 | 0.949 | 0.959 | 0.959 | 0.879 | 0.898 | 0.990 | 3083 | 3819 |
| bm25@chunks-fixed | 98 | 0.337 | 0.653 | 0.796 | 0.796 | 0.484 | 0.555 | 0.949 | 2 | 2 |
| bm25@chunks-structure | 98 | 0.388 | 0.673 | 0.786 | 0.786 | 0.518 | 0.578 | 0.949 | 2 | 2 |
| dense@chunks-fixed | 98 | 0.418 | 0.663 | 0.857 | 0.857 | 0.544 | 0.615 | 0.980 | 253 | 307 |
| dense@chunks-structure | 98 | 0.520 | 0.735 | 0.847 | 0.847 | 0.627 | 0.676 | 0.969 | 257 | 307 |
| hybrid+rerank@chunks-structure~glm-4.7 | 98 | 0.837 | 0.949 | 0.959 | 0.959 | 0.886 | 0.904 | 0.990 | 1484 | 1969 |
| hybrid@chunks-fixed | 98 | 0.408 | 0.765 | 0.867 | 0.867 | 0.560 | 0.630 | 0.969 | 256 | 312 |
| hybrid@chunks-structure | 98 | 0.500 | 0.755 | 0.888 | 0.888 | 0.613 | 0.674 | 0.969 | 259 | 326 |
| wide+rerank+jur@chunks-structure~glm-4.7 | 98 | 0.867 | 0.969 | 0.969 | 0.969 | 0.909 | 0.923 | 0.990 | 5629 | 6795 |

### kind=real

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 137 | 0.869 | 0.942 | 0.949 | 0.949 | 0.902 | 0.914 | 0.985 | 3378 | 4371 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 137 | 0.832 | 0.934 | 0.942 | 0.942 | 0.874 | 0.890 | 0.985 | 3178 | 3832 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 137 | 0.847 | 0.956 | 0.964 | 0.964 | 0.890 | 0.908 | 0.985 | 2932 | 5393 |
| bilingual_union+rerank@chunks-structure~glm-4.7~labor-prompts | 137 | 0.832 | 0.949 | 0.956 | 0.956 | 0.882 | 0.900 | 0.985 | 3048 | 3742 |
| bm25@chunks-fixed | 137 | 0.321 | 0.650 | 0.774 | 0.774 | 0.473 | 0.541 | 0.942 | 2 | 2 |
| bm25@chunks-structure | 137 | 0.343 | 0.671 | 0.781 | 0.781 | 0.490 | 0.556 | 0.934 | 2 | 2 |
| dense@chunks-fixed | 137 | 0.402 | 0.671 | 0.839 | 0.839 | 0.534 | 0.604 | 0.978 | 253 | 304 |
| dense@chunks-structure | 137 | 0.474 | 0.723 | 0.839 | 0.839 | 0.592 | 0.647 | 0.971 | 257 | 308 |
| hybrid+rerank@chunks-structure~glm-4.7 | 137 | 0.847 | 0.949 | 0.956 | 0.956 | 0.891 | 0.907 | 0.985 | 1460 | 1923 |
| hybrid@chunks-fixed | 137 | 0.409 | 0.759 | 0.869 | 0.869 | 0.561 | 0.631 | 0.978 | 257 | 316 |
| hybrid@chunks-structure | 137 | 0.474 | 0.752 | 0.890 | 0.890 | 0.604 | 0.668 | 0.971 | 258 | 323 |
| wide+rerank+jur@chunks-structure~glm-4.7 | 137 | 0.869 | 0.964 | 0.978 | 0.978 | 0.910 | 0.926 | 0.993 | 5744 | 6925 |

### lang=en->en

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 60 | 0.900 | 0.983 | 0.983 | 0.983 | 0.943 | 0.953 | 1.000 | 3324 | 3671 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 60 | 0.867 | 0.983 | 0.983 | 0.983 | 0.911 | 0.928 | 0.983 | 3206 | 3924 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 60 | 0.850 | 0.983 | 1.000 | 1.000 | 0.907 | 0.930 | 1.000 | 2993 | 6080 |
| bilingual_union+rerank@chunks-structure~glm-4.7~labor-prompts | 60 | 0.833 | 0.983 | 0.983 | 0.983 | 0.897 | 0.918 | 1.000 | 3252 | 3822 |
| bm25@chunks-fixed | 60 | 0.350 | 0.683 | 0.817 | 0.817 | 0.500 | 0.570 | 0.983 | 2 | 2 |
| bm25@chunks-structure | 60 | 0.433 | 0.733 | 0.850 | 0.850 | 0.565 | 0.630 | 0.983 | 2 | 2 |
| dense@chunks-fixed | 60 | 0.450 | 0.767 | 0.933 | 0.933 | 0.599 | 0.677 | 0.983 | 253 | 314 |
| dense@chunks-structure | 60 | 0.567 | 0.850 | 0.917 | 0.917 | 0.691 | 0.744 | 0.983 | 256 | 308 |
| hybrid+rerank@chunks-structure~glm-4.7 | 60 | 0.850 | 0.967 | 0.983 | 0.983 | 0.909 | 0.927 | 1.000 | 1605 | 1978 |
| hybrid@chunks-fixed | 60 | 0.450 | 0.817 | 0.900 | 0.900 | 0.605 | 0.670 | 0.967 | 255 | 315 |
| hybrid@chunks-structure | 60 | 0.550 | 0.750 | 0.933 | 0.933 | 0.655 | 0.717 | 0.967 | 256 | 365 |
| wide+rerank+jur@chunks-structure~glm-4.7 | 60 | 0.883 | 0.983 | 0.983 | 0.983 | 0.929 | 0.942 | 1.000 | 5441 | 6756 |

### lang=ko->ko

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 77 | 0.844 | 0.909 | 0.922 | 0.922 | 0.871 | 0.883 | 0.974 | 3416 | 4540 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 77 | 0.805 | 0.896 | 0.909 | 0.909 | 0.845 | 0.861 | 0.987 | 3098 | 3724 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 77 | 0.844 | 0.935 | 0.935 | 0.935 | 0.877 | 0.891 | 0.974 | 2874 | 3655 |
| bilingual_union+rerank@chunks-structure~glm-4.7~labor-prompts | 77 | 0.831 | 0.922 | 0.935 | 0.935 | 0.871 | 0.886 | 0.974 | 2865 | 3504 |
| bm25@chunks-fixed | 77 | 0.299 | 0.623 | 0.740 | 0.740 | 0.452 | 0.518 | 0.909 | 2 | 3 |
| bm25@chunks-structure | 77 | 0.273 | 0.623 | 0.727 | 0.727 | 0.432 | 0.499 | 0.896 | 2 | 2 |
| dense@chunks-fixed | 77 | 0.364 | 0.597 | 0.766 | 0.766 | 0.483 | 0.547 | 0.974 | 255 | 296 |
| dense@chunks-structure | 77 | 0.403 | 0.623 | 0.779 | 0.779 | 0.515 | 0.572 | 0.961 | 257 | 307 |
| hybrid+rerank@chunks-structure~glm-4.7 | 77 | 0.844 | 0.935 | 0.935 | 0.935 | 0.877 | 0.891 | 0.974 | 1438 | 1575 |
| hybrid@chunks-fixed | 77 | 0.377 | 0.714 | 0.844 | 0.844 | 0.526 | 0.600 | 0.987 | 257 | 316 |
| hybrid@chunks-structure | 77 | 0.416 | 0.753 | 0.857 | 0.857 | 0.564 | 0.631 | 0.974 | 261 | 299 |
| wide+rerank+jur@chunks-structure~glm-4.7 | 77 | 0.857 | 0.948 | 0.974 | 0.974 | 0.894 | 0.913 | 0.987 | 5980 | 7103 |
