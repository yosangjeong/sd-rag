"""Amazon Textract on the same OCR pages as Qwen3-VL (evaluation only; the service
engine stays BedrockVisionOcr).

One AnalyzeDocument call (FeatureTypes=["TABLES"]) per page image, rendered exactly as
ingestion renders it (sdrag.ingest.ocr.render_page, JPEG like the Bedrock engine gets).
Its response holds both the plain LINE blocks (the same text detection
DetectDocumentText returns) and the TABLE cells, so two outputs are scored from one
call:

- textract-lines:  LINE blocks in the order Textract returns them
- textract-tables: the same, with the lines that fall inside a table replaced by the
                   table as "| a | b |" rows (what the Qwen3-VL prompt asks for)

A second call per page with FeatureTypes=["TABLES", "LAYOUT"] gives a third output:

- textract-layout: lines in the reading order of the LAYOUT blocks (Textract's own
                   reading-order analysis), tables as "| a | b |" rows

``--agree`` then simulates Textract as a check on Qwen3-VL (no new calls): pages where
the two outputs differ by more than a threshold would be read again.

Raw responses are cached on disk (data/raw/bench/ocr/textract-raw/), keyed by the
image bytes, so re-scoring is free. Pages: eval/ocr_bench.py PAGES x office/poor, and
the 9 sheets of the real iPhone scan (eval/real_scan.py). Scored with the same norm()
and the same CER / recall / extra as both of those scripts.

    cd backend && AWS_PROFILE=<profile> uv run python ../eval/textract_bench.py
"""

import hashlib
import json
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import boto3
from botocore.config import Config
from ocr_bench import BENCH, PAGES, PROFILES, norm, out_path, scan_path
from rapidfuzz.distance import Levenshtein

from sdrag.ingest.ocr import jpeg, render_page

ROOT = Path(__file__).resolve().parent.parent
RAW = BENCH / "textract-raw"
REAL = ROOT / "data" / "raw" / "bench" / "real-scan"
RESULTS = ROOT / "data" / "eval" / "results"
QWEN = "qwen3-vl-235b"
QWEN_REAL = RESULTS / "ocr-real-scan.json"
ENGINES = ("textract-lines", "textract-tables", "textract-layout")
FEATURES = {"tables": ["TABLES"], "layout": ["TABLES", "LAYOUT"]}

client = boto3.client(
    "textract", region_name="ap-southeast-2",
    config=Config(retries={"max_attempts": 8, "mode": "adaptive"}),
)  # fmt: skip


def analyze(image, features: str = "tables") -> tuple[dict, float]:
    data = jpeg(image)
    tag = "analyze-tables" if features == "tables" else f"analyze-{features}"
    key = hashlib.sha256(tag.encode() + b"\n" + data).hexdigest()
    path = RAW / f"{key}.json"
    if path.exists():
        r = json.loads(path.read_text("utf-8"))
        return r["response"], r["seconds"]
    t = time.perf_counter()
    resp = client.analyze_document(Document={"Bytes": data}, FeatureTypes=FEATURES[features])
    seconds = round(time.perf_counter() - t, 2)
    resp.pop("ResponseMetadata", None)
    RAW.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"response": resp, "seconds": seconds}, ensure_ascii=False), "utf-8")
    return resp, seconds


