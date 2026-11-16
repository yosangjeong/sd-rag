"""The brief's target: on one file, retrieve as well as Claude and ChatGPT do.

Three steps:

1. ``select``: 30 labor test items whose gold is in one document, spread over file
   type and question language (seeded); ``select-re`` appends 20 real-estate test items
   chosen the same way (the 30 stay as they were). Writes data/eval/single_file/compare.csv
   with the file to upload (the committed copy in data/corpus/), the question and the
   reference answer.
2. ``ours``: our system with the search scoped to that file (as a user who uploaded
   it and asks about it): answer and whether the gold span is in the top 6 sources.
   Fills the ``ours`` column.
3. (by hand) upload the file to Claude and to ChatGPT, ask the question, paste the
   answers into the ``claude`` and ``chatgpt`` columns (docs: data/eval/single_file/README.md).
4. ``grade``: a judge model from a third family grades every answer against the
   reference answer and the gold text (eval/judges.py, disclosed), the same way for all
   three; writes grades.json and prints accuracy per system.

    cd backend && AWS_PROFILE=... uv run python ../eval/single_file.py select|ours|grade
"""

import csv
import json
import random
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

from evalset import DATA, LLM_CACHE, doc_texts, load_items, overlaps
from judges import correct_prompt, correct_user, wide_passage

from sdrag.agent.answer import answer
from sdrag.common.config import settings
from sdrag.common.llm import BedrockChat, CachedChat, parse_json
from sdrag.common.search_client import make_client
from sdrag.ingest.corpus import corpus_path, load_corpus
from sdrag.retrieval.embed import TitanEmbedder
from sdrag.retrieval.index import PUBLIC
from sdrag.retrieval.rerank import LlmReranker, LlmTranslator
from sdrag.retrieval.search import Searcher

OUT = DATA / "eval" / "single_file"
CSV = OUT / "compare.csv"
N, N_RE, SEED = 30, 20, 20261112
FIELDS = ["qid", "file", "pages", "q_lang", "file_type", "question", "reference", "gold_quote",
          "ours", "ours_gold_in_sources", "claude", "chatgpt"]  # fmt: skip
JUDGE_MODEL = "deepseek.v3.2"  # not the answer model (GLM) nor the question writer (Qwen)

# the correctness judge: eval/judges.py, the same text answers.py uses


def upload_file(doc_id: str) -> str:
    """The file a tester uploads: the committed copy (data/corpus/), so the path holds
    in any clone and does not move with data/raw/."""
    d = next(d for d in load_corpus(DATA) if d.id == doc_id)
    return str(corpus_path(DATA, d.id, d.file_type, d.tags, packed=True).relative_to(DATA.parent))


def pick(set_file: str, n: int) -> list:
    """n single-document items, round-robin over (file type, question language)."""
    texts = doc_texts()
    items = [i for i in load_items(DATA / "eval" / set_file)
             if len({g.doc_id for g in i.gold}) == 1 and i.kind in ("fact", "table")]  # fmt: skip
    rng = random.Random(SEED)
    rng.shuffle(items)
    # round-robin over (file type, question language) so every cell is represented
    cells: dict[tuple, list] = {}
    for it in items:
        cells.setdefault((texts[it.gold[0].doc_id].file_type, it.q_lang), []).append(it)
    chosen, used_docs = [], Counter()
    while len(chosen) < n and any(cells.values()):
        for key in sorted(cells):
            pool = cells[key]
            # prefer documents not chosen yet, so the files to upload vary
            pool.sort(key=lambda i: used_docs[i.gold[0].doc_id])
            if pool and len(chosen) < n:
                it = pool.pop(0)
                chosen.append(it)
                used_docs[it.gold[0].doc_id] += 1
    rows = []
    for it in sorted(chosen, key=lambda i: i.qid):
        g = it.gold[0]
        d = texts[g.doc_id]
        b = d.block_at(g.start)
        rows.append({"qid": it.qid, "file": upload_file(g.doc_id),
                     "pages": b.page or "", "q_lang": it.q_lang, "file_type": d.file_type,
                     "question": it.question,
                     "reference": it.meta.get("check_answer") or it.meta.get("answer", ""),
                     "gold_quote": g.quote})  # fmt: skip
    print(f"{len(chosen)} items, {len(used_docs)} files")
    print(Counter((texts[i.gold[0].doc_id].file_type, i.q_lang) for i in chosen))
    return rows


