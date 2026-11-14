"""Run retrieval systems over an evaluation set and score them.

For every (system, question): the top 20 chunks (id, document, range, heading, page),
the latency, and the scores of evalset.score. Raw per-question output goes to
<out>/<system>.jsonl (the brief asks for it), the summary to <out>/summary.md and
summary.json, broken down by question -> answer language, answer file type and
question kind.

Systems are named <mode>[+rerank][+jur]@<index>, e.g. hybrid@chunks-structure or
wide+rerank+jur@chunks-structure (served); modes are the Searcher methods (bm25,
dense, hybrid, per_language, bilingual, bilingual_union, bilingual_union_dense, wide) and
agent (sdrag.agent).
"+rerank" reorders the first stage's candidates with the LLM reranker (20 for most modes,
30 for bilingual_union, about 50 for wide); "+jur" first asks
which country's law the question is about and searches only that country's statutes
(retrieval/jurisdiction.py, as served). --llm picks the model for these LLM steps.

Cost per query: tokens actually sent, at list prices (PRICES; US on-demand list
prices from third-party trackers, 2026-11-12: Sydney may be somewhat higher).

Latency is measured end to end from this process against the local OpenSearch, so
it includes the query embedding call to Bedrock (no embedding cache here, so every
system pays its own call, as a deployed service would).

    cd backend && AWS_PROFILE=<profile> uv run python ../eval/run_retrieval.py \\
        --set ../data/eval/dev.jsonl --systems bm25@chunks-structure hybrid@chunks-structure
"""

import argparse
import json
import statistics
import time
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path

from evalset import LLM_CACHE, doc_texts, load_items, score
from opensearchpy import OpenSearch

from sdrag.agent.search import SearchAgent
from sdrag.common.config import settings
from sdrag.common.llm import BedrockChat, CachedChat
from sdrag.retrieval.embed import TitanEmbedder
from sdrag.retrieval.index import PUBLIC, list_documents
from sdrag.retrieval.jurisdiction import jurisdiction
from sdrag.retrieval.rerank import LlmReranker, LlmTranslator
from sdrag.retrieval.search import Searcher

DEPTH = 20
# USD per 1M tokens (input, output)
PRICES = {
    "amazon.titan-embed-text-v2:0": (0.02, 0.0),
    # ap-southeast-2 on-demand list prices, AWS Price List API, 2026-11-14
    "zai.glm-4.7": (0.62, 2.27),
    "zai.glm-5": (1.03, 3.30),
    "deepseek.v3.2": (0.64, 1.91),
    "openai.gpt-oss-120b-1:0": (0.155, 0.62),
    "qwen.qwen3-next-80b-a3b": (0.15, 1.20),
    "qwen.qwen3-235b-a22b-2507-v1:0": (0.22, 0.88),  # not in the price list: estimate
}


class Meter:
    """Token totals of the embedder and the LLMs, read before and after each query.
    The cost is priced per model; `read` reports the first chat's tokens."""

    def __init__(self, embedder, chat, *more):
        self.embedder, self.chats = embedder, [chat, *more]
        self.chat = chat

    def read(self) -> tuple[int, ...]:
        toks = [self.embedder.input_tokens]
        for c in self.chats:
            toks += [c.input_tokens, c.output_tokens]
        return tuple(toks)

    def cost(self, d: tuple[int, ...]) -> float:
        e_in = PRICES[self.embedder.model_id][0]
        total = d[0] * e_in
        for i, c in enumerate(self.chats):
            c_in, c_out = PRICES.get(c.model_id, (0.0, 0.0))
            total += d[1 + 2 * i] * c_in + d[2 + 2 * i] * c_out
        return total / 1e6


def run_system(system: str, items, client, embedder, chat, rerank_chat=None,
               aux_chat=None) -> list[dict]:  # fmt: skip
    """rerank_chat: the reranker's model when it is not `chat`'s; aux_chat: the chat
    for translation, jurisdiction and statute terms (a cached one keeps them the same
    across runs that compare rerankers)."""
    aux = aux_chat or chat
    spec, index = system.split("@")
    mode, *stages = spec.split("+")
    # the public corpus only: user uploads in the same index must not change the scores
    s = Searcher(client, index, embedder, LlmTranslator(aux), owners=[PUBLIC])
    reranker = LlmReranker(rerank_chat or chat) if "rerank" in stages else None
    by_country = "jur" in stages  # the served filter: the question's country only
    agent = None
    if mode == "agent":
        docs = list_documents(client, index, [PUBLIC])
        agent = SearchAgent(chat.client, chat.model_id, s, docs)
    meters = [chat] + ([rerank_chat] if rerank_chat else [])
    meter = Meter(embedder, *meters)
    rows = []
    for it in items:
        before = meter.read()
        t = time.perf_counter()
        steps = None
        country = s.country = jurisdiction(aux, it.question) if by_country else None
        if agent:
            res = agent.run(it.question)
            hits, steps = res.hits[:DEPTH], res.steps
            chat.input_tokens += res.input_tokens  # the agent calls Converse itself
            chat.output_tokens += res.output_tokens
        elif mode[9:10].isdigit():  # bilingual0.5: translation weight 0.5
            hits = s.bilingual(it.question, size=DEPTH, translation_weight=float(mode[9:]))
        else:
            hits = getattr(s, mode)(it.question, size=DEPTH)
        if reranker:
            hits = reranker.rerank(it.question, hits, s.last_queries or None)
            s.last_queries = []
        ms = 1000 * (time.perf_counter() - t)
        used = tuple(a - b for a, b in zip(meter.read(), before, strict=True))
        retrieved = [
            {k: h.source.get(k) for k in ("doc_id", "start", "end", "heading", "page_start")}
            | {"chunk_id": h.chunk_id}
            for h in hits
        ]
        sc = score(retrieved, it.gold, it.also)
        rows.append({
            "qid": it.qid, "question": it.question, "latency_ms": round(ms, 1),
            "embed_tokens": used[0], "llm_tokens": list(used[1:]),
            "cost_usd": meter.cost(used),
            **({"country": country} if by_country else {}),
            "scores": asdict(sc), "retrieved": retrieved,
        } | ({"agent_steps": steps} if steps is not None else {}))  # fmt: skip
    return rows


