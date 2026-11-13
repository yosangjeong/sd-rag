"""Re-grade the stored answers of every answer version with the current judge.

The answers are kept (results/answers/<version>/test_sample.jsonl, test_re.jsonl), so
a new judge needs no new answers: each row gets ``correct_v2`` next to the ``correct``
grade it had (judge v1, eval/judges.py), and results/answers/rejudge.md compares the
versions under both judges, with and without the flagged items
(data/eval/item_flags.json). Only the correctness judge changed; groundedness and
declining keep their grades.

    cd backend && AWS_PROFILE=<profile> uv run python ../eval/rejudge.py
"""

import json
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

from evalset import DATA, LLM_CACHE, load_items
from judges import correct_prompt, correct_user

from sdrag.common.config import settings
from sdrag.common.llm import BedrockChat, CachedChat, parse_json

RESULTS = DATA / "eval" / "results" / "answers"
JUDGE_MODEL = "deepseek.v3.2"
SETS = {"test_sample": "labor", "test_re": "real-estate"}


def share(rows: list[dict], key: str) -> str:
    c = Counter(r[key]["grade"] for r in rows)
    n = len(rows)
    return f"{c['correct'] / n:.0%} / {c['partial'] / n:.0%} / {c['wrong'] / n:.0%}"


def main() -> None:
    items = {
        i.qid: i for s in ("test", "test_re") for i in load_items(DATA / "eval" / f"{s}.jsonl")
    }
    flags = json.loads((DATA / "eval" / "item_flags.json").read_text("utf-8"))["flags"]
    judge = CachedChat(BedrockChat(JUDGE_MODEL, settings.aws_region), LLM_CACHE)

    def grade(field: str, row: dict) -> dict:
        it = items[row["qid"]]
        ref = it.meta.get("check_answer") or it.meta.get("answer", "")
        user = correct_user(it.question, ref, it.gold[0].quote, row["answer"])
        out = parse_json(judge.complete(correct_prompt(field), user, max_tokens=400).text) or {}
        return {"grade": out.get("grade", "unparsed"), "why": out.get("why", ""),
                "key_fact": out.get("key_fact", "")}  # fmt: skip

    lines = [
        "# Answer correctness re-graded (`eval/rejudge.py`)",
        "",
        (
            "correct / partial / wrong; judge v1 and v2 in `eval/judges.py`; flagged items in "
            "`data/eval/item_flags.json`."
        ),
        "",
        "| version | set | n | judge v1 | judge v2 | v2 without flagged |",
        "|---|---|---|---|---|---|",
    ]
    for vdir in sorted(p for p in RESULTS.iterdir() if p.is_dir()):
        for name, field in SETS.items():
            path = vdir / f"{name}.jsonl"
            if not path.exists():
                continue
            rows = [json.loads(x) for x in path.read_text("utf-8").splitlines() if x]
            with ThreadPoolExecutor(6) as ex:
                for r, g in zip(rows, ex.map(grade, [field] * len(rows), rows), strict=True):
                    r["correct_v2"] = g
            path.write_text(
                "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), "utf-8"
            )
            kept = [r for r in rows if r["qid"] not in flags]
            lines.append(f"| {vdir.name} | {field} | {len(rows)} | {share(rows, 'correct')} | "
                         f"{share(rows, 'correct_v2')} | {share(kept, 'correct_v2')} (n={len(kept)}) |")  # fmt: skip
    (RESULTS / "rejudge.md").write_text("\n".join(lines) + "\n", "utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