def write(rows: list[dict]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)


def select() -> None:
    write(pick("test.jsonl", N))


def select_re() -> None:
    """Append the real-estate items, keep the labor rows; answers already filled in
    (ours, claude, chatgpt) are kept for every item chosen again. File paths are
    refreshed to the committed copies."""
    rows = list(csv.DictReader(CSV.open(encoding="utf-8")))
    filled = {r["qid"]: r for r in rows}
    rows = [r | {"file": upload_file(load_doc_id(r))} for r in rows if not r["qid"].startswith("r")]
    keep = ("ours", "ours_gold_in_sources", "claude", "chatgpt")
    new = [r | {k: filled[r["qid"]][k] for k in keep if k in filled.get(r["qid"], {})}
           for r in pick("test_re.jsonl", N_RE)]  # fmt: skip
    write(rows + new)


def load_doc_id(row: dict) -> str:
    items = {
        i.qid: i for s in ("test.jsonl", "test_re.jsonl") for i in load_items(DATA / "eval" / s)
    }
    return items[row["qid"]].gold[0].doc_id


def ours() -> None:
    rows = list(csv.DictReader(CSV.open(encoding="utf-8")))
    items = {
        i.qid: i for s in ("test.jsonl", "test_re.jsonl") for i in load_items(DATA / "eval" / s)
    }
    client = make_client(settings.opensearch_url, settings.aws_region)
    emb = TitanEmbedder(settings.embed_model, settings.aws_region, settings.embed_dims)
    chat = BedrockChat(settings.llm_model, settings.aws_region)
    for r in rows:
        if r.get("ours", "").strip():  # answered in an earlier run
            continue
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
    """Grade every filled answer with both judge versions (v1 for comparison with
    earlier reports, v2 the one reported), and with and without the flagged items."""
    rows = list(csv.DictReader(CSV.open(encoding="utf-8")))
    judge = CachedChat(BedrockChat(JUDGE_MODEL, settings.aws_region), LLM_CACHE)
    flags = json.loads((DATA / "eval" / "item_flags.json").read_text("utf-8"))["flags"]
    systems = ("ours", "claude", "chatgpt")
    grades = []
    for r in rows:
        field = "real-estate" if r["qid"].startswith("r") else "labor"
        for system in systems:
            if not r.get(system, "").strip():
                continue
            user = correct_user(r["question"], r["reference"], r["gold_quote"], r[system])
            row = {"qid": r["qid"], "field": field, "system": system, "flagged": r["qid"] in flags}
            for v in (1, 2):
                tokens = 300 if v == 1 else 400  # v1 as it ran (its cache key holds this)
                reply = judge.complete(correct_prompt(field, v), user, max_tokens=tokens)
                out = parse_json(reply.text) or {}
                row[f"v{v}"] = {"grade": out.get("grade", "unparsed"), "why": out.get("why", "")}
            grades.append(row)
    (OUT / "grades.json").write_text(json.dumps(grades, ensure_ascii=False, indent=1), "utf-8")
    for field in ("labor", "real-estate"):
        for system in systems:
            for v, skip in (("v1", False), ("v2", False), ("v2", True)):
                sel = [g for g in grades if g["field"] == field and g["system"] == system
                       and not (skip and g["flagged"])]  # fmt: skip
                if not sel:
                    continue
                c = Counter(g[v]["grade"] for g in sel)
                n = len(sel)
                label = f"{v}{' without flagged' if skip else ''}"
                print(f"{system:8} {field:12} {label:20} n={n:3}  correct {c['correct'] / n:.0%}  "
                      f"partial {c['partial'] / n:.0%}  wrong {c['wrong'] / n:.0%}  "
                      f"no answer {c['no_answer'] / n:.0%}")  # fmt: skip


