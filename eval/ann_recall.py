"""How much the approximate vector search (HNSW) loses against an exact one.

The dense search uses Lucene HNSW (m=16, ef_construction=128, retrieval/index.py). For
every question of the evaluation sets, the top 10 of the served k-NN query (with the
owner filter, as in the service) is compared with an exact search over the same
chunks (OpenSearch's knn_score script: cosine with every chunk vector):

- overlap@10: share of the exact top 10 that HNSW also returns
- identical: questions whose top 10 is the same set
- span hit@10 of dense retrieval under each, scored like eval/run_retrieval.py

No LLM is called; question embeddings come from the embedding cache (Titan for the
few not cached).

    cd backend && AWS_PROFILE=<profile> SDRAG_EMBED_CACHE_DIR=../data/raw/cache/embed \\
        uv run python ../eval/ann_recall.py
"""

import statistics
from pathlib import Path

from evalset import DATA, load_items, score
from opensearchpy import OpenSearch

from sdrag.common.config import settings
from sdrag.retrieval.embed import CachedEmbedder, TitanEmbedder
from sdrag.retrieval.index import PUBLIC

INDEX = "chunks-structure"
K = 10
SETS = ("test", "real", "test_re", "real_re")
OUT = DATA / "eval" / "results" / "ann-recall.md"
FIELDS = ["doc_id", "start", "end"]


def main() -> None:
    client = OpenSearch(hosts=[settings.opensearch_url], timeout=120)
    emb = TitanEmbedder(settings.embed_model, settings.aws_region, settings.embed_dims)
    emb = CachedEmbedder(emb, Path(settings.embed_cache_dir or DATA / "raw" / "cache" / "embed"))
    owner = {"terms": {"owner": [PUBLIC]}}

    def hnsw(vec):
        body = {"size": K, "_source": FIELDS, "query": {"knn": {"embedding": {
            "vector": vec, "k": K, "filter": {"bool": {"filter": [owner]}}}}}}  # fmt: skip
        return client.search(index=INDEX, body=body)["hits"]["hits"]

    def exact(vec):
        body = {"size": K, "_source": FIELDS, "query": {"script_score": {
            "query": {"bool": {"filter": [owner]}},
            "script": {"source": "knn_score", "lang": "knn", "params": {
                "field": "embedding", "query_value": vec, "space_type": "cosinesimil"}}}}}  # fmt: skip
        return client.search(index=INDEX, body=body)["hits"]["hits"]

    lines = [
        "# Approximate (HNSW) vs exact vector search (`eval/ann_recall.py`)",
        "",
        f"Index {INDEX}, top {K}, owner filter as served; dense search only (no BM25, no rerank).",
        "",
        "| set | questions | overlap@10 | identical top 10 | dense hit@10 HNSW | dense hit@10 exact |",
        "|---|---|---|---|---|---|",
    ]
    for name in SETS:
        items = load_items(DATA / "eval" / f"{name}.jsonl")
        vecs = emb.embed([it.question for it in items])
        over, same, hit_a, hit_e = [], 0, [], []
        for it, vec in zip(items, vecs, strict=True):
            a, e = hnsw(vec), exact(vec)
            ida, ide = {h["_id"] for h in a}, {h["_id"] for h in e}
            over.append(len(ida & ide) / max(len(ide), 1))
            same += ida == ide

            for hits, acc in ((a, hit_a), (e, hit_e)):
                got = [h["_source"] | {"chunk_id": h["_id"]} for h in hits]
                acc.append(score(got, it.gold, it.also).span_hit[10])
        lines.append(f"| {name} | {len(items)} | {statistics.mean(over):.1%} | {same / len(items):.1%} | "
                     f"{statistics.mean(hit_a):.3f} | {statistics.mean(hit_e):.3f} |")  # fmt: skip
        print(lines[-1], flush=True)
    OUT.write_text("\n".join(lines) + "\n", "utf-8")


if __name__ == "__main__":
    main()
