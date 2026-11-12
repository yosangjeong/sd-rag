"""Rewrite the "Composition" section of data/eval/README.md from the set files.

    cd backend && uv run python ../eval/describe_sets.py
"""

from collections import Counter

from evalset import DATA, doc_texts, load_items

README = DATA / "eval" / "README.md"
SETS = ("test", "dev", "real", "real_unanswerable")


def main() -> None:
    texts = doc_texts()
    sets = {n: load_items(DATA / "eval" / f"{n}.jsonl") for n in SETS}
    lines = ["## Composition", "", "| | " + " | ".join(SETS) + " |", "|---" * (len(SETS) + 1) + "|"]
    lines.append("| items | " + " | ".join(str(len(v)) for v in sets.values()) + " |")
    breakdowns = [
        (
            "question -> answer",
            lambda i: f"{i.q_lang} -> {'+'.join(sorted(i.answer_langs(texts)))}",
        ),
        ("answer file type", lambda i: "+".join(sorted(i.file_types(texts)))),
        ("kind", lambda i: i.kind),
        ("style", lambda i: i.meta.get("style", "real")),
    ]
    for label, f in breakdowns:
        counts = {n: Counter(f(i) for i in v if i.gold) for n, v in sets.items()}
        for k in sorted({k for c in counts.values() for k in c}):
            lines.append(
                f"| {label}: {k} | " + " | ".join(str(counts[n].get(k, 0)) for n in SETS) + " |"
            )
    lines.append(
        "| with also-spans | "
        + " | ".join(str(sum(1 for i in v if i.also)) for v in sets.values())
        + " |"
    )
    lines.append("| gold annotated by hand | " + " | ".join(
        str(sum(1 for i in v if i.meta.get("manual"))) for v in sets.values()) + " |")  # fmt: skip
    note = ("A real question's language is its source's: easylaw questions are Korean, "
            "dol.gov questions English, so the real set has no cross-lingual items.")  # fmt: skip
    lines += ["", note, ""]
    text = README.read_text("utf-8")
    head = text[: text.index("## Composition")] if "## Composition" in text else text + "\n"
    README.write_text(head + "\n".join(lines), "utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
