"""Stage 3: complete the gold answers by pooling, annotate the real questions, split.

Pooling (as in TREC): the top results of every system to be compared (bm25, dense,
hybrid, per_language over both chunkings) are merged per question, and a judge model
decides which of these candidates answer the question too. Without it, a system that
finds the same rule in another statute (the act and its decree often repeat each
other) would be scored as wrong. Found spans are added as ``also`` (see
evalset.Scores). The pool only holds what some system found; an answer no system
retrieves stays unknown, a known limit of pooling.

Real questions (data/eval/real_questions_candidates.csv: easylaw.go.kr, dol.gov) have
no gold yet: the same pool is judged without a reference answer; the candidates the
judge says answer the question become the gold (the best one) and ``also``
(the rest). A few the judge missed although the corpus answers them were annotated
by hand (``real_manual_gold.json``, marked ``meta.manual``). Questions nothing in the corpus answers are kept apart
(``real_unanswerable.jsonl``) for testing that the agent says it does not know.

Split: 20% of each (answer language, file type) cell of the generated items goes to
the dev set (tuning), 80% to the test set (reported once). The real set is test only.

    cd backend && AWS_PROFILE=sd-assignment SDRAG_EMBED_CACHE_DIR=../data/raw/embed-cache \\
        uv run python ../eval/finalize_qa.py
"""

import argparse
import csv
import hashlib
import json
import random
import re
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from evalset import CACHE, DATA, Gold, Item, doc_texts, locate, overlaps, save_items
from generate_qa import CHECK_MODEL, paths
from opensearchpy import OpenSearch
from sample_passages import SEED, TARGET, TARGET_RE

from sdrag.common.config import settings
from sdrag.common.llm import BedrockChat, CachedChat, parse_json
from sdrag.retrieval.embed import CachedEmbedder, TitanEmbedder
from sdrag.retrieval.search import Searcher

POOL_SYSTEMS = [(m, i) for i in ("chunks-structure", "chunks-fixed")
                for m in ("bm25", "dense", "hybrid", "per_language")]  # fmt: skip
POOL_DEPTH = {"generated": 5, "real": 10, "real_retry": 25}
DEV_SHARE = 0.2
OUT = DATA / "eval"
JUDGE_MODEL = CHECK_MODEL  # not the generator's family
# every also-span is confirmed by a third family: the first judge, shown many
# candidates, still let through the same clause about a different committee or program
CONFIRM_MODEL = "openai.gpt-oss-120b-1:0"

POOL_SYSTEM = """You judge search results for a legal search engine over Korean and US labor law.
Given a question, the reference evidence and answer, and numbered candidate passages, list the candidates that ALSO answer the question on their own.
A candidate counts only if a user who reads nothing but that candidate gets the same answer as the reference (the same number, period, amount, condition or procedure) for this question: the same rule repeated in another statute, decree or section, or another wording of it.
It does NOT count if it is: the same kind of clause about a different program, form, person or situation; a different row of the same table; a definition, purpose or general statement; a passage that only mentions the topic; an answer to part of the question. When unsure, leave it out.
For each one, copy character for character the shortest part of the candidate that answers (one sentence, item or table row).
Return only JSON: {"also": [{"n": <candidate number>, "quote": "..."}]} (an empty list if none, which is the usual case)."""

REAL_SYSTEM = """You judge search results for a legal search engine over Korean and US labor law (statutes and regulations only, no court cases or guidance).
The question was asked by a real user on {site}, so it is about {law}. Passages from another country's law never count, however close.
Given the question and numbered candidate passages, decide which candidates answer it: they state the rule, condition, amount, period or procedure the question asks about. A passage that is only on the same topic does not count; a passage that answers the core of the question counts even if a full answer would add detail.
"best": the candidate that answers it most directly, or null if none does.
"also": other candidates that answer it as well (the same rule in another statute or section).
For each, copy character for character the shortest part that answers (one sentence, item or table row).
Return only JSON: {{"best": {{"n": <number>, "quote": "..."}} | null, "also": [{{"n": <number>, "quote": "..."}}], "note": "<one sentence: why, or what is missing>"}}"""
JURISDICTION = {
    "el": ("easylaw.go.kr, the Korean government's guide to everyday law", "Korean law"),
    "dol": ("dol.gov, the US Department of Labor's website", "US federal law"),
}


CONFIRM_SYSTEM = """You check one search result for a legal search engine over Korean and US labor law.
Given a question, its reference answer and one passage: does the passage, read on its own, give the same answer to this question (the same number, period, amount, condition or procedure, about the same program, body or situation the question is about)?
Return only JSON: {"same_answer": true | false, "why": "<one short sentence>"}"""