def texts(resp: dict) -> dict[str, str]:
    blocks = {b["Id"]: b for b in resp["Blocks"]}

    def children(b, kind="CHILD"):
        return [i for r in b.get("Relationships", []) if r["Type"] == kind for i in r["Ids"]]

    lines = [b for b in resp["Blocks"] if b["BlockType"] == "LINE"]
    plain = "\n".join(b["Text"] for b in lines)

    # words that sit inside each table, and the table as markdown rows
    word_table: dict[str, int] = {}
    tables: list[str] = []
    for t in (b for b in resp["Blocks"] if b["BlockType"] == "TABLE"):
        cells = [blocks[i] for i in children(t) if blocks[i]["BlockType"] == "CELL"]
        rows: dict[int, dict[int, str]] = defaultdict(dict)
        for c in cells:
            words = [blocks[i] for i in children(c) if blocks[i]["BlockType"] == "WORD"]
            for w in words:
                word_table[w["Id"]] = len(tables)
            rows[c["RowIndex"]][c["ColumnIndex"]] = " ".join(w["Text"] for w in words)
        width = max((max(r) for r in rows.values()), default=0)
        tables.append("\n".join(
            "| " + " | ".join(rows[i].get(j, "") for j in range(1, width + 1)) + " |"
            for i in sorted(rows)
        ))  # fmt: skip

    out, placed = [], set()
    for b in lines:
        ids = [word_table.get(w) for w in children(b)]
        inside = [i for i in ids if i is not None]
        if inside and len(inside) * 2 >= len(ids):  # a line mostly inside a table
            if inside[0] not in placed:
                placed.add(inside[0])
                out.append(tables[inside[0]])
            continue
        out.append(b["Text"])
    out += [t for i, t in enumerate(tables) if i not in placed]
    return {"textract-lines": plain, "textract-tables": "\n".join(out)}


def layout_text(resp: dict) -> str:
    """Lines in the order of the LAYOUT blocks (nested LAYOUT blocks, e.g. the items of
    a LAYOUT_LIST, are followed); a LAYOUT_TABLE is written as its TABLE's rows. Lines no
    layout block covers go last. Each line is written once."""
    blocks = {b["Id"]: b for b in resp["Blocks"]}

    def children(b):
        return [i for r in b.get("Relationships", []) if r["Type"] == "CHILD" for i in r["Ids"]]

    word_table: dict[str, int] = {}
    tables: list[str] = []
    for t in (b for b in resp["Blocks"] if b["BlockType"] == "TABLE"):
        rows: dict[int, dict[int, str]] = defaultdict(dict)
        for c in (blocks[i] for i in children(t) if blocks[i]["BlockType"] == "CELL"):
            words = [blocks[i] for i in children(c) if blocks[i]["BlockType"] == "WORD"]
            for w in words:
                word_table[w["Id"]] = len(tables)
            rows[c["RowIndex"]][c["ColumnIndex"]] = " ".join(w["Text"] for w in words)
        width = max((max(r) for r in rows.values()), default=0)
        tables.append("\n".join(
            "| " + " | ".join(rows[i].get(j, "") for j in range(1, width + 1)) + " |"
            for i in sorted(rows)
        ))  # fmt: skip

    def lines_of(b) -> list[str]:
        out = []
        for i in children(b):
            c = blocks.get(i)
            if c is None:
                continue
            if c["BlockType"] == "LINE":
                out.append(i)
            elif c["BlockType"].startswith("LAYOUT_"):
                out += lines_of(c)
        return out

    out, done, placed = [], set(), set()
    for b in resp["Blocks"]:
        if not b["BlockType"].startswith("LAYOUT_"):
            continue
        ids = [i for i in lines_of(b) if i not in done]
        if not ids:
            continue
        done.update(ids)
        if b["BlockType"] == "LAYOUT_TABLE":
            inside = {word_table[w] for i in ids for w in children(blocks[i]) if w in word_table}
            new = sorted(inside - placed)
            if new:
                placed.update(new)
                out += [tables[k] for k in new]
                continue
        out += [blocks[i]["Text"] for i in ids]
    # every line is written once; a TABLE outside any LAYOUT_TABLE stays as its lines
    # (appending it too wrote those words twice)
    out += [b["Text"] for b in resp["Blocks"] if b["BlockType"] == "LINE" and b["Id"] not in done]
    return "\n".join(out)


def all_texts(image) -> tuple[dict[str, str], float, float]:
    resp, s1 = analyze(image)
    lay, s2 = analyze(image, "layout")
    return {**texts(resp), "textract-layout": layout_text(lay)}, s1, s2


