"""Retrieval over the chunk index: BM25, dense, and their fusion.

- ``bm25``: the query against search_text in both analyzers (Korean nori, English)
- ``dense``: k-NN on the Titan embedding of the query
- ``hybrid``: both, fused by Reciprocal Rank Fusion
- ``bilingual``: the hybrid search run with the question and with its translation into
  the other corpus language (rerank.LlmTranslator), fused
- ``wide`` (served): bilingual_union plus each first-stage list on its own and the
  decree/rule articles that cite the retrieved law articles, about 50 candidates for
  the reranker (docs/decisions.md, "Wider candidate pool")
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

import re
from dataclasses import dataclass, field

from opensearchpy import OpenSearch

from sdrag.retrieval.embed import Embedder
from sdrag.retrieval.terms import expand

RRF_K = 60
LANGS = ("ko", "en")
SOURCE = ["chunk_id", "doc_id", "owner", "title", "heading", "lang", "file_type", "page_start",
          "page_end", "start", "end", "text", "ocr"]  # fmt: skip


@dataclass
class Hit:
    chunk_id: str
    score: float
    source: dict = field(repr=False)


COUNTRIES = ("kr", "us")  # public document ids start with the country: kr-..., us-...


def _filters(langs, doc_ids, owners=None, scope=None, country=None) -> list[dict]:
    f = [{"terms": {"owner": owners}}] if owners else []
    if country:  # leave out the other countries' public statutes; uploads stay
        others = [{"prefix": {"doc_id": f"{c}-"}} for c in COUNTRIES if c != country]
        public = {"term": {"owner": "public"}}
        f.append({"bool": {"must_not": [{"bool": {"filter": [public], "should": others,
                                                    "minimum_should_match": 1}}]}})  # fmt: skip
    if scope:
        f.append({"terms": {"doc_id": scope}})
    if langs:
        f.append({"terms": {"lang": langs}})
    if doc_ids:
        f.append({"terms": {"doc_id": doc_ids}})
    return f


def _hits(resp: dict) -> list[Hit]:
    return [Hit(h["_id"], h["_score"], h["_source"]) for h in resp["hits"]["hits"]]


def rrf(*lists: list[Hit], k: int = RRF_K, size: int = 10, weights=None) -> list[Hit]:
    """weights: one per list (default 1): a list's ranks count weight / (k + rank)."""
    scores: dict[str, float] = {}
    first: dict[str, Hit] = {}
    for hits, w in zip(lists, weights or [1.0] * len(lists), strict=True):
        for rank, h in enumerate(hits, start=1):
            scores[h.chunk_id] = scores.get(h.chunk_id, 0.0) + w / (k + rank)
            first.setdefault(h.chunk_id, h)
    best = sorted(scores, key=lambda c: (-scores[c], c))[:size]
    return [Hit(c, scores[c], first[c].source) for c in best]


