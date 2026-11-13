"""OCR accuracy on the corpus's own scans, as indexed: every page of every scan document.

eval/ocr_bench.py chose the engine on sample pages of labor statutes. This scores
what ingestion actually produced for all seven scan documents (four labor, three
real estate): the cached transcriptions (sdrag.ingest.ocr.CachedOcr, the cache the
index was built with) against each page's source text, which make_scans.py saved
beside the scan (<id>.truth.json). Same normalization and measures as ocr_bench.py
(CER, recall, extra). No model is called: a page missing from the cache is reported,
not transcribed.

    cd backend && uv run python ../eval/ocr_corpus.py [--cache ../data/raw/cache/ocr]
"""

import argparse
import json
import statistics
from collections import Counter
from pathlib import Path

from evalset import OCR_CACHE
from ocr_bench import norm
from rapidfuzz.distance import Levenshtein

from sdrag.common.config import settings
from sdrag.ingest.corpus import load_corpus
from sdrag.ingest.ocr import CachedOcr, OcrEngine, render_page

DATA = Path(__file__).resolve().parents[1] / "data"
OUT = DATA / "eval" / "results" / "ocr-corpus.md"


class NotCached(Exception):
    pass


class NoCall(OcrEngine):
    """Stands in for the model: the cache must already hold every page."""

    def __init__(self, name: str) -> None:
        self.name = name

    def transcribe(self, image):
        raise NotCached


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", type=Path, default=OCR_CACHE)
    a = ap.parse_args()
    ocr = CachedOcr(NoCall(settings.ocr_model), a.cache)  # the key holds the model id
    rows, missing = [], []
    for d in load_corpus(DATA):
        if d.file_type != "scan":
            continue
        truth = json.loads(d.path.with_suffix(".truth.json").read_text("utf-8"))
        field = "real estate" if "realestate" in d.tags else "labor"
        cer, rec, extra = [], [], []
        for page in sorted(truth, key=int):
            try:
                res = ocr.transcribe(render_page(d.path, int(page)))
            except NotCached:
                missing.append(f"{d.id} p{page}")
                continue
            o, t = norm(res.text), norm(truth[page])
            if not t:
                continue
            common = sum((Counter(o) & Counter(t)).values())
            cer.append(Levenshtein.distance(o, t) / len(t))
            rec.append(common / len(t))
            extra.append(1 - common / len(o) if o else 0.0)
        rows.append((field, d.id, d.lang, len(cer), cer, rec, extra))

    def mean(xs):
        return f"{statistics.mean(xs):.1%}" if xs else "-"

    lines = [
        "# OCR on the corpus scans (`eval/ocr_corpus.py`)",
        "",
        (
            f"Engine {settings.ocr_model}, cached transcriptions the index was built from, "
            "against the source page text; page-weighted means. CER counts reading order, "
            "so table pages score worse on it than on recall."
        ),
        "",
        "| field | document | lang | pages | CER | recall | extra |",
        "|---|---|---|---|---|---|---|",
    ]
    for field, doc, lang, n, cer, rec, extra in rows:
        lines.append(
            f"| {field} | {doc} | {lang} | {n} | {mean(cer)} | {mean(rec)} | {mean(extra)} |"
        )
    for field in ("labor", "real estate"):
        sel = [r for r in rows if r[0] == field]
        lines.append(
            f"| **{field}** | all | | {sum(r[3] for r in sel)} | "
            f"**{mean([x for r in sel for x in r[4]])}** | {mean([x for r in sel for x in r[5]])} | "
            f"{mean([x for r in sel for x in r[6]])} |"
        )
    if missing:
        lines += ["", f"Not in the cache (not scored): {', '.join(missing)}"]
    OUT.write_text("\n".join(lines) + "\n", "utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