def confirm(llm, question: str, answer: str, g: Gold, texts) -> bool:
    d = texts[g.doc_id]
    b = d.block_at(g.start)
    context = d.text[max(b.start, g.start - 300) : min(b.end, g.end + 300)]
    user = (f"Question: {question}\nReference answer: {answer}\n\n"
            f"Passage ({d.title} > {b.heading or ''}):\n{context}")  # fmt: skip
    out = parse_json(llm.complete(CONFIRM_SYSTEM, user, max_tokens=800).text)
    return isinstance(out, dict) and out.get("same_answer") is True


def dedupe(spans: list[Gold]) -> list[Gold]:
    """Drop spans overlapping an earlier one (two chunkings return the same text)."""
    out: list[Gold] = []
    for g in spans:
        if not any(overlaps(vars(g), h) for h in out):
            out.append(g)
    return out


def pool(searchers, question: str, depth: int) -> list[dict]:
    """Union of every system's top `depth`, in order of first appearance."""
    seen, out = set(), []
    for s, mode in searchers:
        for h in getattr(s, mode)(question, size=depth):
            if h.chunk_id not in seen:
                seen.add(h.chunk_id)
                out.append(h.source | {"chunk_id": h.chunk_id})
    return out


def candidates_block(cands: list[dict]) -> str:
    return "\n\n".join(
        f"[{n}] {c['title']} > {c['heading'] or ''}\n{c['text']}" for n, c in enumerate(cands, 1)
    )


def to_gold(texts, cand: dict, quote: str) -> Gold | None:
    """Locate a judge's quote inside the candidate's range of the canonical text."""
    text = texts[cand["doc_id"]].text
    loc = locate(text[cand["start"] : cand["end"]], (quote or "").strip())
    if loc is None:
        return None
    s, e = cand["start"] + loc[0], cand["start"] + loc[1]
    return Gold(cand["doc_id"], s, e, text[s:e])


def judge_generated(llm, texts, item: Item, cands: list[dict]) -> tuple[list[Gold], dict]:
    new = [c for c in cands if not any(overlaps(c, g) for g in item.gold)]
    if not new:
        return [], {"n_candidates": 0}
    ref = "\n".join(f"- {g.quote}" for g in item.gold)
    user = (
        f"Question: {item.question}\n\nReference evidence:\n{ref}\n\n"
        f"Reference answer: {item.meta.get('check_answer') or item.meta.get('answer')}\n\n"
        f"Candidates:\n\n{candidates_block(new)}"
    )
    c = llm.complete(POOL_SYSTEM, user, max_tokens=1200)
    out = parse_json(c.text)
    found = []
    for x in (out or {}).get("also", []) if isinstance(out, dict) else []:
        n = x.get("n") if isinstance(x, dict) else None
        ok = isinstance(n, int) and 1 <= n <= len(new)
        if ok and (g := to_gold(texts, new[n - 1], x.get("quote", ""))):
            found.append(g)
    found = [g for g in dedupe(found) if not any(overlaps(vars(g), h) for h in item.gold)]
    return found, {"n_candidates": len(new), "raw": c.text}


def judge_real(
    llm, texts, qid: str, question: str, cands: list[dict]
) -> tuple[Gold | None, list[Gold], dict]:
    site, law = JURISDICTION[qid.split("-")[0]]
    user = f"Question: {question}\n\nCandidates:\n\n{candidates_block(cands)}"
    c = llm.complete(REAL_SYSTEM.format(site=site, law=law), user, max_tokens=1500)
    out = parse_json(c.text)
    if not isinstance(out, dict):
        return None, [], {"raw": c.text, "error": "no JSON"}

    def one(x):
        n = x.get("n") if isinstance(x, dict) else None
        if isinstance(n, int) and 1 <= n <= len(cands):
            c = cands[n - 1]
            # a quote that cannot be located (the judge re-worded it) falls back to the
            # whole candidate chunk: the judge's choice of passage is what matters
            fallback = Gold(
                c["doc_id"], c["start"], c["end"], texts[c["doc_id"]].text[c["start"] : c["end"]]
            )
            return to_gold(texts, c, x.get("quote", "")) or fallback
        return None

    best = one(out.get("best")) if out.get("best") else None
    also = [g for g in (one(x) for x in out.get("also") or []) if g]
    if best is None and also:
        best, also = also[0], also[1:]
    also = [g for g in dedupe(also) if not (best and overlaps(vars(g), best))]
    return best, also, {"raw": c.text, "note": out.get("note", ""), "n_candidates": len(cands)}


