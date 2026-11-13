"""Pick the embedding model: title-to-article retrieval, within and across languages.

This is a development set for model selection, not the held-out evaluation set (the
brief requires that one to be untouched by tuning). It is built from the corpus:

- documents: every corpus document (no eval-truth rows; scans read through the OCR
  cache), cut by chunk.chunk_structure. The article / section title is removed from
  the chunk text, so a title query cannot simply match itself.
- queries: titles of Korean articles (제23조(해고 등의 제한) -> "해고 등의 제한") and US
  sections (§ 541.100 -> "General rule for executive employees"), only titles found
  in a single document (no "목적", "정의", "Definitions"), 80 per language, seeded.
  Each title is also translated (Qwen3-VL on Bedrock, in-region) for the cross-lingual
  sets: ko->ko, en->ko (English question, Korean article), en->en, ko->en.
- a hit: any chunk of the titled article / section in the top k.

Only models callable in the project Region (ap-southeast-2) without cross-Region
inference are compared. Titan returns its token counts, used to check
chunk.est_tokens. Embeddings and translations are cached under data/raw/bench/embed/.

    cd backend && AWS_PROFILE=sd-assignment uv run python ../eval/embed_bench.py
"""

import hashlib
import json
import random
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import boto3
import numpy as np
from botocore.config import Config

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "data" / "scripts"))
import fetch

from sdrag.ingest.chunk import chunk_structure, est_tokens
from sdrag.ingest.corpus import load_corpus
from sdrag.ingest.ocr import BedrockVisionOcr, CachedOcr
from sdrag.ingest.parse import parse

REGION = "ap-southeast-2"
OUT = fetch.DATA / "raw" / "bench" / "embed"
PER_LANG = 80
# chunks small enough for Cohere v3's 512-token input (p99 of real / estimated tokens
# is 1.6), so both models see the same, untruncated chunks
CHUNK_TOKENS = 350
TOP_K = 10
client = boto3.client(
    "bedrock-runtime",
    region_name=REGION,
    config=Config(retries={"max_attempts": 8, "mode": "adaptive"}, read_timeout=120),
)

RE_KO_TITLE = re.compile(r"^(?:부칙 )?제\d+조(?:의\d+)?\((.+)\)$")
RE_EN_TITLE = re.compile(r"^§ [\d.]+[a-z]? (.+)$")
RE_KO_HEAD = re.compile(r"^\s*(?:부\s*칙\s*)?제\s*\d+\s*조(?:\s*의\s*\d+)?\s*\([^)]*\)\s*")
RE_EN_HEAD = re.compile(r"^\s*§\s?[\d.]+[a-z]?\.?[^\n]*\n")


# ---------- corpus ----------


def load_chunks() -> list[dict]:
    ocr = CachedOcr(
        BedrockVisionOcr("qwen.qwen3-vl-235b-a22b", REGION), fetch.DATA / "raw" / "cache" / "ocr"
    )
    chunks = []
    for d in load_corpus(fetch.DATA):
        for c in chunk_structure(parse(d.path, ocr=ocr), d.id, max_tokens=CHUNK_TOKENS):
            body = RE_KO_HEAD.sub("", c.text) if d.lang == "ko" else RE_EN_HEAD.sub("", c.text)
            if body.strip():
                chunks.append(
                    {
                        "id": c.id,
                        "doc": d.id,
                        "lang": d.lang,
                        "heading": c.heading,
                        "text": body,
                    }
                )
    return chunks


def make_queries(chunks: list[dict]) -> list[dict]:
    """Unique titles -> (doc, heading) targets."""
    titles: dict[tuple[str, str], set[tuple[str, str]]] = {}
    for c in chunks:
        m = (RE_KO_TITLE if c["lang"] == "ko" else RE_EN_TITLE).match(c["heading"] or "")
        if m:
            titles.setdefault((c["lang"], m.group(1).strip()), set()).add((c["doc"], c["heading"]))
    picked = []
    for lang, minimum in (("ko", 5), ("en", 15)):
        pool = sorted(
            t for (lg, t), docs in titles.items()
            if lg == lang and len(docs) == 1 and len(t) >= minimum and "삭제" not in t
        )  # fmt: skip
        for t in random.Random(0).sample(pool, min(PER_LANG, len(pool))):
            doc, heading = next(iter(titles[(lang, t)]))
            picked.append({"lang": lang, "title": t, "doc": doc, "heading": heading})
    return picked


def translate(queries: list[dict]) -> None:
    """Add "translated" to each query (ko->en, en->ko) with Qwen3-VL, 40 per call."""
    path = OUT / "translations.json"
    cache = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    for lang, target in (("ko", "English"), ("en", "Korean")):
        todo = [q["title"] for q in queries if q["lang"] == lang and q["title"] not in cache]
        for i in range(0, len(todo), 40):
            batch = todo[i : i + 40]
            prompt = (
                f"Translate each line into {target} literally, as a title: add nothing. "
                "Return only a JSON array of strings, one per line, same order.\n\n"
                + "\n".join(batch)
            )
            r = client.converse(
                modelId="qwen.qwen3-vl-235b-a22b",
                messages=[{"role": "user", "content": [{"text": prompt}]}],
                inferenceConfig={"maxTokens": 4000, "temperature": 0},
            )
            text = r["output"]["message"]["content"][0]["text"]
            out = json.loads(text[text.index("[") : text.rindex("]") + 1])
            if len(out) != len(batch):
                raise RuntimeError(f"translation returned {len(out)} lines for {len(batch)}")
            cache.update(zip(batch, out))
    OUT.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    for q in queries:
        q["translated"] = cache[q["title"]]


