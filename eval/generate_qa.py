"""Stage 2 of the generated evaluation set: write a question for each sampled passage,
then have a second model, from another family, check it.

Generation (``GEN_SYSTEM``): the model sees the passage(s), the language to ask in and
a style, and returns the question, the shortest verbatim quote that answers it (the
gold span) and a short answer. Rules that matter for a fair retrieval test:

- no article / section numbers, and words of its own rather than the statute's:
  questions that copy the text favor keyword search
- the country is named only when the question is in the other language ("in Korea",
  "미국에서"): a user asking about their own country's law does not say so
- three styles, as users ask: a full question, a short keyword query, a situation

Verification (``CHECK_SYSTEM``, a different model): from the question and the
passages, is the question answerable from them, is it unambiguous, and for "multi"
items does it need both passages. Items that fail are dropped and counted.

The quote is located in the canonical text (exact, then ignoring whitespace); an item
whose quote is not in its passage is dropped too.

    cd backend && AWS_PROFILE=<profile> uv run python ../eval/generate_qa.py
"""

import argparse
import json
import random
import re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from evalset import CACHE, doc_texts, locate

from sdrag.common.config import settings
from sdrag.common.llm import BedrockChat, CachedChat, parse_json

PASSAGES = CACHE / "qa" / "passages.jsonl"
OUT = CACHE / "qa" / "generated.jsonl"


def paths(name: str):
    """(passages, generated) of a set (sample_passages.SETS)."""
    if name == "labor":
        return PASSAGES, OUT
    return CACHE / "qa" / f"passages-{name}.jsonl", CACHE / "qa" / f"generated-{name}.jsonl"


GEN_MODEL = "qwen.qwen3-next-80b-a3b"
CHECK_MODEL = "deepseek.v3.2"
SEED = 20261112

STYLES = {
    "question": "a complete, natural question",
    "keywords": "a short search query of 2 to 6 words, as typed into a search box (not a full sentence)",
    "situation": "a question that describes the asker's own situation in one or two sentences, then asks",
}  # fmt: skip
STYLE_WEIGHTS = {"question": 0.5, "keywords": 0.2, "situation": 0.3}
LANG_NAME = {"ko": "Korean", "en": "English"}
COUNTRY = {"ko": ("Korea", "한국"), "en": ("the United States", "미국")}

GEN_SYSTEM = """You write test questions for a search engine over Korean and US labor law.
You are given one or two passages from the corpus. Write ONE question that a worker, employer or HR person could ask and that the passage(s) answer.

Rules:
- Write the question in {q_lang}. Style: {style}.
- Do not cite article, section, paragraph or annex numbers, and do not quote the passage: use your own everyday words for the same idea. You may name a law by its common name only if a user naturally would.
- {country_rule}
- The question must have one clear answer in the passage(s), and must make sense on its own to someone who has not seen them.
- {kind_rule}
- "evidence": copy, character for character, the shortest part of the passage(s) that answers the question (usually one sentence, one numbered item or one table row; at most about 300 characters). {evidence_rule}
- "answer": the answer in one short sentence, in {q_lang}.
- If the passage holds nothing a user would ask about (only a heading, a list of amendments, a table of contents, unreadable text), return {{"skip": true, "reason": "..."}}.

Return only JSON: {{"question": "...", "evidence": [...], "answer": "..."}}"""

KIND_RULE = {
    "fact": "Ask about a concrete rule, condition, period, amount or procedure in the passage.",
    "table": "The passage is rows of a table (with its header row as context). Ask for a value that has to be read from a specific row and column.",
    "multi": "Passage 1 is from an act that leaves a detail to a decree or rule; passage 2 is the decree or rule that fills it in. Ask a question that needs BOTH: the rule from passage 1 and the detail from passage 2.",
}  # fmt: skip
EVIDENCE_RULE = {
    "fact": "Give a list with one string.",
    "table": "Give a list with one string: the table row (or rows) holding the value, copied as written.",
    "multi": "Give a list with two strings: first the part of passage 1, then the part of passage 2.",
}  # fmt: skip

CHECK_SYSTEM = """You review test questions for a legal search engine. Given a question and the passage(s) it was written from, judge strictly.
- "answerable": "yes" if the passage(s) fully answer the question, "partial" if only in part, "no" otherwise.
- "ambiguous": true if the question is unclear, or could just as well be about something else, or depends on context the asker did not give.
- "needs_all": true if answering needs every passage given (only meaningful when there are two).
- "answer": the answer from the passage(s), one sentence.
Return only JSON: {"answerable": "...", "ambiguous": false, "needs_all": true, "answer": "..."}"""


def country_rule(q_lang: str, answer_lang: str) -> str:
    if q_lang == answer_lang:
        return "Do not name the country: the asker is asking about their own country's law."
    en, ko = COUNTRY[answer_lang]
    name = en if q_lang == "en" else ko
    return f'The passage is {en}\'s law and the question is in another language, so make clear it is about {name} (e.g. "in {en}" / "{ko}에서").'


def passage_block(p: dict) -> str:
    out = []
    for i, part in enumerate(p["parts"], 1):
        head = f"[Passage {i}] {part['title']} > {part['heading'] or ''}".rstrip(" >")
        ctx = f"(table header row: {part['context']})\n" if part.get("context") else ""
        out.append(f"{head}\n{ctx}{part['text']}")
    return "\n\n".join(out)