NOW = OUT / "ours20_now.json"


def ours_now() -> None:
    """The 20 compared rows answered by the served code path (service.RagService.ask,
    wide pool, statute terms, reranker, answer step) with the search scoped to the file,
    as when a user uploads it and asks. The ``ours`` column was made on 2026-11-13 by
    the older retrieval path (bilingual_union); it stays as it was, fixed before the
    Claude and ChatGPT answers were seen. This run uses the code as committed before
    they were seen too (no change since)."""
    import datetime as dt
    import subprocess

    from sdrag.service import RagService

    rows = {r["qid"]: r for r in csv.DictReader(CSV.open(encoding="utf-8"))}
    qids = json.loads((OUT / "subset20.json").read_text("utf-8"))["qids"]
    items = {
        i.qid: i for s in ("test.jsonl", "test_re.jsonl") for i in load_items(DATA / "eval" / s)
    }
    client = make_client(settings.opensearch_url, settings.aws_region)
    emb = TitanEmbedder(settings.embed_model, settings.aws_region, settings.embed_dims)
    service = RagService(client, settings.index, emb,
                         BedrockChat(settings.llm_model, settings.aws_region))  # fmt: skip
    git = ["git", "rev-parse", "--short", "HEAD"]
    commit = subprocess.run(git, check=False, capture_output=True, text=True).stdout.strip()

    def one(q):
        it = items[q]
        reply = service.ask("eval", rows[q]["question"], scope=[it.gold[0].doc_id])
        cited = [c.chunk_id for c in reply.answer.citations]
        top = reply.retrieved[:6]
        body = {"size": 6, "_source": ["doc_id", "start", "end"], "query": {"terms": {"chunk_id": top}}}
        srcs = [h["_source"] for h in client.search(index=settings.index, body=body)["hits"]["hits"]]
        found = any(s["doc_id"] == g.doc_id and s["start"] < g.end and s["end"] > g.start
                    for s in srcs for g in [*it.gold, *it.also])  # fmt: skip
        print(q, "gold in top 6:", found, reply.answer.text[:70].replace("\n", " "), flush=True)
        return q, {"answer": reply.answer.text, "gold_in_sources": found, "cited": cited}

    with ThreadPoolExecutor(4) as ex:
        out = dict(ex.map(one, qids))
    meta = {"date": dt.date.today().isoformat(), "commit": commit, "model": settings.llm_model}
    NOW.write_text(json.dumps({"meta": meta, "answers": out}, ensure_ascii=False, indent=1), "utf-8")


def whole_passage(client, it, extra: list[str]) -> str:
    """The chunks (whole articles) that hold the item's gold spans in its file, plus
    the extra chunks named in fixes20.json. A long chunk (a big table) is cut to the
    part around the gold span."""
    doc = it.gold[0].doc_id
    seen, parts = set(), []
    spans = [g for g in [*it.gold, *it.also] if g.doc_id == doc]
    for g in spans:
        body = {"size": 5, "_source": ["chunk_id", "heading", "start", "end", "text"],
                "query": {"bool": {"filter": [{"term": {"doc_id": doc}},
                                              {"range": {"start": {"lt": g.end}}},
                                              {"range": {"end": {"gt": g.start}}}]}}}  # fmt: skip
        for h in client.search(index=settings.index, body=body)["hits"]["hits"]:
            c = h["_source"]
            if c["chunk_id"] in seen:
                continue
            seen.add(c["chunk_id"])
            text = c["text"]
            if len(text) > 4000:
                at = max(0, g.start - c["start"])
                text = "…" + text[max(0, at - 1500) : at + 1500] + "…"
            parts.append(f"[{c.get('heading') or ''}]\n{text}")
    for cid in extra:
        if cid not in seen:
            body = {"size": 1, "_source": ["heading", "text"], "query": {"term": {"chunk_id": cid}}}
            c = client.search(index=settings.index, body=body)["hits"]["hits"][0]["_source"]
            parts.append(f"[{c.get('heading') or ''}]\n{c['text']}")
    return "\n\n".join(parts)


