"""Answer accuracy of one stored answer run, by question language and by the gold
documents' file type (the brief asks for results split both ways; the retrieval
summaries already are). No model calls: the grades are the run's own.

    cd backend && uv run python ../eval/answer_slices.py v11-final
writes data/eval/results/answers/<version>/slices.md
"""

import json
import sys
from collections import defaultdict

from evalset import DATA, doc_texts, load_items

R = DATA / "eval" / "results" / "answers"
SETS = (("test_sample", "labor", "test.jsonl"), ("test_re", "real estate", "test_re.jsonl"))


def main(version: str) -> None:
    texts = doc_texts()
    note = ("Share graded correct: judge v3 (reported) / judge v2 (stricter). \"mixed\": "
            "questions whose gold spans documents of more than one file type.")
    lines = [f"# Answer accuracy by slice (`{version}`)", "", note, ""]
    for name, label, items_file in SETS:
        path = R / version / f"{name}.jsonl"
        if not path.exists():
            continue
        items = {i.qid: i for i in load_items(DATA / "eval" / items_file)}
        rows = [json.loads(x) for x in path.read_text("utf-8").splitlines() if x]
        for key, title in (("lang", "question language"), ("type", "file type")):
            agg = defaultdict(lambda: [0, 0, 0])
            for r in rows:
                it = items[r["qid"]]
                types = sorted(it.file_types(texts))
                k = it.q_lang if key == "lang" else (types[0] if len(types) == 1 else "mixed")
                a = agg[k]
                a[0] += 1
                a[1] += r["correct"]["grade"] == "correct"
                a[2] += r["correct_v2"]["grade"] == "correct"
            lines += [f"## {label}, by {title}", "", "| slice | n | correct (v3) | correct (v2) |",
                      "|---|---|---|---|"]  # fmt: skip
            lines += [f"| {k} | {n} | {c / n:.0%} | {c2 / n:.0%} |" for k, (n, c, c2) in sorted(agg.items())]
            lines.append("")
    out = R / version / "slices.md"
    out.write_text("\n".join(lines), "utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv[1])
