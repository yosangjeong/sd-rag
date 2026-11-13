# Approximate (HNSW) vs exact vector search (`eval/ann_recall.py`)

Index chunks-structure, top 10, owner filter as served; dense search only (no BM25, no rerank).

| set | questions | overlap@10 | identical top 10 | dense hit@10 HNSW | dense hit@10 exact |
|---|---|---|---|---|---|
| test | 338 | 99.9% | 98.8% | 0.784 | 0.784 |
| real | 137 | 100.0% | 100.0% | 0.832 | 0.832 |
| test_re | 82 | 99.9% | 98.8% | 0.866 | 0.866 |
| real_re | 83 | 99.3% | 95.2% | 0.723 | 0.735 |
