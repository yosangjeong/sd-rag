"""Stage 1 of the generated evaluation set: choose the passages questions are written from.

Answers are chosen before questions, from the documents' canonical text, not from the
index: sampling chunks would favor the chunking strategy that made them. A passage is
a piece of one article / annex / US section (cut at paragraph boundaries to at most
~350 tokens) or a few rows of a table with its header. The question generator then
quotes the minimal evidence inside the passage, and that quote is the gold span.

Strata: the brief asks for results by language and by file type, so passages are drawn
per (answer language, file type) cell, spread over the documents of the cell. Kinds:

- fact: a text passage
- table: table rows (Korean annexes, CFR / Federal Register tables)
- multi: two passages that only answer together: an article of a Korean act that
  leaves a detail to the decree or rule ("대통령령으로 정하는"), and the decree or rule
  article that cites it ("법 제N조"); the question needs both

Each passage also gets the question language: some answers in Korean are asked in
English and vice versa (cross-lingual retrieval is required).

Skipped: front matter (no heading), 부칙 (transitional provisions), repealed US
sections, passages under 120 characters.

    cd backend && uv run python ../eval/sample_passages.py
"""

import json
import random
import re
from collections import Counter, defaultdict

from evalset import CACHE, DocText, doc_texts

from sdrag.ingest.chunk import split_span

SEED = 20261112
OUT = CACHE / "qa" / "passages.jsonl"

# items per (answer lang, file type); 400 in all = 80 dev + 320 test. RESERVE times as
# many passages are drawn: about a third fail generation or the check (boilerplate,
# unreadable rows), and the set is filled from the survivors in sampling order
# Korean answers come in four formats; English ones are PDFs and one synthetic scan
# (the 1938 Federal Register is a real scan, but govinfo ships it with a text layer, so
# it is parsed, and reported, as a PDF)
TARGET = {
    ("ko", "pdf"): 60, ("ko", "hwpx"): 60, ("ko", "docx"): 60, ("ko", "scan"): 45,
    ("en", "pdf"): 160, ("en", "scan"): 15,
}  # fmt: skip
# share of each cell asked in the other language
RESERVE = 1.6
CROSS = {"ko": 0.33, "en": 0.45}
TABLE_SHARE, MULTI_SHARE = 0.15, 0.12
MAX_TOKENS, MIN_CHARS = 350, 120


def skip_heading(h: str | None, headed: bool = True) -> bool:
    if h is None:
        return headed  # front matter, unless the document has no headings at all
    return h.startswith("부칙") or "Repealed" in h


def text_units(d: DocText) -> list[tuple[int, int, str]]:
    """(start, end, heading) of runs of text blocks under one heading."""
    units: list[list] = []
    headed = any(b.heading for b in d.blocks)
    for b in d.blocks:
        if b.kind != "text" or skip_heading(b.heading, headed):
            continue
        if units and units[-1][2] == b.heading and units[-1][1] + 2 >= b.start:
            units[-1][1] = b.end
        else:
            units.append([b.start, b.end, b.heading])
    return [tuple(u) for u in units]


def text_passages(d: DocText) -> list[dict]:
    out = []
    for s, e, h in text_units(d):
        for ps, pe in split_span(d.text, s, e, MAX_TOKENS):
            if pe - ps >= MIN_CHARS:
                out.append({"doc_id": d.id, "start": ps, "end": pe, "heading": h})
    return out


def table_passages(d: DocText, rows_per: int = 4) -> list[dict]:
    """Windows of a few data rows; the header row goes along as context (not gold)."""
    out = []
    for b in d.blocks:
        if b.kind != "table" or skip_heading(b.heading):
            continue
        lines = d.text[b.start : b.end].split("\n")
        if len(lines) < 3:
            continue
        header = lines[0]
        pos = b.start + len(header) + 1
        starts = []
        for ln in lines[1:]:
            starts.append((pos, pos + len(ln)))
            pos += len(ln) + 1
        for i in range(0, len(starts), rows_per):
            ws, we = starts[i][0], starts[min(i + rows_per, len(starts)) - 1][1]
            if we - ws >= MIN_CHARS // 2:
                out.append({"doc_id": d.id, "start": ws, "end": we, "heading": b.heading,
                            "context": header})  # fmt: skip
    return out