def fill(generated: list[dict], passages: dict[str, dict], targets: dict) -> list[Item]:
    """Every item that survived generation and the check. The reserve drawn at
    sampling was sized for losses; the cells it over-filled are kept whole (more
    items), and the ones it under-filled are reported against their target."""
    items, per_cell = [], Counter()
    for r in generated:
        if r["item"]:
            p = passages[r["pid"]]
            per_cell[(p["answer_lang"], p["file_type"])] += 1
            items.append(Item(**(r["item"] | {"gold": [Gold(**g) for g in r["item"]["gold"]]})))
    for cell, target in targets.items():
        print(f"  {cell}: {per_cell[cell]} (target {target})")
    return items


# OCR errors the generator copied from a scanned passage into its question: a user
# would type the right word, and keeping the error would favor keyword search on the
# OCR text (docs/decisions.md, OCR: 융자 read as 용자 throughout one statute)
OCR_FIXES = [(re.compile(r"(?<![사이])용자"), "융자")]
RE_HAN = re.compile(r"[\u4e00-\u9fff]")


def clean(items: list[Item], texts) -> tuple[list[Item], Counter]:
    """Fix known OCR errors in questions about scans; drop Korean questions with Chinese
    characters in them (a generation slip: "收取하는"); drop a question when an earlier
    one in the same language has the same answer (their gold and also spans overlap:
    the same rule asked twice, from two places that repeat it)."""
    out, dropped = [], Counter()
    for it in sorted(items, key=lambda i: i.qid):
        if any(texts[g.doc_id].file_type == "scan" for g in it.gold):
            q = it.question
            for pat, fix in OCR_FIXES:
                q = pat.sub(fix, q)
            if q != it.question:
                it.meta["edited"] = f"OCR error fixed; was: {it.question}"
                it.question = q
        if it.q_lang == "ko" and RE_HAN.search(it.question):
            dropped["Chinese characters in a Korean question"] += 1
            continue
        mine = [*it.gold, *it.also]
        if any(
            o.q_lang == it.q_lang
            and any(overlaps(vars(g), h) for g in mine for h in [*o.gold, *o.also])
            for o in out
        ):
            dropped["same answer as an earlier question"] += 1
            continue
        out.append(it)
    return out, dropped