def groups(it, texts) -> dict[str, str]:
    """The report's breakdowns: question -> answer language, file type, kind."""
    a_langs = "+".join(sorted(it.answer_langs(texts)))
    ftypes = "+".join(sorted(it.file_types(texts)))
    return {"all": "all", "lang": f"{it.q_lang}->{a_langs}", "file_type": ftypes,
            "kind": it.kind}  # fmt: skip


METRICS = [("span_hit", 1), ("span_hit", 5), ("span_hit", 10), ("span_recall", 10),
           ("span_mrr", None), ("span_ndcg10", None), ("doc_hit", 10)]  # fmt: skip


def metric(row: dict, name: str, k) -> float:
    v = row["scores"][name]
    if k is None:
        return v
    return v[k] if k in v else v[str(k)]  # int keys in memory, str keys after JSON


def summarize(results: dict[str, list[dict]], items, texts) -> dict:
    by_q = {it.qid: groups(it, texts) for it in items}
    out: dict = {}
    for system, rows in results.items():
        cells: dict[tuple, list[dict]] = defaultdict(list)
        for r in rows:
            for g, v in by_q[r["qid"]].items():
                cells[(g, v)].append(r)
        out[system] = {
            f"{g}={v}": {
                "n": len(rs),
                **{f"{m}@{k}" if k else m: round(statistics.mean(metric(r, m, k) for r in rs), 4)
                   for m, k in METRICS},
                "latency_ms_p50": round(statistics.median(r["latency_ms"] for r in rs), 1),
                "latency_ms_p95": round(sorted(r["latency_ms"] for r in rs)[int(0.95 * (len(rs) - 1))], 1),
                "cost_usd_per_query": statistics.mean(r["cost_usd"] for r in rs),
            }
            for (g, v), rs in sorted(cells.items())
        }  # fmt: skip
    return out


def to_markdown(summary: dict) -> str:
    cols = [f"{m}@{k}" if k else m for m, k in METRICS]
    lines = []
    keys = sorted({c for s in summary.values() for c in s}, key=lambda c: (c != "all=all", c))
    for cell in keys:
        lines.append(f"\n### {cell}\n")
        lines.append("| system | n | " + " | ".join(cols) + " | p50 ms | p95 ms |")
        lines.append("|---" * (len(cols) + 4) + "|")
        for system, s in summary.items():
            if cell in s:
                c = s[cell]
                lines.append(f"| {system} | {c['n']} | " + " | ".join(f"{c[x]:.3f}" for x in cols)
                             + f" | {c['latency_ms_p50']:.0f} | {c['latency_ms_p95']:.0f} |")  # fmt: skip
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", type=Path, required=True)
    ap.add_argument("--systems", nargs="*", default=[], help="none: only rebuild the summary")
    ap.add_argument(
        "--out", type=Path, help="default: ../data/eval/results/retrieval-70docs/<set name>"
    )
    ap.add_argument("--llm", default="zai.glm-4.7", help="reranker and translator model")
    ap.add_argument("--rerank-llm", help="another model for the reranker only (labels ~rr-<model>)")
    ap.add_argument("--cache-aux", action="store_true",
                    help="cache translation, jurisdiction and statute-terms replies (LLM_CACHE), "
                         "so runs comparing rerankers share them")  # fmt: skip
    a = ap.parse_args()
    items = load_items(a.set)
    texts = doc_texts()
    out = a.out or a.set.parent / "results" / "retrieval-70docs" / a.set.stem
    out.mkdir(parents=True, exist_ok=True)
    client = OpenSearch(hosts=[settings.opensearch_url], timeout=60)
    embedder = TitanEmbedder(settings.embed_model, settings.aws_region, settings.embed_dims)
    chat = BedrockChat(a.llm, settings.aws_region)
    aux = CachedChat(chat, LLM_CACHE) if a.cache_aux else None
    rerank_chat = BedrockChat(a.rerank_llm, settings.aws_region) if a.rerank_llm else None
    for system in a.systems:
        rows = run_system(system, items, client, embedder, chat, rerank_chat, aux)
        uses_llm = "+rerank" in system or system.startswith(("bilingual", "agent"))
        label = f"{system}~{a.llm.split('.', 1)[1]}" if uses_llm else system  # e.g. ~glm-4
        if rerank_chat and "+rerank" in system:
            label += f"~rr-{a.rerank_llm.split('.', 1)[1].split(':')[0]}"
        (out / f"{label}.jsonl").write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), "utf-8"
        )
        print(f"{label}: done ({len(rows)} questions)")
    # the summary covers every system run on this set so far, not only this run's
    results = {
        p.stem: [json.loads(x) for x in p.read_text("utf-8").splitlines() if x]
        for p in sorted(out.glob("*.jsonl"))
    }
    results = {k: v for k, v in results.items() if v}  # an interrupted run leaves an empty file
    summary = summarize(results, items, texts)
    (out / "summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), "utf-8")
    (out / "summary.md").write_text(to_markdown(summary), "utf-8")
    print(to_markdown({s: {"all=all": v["all=all"]} for s, v in summary.items()}))


if __name__ == "__main__":
    main()
