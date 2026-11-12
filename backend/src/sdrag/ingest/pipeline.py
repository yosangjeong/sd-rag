"""Ingestion: corpus document -> parse (OCR for scanned pages) -> chunk -> embed -> index.

Run locally against infra/local/opensearch (caches keep OCR and embeddings from being
paid twice):

    cd backend && AWS_PROFILE=sd-assignment SDRAG_OCR_CACHE_DIR=../data/raw/ocr-cache \\
        SDRAG_EMBED_CACHE_DIR=../data/raw/embed-cache \\
        uv run python -m sdrag.ingest.pipeline --strategy structure --recreate

Per-document and per-stage timings are recorded: the brief asks for ingestion
throughput and duration.
"""

import argparse
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from opensearchpy import OpenSearch

from sdrag.common.config import settings
from sdrag.common.search_client import make_client
from sdrag.ingest.chunk import STRATEGIES, embed_input
from sdrag.ingest.corpus import CorpusDoc, load_corpus
from sdrag.ingest.ocr import BedrockVisionOcr, CachedOcr, OcrEngine
from sdrag.ingest.parse import parse
from sdrag.retrieval.embed import CachedEmbedder, Embedder, TitanEmbedder
from sdrag.retrieval.index import PUBLIC, bulk_index, create_index, to_source


@dataclass
class DocStats:
    doc_id: str
    file_type: str
    chunks: int
    ocr_pages: int
    needs_ocr_pages: int
    parse_s: float
    embed_s: float
    index_s: float


def ingest(
    doc: CorpusDoc,
    client: OpenSearch,
    index: str,
    strategy: str,
    embedder: Embedder,
    ocr: OcrEngine | None,
) -> DocStats:
    t0 = time.perf_counter()
    parsed = parse(doc.path, ocr=ocr)
    chunks = STRATEGIES[strategy](parsed, doc.id)
    t1 = time.perf_counter()
    vectors = embedder.embed([embed_input(c, doc.title) for c in chunks])
    t2 = time.perf_counter()
    ocr_pages = set(parsed.ocr_pages)
    bulk_index(client, index, [to_source(doc, c, v, ocr_pages) for c, v in zip(chunks, vectors)])
    t3 = time.perf_counter()
    return DocStats(
        doc.id, doc.file_type, len(chunks), len(parsed.ocr_pages), len(parsed.needs_ocr_pages),
        round(t1 - t0, 2), round(t2 - t1, 2), round(t3 - t2, 2),
    )  # fmt: skip


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--data", type=Path, default=Path(__file__).resolve().parents[4] / "data")
    ap.add_argument("--strategy", choices=STRATEGIES, default="structure")
    ap.add_argument("--index", help="default: chunks-<strategy>")
    ap.add_argument("--recreate", action="store_true", help="drop and rebuild the index")
    ap.add_argument("--replace-public", action="store_true",
                    help="delete the public corpus's chunks first, keeping users' uploads")  # fmt: skip
    ap.add_argument("--stats", type=Path, help="write per-document stats (JSON)")
    a = ap.parse_args()

    index = a.index or f"chunks-{a.strategy}"
    client = make_client(settings.opensearch_url, settings.aws_region, 120)
    titan = TitanEmbedder(settings.embed_model, settings.aws_region, settings.embed_dims)
    embedder: Embedder = titan
    if settings.embed_cache_dir:
        embedder = CachedEmbedder(titan, Path(settings.embed_cache_dir))
    ocr: OcrEngine = BedrockVisionOcr(settings.ocr_model, settings.aws_region)
    if settings.ocr_cache_dir:
        ocr = CachedOcr(ocr, Path(settings.ocr_cache_dir))

    create_index(client, index, settings.embed_dims, recreate=a.recreate)
    if a.replace_public:  # a re-index in service: chunks a new chunking no longer makes go too
        client.delete_by_query(index=index, body={"query": {"term": {"owner": PUBLIC}}},
                               refresh=True, request_timeout=300)  # fmt: skip
    t = time.perf_counter()
    stats = []
    for doc in load_corpus(a.data):
        s = ingest(doc, client, index, a.strategy, embedder, ocr)
        stats.append(s)
        print(f"{s.doc_id:34} {s.file_type:5} {s.chunks:5} chunks  parse {s.parse_s:6.1f}s  "
              f"embed {s.embed_s:6.1f}s  index {s.index_s:5.1f}s")  # fmt: skip
    client.indices.refresh(index=index)
    total = time.perf_counter() - t
    n = sum(s.chunks for s in stats)
    print(f"\n{len(stats)} documents, {n} chunks in {total:.0f}s ({len(stats) / total * 60:.1f} docs/min); "
          f"embedding tokens sent this run: {titan.input_tokens:,}")  # fmt: skip
    if a.stats:
        a.stats.write_text(json.dumps([asdict(s) for s in stats], indent=1))


if __name__ == "__main__":
    main()