def split(items: list[Item], texts) -> tuple[list[Item], list[Item]]:
    rng = random.Random(SEED)
    by_cell = defaultdict(list)
    for it in items:
        by_cell[(it.meta["answer_lang"], it.meta["file_type"])].append(it)
    dev, test = [], []
    for cell in sorted(by_cell):
        xs = sorted(by_cell[cell], key=lambda it: it.qid)
        rng.shuffle(xs)
        k = round(len(xs) * DEV_SHARE)
        dev += xs[:k]
        test += xs[k:]
    return sorted(dev, key=lambda i: i.qid), sorted(test, key=lambda i: i.qid)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--set", default="labor", help="labor (with the real questions) or re")
    a = ap.parse_args()
    passages_path, generated_path = paths(a.set)
    texts = doc_texts()
    passages = {json.loads(x)["pid"]: json.loads(x)
                for x in passages_path.read_text("utf-8").splitlines() if x}  # fmt: skip
    generated = [json.loads(x) for x in generated_path.read_text("utf-8").splitlines() if x]
    print("filling cells:")
    items = fill(generated, passages, TARGET if a.set == "labor" else TARGET_RE)

    client = OpenSearch(hosts=[settings.opensearch_url], timeout=60)
    emb = TitanEmbedder(settings.embed_model, settings.aws_region, settings.embed_dims)
    emb = CachedEmbedder(emb, Path(settings.embed_cache_dir or DATA / "raw" / "embed-cache"))
    searchers = [(Searcher(client, idx, emb), mode) for mode, idx in POOL_SYSTEMS]
    judge = CachedChat(BedrockChat(JUDGE_MODEL, settings.aws_region), CACHE / "llm")
    log = []

    confirmer = CachedChat(BedrockChat(CONFIRM_MODEL, settings.aws_region), CACHE / "llm")

    def do_generated(it: Item):
        cands = pool(searchers, it.question, POOL_DEPTH["generated"])
        also, info = judge_generated(judge, texts, it, cands)
        answer = it.meta.get("check_answer") or it.meta.get("answer", "")
        it.also = [g for g in also if confirm(confirmer, it.question, answer, g, texts)]
        return {
            "qid": it.qid,
            "also": len(it.also),
            "also_unconfirmed": len(also) - len(it.also),
            **info,
        }

    with ThreadPoolExecutor(a.workers) as ex:
        log += list(ex.map(do_generated, items))
    print("pooling: also-spans confirmed", sum(x["also"] for x in log),
          "rejected", sum(x["also_unconfirmed"] for x in log))  # fmt: skip
    print("pooling: items with an also-span:", sum(1 for x in log if x["also"]), "of", len(items))
    items, dropped = clean(items, texts)
    print(f"cleaning: {len(items)} kept, dropped {dict(dropped)}, "
          f"OCR-fixed {sum(1 for i in items if 'edited' in i.meta)}")  # fmt: skip

    if a.set != "labor":  # an added set: generated items only, written next to the others
        dev, test = split(items, texts)
        names = (f"dev_{a.set}.jsonl", f"test_{a.set}.jsonl")
        save_items(OUT / names[0], dev)
        save_items(OUT / names[1], test)
        sums = {ln.split()[1]: ln for ln in (OUT / "SHA256SUMS").read_text().splitlines() if ln}
        sums |= {n: f"{sha256(OUT / n)}  {n}" for n in names}
        (OUT / "SHA256SUMS").write_text("".join(v + "\n" for v in sums.values()))
        print(f"{a.set}: dev {len(dev)}, test {len(test)}")
        print("test", Counter((i.q_lang, "+".join(sorted(i.answer_langs(texts)))) for i in test),
              Counter("+".join(sorted(i.file_types(texts))) for i in test), Counter(i.kind for i in test))  # fmt: skip
        return

    with (DATA / "eval" / "real_questions_candidates.csv").open(encoding="utf-8") as f:
        real_rows = list(csv.DictReader(f))

    def do_real(r):
        cands = pool(searchers, r["question"], POOL_DEPTH["real"])
        best, also, info = judge_real(judge, texts, r["qid"], r["question"], cands)
        if best is None:  # a deeper pool before calling it unanswerable
            cands = pool(searchers, r["question"], POOL_DEPTH["real_retry"])
            best, also, info = judge_real(judge, texts, r["qid"], r["question"], cands)
            info["retry"] = True
        if best:  # the best quote stands in for the reference answer
            also = [g for g in also if confirm(confirmer, r["question"], best.quote, g, texts)]
        return r, best, also, info

    with ThreadPoolExecutor(a.workers) as ex:
        real_out = list(ex.map(do_real, real_rows))
    manual = json.loads((OUT / "real_manual_gold.json").read_text("utf-8"))["gold"]
    real, unanswerable = [], []
    for r, best, also, info in real_out:
        if best is None and r["qid"] in manual:
            best, info["manual"] = Gold(**manual[r["qid"]][0]), True
        meta = {"topic": r["topic"], "url": r["url"], "license": r["license"],
                "judge_note": info.get("note", ""), "manual": info.get("manual", False)}  # fmt: skip
        src = "easylaw" if r["qid"].startswith("el") else "dol-whd"
        it = Item(
            r["qid"], r["question"], r["lang"], [best] if best else [], "real", src, meta, also
        )
        (real if best else unanswerable).append(it)
        log.append({"qid": r["qid"], **info})

    dev, test = split(items, texts)
    save_items(OUT / "dev.jsonl", dev)
    save_items(OUT / "test.jsonl", test)
    save_items(OUT / "real.jsonl", real)
    save_items(OUT / "real_unanswerable.jsonl", unanswerable)
    (CACHE / "qa" / "finalize_log.jsonl").write_text(
        "".join(json.dumps(x, ensure_ascii=False) + "\n" for x in log), "utf-8"
    )
    sums = "".join(f"{sha256(OUT / n)}  {n}\n" for n in
                   ("dev.jsonl", "test.jsonl", "real.jsonl", "real_unanswerable.jsonl"))  # fmt: skip
    (OUT / "SHA256SUMS").write_text(sums)
    print(f"dev {len(dev)}, test {len(test)}, real {len(real)} (+{len(unanswerable)} unanswerable)")
    for name, xs in (("test", test), ("real", real)):
        print(name, Counter((i.q_lang, "+".join(sorted(i.answer_langs(texts)))) for i in xs),
              Counter("+".join(sorted(i.file_types(texts))) for i in xs), Counter(i.kind for i in xs))  # fmt: skip
    print(
        f"judge {JUDGE_MODEL}: {judge.inner.input_tokens:,} in / {judge.inner.output_tokens:,} out (uncached)"
    )


if __name__ == "__main__":
    main()
