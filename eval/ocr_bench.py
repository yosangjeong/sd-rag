"""Compare OCR engines on synthetic scans of our own PDF pages (ground truth = page text).

Pages of the corpus PDFs are scanned with data/scripts/scanify.py at two quality
levels (office, poor); each engine transcribes every page image; the output is scored
against the source page's text (pypdf), all whitespace and table pipes removed:

Runs of leader dots count as "..." on both sides (the prompt asks for that: models
loop on long dot runs otherwise).

- CER:     edit distance / truth length. Reading order counts, so tables (whose
           source text order is itself arbitrary) are scored mostly by the next two
- recall:  share of the truth's characters (as a multiset) found in the output
- extra:   share of the output's characters not in the truth: invented text

Raw outputs, token usage and latency are kept under data/raw/bench/ocr/out/ so
re-scoring needs no new calls and every transcription can be inspected.

Transcription goes through sdrag.ingest.ocr, so what is measured is what ingestion
runs (prompt, 200 dpi rendering, repetition guard).

    cd backend && AWS_PROFILE=<profile> uv run python ../eval/ocr_bench.py [--engines a,b]
"""

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path

from rapidfuzz.distance import Levenshtein

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "data" / "scripts"))
import scanify

from sdrag.ingest import layout
from sdrag.ingest.ocr import BedrockVisionOcr, OcrError, render_page

DATA = ROOT / "data"
BENCH = layout.bench(DATA, "ocr")
PROFILES = ["office", "poor"]

# (manifest id, 1-based page, page type)
PAGES = [
    ("kr-labor-standards-law", 1, "ko-body"),
    ("kr-labor-standards-law", 2, "ko-body"),
    ("kr-industrial-accident-dec", 45, "ko-body"),
    ("kr-occupational-safety-rul", 71, "ko-table"),
    ("kr-occupational-safety-rul", 96, "ko-table"),
    ("kr-occupational-safety-rul", 139, "ko-table"),
    ("us-cfr29-541", 3, "en-2col"),
    ("us-cfr29-541", 4, "en-2col"),
    ("us-cfr29-778", 36, "en-table"),
    ("us-fr-2026-20646", 1, "en-table"),
    ("us-fr-2026-20646", 2, "en-3col"),
    ("us-usc29-ch8", 4, "en-2col"),
]

# Bedrock vision models callable from this account in ap-southeast-2 (checked 2026-11-11)
BEDROCK = {
    "claude-sonnet-4.6": "au.anthropic.claude-sonnet-4-6",
    "claude-haiku-4.5": "au.anthropic.claude-haiku-4-5-20251001-v1:0",
    "qwen3-vl-235b": "qwen.qwen3-vl-235b-a22b",
    "nova-pro": "amazon.nova-pro-v1:0",
}


def source_pdf(doc_id: str) -> Path:
    with (DATA / "manifest.csv").open(encoding="utf-8") as f:
        row = next(r for r in csv.DictReader(f) if r["id"] == doc_id)
    from sdrag.ingest import layout

    if doc_id.startswith("kr-"):
        return next(layout.kr_dir(DATA, doc_id, row["tags"]).glob("*.pdf"))
    return layout.corpus_dir(DATA, doc_id, row["tags"]) / f"{doc_id}.pdf"


def scan_path(profile: str, doc_id: str, page: int) -> Path:
    return BENCH / profile / f"{doc_id}-p{page}.pdf"


def build() -> None:
    for profile in PROFILES:
        for doc_id, page, _ in PAGES:
            out = scan_path(profile, doc_id, page)
            if not out.exists():
                scanify.scan(source_pdf(doc_id), out, [page], profile, seed=0)


def out_path(engine: str, profile: str, doc_id: str, page: int) -> Path:
    return BENCH / "out" / engine / profile / f"{doc_id}-p{page}.json"


def transcribe(engine: str) -> None:
    """Through the production OCR code (sdrag.ingest.ocr): prompt, rendering and guards
    are exactly what ingestion uses."""
    ocr = BedrockVisionOcr(BEDROCK[engine], region="ap-southeast-2")
    jobs = [
        (profile, doc_id, page)
        for profile in PROFILES
        for doc_id, page, _ in PAGES
        if not out_path(engine, profile, doc_id, page).exists()
    ]

    def one(job):
        profile, doc_id, page = job
        try:
            res = ocr.transcribe(render_page(scan_path(profile, doc_id, page), 1))
        except OcrError as e:  # keep going; the page is retried on the next run
            print(f"  {engine} {profile} {doc_id} p{page}: {e}")
            return
        out = out_path(engine, profile, doc_id, page)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(asdict(res), ensure_ascii=False, indent=1), encoding="utf-8")

    with ThreadPoolExecutor(4) as pool:
        list(pool.map(one, jobs))


TABLE_RULE = re.compile(r"^\s*\|?[\s|:-]*-{3,}[\s|:-]*$", re.MULTILINE)  # | --- | --- |


LEADER = re.compile(r"[.…·]{3,}")  # leader dots: the prompt asks for '...'


def norm(text: str) -> str:
    text = LEADER.sub("...", re.sub(r"(?<=[.…·])\s+(?=[.…·])", "", TABLE_RULE.sub("", text)))
    return re.sub(r"[\s|]", "", text)


def score(engine: str) -> dict:
    by_type: dict = defaultdict(lambda: defaultdict(list))
    for profile in PROFILES:
        for doc_id, page, kind in PAGES:
            out = out_path(engine, profile, doc_id, page)
            if not out.exists():
                continue
            res = json.loads(out.read_text(encoding="utf-8"))
            truth = json.loads(
                scan_path(profile, doc_id, page).with_suffix(".truth.json").read_text("utf-8")
            )[str(page)]
            o, t = norm(res["text"]), norm(truth)
            common = sum((Counter(o) & Counter(t)).values())
            m = by_type[(profile, kind)]
            m["cer"].append(Levenshtein.distance(o, t) / len(t))
            m["recall"].append(common / len(t))
            m["extra"].append(1 - common / len(o) if o else 0.0)
            m["seconds"].append(res["seconds"])
            m["in"].append(res["input_tokens"])
            m["out"].append(res["output_tokens"])
    return by_type


def report(engines: list[str]) -> None:
    kinds = sorted({k for _, _, k in PAGES})
    for profile in PROFILES:
        print(f"\n== {profile}  (CER / recall / extra, page-weighted mean)")
        print(
            f"{'engine':20}"
            + "".join(f"{k:>24}" for k in kinds)
            + f"{'sec/page':>10}{'tok in/out':>14}"
        )
        for engine in engines:
            s = score(engine)
            cells, secs, tin, tout = [], [], [], []
            for k in kinds:
                m = s.get((profile, k))
                if not m:
                    cells.append(f"{'-':>24}")
                    continue
                avg = {x: sum(v) / len(v) for x, v in m.items()}
                cells.append(f"{avg['cer']:7.1%}/{avg['recall']:6.1%}/{avg['extra']:6.1%} ")
                secs += m["seconds"]
                tin += m["in"]
                tout += m["out"]
            n = len(secs) or 1
            print(
                f"{engine:20}" + "".join(cells)
                + f"{sum(secs) / n:10.1f}{sum(tin) // n:>8}/{sum(tout) // n:<6}"
            )  # fmt: skip


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--engines", default=",".join(BEDROCK))
    ap.add_argument("--score-only", action="store_true")
    a = ap.parse_args()
    engines = a.engines.split(",")
    build()
    if not a.score_only:
        for engine in engines:
            print(f"transcribing with {engine}")
            transcribe(engine)
    report(engines)


if __name__ == "__main__":
    main()
