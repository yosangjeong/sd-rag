
### all=all

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 137 | 0.854 | 0.942 | 0.949 | 0.949 | 0.893 | 0.907 | 0.985 | 3378 | 4371 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 137 | 0.796 | 0.934 | 0.942 | 0.942 | 0.855 | 0.876 | 0.985 | 3178 | 3832 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 137 | 0.832 | 0.956 | 0.964 | 0.964 | 0.881 | 0.901 | 0.985 | 2932 | 5393 |
| bilingual_union+rerank@chunks-structure~glm-4.7~labor-prompts | 137 | 0.825 | 0.942 | 0.956 | 0.956 | 0.878 | 0.897 | 0.985 | 3048 | 3742 |
| bm25@chunks-fixed | 137 | 0.321 | 0.635 | 0.752 | 0.752 | 0.468 | 0.530 | 0.942 | 2 | 2 |
| bm25@chunks-structure | 137 | 0.343 | 0.664 | 0.774 | 0.774 | 0.486 | 0.551 | 0.934 | 2 | 2 |
| dense@chunks-fixed | 137 | 0.372 | 0.664 | 0.832 | 0.832 | 0.512 | 0.586 | 0.978 | 253 | 304 |
| dense@chunks-structure | 137 | 0.474 | 0.715 | 0.832 | 0.832 | 0.588 | 0.642 | 0.971 | 257 | 308 |
| hybrid+rerank@chunks-structure~glm-4.7 | 137 | 0.839 | 0.949 | 0.956 | 0.956 | 0.887 | 0.904 | 0.985 | 1460 | 1923 |
| hybrid@chunks-fixed | 137 | 0.380 | 0.752 | 0.861 | 0.861 | 0.539 | 0.613 | 0.978 | 257 | 316 |
| hybrid@chunks-structure | 137 | 0.467 | 0.752 | 0.890 | 0.890 | 0.595 | 0.662 | 0.971 | 258 | 323 |

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

### file_type=hwpx

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 17 | 0.941 | 0.941 | 0.941 | 0.941 | 0.941 | 0.941 | 1.000 | 3419 | 3788 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 17 | 0.824 | 1.000 | 1.000 | 1.000 | 0.912 | 0.935 | 1.000 | 3038 | 3787 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 17 | 0.941 | 0.941 | 0.941 | 0.941 | 0.941 | 0.941 | 1.000 | 2882 | 3471 |
| bilingual_union+rerank@chunks-structure~glm-4.7~labor-prompts | 17 | 0.882 | 0.941 | 0.941 | 0.941 | 0.912 | 0.919 | 1.000 | 2798 | 3341 |
| bm25@chunks-fixed | 17 | 0.471 | 0.765 | 0.765 | 0.765 | 0.606 | 0.641 | 0.941 | 2 | 2 |
| bm25@chunks-structure | 17 | 0.412 | 0.706 | 0.824 | 0.824 | 0.574 | 0.631 | 0.941 | 2 | 2 |
| dense@chunks-fixed | 17 | 0.471 | 0.824 | 0.882 | 0.882 | 0.619 | 0.680 | 1.000 | 248 | 296 |
| dense@chunks-structure | 17 | 0.294 | 0.706 | 0.824 | 0.824 | 0.456 | 0.539 | 1.000 | 247 | 304 |
| hybrid+rerank@chunks-structure~glm-4.7 | 17 | 0.941 | 0.941 | 0.941 | 0.941 | 0.941 | 0.941 | 1.000 | 1415 | 1471 |
| hybrid@chunks-fixed | 17 | 0.529 | 0.765 | 0.941 | 0.941 | 0.644 | 0.714 | 1.000 | 266 | 322 |
| hybrid@chunks-structure | 17 | 0.412 | 0.706 | 0.941 | 0.941 | 0.577 | 0.663 | 1.000 | 272 | 299 |

