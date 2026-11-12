"""Run retrieval systems over an evaluation set and score them.

For every (system, question): the top 20 chunks (id, document, range, heading, page),
the latency, and the scores of evalset.score. Raw per-question output goes to
<out>/<system>.jsonl (the brief asks for it), the summary to <out>/summary.md and
summary.json, broken down by question -> answer language, answer file type and
question kind.

Systems are named <mode>[+rerank]@<index>, e.g. hybrid@chunks-structure or
bilingual+rerank@chunks-structure; modes are the Searcher methods (bm25, dense,
hybrid, per_language, bilingual) and agent (sdrag.agent). "+rerank" reorders the first stage's top 20 with
the LLM reranker. --llm picks the model for reranking and translation.

Cost per query: tokens actually sent, at list prices (PRICES; US on-demand list
prices from third-party trackers, 2026-11-12: Sydney may be somewhat higher).

Latency is measured end to end from this process against the local OpenSearch, so
it includes the query embedding call to Bedrock (no embedding cache here, so every
system pays its own call, as a deployed service would).

    cd backend && AWS_PROFILE=sd-assignment uv run python ../eval/run_retrieval.py \\
        --set ../data/eval/dev.jsonl --systems bm25@chunks-structure hybrid@chunks-structure
"""

import argparse
import json
import statistics
import time
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path

from evalset import doc_texts, load_items, score
from opensearchpy import OpenSearch

from sdrag.agent.search import SearchAgent, corpus_documents
from sdrag.common.config import settings
from sdrag.common.llm import BedrockChat
from sdrag.ingest.corpus import load_corpus
from sdrag.retrieval.embed import TitanEmbedder
from sdrag.retrieval.rerank import LlmReranker, LlmTranslator
from sdrag.retrieval.search import Searcher

DEPTH = 20
# USD per 1M tokens (input, output)
PRICES = {
    "amazon.titan-embed-text-v2:0": (0.02, 0.0),
    "zai.glm-4.7": (0.60, 2.20),
    "openai.gpt-oss-120b-1:0": (0.15, 0.60),
    "qwen.qwen3-next-80b-a3b": (0.15, 1.20),
}


class Meter:
    """Token totals of the embedder and the LLM, read before and after each query."""

    def __init__(self, embedder, chat):
        self.embedder, self.chat = embedder, chat

    def read(self) -> tuple[int, int, int]:
        return self.embedder.input_tokens, self.chat.input_tokens, self.chat.output_tokens

    def cost(self, d: tuple[int, int, int]) -> float:
        e_in = PRICES[self.embedder.model_id][0]
        c_in, c_out = PRICES.get(self.chat.model_id, (0.0, 0.0))
        return (d[0] * e_in + d[1] * c_in + d[2] * c_out) / 1e6


def run_system(system: str, items, client, embedder, chat) -> list[dict]:
    spec, index = system.split("@")
    mode, _, stage2 = spec.partition("+")
    s = Searcher(client, index, embedder, LlmTranslator(chat))
    reranker = LlmReranker(chat) if stage2 == "rerank" else None
    agent = None
    if mode == "agent":
        docs = corpus_documents(load_corpus(Path(__file__).resolve().parents[1] / "data"))
        agent = SearchAgent(chat.client, chat.model_id, s, docs)
    meter = Meter(embedder, chat)
    rows = []
    for it in items:
        before = meter.read()
        t = time.perf_counter()
        steps = None
        if agent:
            res = agent.run(it.question)
            hits, steps = res.hits[:DEPTH], res.steps
            chat.input_tokens += res.input_tokens  # the agent calls Converse itself
            chat.output_tokens += res.output_tokens
        else:
            hits = getattr(s, mode)(it.question, size=DEPTH)
        if reranker:
            hits = reranker.rerank(it.question, hits)
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
            "embed_tokens": used[0], "llm_tokens": [used[1], used[2]],
            "cost_usd": meter.cost(used),
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
    ap.add_argument("--systems", nargs="+", required=True)
    ap.add_argument("--out", type=Path, help="default: ../data/eval/results/<set name>")
    ap.add_argument("--llm", default="zai.glm-4.7", help="reranker and translator model")
    a = ap.parse_args()
    items = load_items(a.set)
    texts = doc_texts()
    out = a.out or a.set.parent / "results" / a.set.stem
    out.mkdir(parents=True, exist_ok=True)
    client = OpenSearch(hosts=[settings.opensearch_url], timeout=60)
    embedder = TitanEmbedder(settings.embed_model, settings.aws_region, settings.embed_dims)
    chat = BedrockChat(a.llm, settings.aws_region)
    for system in a.systems:
        rows = run_system(system, items, client, embedder, chat)
        uses_llm = "+rerank" in system or system.startswith(("bilingual", "agent"))
        label = f"{system}~{a.llm.split('.', 1)[1]}" if uses_llm else system  # e.g. ~glm-4
        (out / f"{label}.jsonl").write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), "utf-8"
        )
        print(f"{label}: done ({len(rows)} questions)")
    # the summary covers every system run on this set so far, not only this run's
    results = {
        p.stem: [json.loads(x) for x in p.read_text("utf-8").splitlines() if x]
        for p in sorted(out.glob("*.jsonl"))
    }
    summary = summarize(results, items, texts)
    (out / "summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), "utf-8")
    (out / "summary.md").write_text(to_markdown(summary), "utf-8")
    print(to_markdown({s: {"all=all": v["all=all"]} for s, v in summary.items()}))


if __name__ == "__main__":
    main()