def scores(o: str, t: str) -> dict:
    o, t = norm(o), norm(t)
    common = sum((Counter(o) & Counter(t)).values())
    return {"cer": Levenshtein.distance(o, t) / len(t), "recall": common / len(t),
            "extra": 1 - common / len(o) if o else 0.0}  # fmt: skip


def bench_jobs():
    return [(p, d, pg, k) for p in PROFILES for d, pg, k in PAGES]


def run_bench() -> None:
    def one(job):
        profile, doc_id, page, _ = job
        tx, s1, s2 = all_texts(render_page(scan_path(profile, doc_id, page), 1))
        for engine, text in tx.items():
            seconds = s2 if engine == "textract-layout" else s1
            out = out_path(engine, profile, doc_id, page)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps({"text": text, "input_tokens": 0, "output_tokens": 0,
                                       "seconds": seconds, "split": False},
                                      ensure_ascii=False, indent=1), "utf-8")  # fmt: skip

    with ThreadPoolExecutor(4) as pool:
        list(pool.map(one, bench_jobs()))


def bench_table() -> list[str]:
    from ocr_bench import score

    kinds = ["ko-body", "ko-table", "en-2col", "en-3col", "en-table"]
    lines = []
    for profile in PROFILES:
        lines += [f"### Synthetic scans, {profile} quality (CER / recall / extra, page-weighted mean)", "",
                  "| engine | " + " | ".join(kinds) + " | s/page |",
                  "|---|" + "---|" * (len(kinds) + 1)]  # fmt: skip
        for engine in (QWEN, *ENGINES):
            s = score(engine)
            cells, secs = [], []
            for k in kinds:
                m = s.get((profile, k))
                if not m:
                    cells.append("-")
                    continue
                avg = {x: sum(v) / len(v) for x, v in m.items()}
                cells.append(f"{avg['cer']:.1%} / {avg['recall']:.1%} / {avg['extra']:.1%}")
                secs += m["seconds"]
            lines.append(f"| {engine} | " + " | ".join(cells) + f" | {sum(secs) / len(secs):.1f} |")
        lines.append("")
    return lines


def real_table() -> list[str]:
    plan = json.loads((REAL / "plan.json").read_text("utf-8"))
    qwen = {r["sheet"]: r for r in json.loads(QWEN_REAL.read_text("utf-8"))}
    pdf = REAL / "iphone-scan.pdf"
    rows, secs, secs_l = [], [], []
    for p in plan:
        tx, seconds, s2 = all_texts(render_page(pdf, p["sheet"]))
        secs.append(seconds)
        secs_l.append(s2)
        rows.append((p, qwen[p["sheet"]], {e: scores(tx[e], p["truth"]) for e in ENGINES}))

    def f(m):
        return f"{m['cer']:.1%} / {m['extra']:.1%}"

    lines = ["### Real iPhone scan, 9 sheets (CER / extra)", "",
             "| sheet | content | scanned | qwen3-vl-235b | " + " | ".join(ENGINES) + " |",
             "|---|---|---|---|" + "---|" * len(ENGINES)]  # fmt: skip
    for p, q, t in rows:
        lines.append(f"| {p['sheet']} | {p['kind']} | {p['how']} | {f(q)} | "
                     + " | ".join(f(t[e]) for e in ENGINES) + " |")  # fmt: skip

    def mean(ms, k):
        return sum(m[k] for m in ms) / len(ms)

    q_all = [q for _, q, _ in rows]
    cols = [q_all] + [[t[e] for _, _, t in rows] for e in ENGINES]
    lines.append("| **all** | | | " + " | ".join(
        f"**{mean(c, 'cer'):.1%}** / {mean(c, 'extra'):.1%}" for c in cols) + " |")  # fmt: skip
    qwen_s = sum(q["seconds"] for q in q_all) / len(q_all)
    note = (
        f"Textract {sum(secs) / len(secs):.1f} s/page on the real scan, with LAYOUT "
        f"{sum(secs_l) / len(secs_l):.1f} s (Qwen3-VL: {qwen_s:.1f} s)."
    )
    lines += ["", note, ""]
    return lines


