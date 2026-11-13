"""Check the evaluation items themselves: is each reference answer right, and each
question answerable as asked?

Answer grading compares a system's answer with the item's reference answer, which the
question writer (Qwen) produced from the gold passage. A reference that misreads the
passage (it says "included" where the statute says "not included") or a question that
is garbled makes a correct answer look wrong. Looking only at the items our system
missed would favor our system, so every item used for answer grading is checked the
same way: the answer-quality samples (labor 100, real estate 82) and the single-file
rows (50).

The checker is gpt-oss-120b, a third family (neither the question writer nor the
DeepSeek judge). It sees the question, the reference and the gold passage with its
surrounding text. Every item it flags is then checked against the statutes (by Claude Code, the coding
assistant); the confirmed ones, with the reason, go to data/eval/item_flags.json, which answers.py and single_file.py
report with and without.

    cd backend && AWS_PROFILE=<profile> uv run python ../eval/check_items.py
"""

import csv
import json
from concurrent.futures import ThreadPoolExecutor

from evalset import CACHE, DATA, doc_texts, load_items

from sdrag.common.config import settings
from sdrag.common.llm import BedrockChat, CachedChat, parse_json

CHECK_MODEL = "openai.gpt-oss-120b-1:0"
OUT = DATA / "eval" / "results" / "item-check.jsonl"

CHECK_SYSTEM = """You check items of an evaluation set for a legal document search engine (Korean and US statutes). Each item has a question, a reference answer written by a model from a passage, and that passage with its surrounding text.
Judge the item, not any system's answer:
- "reference": "ok" if the reference answer is what the passage says for this question; "wrong" if it contradicts or misreads the passage (for example says a rule applies where the passage says it does not, or gives a different number); "incomplete" if it leaves out part of what the question asks and the passage states.
- "question": "ok" if a careful reader can tell what is asked; "unclear" if it is garbled, self-contradictory or asks something other than what the reference answers.
Return only JSON: {"reference": "ok" | "wrong" | "incomplete", "question": "ok" | "unclear", "why": "<one sentence>"}"""


def main() -> None:
    texts = doc_texts()
    items = {
        i.qid: i for s in ("test", "test_re") for i in load_items(DATA / "eval" / f"{s}.jsonl")
    }
    answers = DATA / "eval" / "results" / "answers" / "v6-country-filter"
    qids = []
    for name in ("test_sample", "test_re"):
        qids += [
            json.loads(x)["qid"]
            for x in (answers / f"{name}.jsonl").read_text("utf-8").splitlines()
            if x
        ]
    with (DATA / "eval" / "single_file" / "compare.csv").open(encoding="utf-8") as f:
        qids += [r["qid"] for r in csv.DictReader(f)]
    qids = sorted(set(qids))
    llm = CachedChat(BedrockChat(CHECK_MODEL, settings.aws_region), CACHE / "llm")

    def one(qid: str) -> dict:
        it = items[qid]
        g = it.gold[0]
        d = texts[g.doc_id]
        b = d.block_at(g.start)
        context = d.text[max(b.start, g.start - 400) : min(b.end, g.end + 400)]
        ref = it.meta.get("check_answer") or it.meta.get("answer", "")
        user = (f"Question: {it.question}\nReference answer: {ref}\n\n"
                f"Passage ({d.title} > {b.heading or ''}), the part the reference was written from:\n"
                f"{g.quote}\n\nSurrounding text:\n{context}")  # fmt: skip
        out = parse_json(llm.complete(CHECK_SYSTEM, user, max_tokens=1500).text) or {}
        return {"qid": qid, "question": it.question, "reference": ref,
                "check": {k: out.get(k, "unparsed") for k in ("reference", "question", "why")}}  # fmt: skip

    with ThreadPoolExecutor(6) as ex:
        rows = list(ex.map(one, qids))
    OUT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), "utf-8")
    flagged = [r for r in rows if r["check"]["reference"] != "ok" or r["check"]["question"] != "ok"]
    print(f"{len(rows)} items checked, {len(flagged)} flagged -> {OUT}")
    for r in flagged:
        c = r["check"]
        print(f"{r['qid']} ref={c['reference']} q={c['question']}: {c['why']}")


if __name__ == "__main__":
    main()