class Searcher:
    def __init__(self, client: OpenSearch, index: str, embedder: Embedder, translator=None,
                 owners: list[str] | None = None, scope: list[str] | None = None,
                 country: str | None = None) -> None:  # fmt: skip
        """owners: when set, every query is limited to chunks of these owners (the
        service passes [user id, "public"]); None searches everything (evaluation).
        scope: when set, every query is limited to these documents ("search this file").
        country: "kr" | "us": public statutes of the other country are left out
        (retrieval/jurisdiction.py); uploads are not affected."""
        self.client, self.index, self.embedder = client, index, embedder
        self.translator, self.owners, self.scope = translator, owners, scope
        self.country = country
        self.last_queries: list[str] = []  # the texts the last wide() searched with

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
                    "filter": _filters(langs, doc_ids, self.owners, self.scope, self.country),
                }
            },
        }
        return _hits(self.client.search(index=self.index, body=body))

    def dense(self, query: str, size: int = 10, langs=None, doc_ids=None, vector=None) -> list[Hit]:
        vector = vector or self.embedder.embed([query])[0]
        knn = {"vector": vector, "k": size}
        if f := _filters(langs, doc_ids, self.owners, self.scope, self.country):
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
                  translation: str | None = None,
                  translation_weight: float = 1.0) -> list[Hit]:  # fmt: skip
        if translation is None:
            translation, _ = self.translator.to_other_language(query)
        if not translation.strip():  # the model returned nothing: search the question alone
            return self.hybrid(query, size, depth, None, doc_ids)
        return rrf(
            self.hybrid(query, depth, depth, None, doc_ids),
            self.hybrid(translation, depth, depth, None, doc_ids),
            size=size,
            weights=[1.0, translation_weight],
        )

    def bilingual_union(self, query: str, size: int = 20, extra: int = 10, doc_ids=None,
                        translation: str | None = None, base: str = "hybrid") -> list[Hit]:  # fmt: skip
        """The question's own top `size`, then up to `extra` more from its translation.

        For a reranker: the question's candidates are all kept (fusing the two lists
        let the translation's results push them out, which cost same-language
        questions), and the translation still adds the other language's best.
        base: the first-stage search for both, "hybrid" (served) or "dense" (ablation)."""
        if translation is None:
            translation, _ = self.translator.to_other_language(query)

        def first(q: str) -> list[Hit]:
            if base == "dense":
                return self.dense(q, size, None, doc_ids)
            return self.hybrid(q, size, 50, None, doc_ids)

        own = first(query)
        if not translation.strip():
            return own
        seen = {h.chunk_id for h in own}
        more = [h for h in first(translation) if h.chunk_id not in seen]
        return own + more[:extra]

    def bilingual_union_dense(self, query: str, size: int = 20, extra: int = 10,
                              doc_ids=None) -> list[Hit]:  # fmt: skip
        """bilingual_union on dense search alone, for the ablation (eval/run_retrieval.py)."""
        return self.bilingual_union(query, size, extra, doc_ids, base="dense")

    def wide(self, query: str, size: int = 20, extra: int = 10, each: int = 5, refs: int = 5,
             defs: int = 3,
             doc_ids=None, translation: str | None = None,
             statute_terms: str | None = None, fused: bool = False) -> list[Hit]:  # fmt: skip
        """A wider candidate list for the reranker than bilingual_union, in five parts:

        1. bilingual_union: the question's hybrid top `size`, its translation's `extra`.
        2. Each first-stage list on its own, top `each` of BM25 and of dense for both the
           question and its translation. RRF keeps a chunk that only one list ranks high
           below chunks both lists rank middling: of 49 served misses (top 6), a gold
           BM25 put 3rd was 38th after fusion.
        3. Cross-references (`references`): where a Korean statute leaves the figure,
           the authority or the procedure to a decree or rule ("대통령령으로 정한다"), the
           answer is in the decree article that cites it ("법 제39조제3항제6호"), which
           shares few words with the question. 15 of the 49 misses were such a decree
           or rule article while its law article was retrieved.
        4. The question in the statute's terms (`LlmTranslator.to_statute_terms`): its
           hybrid top `extra` not yet in. A situation question ("주변에서 계약기간을 1년으로
           하라는데") or a provision's popular name shares few words with the article.
        5. Definition articles (`definitions`): "평균임금은 어떻게 계산하나요" is answered
           by 제2조(정의), which lists dozens of terms and matches no single question well.

        BM25 searches each query with the statute terms of its everyday words appended
        (terms.expand: 집주인 -> 임대인); the vector search embeds the query as it is.
        """
        if translation is None:
            translation, _ = self.translator.to_other_language(query)
        if statute_terms is None and hasattr(self.translator, "to_statute_terms"):
            statute_terms = self.translator.to_statute_terms(query)
        queries = [query] + ([translation] if translation.strip() else [])
        lists = []
        for q in queries:
            vector = self.embedder.embed([q])[0]
            b = self.bm25(expand(q), 50, None, doc_ids)  # everyday words -> statute terms
            d = self.dense(q, 50, None, doc_ids, vector)
            lists.append((rrf(b, d, size=size), b, d))
        out: dict[str, Hit] = {}

        def add(hits, n):
            for h in [h for h in hits if h.chunk_id not in out][:n]:
                out[h.chunk_id] = h

        add(lists[0][0], size)
        if len(lists) > 1:
            add(lists[1][0], extra)
        for _, b, d in lists:
            add(b, each)
            add(d, each)
        ranked = [x for _, b, d in lists for x in (b, d)]  # every list, for `fused`
        terms = (statute_terms or "").strip()
        if terms and terms not in queries:
            t_hits = self.hybrid(terms, extra, 50, None, doc_ids)
            add(t_hits, extra)
            ranked.append(t_hits)
            queries.append(terms)
        r_hits = self.references(queries, list(out.values()), doc_ids)
        d_hits = self.definitions(queries, doc_ids)
        add(r_hits, refs)
        add(d_hits, defs)
        ranked += [r_hits, d_hits]
        self.last_queries = queries  # for the reranker's passage windows
        pool = list(out.values())
        if fused:  # present the pool in the order all its lists agree on, not arrival
            fused_rank = {h.chunk_id: i for i, h in enumerate(rrf(*ranked, size=10_000))}
            pool.sort(key=lambda h: fused_rank.get(h.chunk_id, len(fused_rank)))
        return pool

    def wide_no_terms(self, query: str, size: int = 20, **kw) -> list[Hit]:
        """wide without the statute-terms query (an ablation: what that LLM call adds)."""
        return self.wide(query, size, statute_terms="", **kw)

    def wide_fused(self, query: str, size: int = 20, **kw) -> list[Hit]:
        """wide with the pool ordered by RRF over all its lists (an ablation)."""
        return self.wide(query, size, fused=True, **kw)

    def references(self, queries: list[str], hits: list[Hit], doc_ids=None, per_article: int = 3,
                   articles: int = 15) -> list[Hit]:  # fmt: skip
        """Decree and rule chunks that cite the law (or decree) articles among `hits`:
        for "제39조(과태료)" of kr-equal-employment-law, the chunks of -dec and -rul
        with the phrase "법 제39", best `per_article` by BM25 on the queries (the
        question and its translation: an English question shares no words with a
        Korean decree table), all of them ordered by that score.

        The first version looked at the first 8 articles only and scored with the
        question alone; for a fine asked in English the 제39조(과태료) article was the
        9th among the candidates and the decree's fine table never came up."""
        seen, found = set(), {}
        for h in hits:
            doc = h.source.get("doc_id", "")
            m = RE_ARTICLE.match(h.source.get("heading") or "")
            fam, _, kind = doc.rpartition("-")
            if not m or not doc.startswith("kr-") or kind not in CITED_BY:
                continue
            key = (fam, kind, m.group(1))
            if key in seen:
                continue
            seen.add(key)
            if len(seen) > articles:
                break
            phrase = f"{'법' if kind == 'law' else '영'} 제{m.group(1)}"
            targets = [f"{fam}-{k}" for k in CITED_BY[kind]]
            if doc_ids:
                targets = [t for t in targets if t in doc_ids]
            if not targets:
                continue
            filters = _filters(None, targets, self.owners, self.scope, self.country)
            filters.append({"match_phrase": {"search_text": phrase}})
            should = [{"multi_match": {"query": q, "fields": ["search_text", "search_text.en"]}}
                      for q in queries if q.strip()]  # fmt: skip
            body = {"size": per_article, "_source": SOURCE,
                    "query": {"bool": {"should": should, "filter": filters}}}  # fmt: skip
            for r in _hits(self.client.search(index=self.index, body=body)):
                if r.chunk_id not in found or r.score > found[r.chunk_id].score:
                    found[r.chunk_id] = r
        return sorted(found.values(), key=lambda r: (-r.score, r.chunk_id))

    def definitions(self, queries: list[str], doc_ids=None, size: int = 3) -> list[Hit]:
        """The definition articles ("제2조(정의)", "§ 1024.2 Definitions.") that best match
        the queries by BM25: a question about what a term means, or how it is computed,
        is answered there. 133 such chunks in the 70-document corpus."""
        should = [{"multi_match": {"query": expand(q), "fields": ["search_text", "search_text.en"]}}
                  for q in queries if q.strip()]  # fmt: skip
        heading = {"bool": {"should": [
            {"wildcard": {"heading": "*(정의)*"}},
            {"wildcard": {"heading": {"value": "*definition*", "case_insensitive": True}}}],
            "minimum_should_match": 1}}  # fmt: skip
        filters = _filters(None, doc_ids, self.owners, self.scope, self.country) + [heading]
        body = {"size": size, "_source": SOURCE,
                "query": {"bool": {"should": should, "minimum_should_match": 1, "filter": filters}}}  # fmt: skip
        return _hits(self.client.search(index=self.index, body=body))


# a Korean article heading: "제39조(과태료)", "제18조의3(난임치료휴가) [2026. 11. 27. 시행]"
RE_ARTICLE = re.compile(r"제(\d+)조(?:의\d+)?\(")
# which documents cite a law or decree article: the decree and rule cite "법 제N조",
# the rule cites "영 제N조"
CITED_BY = {"law": ("dec", "rul"), "dec": ("rul",)}