### file_type=pdf

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 98 | 0.837 | 0.949 | 0.959 | 0.959 | 0.886 | 0.904 | 0.990 | 3343 | 3784 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 98 | 0.816 | 0.939 | 0.949 | 0.949 | 0.867 | 0.887 | 0.980 | 3164 | 3836 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 98 | 0.806 | 0.959 | 0.969 | 0.969 | 0.867 | 0.892 | 0.990 | 2929 | 5630 |
| bilingual_union+rerank@chunks-structure~glm-4.7~labor-prompts | 98 | 0.816 | 0.939 | 0.959 | 0.959 | 0.873 | 0.894 | 0.990 | 3083 | 3819 |
| bm25@chunks-fixed | 98 | 0.337 | 0.633 | 0.775 | 0.775 | 0.477 | 0.543 | 0.949 | 2 | 2 |
| bm25@chunks-structure | 98 | 0.388 | 0.663 | 0.775 | 0.775 | 0.512 | 0.570 | 0.949 | 2 | 2 |
| dense@chunks-fixed | 98 | 0.388 | 0.653 | 0.847 | 0.847 | 0.521 | 0.595 | 0.980 | 253 | 307 |
| dense@chunks-structure | 98 | 0.520 | 0.725 | 0.837 | 0.837 | 0.622 | 0.669 | 0.969 | 257 | 307 |
| hybrid+rerank@chunks-structure~glm-4.7 | 98 | 0.827 | 0.949 | 0.959 | 0.959 | 0.881 | 0.900 | 0.990 | 1484 | 1969 |
| hybrid@chunks-fixed | 98 | 0.367 | 0.755 | 0.857 | 0.857 | 0.530 | 0.604 | 0.969 | 256 | 312 |
| hybrid@chunks-structure | 98 | 0.490 | 0.755 | 0.888 | 0.888 | 0.602 | 0.664 | 0.969 | 259 | 326 |

### kind=real

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 137 | 0.854 | 0.942 | 0.949 | 0.949 | 0.893 | 0.907 | 0.985 | 3378 | 4371 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 137 | 0.796 | 0.934 | 0.942 | 0.942 | 0.855 | 0.876 | 0.985 | 3178 | 3832 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 137 | 0.832 | 0.956 | 0.964 | 0.964 | 0.881 | 0.901 | 0.985 | 2932 | 5393 |
| bilingual_union+rerank@chunks-structure~glm-4.7~labor-prompts | 137 | 0.825 | 0.942 | 0.956 | 0.956 | 0.878 | 0.897 | 0.985 | 3048 | 3742 |
| bm25@chunks-fixed | 137 | 0.321 | 0.635 | 0.752 | 0.752 | 0.468 | 0.530 | 0.942 | 2 | 2 |
| bm25@chunks-structure | 137 | 0.343 | 0.664 | 0.774 | 0.774 | 0.486 | 0.551 | 0.934 | 2 | 2 |
| dense@chunks-fixed | 137 | 0.372 | 0.664 | 0.832 | 0.832 | 0.512 | 0.586 | 0.978 | 253 | 304 |
| dense@chunks-structure | 137 | 0.474 | 0.715 | 0.832 | 0.832 | 0.588 | 0.642 | 0.971 | 257 | 308 |
| hybrid+rerank@chunks-structure~glm-4.7 | 137 | 0.839 | 0.949 | 0.956 | 0.956 | 0.887 | 0.904 | 0.985 | 1460 | 1923 |
| hybrid@chunks-fixed | 137 | 0.380 | 0.752 | 0.861 | 0.861 | 0.539 | 0.613 | 0.978 | 257 | 316 |
| hybrid@chunks-structure | 137 | 0.467 | 0.752 | 0.890 | 0.890 | 0.595 | 0.662 | 0.971 | 258 | 323 |

