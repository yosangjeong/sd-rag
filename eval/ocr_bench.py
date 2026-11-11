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

Raw outputs, token usage and latency are kept under data/raw/ocr-bench/out/ so
re-scoring needs no new calls and every transcription can be inspected.

    cd backend && AWS_PROFILE=sd-assignment uv run python ../eval/ocr_bench.py [--engines a,b]
"""

import argparse
import csv
import io
import json
import re
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import boto3
import pypdfium2 as pdfium
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from PIL import Image
from rapidfuzz.distance import Levenshtein

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "data" / "scripts"))
import scanify

DATA = ROOT / "data"
BENCH = DATA / "raw" / "ocr-bench"
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

PROMPT = (
    "Transcribe all text on this scanned page exactly as printed, in reading order "
    "(on multi-column pages, column by column). Do not translate, correct, summarize "
    "or add anything. Keep line breaks. Write tables as rows like | cell | cell |. "
    "Write a run of leader dots or dashes as '...'. Output only the transcription."
)

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
    if doc_id.startswith("kr-"):
        family, _, kind = doc_id.rpartition("-")
        return next((DATA / "raw" / "kr-inbox" / family / kind).glob("*.pdf"))
    return DATA / "raw" / f"{doc_id}.{row['format']}"


def scan_path(profile: str, doc_id: str, page: int) -> Path:
    return BENCH / profile / f"{doc_id}-p{page}.pdf"


def build() -> None:
    for profile in PROFILES:
        for doc_id, page, _ in PAGES:
            out = scan_path(profile, doc_id, page)
            if not out.exists():
                scanify.scan(source_pdf(doc_id), out, [page], profile, seed=0)


def page_image(pdf: Path) -> Image.Image:
    """The scan's page image (the scan holds one image per page)."""
    p = scanify.PROFILES["office" if "/office/" in str(pdf) else "poor"]
    return pdfium.PdfDocument(pdf)[0].render(scale=p["dpi"] / 72).to_pil().convert("L")


def jpeg(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=90)
    return buf.getvalue()


def halves(img: Image.Image) -> list[Image.Image]:
    """Cut a page in two at the blankest pixel row of its middle fifth, so no text line
    is cut: its rows are averaged and the brightest (emptiest) one wins."""
    w, h = img.size
    band = img.crop((0, int(h * 0.4), w, int(h * 0.6))).resize((1, int(h * 0.2)))
    rows = list(band.get_flattened_data())
    cut = int(h * 0.4) + max(range(len(rows)), key=rows.__getitem__)
    return [img.crop((0, 0, w, cut)), img.crop((0, cut, w, h))]


def bedrock_ocr(model_id: str):
    client = boto3.client(
        "bedrock-runtime",
        # a dense page takes a VLM 20-30 s; botocore's default 60 s read timeout cut some
        config=Config(retries={"max_attempts": 6, "mode": "adaptive"}, read_timeout=300),
    )

    def call(image: bytes) -> dict:
        r = client.converse(
            modelId=model_id,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"image": {"format": "jpeg", "source": {"bytes": image}}},
                        {"text": PROMPT},
                    ],
                }
            ],
            inferenceConfig={"maxTokens": 6000, "temperature": 0},
        )
        return {
            "text": "".join(b.get("text", "") for b in r["output"]["message"]["content"]),
            "usage": r["usage"],
            "stop": r["stopReason"],
        }

    def run(img: Image.Image) -> dict:
        """Transcribe a page. Output cut by the token limit means the model got stuck
        repeating itself (leader dots, "1818..."): read the two halves separately."""
        t = time.perf_counter()
        res = call(jpeg(img))
        res["split"] = False
        if res["stop"] == "max_tokens":
            parts = [call(jpeg(half)) for half in halves(img)]
            res = {
                "text": "\n".join(x["text"] for x in parts),
                "usage": {
                    k: res["usage"][k] + sum(x["usage"][k] for x in parts)
                    for k in ("inputTokens", "outputTokens")
                },
                "stop": ",".join(x["stop"] for x in parts),
                "split": True,
            }
        res["seconds"] = round(time.perf_counter() - t, 2)
        return res

    return run


def out_path(engine: str, profile: str, doc_id: str, page: int) -> Path:
    return BENCH / "out" / engine / profile / f"{doc_id}-p{page}.json"


def transcribe(engine: str) -> None:
    run = bedrock_ocr(BEDROCK[engine])
    jobs = [
        (profile, doc_id, page)
        for profile in PROFILES
        for doc_id, page, _ in PAGES
        if not out_path(engine, profile, doc_id, page).exists()
    ]

    def one(job):
        profile, doc_id, page = job
        try:
            res = run(page_image(scan_path(profile, doc_id, page)))
        except (ClientError, BotoCoreError) as e:  # keep going; retried on the next run
            print(f"  {engine} {profile} {doc_id} p{page}: {e}")
            return
        out = out_path(engine, profile, doc_id, page)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")

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
            m["in"].append(res["usage"]["inputTokens"])
            m["out"].append(res["usage"]["outputTokens"])
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
