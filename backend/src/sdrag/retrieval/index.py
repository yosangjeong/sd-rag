"""The OpenSearch index of chunks: one document per chunk.

Fields:

- ``text``: the chunk as stored, shown in the answer's citation
- ``search_text``: what is embedded (chunk.embed_input: statute title > heading, then
  the text), analyzed twice for BM25: Korean (nori: morphemes, hanja read as hangul,
  particles dropped) and English (stemmed). Middle dots ㆍ · • become spaces first: OCR
  writes · where law.go.kr has ㆍ, and either way they separate words
- ``embedding``: Titan v2 vector, Lucene HNSW, cosine similarity
- where the chunk is, for citations and filters: doc_id, title, heading, page range,
  character span, lang, file_type (pdf | hwpx | docx | scan), ocr
- ``owner``: "public" for the shared corpus, otherwise the id of the user who uploaded
  the document. Every search filters on it (search.Searcher ``owners``), so one user's
  uploads never reach another user's results

Index names carry the chunking strategy (chunks-structure, chunks-fixed) so the
ablation can query both side by side.
"""

import time

from opensearchpy import OpenSearch, TransportError, helpers

from sdrag.ingest.chunk import Chunk, embed_input
from sdrag.ingest.corpus import CorpusDoc

SETTINGS = {
    "index": {"knn": True, "number_of_shards": 1, "number_of_replicas": 0},
    "analysis": {
        "char_filter": {"middle_dots": {"type": "mapping", "mappings": ["ㆍ=> ", "·=> ", "•=> "]}},
        "tokenizer": {"ko": {"type": "nori_tokenizer", "decompound_mode": "mixed"}},
        "filter": {
            "en_stem": {"type": "stemmer", "language": "english"},
            "en_stop": {"type": "stop", "stopwords": "_english_"},
        },
        "analyzer": {
            "ko": {
                "type": "custom",
                "char_filter": ["middle_dots"],
                "tokenizer": "ko",
                "filter": ["nori_readingform", "nori_part_of_speech", "lowercase"],
            },
            "en": {
                "type": "custom",
                "char_filter": ["middle_dots"],
                "tokenizer": "standard",
                "filter": ["lowercase", "en_stop", "en_stem"],
            },
        },
    },
}


def mappings(dims: int) -> dict:
    return {
        "dynamic": "strict",
        "properties": {
            "chunk_id": {"type": "keyword"},
            "doc_id": {"type": "keyword"},
            "owner": {"type": "keyword"},
            "title": {"type": "keyword"},
            "heading": {"type": "keyword"},
            "lang": {"type": "keyword"},
            "file_type": {"type": "keyword"},
            "kind": {"type": "keyword"},
            "ocr": {"type": "boolean"},
            "page_start": {"type": "integer"},
            "page_end": {"type": "integer"},
            "start": {"type": "integer"},
            "end": {"type": "integer"},
            "text": {"type": "text", "index": False},
            "search_text": {
                "type": "text",
                "analyzer": "ko",
                "fields": {"en": {"type": "text", "analyzer": "en"}},
            },
            "embedding": {
                "type": "knn_vector",
                "dimension": dims,
                "method": {
                    "name": "hnsw",
                    "engine": "lucene",
                    "space_type": "cosinesimil",
                    "parameters": {"m": 16, "ef_construction": 128},
                },
            },
        },
    }


def create_index(client: OpenSearch, name: str, dims: int, recreate: bool = False) -> None:
    if client.indices.exists(index=name):
        if not recreate:
            return
        client.indices.delete(index=name)
    client.indices.create(index=name, body={"settings": SETTINGS, "mappings": mappings(dims)})


PUBLIC = "public"


def to_source(doc: CorpusDoc, chunk: Chunk, vector: list[float], ocr_pages: set[int],
              owner: str = PUBLIC) -> dict:  # fmt: skip
    return {
        "chunk_id": chunk.id,
        "doc_id": doc.id,
        "owner": owner,
        "title": doc.title,
        "heading": chunk.heading,
        "lang": doc.lang,
        "file_type": doc.file_type,
        "kind": chunk.kind,
        "ocr": chunk.page_start in ocr_pages if chunk.page_start else False,
        "page_start": chunk.page_start,
        "page_end": chunk.page_end,
        "start": chunk.start,
        "end": chunk.end,
        "text": chunk.text,
        "search_text": embed_input(chunk, doc.title),
        "embedding": vector,
    }


RETRYABLE = (429, 502, 503, 504)  # the node is busy (rehearsal on t3.small: 4 workers at once)


def bulk_index(client: OpenSearch, name: str, sources: list[dict], attempts: int = 6) -> None:
    """Index in batches of 200; documents the node rejects as busy (429) are retried by
    the helper with backoff, and a whole request that fails busy is sent again after
    2, 4, 8 ... seconds. Chunk ids are the document ids, so a repeat overwrites."""
    actions = [{"_index": name, "_id": s["chunk_id"], "_source": s} for s in sources]
    for attempt in range(attempts):
        try:
            helpers.bulk(client, actions, chunk_size=200, request_timeout=120,
                         max_retries=5, initial_backoff=2, max_backoff=60)  # fmt: skip
            return
        except TransportError as e:
            if e.status_code not in RETRYABLE or attempt == attempts - 1:
                raise
            time.sleep(2 ** (attempt + 1))


def list_documents(client: OpenSearch, name: str, owners: list[str]) -> list[dict]:
    """The documents of these owners in the index: id, owner, language, title, file type."""
    body = {
        "size": 0,
        "query": {"terms": {"owner": owners}},
        "aggs": {"docs": {"terms": {"field": "doc_id", "size": 1000}, "aggs": {
            "one": {"top_hits": {"size": 1, "_source": ["title", "lang", "file_type", "owner"]}}}}},
    }  # fmt: skip
    out = []
    for b in client.search(index=name, body=body)["aggregations"]["docs"]["buckets"]:
        s = b["one"]["hits"]["hits"][0]["_source"]
        out.append(
            {"id": b["key"], "owner": s.get("owner", PUBLIC), "lang": s["lang"],
             "title": s["title"], "file_type": s["file_type"]}
        )  # fmt: skip
    return sorted(out, key=lambda d: d["id"])