### lang=en->en

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 60 | 0.867 | 0.983 | 0.983 | 0.983 | 0.922 | 0.937 | 1.000 | 3324 | 3671 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 60 | 0.833 | 0.983 | 0.983 | 0.983 | 0.892 | 0.914 | 0.983 | 3206 | 3924 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 60 | 0.817 | 0.983 | 1.000 | 1.000 | 0.886 | 0.914 | 1.000 | 2993 | 6080 |
| bilingual_union+rerank@chunks-structure~glm-4.7~labor-prompts | 60 | 0.817 | 0.967 | 0.983 | 0.983 | 0.888 | 0.911 | 1.000 | 3252 | 3822 |
| bm25@chunks-fixed | 60 | 0.350 | 0.650 | 0.783 | 0.783 | 0.489 | 0.552 | 0.983 | 2 | 2 |
| bm25@chunks-structure | 60 | 0.433 | 0.717 | 0.833 | 0.833 | 0.561 | 0.622 | 0.983 | 2 | 2 |
| dense@chunks-fixed | 60 | 0.400 | 0.750 | 0.933 | 0.933 | 0.564 | 0.650 | 0.983 | 253 | 314 |
| dense@chunks-structure | 60 | 0.567 | 0.833 | 0.917 | 0.917 | 0.686 | 0.740 | 0.983 | 256 | 308 |
| hybrid+rerank@chunks-structure~glm-4.7 | 60 | 0.833 | 0.967 | 0.983 | 0.983 | 0.900 | 0.920 | 1.000 | 1605 | 1978 |
| hybrid@chunks-fixed | 60 | 0.383 | 0.817 | 0.900 | 0.900 | 0.559 | 0.636 | 0.967 | 255 | 315 |
| hybrid@chunks-structure | 60 | 0.550 | 0.750 | 0.933 | 0.933 | 0.647 | 0.710 | 0.967 | 256 | 365 |

### lang=ko->ko

| system | n | span_hit@1 | span_hit@5 | span_hit@10 | span_recall@10 | span_mrr | span_ndcg10 | doc_hit@10 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| bilingual_union+rerank+jur@chunks-structure~glm-4.7 | 77 | 0.844 | 0.909 | 0.922 | 0.922 | 0.871 | 0.883 | 0.974 | 3416 | 4540 |
| bilingual_union+rerank@chunks-fixed~glm-4.7 | 77 | 0.766 | 0.896 | 0.909 | 0.909 | 0.825 | 0.846 | 0.987 | 3098 | 3724 |
| bilingual_union+rerank@chunks-structure~glm-4.7 | 77 | 0.844 | 0.935 | 0.935 | 0.935 | 0.877 | 0.891 | 0.974 | 2874 | 3655 |
| bilingual_union+rerank@chunks-structure~glm-4.7~labor-prompts | 77 | 0.831 | 0.922 | 0.935 | 0.935 | 0.871 | 0.886 | 0.974 | 2865 | 3504 |
| bm25@chunks-fixed | 77 | 0.299 | 0.623 | 0.727 | 0.727 | 0.452 | 0.514 | 0.909 | 2 | 3 |
| bm25@chunks-structure | 77 | 0.273 | 0.623 | 0.727 | 0.727 | 0.428 | 0.495 | 0.896 | 2 | 2 |
| dense@chunks-fixed | 77 | 0.351 | 0.597 | 0.753 | 0.753 | 0.472 | 0.536 | 0.974 | 255 | 296 |
| dense@chunks-structure | 77 | 0.403 | 0.623 | 0.766 | 0.766 | 0.512 | 0.567 | 0.961 | 257 | 307 |
| hybrid+rerank@chunks-structure~glm-4.7 | 77 | 0.844 | 0.935 | 0.935 | 0.935 | 0.877 | 0.891 | 0.974 | 1438 | 1575 |
| hybrid@chunks-fixed | 77 | 0.377 | 0.701 | 0.831 | 0.831 | 0.524 | 0.595 | 0.987 | 257 | 316 |
| hybrid@chunks-structure | 77 | 0.403 | 0.753 | 0.857 | 0.857 | 0.555 | 0.624 | 0.974 | 261 | 299 |