# ---------- models ----------


def _body(r) -> dict:
    return json.loads(r["body"].read())


def cohere_v3(texts: list[str], kind: str) -> tuple[list[list[float]], list[int | None]]:
    vecs = []
    for i in range(0, len(texts), 96):  # API limit: 96 texts per call
        r = client.invoke_model(
            modelId="cohere.embed-multilingual-v3",
            body=json.dumps(
                {
                    "texts": texts[i : i + 96],
                    "input_type": "search_query" if kind == "query" else "search_document",
                    "truncate": "END",  # 512-token limit: cut the end instead of failing
                }
            ),
        )
        vecs += _body(r)["embeddings"]
    return vecs, [None] * len(texts)


def titan_v2(texts: list[str], kind: str) -> tuple[list[list[float]], list[int | None]]:
    def one(t):
        r = client.invoke_model(
            modelId="amazon.titan-embed-text-v2:0",
            body=json.dumps({"inputText": t, "dimensions": 1024, "normalize": True}),
        )
        b = _body(r)
        return b["embedding"], b["inputTextTokenCount"]

    with ThreadPoolExecutor(8) as pool:
        res = list(pool.map(one, texts))
    return [v for v, _ in res], [n for _, n in res]


MODELS = {"cohere-multilingual-v3": cohere_v3, "titan-text-v2": titan_v2}


def embed(model: str, texts: list[str], kind: str) -> tuple[np.ndarray, list]:
    key = hashlib.sha256(("\n\x00".join(texts) + kind).encode()).hexdigest()[:16]
    path = OUT / f"{model}-{kind}-{key}.json"
    if path.exists():
        cached = json.loads(path.read_text())
        vecs, tokens = cached["vecs"], cached["tokens"]
    else:
        vecs, tokens = MODELS[model](texts, kind)
        OUT.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"vecs": vecs, "tokens": tokens}))
    m = np.asarray(vecs, dtype=np.float32)
    return m / np.linalg.norm(m, axis=1, keepdims=True), tokens


# ---------- scoring ----------


def evaluate(model: str, chunks: list[dict], queries: list[dict]) -> dict:
    docs, tokens = embed(model, [c["text"] for c in chunks], "document")
    sets = {}
    for qlang in ("ko", "en"):
        for doclang in ("ko", "en"):
            qs = [q for q in queries if q["lang"] == doclang]
            texts = [q["title"] if qlang == doclang else q["translated"] for q in qs]
            qv, _ = embed(model, texts, "query")
            sims = qv @ docs.T
            # "filtered": search only chunks in the answer's language, i.e. what a
            # per-language search would find (tests the query-language bias)
            in_lang = np.array([c["lang"] == doclang for c in chunks])
            for mode, s in (("all", sims), ("filtered", np.where(in_lang, sims, -np.inf))):
                ranks = np.argsort(-s, axis=1)[:, :TOP_K]
                r1 = r10 = mrr = 0.0
                for q, row in zip(qs, ranks):
                    hits = [
                        k
                        for k, i in enumerate(row)
                        if (chunks[i]["doc"], chunks[i]["heading"]) == (q["doc"], q["heading"])
                    ]
                    if hits:
                        r10 += 1
                        r1 += hits[0] == 0
                        mrr += 1 / (hits[0] + 1)
                n = len(qs)
                sets[(mode, f"{qlang}->{doclang}")] = (r1 / n, r10 / n, mrr / n)
    return {"sets": sets, "tokens": tokens}


SETS = ("ko->ko", "ko->en", "en->ko", "en->en")  # query language -> answer language


def main() -> None:
    chunks = load_chunks()
    queries = make_queries(chunks)
    translate(queries)
    print(f"{len(chunks)} chunks, {len(queries)} queries "
          f"({sum(q['lang'] == 'ko' for q in queries)} ko / {sum(q['lang'] == 'en' for q in queries)} en titles)")  # fmt: skip
    results = {model: evaluate(model, chunks, queries) for model in MODELS}
    for mode, label in (("all", "whole corpus"), ("filtered", "answer-language chunks only")):
        print(f"\n== {label}")
        print(f"{'model':24}" + "".join(f"{s:>22}" for s in SETS))
        print(f"{'':24}" + f"{'R@1 / R@10 / MRR':>22}" * len(SETS))
        for model, res in results.items():
            cells = "".join(
                "{:6.1%} /{:6.1%} /{:5.2f}  ".format(*res["sets"][(mode, s)]) for s in SETS
            )
            print(f"{model:24}{cells}")
    titan_tokens = results["titan-text-v2"]["tokens"]
    if titan_tokens:
        print("\nest_tokens vs Titan's token count (ratio actual / estimate):")
        for lang in ("ko", "en"):
            pairs = [
                (n, est_tokens(c["text"]))
                for c, n in zip(chunks, titan_tokens)
                if c["lang"] == lang
            ]
            ratios = sorted(n / e for n, e in pairs if e)
            print(f"  {lang}: median {ratios[len(ratios) // 2]:.2f}  p90 {ratios[len(ratios) * 9 // 10]:.2f}  "
                  f"max {ratios[-1]:.2f}  chunks over 512 real tokens: {sum(n > 512 for n, _ in pairs)}/{len(pairs)}")  # fmt: skip


if __name__ == "__main__":
    main()
