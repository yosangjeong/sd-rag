"""Smoke test of the local index: a few questions through every retrieval mode.

Not an evaluation (the held-out set is separate): it shows that each mode returns
sensible sources (document, heading, page) and how long a query takes.

    cd backend && AWS_PROFILE=sd-assignment SDRAG_EMBED_CACHE_DIR=../data/raw/embed-cache \\
        uv run python ../eval/search_smoke.py [--index chunks-structure]
"""

import argparse
import time
from pathlib import Path

from opensearchpy import OpenSearch

from sdrag.common.config import settings
from sdrag.retrieval.embed import CachedEmbedder, TitanEmbedder
from sdrag.retrieval.search import Searcher

QUESTIONS = [
    "근로자를 해고하려면 며칠 전에 예고해야 하나요?",  # ko -> ko (근로기준법 제26조)
    "How many days' notice must an employer give before dismissing a worker in Korea?",  # en -> ko
    "연장근로 수당은 통상임금의 몇 배인가요?",  # ko -> ko, and the US FLSA overtime rule (ko -> en)
    "What is the minimum wage for federal contracts in 2027?",  # en -> en (scanned FR notice)
    "미국 연방 계약 최저임금은 얼마인가요?",  # ko -> en (scanned FR notice)
    "체불 임금등 융자 신청",  # ko, the statute whose OCR reads 융자 as 용자
]


def show(hits) -> str:
    out = []
    for h in hits[:3]:
        s = h.source
        where = f"p{s['page_start']}" if s.get("page_start") else ""
        out.append(f"{s['doc_id']} {s['heading'] or ''} {where}".strip())
    return " | ".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", default="chunks-structure")
    a = ap.parse_args()
    emb = TitanEmbedder(settings.embed_model, settings.aws_region, settings.embed_dims)
    if settings.embed_cache_dir:
        emb = CachedEmbedder(emb, Path(settings.embed_cache_dir))
    s = Searcher(OpenSearch(hosts=[settings.opensearch_url]), a.index, emb)
    for q in QUESTIONS:
        print(f"\nQ: {q}")
        for mode in ("bm25", "dense", "hybrid", "per_language"):
            t = time.perf_counter()
            hits = getattr(s, mode)(q)
            print(f"  {mode:13} {1000 * (time.perf_counter() - t):5.0f} ms  {show(hits)}")


if __name__ == "__main__":
    main()