def agree_rows() -> list[dict]:
    """Per page: Qwen3-VL's error against the truth, and how far it is from Textract
    (LAYOUT output): `diff` = edit distance / longer length (order counts), `only` =
    share of Qwen3-VL's characters Textract does not have (order does not count)."""
    pages = []
    for profile, doc_id, page, _ in bench_jobs():
        q = json.loads(out_path(QWEN, profile, doc_id, page).read_text("utf-8"))["text"]
        t = json.loads(out_path("textract-layout", profile, doc_id, page).read_text("utf-8"))[
            "text"
        ]
        truth = json.loads(
            scan_path(profile, doc_id, page).with_suffix(".truth.json").read_text("utf-8")
        )[str(page)]
        pages.append((f"{profile} {doc_id} p{page}", q, t, truth))
    plan = json.loads((REAL / "plan.json").read_text("utf-8"))
    qwen = {r["sheet"]: r for r in json.loads(QWEN_REAL.read_text("utf-8"))}
    for p in plan:
        tx, _, _ = all_texts(render_page(REAL / "iphone-scan.pdf", p["sheet"]))
        pages.append(
            (
                f"real sheet {p['sheet']}",
                qwen[p["sheet"]]["text"],
                tx["textract-layout"],
                p["truth"],
            )
        )
    rows = []
    for name, q, t, truth in pages:
        qn, tn = norm(q), norm(t)
        common = sum((Counter(qn) & Counter(tn)).values())
        rows.append({"page": name, "qwen_cer": scores(q, truth)["cer"],
                     "diff": Levenshtein.distance(qn, tn) / max(len(qn), len(tn), 1),
                     "only": 1 - common / len(qn) if qn else 0.0})  # fmt: skip
    return rows


def agree_table(bad: float = 0.05, thresholds=(0.03, 0.05, 0.10)) -> list[str]:
    rows = agree_rows()
    n_bad = sum(r["qwen_cer"] > bad for r in rows)
    lines = [f"### Textract as a check on Qwen3-VL ({len(rows)} pages, {n_bad} with Qwen3-VL CER over {bad:.0%})", "",
             "| flag a page when | flagged | of them Qwen3-VL CER > 5% (caught) | missed bad pages | good pages flagged |",
             "|---|---|---|---|---|"]  # fmt: skip
    for key, label in (
        ("diff", "edit distance Qwen3-VL vs Textract"),
        ("only", "Qwen3-VL characters Textract lacks"),
    ):
        for th in thresholds:
            f = [r for r in rows if r[key] > th]
            caught = sum(r["qwen_cer"] > bad for r in f)
            lines.append(
                f"| {label} > {th:.0%} | {len(f)} | {caught} | {n_bad - caught} | {len(f) - caught} |"
            )
    lines += ["", "| page | Qwen3-VL CER | diff | only |", "|---|---|---|---|"]
    lines += [f"| {r['page']} | {r['qwen_cer']:.1%} | {r['diff']:.1%} | {r['only']:.1%} |"
              for r in sorted(rows, key=lambda r: -r["qwen_cer"]) if r["qwen_cer"] > bad or r["diff"] > 0.05]  # fmt: skip
    return lines + [""]


def main() -> None:
    n = len(bench_jobs()) + len(json.loads((REAL / "plan.json").read_text("utf-8")))
    print(
        f"{n} pages; new calls are TABLES+LAYOUT (~$0.015 + $0.004 per page): about "
        f"${n * 0.02:.2f} at most (TABLES-only responses are cached)"
    )
    if "--probe" in sys.argv:
        d, pg, _ = PAGES[0]
        tx, s1, s2 = all_texts(render_page(scan_path("office", d, pg), 1))
        print(s1, s2, tx["textract-layout"][:600])
        return
    if "--agree" in sys.argv:
        print("\n".join(agree_table()))
        return
    run_bench()
    body = bench_table() + real_table()
    print("\n".join(body))
    # the tables of data/eval/results/ocr-textract.md (its text around them is written by hand)


if __name__ == "__main__":
    main()
