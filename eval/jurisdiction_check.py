"""Answers that cite the other country's law: for each question of an answer run
(eval/answers.py output), does a citation come from a public statute of another
country than the expected one? Expected: the gold document's country for test items
(some questions name the other country), the language's for the unanswerable real
questions (Korean -> kr-, English -> us-; none names a country).

    python3 eval/jurisdiction_check.py data/eval/results/answers/v4-prompt-rule [more runs ...]
"""

import json
import re
import sys
from pathlib import Path


def own(question: str) -> str:
    hangul = len(re.findall(r"[가-힣]", question))
    return "kr" if hangul > len(re.findall(r"[A-Za-z]", question)) / 3 else "us"


EVAL = Path(__file__).resolve().parents[1] / "data" / "eval"
GOLD = {}
for s in ("test", "test_re"):
    for line in (EVAL / f"{s}.jsonl").read_text("utf-8").splitlines():
        it = json.loads(line)
        GOLD[it["qid"]] = it["gold"][0]["doc_id"].split("-", 1)[0]


def other_cited(row: dict) -> bool:
    prefixes = {c.split("-", 1)[0] for c in row["cited"]} & {"kr", "us"}
    return bool(prefixes - {GOLD.get(row["qid"]) or own(row["question"])})


for run in map(Path, sys.argv[1:]):
    for name in ("test_sample", "unanswerable", "test_re", "unanswerable_re"):
        if not (run / f"{name}.jsonl").exists():
            continue
        rows = [json.loads(x) for x in (run / f"{name}.jsonl").read_text("utf-8").splitlines()]
        n = sum(other_cited(r) for r in rows)
        print(f"{run.name:32} {name:12} other country cited: {n} / {len(rows)}")
