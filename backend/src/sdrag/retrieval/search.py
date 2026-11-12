"""Retrieval over the chunk index: BM25, dense, and their fusion.

- ``bm25``: the query against search_text in both analyzers (Korean nori, English)
- ``dense``: k-NN on the Titan embedding of the query
- ``hybrid``: both, fused by Reciprocal Rank Fusion
- ``bilingual``: the hybrid search run with the question and with its translation into
  the other corpus language (rerank.LlmTranslator), fused
- ``per_language``: the hybrid search run once per corpus language and fused. Both
  embedding models measured favor chunks in the query's language: a Korean query put
  Korean chunks in 74% of Titan's top 10, and the corpus holds 4.5x more Korean than
  English chunks, so an English answer to a Korean question was easily outranked
  (eval/embed_bench.py: R@10 ko->en 38.8% over the whole corpus, 62.5% within English)

RRF (score = sum of 1 / (k + rank)) fuses by rank, so lists whose scores live on
different scales (BM25, cosine) need no normalization. k = 60 is the usual constant
(Cormack et al., 2009). Fusion is done here rather than in an OpenSearch search
pipeline so that the same code merges the per-language lists.
"""

from dataclasses import dataclass, field

from opensearchpy import OpenSearch

from sdrag.retrieval.embed import Embedder

RRF_K = 60
LANGS = ("ko", "en")
SOURCE = ["chunk_id", "doc_id", "owner", "title", "heading", "lang", "file_type", "page_start",
          "page_end", "start", "end", "text", "ocr"]  # fmt: skip


@dataclass
class Hit:
    chunk_id: str
    score: float
    source: dict = field(repr=False)


def _filters(langs, doc_ids, owners=None) -> list[dict]:
    f = [{"terms": {"owner": owners}}] if owners else []
    if langs:
        f.append({"terms": {"lang": langs}})
    if doc_ids:
        f.append({"terms": {"doc_id": doc_ids}})
    return f


def _hits(resp: dict) -> list[Hit]:
    return [Hit(h["_id"], h["_score"], h["_source"]) for h in resp["hits"]["hits"]]


def rrf(*lists: list[Hit], k: int = RRF_K, size: int = 10) -> list[Hit]:
    scores: dict[str, float] = {}
    first: dict[str, Hit] = {}
    for hits in lists:
        for rank, h in enumerate(hits, start=1):
            scores[h.chunk_id] = scores.get(h.chunk_id, 0.0) + 1.0 / (k + rank)
            first.setdefault(h.chunk_id, h)
    best = sorted(scores, key=lambda c: (-scores[c], c))[:size]
    return [Hit(c, scores[c], first[c].source) for c in best]


class Searcher:
    def __init__(self, client: OpenSearch, index: str, embedder: Embedder, translator=None,
                 owners: list[str] | None = None) -> None:  # fmt: skip
        """owners: when set, every query is limited to chunks of these owners (the
        service passes [user id, "public"]); None searches everything (evaluation)."""
        self.client, self.index, self.embedder = client, index, embedder
        self.translator, self.owners = translator, owners

    def bm25(self, query: str, size: int = 10, langs=None, doc_ids=None) -> list[Hit]:
        body = {
            "size": size,
            "_source": SOURCE,
            "query": {
                "bool": {
                    "must": {
                        "multi_match": {
                            "query": query,
                            "fields": ["search_text", "search_text.en"],
                            "type": "most_fields",
                        }
                    },
                    "filter": _filters(langs, doc_ids, self.owners),
                }
            },
        }
        return _hits(self.client.search(index=self.index, body=body))

    def dense(self, query: str, size: int = 10, langs=None, doc_ids=None, vector=None) -> list[Hit]:
        vector = vector or self.embedder.embed([query])[0]
        knn = {"vector": vector, "k": size}
        if f := _filters(langs, doc_ids, self.owners):
            knn["filter"] = {"bool": {"filter": f}}  # Lucene filters while searching
        body = {"size": size, "_source": SOURCE, "query": {"knn": {"embedding": knn}}}
        return _hits(self.client.search(index=self.index, body=body))

    def hybrid(self, query: str, size: int = 10, depth: int = 50, langs=None, doc_ids=None,
               vector=None) -> list[Hit]:  # fmt: skip
        vector = vector or self.embedder.embed([query])[0]
        return rrf(
            self.bm25(query, depth, langs, doc_ids),
            self.dense(query, depth, langs, doc_ids, vector),
            size=size,
        )

    def per_language(self, query: str, size: int = 10, depth: int = 50, doc_ids=None) -> list[Hit]:
        vector = self.embedder.embed([query])[0]
        return rrf(
            *(self.hybrid(query, depth, depth, [lang], doc_ids, vector) for lang in LANGS),
            size=size,
        )

    def bilingual(self, query: str, size: int = 10, depth: int = 50, doc_ids=None,
                  translation: str | None = None) -> list[Hit]:  # fmt: skip
        if translation is None:
            translation, _ = self.translator.to_other_language(query)
        if not translation.strip():  # the model returned nothing: search the question alone
            return self.hybrid(query, size, depth, None, doc_ids)
        return rrf(
            self.hybrid(query, depth, depth, None, doc_ids),
            self.hybrid(translation, depth, depth, None, doc_ids),
            size=size,
        )