def generate(llm, p: dict) -> dict:
    system = GEN_SYSTEM.format(
        q_lang=LANG_NAME[p["q_lang"]],
        style=STYLES[p["style"]],
        country_rule=country_rule(p["q_lang"], p["answer_lang"]),
        kind_rule=KIND_RULE[p["kind"]],
        evidence_rule=EVIDENCE_RULE[p["kind"]],
    )
    c = llm.complete(system, passage_block(p), max_tokens=800, temperature=0.5)
    return {"raw": c.text, "out": parse_json(c.text)}


def check(llm, p: dict, question: str) -> dict:
    c = llm.complete(CHECK_SYSTEM, f"Question: {question}\n\n{passage_block(p)}", max_tokens=400)
    return {"raw": c.text, "out": parse_json(c.text)}


def overlap(question: str, passage: str) -> float:
    """Share of the question's word bigrams (Korean: character bigrams within words)
    that also occur in the passage: how much the question copies the text."""

    def grams(s: str) -> set[str]:
        words = re.findall(r"\w+", s.lower())
        g = set()
        for w in words:
            if re.search(r"[가-힣]", w):
                g |= {w[i : i + 2] for i in range(len(w) - 1)}
            else:
                g.add(w)
        return g

    q = grams(question)
    return len(q & grams(passage)) / len(q) if q else 0.0


def build(p: dict, gen: dict, chk: dict | None, texts) -> tuple[dict | None, str]:
    """(item, '') or (None, reason it was dropped)."""
    out = gen["out"]
    if not isinstance(out, dict):
        return None, "generation: no JSON"
    if out.get("skip"):
        return None, "generation: skipped passage"
    q, ev = out.get("question", "").strip(), out.get("evidence")
    if not q or not isinstance(ev, list) or not ev:
        return None, "generation: missing fields"
    if p["kind"] == "multi" and len(ev) != 2:
        return None, "generation: multi without two quotes"
    gold = []
    parts = p["parts"] if p["kind"] == "multi" else p["parts"] * len(ev)
    for quote, part in zip(ev, parts):
        text = texts[part["doc_id"]].text
        window = text[part["start"] : part["end"]]
        loc = locate(window, quote.strip())
        if loc is None:
            return None, "evidence: quote not in passage"
        s, e = part["start"] + loc[0], part["start"] + loc[1]
        gold.append({"doc_id": part["doc_id"], "start": s, "end": e, "quote": text[s:e]})
    c = (chk or {}).get("out")
    if not isinstance(c, dict):
        return None, "check: no JSON"
    if c.get("answerable") != "yes":
        return None, f"check: answerable={c.get('answerable')}"
    if c.get("ambiguous"):
        return None, "check: ambiguous"
    if p["kind"] == "multi" and not c.get("needs_all"):
        return None, "check: multi answerable from one passage"
    item = {
        "qid": p["pid"].replace("p", "g", 1),  # r-pids (real-estate set) stay r
        "question": q,
        "q_lang": p["q_lang"],
        "gold": gold,
        "kind": p["kind"],
        "source": f"generated:{GEN_MODEL}",
        "meta": {
            "style": p["style"],
            "answer": out.get("answer", ""),
            "check_answer": c.get("answer", ""),
            "answer_lang": p["answer_lang"],
            "file_type": p["file_type"],
            "overlap": round(overlap(q, " ".join(x["text"] for x in p["parts"])), 3),
        },
    }
    return item, ""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, help="first N passages only (a trial run)")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--set", default="labor")
    a = ap.parse_args()
    passages_path, out_path = paths(a.set)

    texts = doc_texts()
    passages = [json.loads(x) for x in passages_path.read_text("utf-8").splitlines() if x]
    rng = random.Random(SEED)
    for p in passages:  # style is drawn here, not at sampling, so it can be re-weighted
        p["style"] = rng.choices(list(STYLE_WEIGHTS), weights=list(STYLE_WEIGHTS.values()))[0]
        for part in p["parts"]:
            part["title"] = texts[part["doc_id"]].title
    passages = passages[: a.limit] if a.limit else passages

    cache = Path(CACHE / "llm")
    gen_llm = BedrockChat(GEN_MODEL, settings.aws_region)
    chk_llm = BedrockChat(CHECK_MODEL, settings.aws_region)
    gen_c, chk_c = CachedChat(gen_llm, cache), CachedChat(chk_llm, cache)

    with ThreadPoolExecutor(a.workers) as pool:
        gens = list(pool.map(lambda p: generate(gen_c, p), passages))

        def chk(pg):
            p, g = pg
            q = g["out"].get("question") if isinstance(g["out"], dict) else None
            return check(chk_c, p, q) if q else None

        chks = list(pool.map(chk, zip(passages, gens)))

    items, dropped = [], Counter()
    with out_path.open("w", encoding="utf-8") as f:
        for p, g, c in zip(passages, gens, chks):
            item, why = build(p, g, c, texts)
            f.write(json.dumps({"pid": p["pid"], "item": item, "dropped": why, "gen": g,
                                "check": c}, ensure_ascii=False) + "\n")  # fmt: skip
            if item:
                items.append(item)
            else:
                dropped[why] += 1
    print(f"{len(items)} kept of {len(passages)}; dropped: {dict(dropped)}")
    print("kept by kind:", Counter(i["kind"] for i in items))
    print(
        "kept by (q_lang, answer_lang):",
        Counter((i["q_lang"], i["meta"]["answer_lang"]) for i in items),
    )
    for llm in (gen_llm, chk_llm):
        print(
            f"{llm.name}: {llm.input_tokens:,} in / {llm.output_tokens:,} out tokens (uncached calls)"
        )


if __name__ == "__main__":
    main()
