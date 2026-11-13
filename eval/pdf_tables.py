"""Measure how well PDF parsing recovers tables, against a structured edition of the same text.

law.go.kr serves each statute as PDF and as HWPX; govinfo serves the CFR as PDF and
as XML (GPOTABLE). Both are structured, so they serve as ground truth for the tables
our parser extracts from the PDF (a labor and a real-estate Korean statute, and
Regulation X, 12 CFR 1024, in English):

- cell exact:    share of truth cells found as one cell of some PDF table
- cell in table: share of truth cells whose text lies inside PDF table blocks, cell
                 borders aside. HWPX keeps multi-line cells and nested tables as one
                 cell where the PDF shows several, so "cell exact" undercounts
- row match:     share of truth rows rebuilt as one PDF table row (same cells, in order)
- chars kept:    share of the truth tables' characters (as a multiset, order ignored)
                 found anywhere in the PDF output: content lost vs. content moved

Cells are compared with all whitespace removed (PDF line wraps differ from HWPX), and
empty cells are left out (merged cells are empty in HWPX, missing in PDF tables).

    cd backend && uv run python ../eval/pdf_tables.py
"""

import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

from sdrag.ingest import layout
from sdrag.ingest.parse import parse

DATA = Path(__file__).resolve().parent.parent / "data"
RAW = DATA / "raw"


def corpus_pair(pair: str) -> Path:
    """<family>/<kind> folder of a Korean statute, in whichever field holds it."""
    return next(r / pair for r in layout.kr_family_roots(DATA) if (r / pair).is_dir())


PAIRS = ["kr-occupational-safety/rul", "kr-industrial-accident/dec", "kr-housing-lease/dec"]
CFR = [("us-cfr12-1024", RAW / "truth" / "us-cfr12" / "1024" / "us-cfr12-1024-truth.xml")]


def norm(cell: str) -> str:
    return re.sub(r"\s+", "", cell)


def rows_of(doc) -> list[tuple[str, ...]]:
    return [
        tuple(n for c in r if (n := norm(c)))
        for b in doc.blocks
        if b.kind == "table"
        for r in b.rows or []
    ]


def xml_rows(path: Path) -> tuple[list[tuple[str, ...]], int]:
    """Rows of every GPOTABLE in a govinfo CFR XML file (column heads as the first row)."""
    tables = list(ET.parse(path).getroot().iter("GPOTABLE"))
    rows = []
    for t in tables:
        heads = tuple(n for h in t.iter("CHED") if (n := norm("".join(h.itertext()))))
        rows += [heads] if heads else []
        for row in t.iter("ROW"):
            rows.append(tuple(n for e in row.iter("ENT") if (n := norm("".join(e.itertext())))))
    return rows, len(tables)


def score(truth_path: Path, pdf_path: Path) -> dict:
    pdf = parse(pdf_path)
    if truth_path.suffix == ".xml":
        t_rows, n_truth = xml_rows(truth_path)
    else:
        truth = parse(truth_path)
        t_rows, n_truth = rows_of(truth), sum(b.kind == "table" for b in truth.blocks)
    return compare([r for r in t_rows if r], n_truth, pdf)


def compare(t_rows: list[tuple[str, ...]], n_truth: int, pdf) -> dict:
    t_cells = [c for r in t_rows for c in r]
    p_rows = Counter(r for r in rows_of(pdf) if r)
    p_cells = Counter(c for r in rows_of(pdf) for c in r)
    p_tables = norm("".join(b.text for b in pdf.blocks if b.kind == "table").replace("|", ""))
    p_all = Counter(norm("".join(b.text for b in pdf.blocks)).replace("|", ""))
    t_chars = Counter("".join(t_cells))
    return {
        "truth tables": n_truth,
        "pdf tables": sum(b.kind == "table" for b in pdf.blocks),
        "cell exact": sum((Counter(t_cells) & p_cells).values()) / len(t_cells),
        "cell in table": sum(c in p_tables for c in t_cells) / len(t_cells),
        "row match": sum((Counter(t_rows) & p_rows).values()) / len(t_rows),
        "chars kept": sum((t_chars & p_all).values()) / sum(t_chars.values()),
        "cells": len(t_cells),
        "rows": len(t_rows),
    }


def main() -> None:
    cases = []
    for pair in PAIRS:
        truth = next((RAW / "truth" / pair).glob("*.hwpx"), None)
        if truth is None:
            print(
                f"{pair:28} no HWPX ground truth in data/raw/truth/{pair}/ (data/scripts/fetch.py)"
            )
            continue
        cases.append((pair, truth, next(corpus_pair(pair).glob("*.pdf"))))
    for doc_id, truth in CFR:
        cases.append(
            (doc_id, truth, layout.corpus_dir(DATA, doc_id, "realestate") / f"{doc_id}.pdf")
        )
    for pair, truth, pdf in cases:
        s = score(truth, pdf)
        print(
            f"{pair:28} tables {s['pdf tables']:3}/{s['truth tables']:<3} "
            f"cell exact {s['cell exact']:6.1%}  in table {s['cell in table']:6.1%}  "
            f"row match {s['row match']:6.1%}  chars kept {s['chars kept']:6.1%}  "
            f"({s['cells']} cells, {s['rows']} rows)"
        )


if __name__ == "__main__":
    sys.exit(main())