RE_CITE = re.compile(r"법\s*제(\d+)조(의\d+)?")
RE_DELEGATE = re.compile(r"대통령령|고용노동부령")


def multi_pairs(texts: dict[str, DocText]) -> list[dict]:
    """(act article that delegates, decree/rule passage that cites it)."""
    pairs = []
    for d in texts.values():
        m = re.match(r"(kr-.+)-(dec|rul)$", d.id)
        if not m or f"{m.group(1)}-law" not in texts:
            continue
        law = texts[f"{m.group(1)}-law"]
        articles = {}
        for s, e, h in text_units(law):
            if a := re.match(r"제(\d+)조(의\d+)?\(", h):
                articles[(a.group(1), a.group(2) or "")] = (s, e, h)
        for p in text_passages(d):
            for c in RE_CITE.finditer(d.text, p["start"], p["end"]):
                art = articles.get((c.group(1), c.group(2) or ""))
                if art and RE_DELEGATE.search(law.text, art[0], art[1]):
                    s, e, h = art
                    law_p = next(
                        (x for x in text_passages(law) if x["start"] >= s and x["end"] <= e
                         and RE_DELEGATE.search(law.text, x["start"], x["end"])),
                        None,
                    )  # fmt: skip
                    if law_p:
                        pairs.append({"parts": [law_p, p]})
                    break
    return pairs


def main() -> None:
    rng = random.Random(SEED)
    texts = doc_texts()
    by_cell: dict[tuple, list[DocText]] = defaultdict(list)
    for d in texts.values():
        by_cell[(d.lang, d.file_type)].append(d)
    pairs = multi_pairs(texts)
    rng.shuffle(pairs)

    out = []
    for cell, target in TARGET.items():
        n = round(target * RESERVE)
        docs = sorted(by_cell[cell], key=lambda d: d.id)
        lang, ftype = cell
        n_multi = round(n * MULTI_SHARE) if lang == "ko" and ftype != "scan" else 0
        # a pair belongs to the cell of its decree / rule passage (the part the act sends
        # the reader to); its act article may be in another format, which is fine
        cell_pairs = [p for p in pairs if texts[p["parts"][1]["doc_id"]].file_type == ftype]
        chosen = [{"kind": "multi", **p} for p in cell_pairs[:n_multi]]
        tables = [t for d in docs for t in table_passages(d)]
        n_table = min(round(n * TABLE_SHARE), len(tables))
        chosen += [{"kind": "table", "parts": [t]} for t in rng.sample(tables, n_table)]
        # fact passages: round-robin over the cell's documents so no statute dominates
        pools = {d.id: rng.sample(text_passages(d), len(text_passages(d))) for d in docs}
        used = {(p["parts"][0]["doc_id"], p["parts"][0]["start"]) for p in chosen}
        while len(chosen) < n and any(pools.values()):
            for d in docs:
                if len(chosen) >= n:
                    break
                while pools[d.id]:
                    p = pools[d.id].pop()
                    if (p["doc_id"], p["start"]) not in used:
                        chosen.append({"kind": "fact", "parts": [p]})
                        used.add((p["doc_id"], p["start"]))
                        break
        for c in chosen:
            c["answer_lang"], c["file_type"] = lang, ftype
            c["q_lang"] = ("en" if lang == "ko" else "ko") if rng.random() < CROSS[lang] else lang
        out += chosen
        rng.shuffle(chosen)  # kinds were appended in blocks; filling takes them mixed
        for rank, c in enumerate(chosen):
            c["rank"] = rank  # filling order within the cell
        print(f"{lang} {ftype:5} {len(chosen):4} / {n}  "
              f"{dict(Counter(c['kind'] for c in chosen))}  docs={len(docs)}")  # fmt: skip

    rng.shuffle(out)
    for i, c in enumerate(out, 1):
        c["pid"] = f"p{i:04d}"
        for part in c["parts"]:
            part["text"] = texts[part["doc_id"]].text[part["start"] : part["end"]]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("".join(json.dumps(c, ensure_ascii=False) + "\n" for c in out), "utf-8")
    print(f"{len(out)} passages -> {OUT}")
    print("question language:", Counter((c["q_lang"], c["answer_lang"]) for c in out))


if __name__ == "__main__":
    main()