def grade_full() -> None:
    """The 20 compared rows (subset20.json), all three systems, graded by judge v2 with
    the references checked against the statutes (fixes20.json) and the whole articles
    as the passage instead of the gold sentence. Writes grades20.json.
    ``--skip-fix r0176 ...``: grade those rows with their original reference and passage
    (a fix made after the answers were seen is shown both ways). ``--wide``: the passage
    of judge v4 (judges.wide_passage), writes grades20-wide.json."""
    rows = {r["qid"]: r for r in csv.DictReader(CSV.open(encoding="utf-8"))}
    qids = json.loads((OUT / "subset20.json").read_text("utf-8"))["qids"]
    fixes = json.loads((OUT / "fixes20.json").read_text("utf-8"))["fixes"]
    skip = sys.argv[sys.argv.index("--skip-fix") + 1 :] if "--skip-fix" in sys.argv else []
    skip = [q for q in skip if not q.startswith("--")]
    fixes = {q: f for q, f in fixes.items() if q not in skip}  # as graded before that fix
    wide = "--wide" in sys.argv
    items = {
        i.qid: i for s in ("test.jsonl", "test_re.jsonl") for i in load_items(DATA / "eval" / s)
    }
    client = make_client(settings.opensearch_url, settings.aws_region)
    judge = CachedChat(BedrockChat(JUDGE_MODEL, settings.aws_region), LLM_CACHE)
    systems = ("ours", "claude", "chatgpt")
    if NOW.exists():  # the served code path, run later (ours_now)
        systems += ("ours_now",)
        for q, a in json.loads(NOW.read_text("utf-8"))["answers"].items():
            rows[q]["ours_now"] = a["answer"]
    jobs = []
    for q in qids:
        r, fix = rows[q], fixes.get(q, {})
        reference = fix.get("reference", r["reference"])
        if wide:  # judge v4's passage (judges.wide_passage)
            it = items[q]
            spans = [(g.start, g.end) for g in [*it.gold, *it.also] if g.doc_id == it.gold[0].doc_id]
            passage = wide_passage(client, settings.index, it.gold[0].doc_id, spans,
                                   fix.get("extra_chunks", []))  # fmt: skip
        else:
            passage = whole_passage(client, items[q], fix.get("extra_chunks", []))
        jobs += [(q, s, correct_user(r["question"], reference, passage, r[s])) for s in systems]

    def one(job):  # the judge is slow some days: a few calls at a time
        q, system, user = job
        field = "real-estate" if q.startswith("r") else "labor"
        out = parse_json(judge.complete(correct_prompt(field, 2), user, max_tokens=400).text) or {}
        print(q, system, out.get("grade"), flush=True)
        return {"qid": q, "field": field, "system": system, "fixed": q in fixes,
                "grade": out.get("grade", "unparsed"), "key_fact": out.get("key_fact", ""),
                "why": out.get("why", "")}  # fmt: skip

    with ThreadPoolExecutor(4) as ex:
        grades = list(ex.map(one, jobs))
    name = "grades20" + "".join(f"-skip-{q}" for q in skip) + ("-wide" if wide else "") + ".json"
    (OUT / name).write_text(json.dumps(grades, ensure_ascii=False, indent=1), "utf-8")
    for field in ("labor", "real-estate", None):
        for system in systems:
            sel = [g for g in grades if g["system"] == system and field in (None, g["field"])]
            c, n = Counter(g["grade"] for g in sel), len(sel)
            print(f"{system:8} {field or 'all':12} n={n:3}  correct {c['correct']:2}  partial "
                  f"{c['partial']:2}  wrong {c['wrong']:2}  no answer {c['no_answer']:2}")  # fmt: skip


if __name__ == "__main__":
    cmds = {"select": select, "select-re": select_re, "ours": ours, "grade": grade,
            "ours-now": ours_now, "grade-full": grade_full}  # fmt: skip
    cmds[sys.argv[1]]()
