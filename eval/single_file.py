"""The brief's target: on one file, retrieve as well as Claude and ChatGPT do.

Three steps:

1. ``select``: 30 test items whose gold is in one document, spread over answer language,
   file type and question language (seeded). Writes data/eval/single_file/compare.csv
   with the file to upload, the question and the reference answer.
2. ``ours``: our system with the search scoped to that file (as a user who uploaded
   it and asks about it): answer and whether the gold span is in the top 6 sources.
   Fills the ``ours`` column.
3. (by hand) upload the file to Claude and to ChatGPT, ask the question, paste the
   answers into the ``claude`` and ``chatgpt`` columns (docs: data/eval/single_file/README.md).
4. ``grade``: a judge model from a third family grades every answer against the
   reference answer and the gold text (JUDGE_SYSTEM, disclosed), the same way for all
   three; writes grades.json and prints accuracy per system.

    cd backend && AWS_PROFILE=... uv run python ../eval/single_file.py select|ours|grade
"""

import csv
import json
import random
import sys
from collections import Counter

from evalset import DATA, doc_texts, load_items, overlaps

from sdrag.agent.answer import answer
from sdrag.common.config import settings
from sdrag.common.llm import BedrockChat, CachedChat, parse_json
from sdrag.common.search_client import make_client
from sdrag.ingest.corpus import load_corpus
from sdrag.retrieval.embed import TitanEmbedder
from sdrag.retrieval.index import PUBLIC
from sdrag.retrieval.rerank import LlmReranker, LlmTranslator
from sdrag.retrieval.search import Searcher

OUT = DATA / "eval" / "single_file"
CSV = OUT / "compare.csv"
N, SEED = 30, 20261112
FIELDS = ["qid", "file", "pages", "q_lang", "file_type", "question", "reference", "gold_quote",
          "ours", "ours_gold_in_sources", "claude", "chatgpt"]  # fmt: skip
JUDGE_MODEL = "deepseek.v3.2"  # not the answer model (GLM) nor the question writer (Qwen)

JUDGE_SYSTEM = """You grade answers to questions about Korean and US labor law documents.
Given the question, the reference answer, the passage it comes from, and a candidate answer, decide:
- "correct": the candidate states the same key fact as the reference (number, period, condition, procedure); extra correct detail is fine.
- "partial": it states part of it, or the right fact with a wrong condition.
- "wrong": it states something else, or contradicts the reference.
- "no_answer": it says it cannot find the answer, or answers nothing.
Judge the content, not the language or style.
Return only JSON: {"grade": "correct" | "partial" | "wrong" | "no_answer", "why": "<one sentence>"}"""


def select() -> None:
    texts = doc_texts()
    items = [i for i in load_items(DATA / "eval" / "test.jsonl")
             if len({g.doc_id for g in i.gold}) == 1 and i.kind in ("fact", "table")]  # fmt: skip
    rng = random.Random(SEED)
    rng.shuffle(items)
    # round-robin over (file type, question language) so every cell is represented
    cells: dict[tuple, list] = {}
    for it in items:
        cells.setdefault((texts[it.gold[0].doc_id].file_type, it.q_lang), []).append(it)
    chosen, used_docs = [], Counter()
    while len(chosen) < N and any(cells.values()):
        for key in sorted(cells):
            pool = cells[key]
            # prefer documents not chosen yet, so the files to upload vary
            pool.sort(key=lambda i: used_docs[i.gold[0].doc_id])
            if pool and len(chosen) < N:
                it = pool.pop(0)
                chosen.append(it)
                used_docs[it.gold[0].doc_id] += 1
    paths = {d.id: d.path for d in load_corpus(DATA)}
    OUT.mkdir(parents=True, exist_ok=True)
    with CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for it in sorted(chosen, key=lambda i: i.qid):
            g = it.gold[0]
            d = texts[g.doc_id]
            b = d.block_at(g.start)
            w.writerow({"qid": it.qid, "file": str(paths[g.doc_id].relative_to(DATA.parent)),
                        "pages": b.page or "", "q_lang": it.q_lang, "file_type": d.file_type,
                        "question": it.question,
                        "reference": it.meta.get("check_answer") or it.meta.get("answer", ""),
                        "gold_quote": g.quote})  # fmt: skip
    print(f"{len(chosen)} items, {len(used_docs)} files -> {CSV}")
    print(Counter((texts[i.gold[0].doc_id].file_type, i.q_lang) for i in chosen))


def ours() -> None:
    rows = list(csv.DictReader(CSV.open(encoding="utf-8")))
    items = {i.qid: i for i in load_items(DATA / "eval" / "test.jsonl")}
    client = make_client(settings.opensearch_url, settings.aws_region)
    emb = TitanEmbedder(settings.embed_model, settings.aws_region, settings.embed_dims)
    chat = BedrockChat(settings.llm_model, settings.aws_region)
    for r in rows:
        it = items[r["qid"]]
        s = Searcher(client, settings.index, emb, LlmTranslator(chat), owners=[PUBLIC],
                     scope=[it.gold[0].doc_id])  # fmt: skip
        hits = LlmReranker(chat).rerank(it.question, s.bilingual_union(it.question, 20, 10))
        sources = hits[:6]
        r["ours"] = answer(chat, it.question, sources).text
        found = any(overlaps(h.source, g) for h in sources for g in [*it.gold, *it.also])
        r["ours_gold_in_sources"] = "yes" if found else "no"
        print(r["qid"], r["ours_gold_in_sources"], r["ours"][:80].replace("\n", " "))
    with CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)


def grade() -> None:
    rows = list(csv.DictReader(CSV.open(encoding="utf-8")))
    judge = CachedChat(
        BedrockChat(JUDGE_MODEL, settings.aws_region), DATA / "raw" / "eval-cache" / "llm"
    )
    grades, tally = [], {s: Counter() for s in ("ours", "claude", "chatgpt")}
    for r in rows:
        for system, counts in tally.items():
            if not r.get(system, "").strip():
                continue
            user = (f"Question: {r['question']}\nReference answer: {r['reference']}\n"
                    f"Passage: {r['gold_quote']}\n\nCandidate answer: {r[system]}")  # fmt: skip
            out = parse_json(judge.complete(JUDGE_SYSTEM, user, max_tokens=300).text) or {}
            g = out.get("grade", "unparsed")
            counts[g] += 1
            grades.append(
                {"qid": r["qid"], "system": system, "grade": g, "why": out.get("why", "")}
            )
    (OUT / "grades.json").write_text(json.dumps(grades, ensure_ascii=False, indent=1), "utf-8")
    for system, c in tally.items():
        n = sum(c.values())
        if n:
            print(f"{system:8} n={n:3}  correct {c['correct'] / n:.0%}  partial {c['partial'] / n:.0%}  "
                  f"wrong {c['wrong'] / n:.0%}  no answer {c['no_answer'] / n:.0%}")  # fmt: skip


if __name__ == "__main__":
    {"select": select, "ours": ours, "grade": grade}[sys.argv[1]]()
