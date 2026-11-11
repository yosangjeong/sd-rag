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

Index names carry the chunking strategy (chunks-structure, chunks-fixed) so the
ablation can query both side by side.
"""

from opensearchpy import OpenSearch, helpers

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


def to_source(doc: CorpusDoc, chunk: Chunk, vector: list[float], ocr_pages: set[int]) -> dict:
    return {
        "chunk_id": chunk.id,
        "doc_id": doc.id,
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


def bulk_index(client: OpenSearch, name: str, sources: list[dict]) -> None:
    helpers.bulk(
        client,
        ({"_index": name, "_id": s["chunk_id"], "_source": s} for s in sources),
        chunk_size=200,
        request_timeout=120,
    )
