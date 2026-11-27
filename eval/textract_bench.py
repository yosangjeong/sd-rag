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
ENGINES = ("textract-lines", "textract-tables")

client = boto3.client(
    "textract", region_name="ap-southeast-2",
    config=Config(retries={"max_attempts": 8, "mode": "adaptive"}),
)  # fmt: skip


def analyze(image) -> tuple[dict, float]:
    data = jpeg(image)
    key = hashlib.sha256(b"analyze-tables\n" + data).hexdigest()
    path = RAW / f"{key}.json"
    if path.exists():
        r = json.loads(path.read_text("utf-8"))
        return r["response"], r["seconds"]
    t = time.perf_counter()
    resp = client.analyze_document(Document={"Bytes": data}, FeatureTypes=["TABLES"])
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
        resp, seconds = analyze(render_page(scan_path(profile, doc_id, page), 1))
        for engine, text in texts(resp).items():
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
    rows, secs = [], []
    for p in plan:
        resp, seconds = analyze(render_page(pdf, p["sheet"]))
        secs.append(seconds)
        tx = texts(resp)
        rows.append((p, qwen[p["sheet"]], {e: scores(tx[e], p["truth"]) for e in ENGINES}))

    def f(m):
        return f"{m['cer']:.1%} / {m['extra']:.1%}"

    lines = ["### Real iPhone scan, 9 sheets (CER / extra)", "",
             "| sheet | content | scanned | qwen3-vl-235b | textract-lines | textract-tables |",
             "|---|---|---|---|---|---|"]  # fmt: skip
    for p, q, t in rows:
        lines.append(f"| {p['sheet']} | {p['kind']} | {p['how']} | {f(q)} | "
                     f"{f(t['textract-lines'])} | {f(t['textract-tables'])} |")  # fmt: skip

    def mean(ms, k):
        return sum(m[k] for m in ms) / len(ms)

    q_all = [q for _, q, _ in rows]
    cols = [q_all] + [[t[e] for _, _, t in rows] for e in ENGINES]
    lines.append("| **all** | | | " + " | ".join(
        f"**{mean(c, 'cer'):.1%}** / {mean(c, 'extra'):.1%}" for c in cols) + " |")  # fmt: skip
    qwen_s = sum(q["seconds"] for q in q_all) / len(q_all)
    note = (
        f"Textract {sum(secs) / len(secs):.1f} s/page on the real scan (Qwen3-VL: {qwen_s:.1f} s)."
    )
    lines += ["", note, ""]
    return lines


def main() -> None:
    n = len(bench_jobs()) + len(json.loads((REAL / "plan.json").read_text("utf-8")))
    print(f"{n} pages, AnalyzeDocument TABLES ~$0.015-0.02/page -> about ${n * 0.02:.2f} at most")
    if "--probe" in sys.argv:
        d, pg, _ = PAGES[0]
        resp, s = analyze(render_page(scan_path("office", d, pg), 1))
        print(s, texts(resp)["textract-tables"][:600])
        return
    run_bench()
    body = bench_table() + real_table()
    print("\n".join(body))
    # the tables of data/eval/results/ocr-textract.md (its text around them is written by hand)


if __name__ == "__main__":
    main()
