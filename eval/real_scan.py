"""OCR on a real phone scan: 9 printed pages, scanned with an iPhone (Notes, "문서 스캔").

The synthetic scans (make_scans.py, eval/ocr_corpus.py) are rendered pages with noise,
blur and rotation added in code. This checks the same engine on paper: pages printed
at 100% and scanned as a user would, some on purpose badly (plan.json `how`: straight,
a little skewed, shadowed, dark). Each page is transcribed with the served OCR engine
(cached) and scored like ocr_bench.py (same normalization: CER, recall, extra) against
the page's text in the source PDF (plan.json `truth`).

The scan stays out of the corpus and the question sets (they are frozen).

    cd backend && AWS_PROFILE=... uv run python ../eval/real_scan.py <scan.pdf>
"""

import json
import sys
from collections import Counter
from pathlib import Path

from evalset import OCR_CACHE
from ocr_bench import norm
from rapidfuzz.distance import Levenshtein

from sdrag.common.config import settings
from sdrag.ingest.ocr import BedrockVisionOcr, CachedOcr, render_page

DATA = Path(__file__).resolve().parents[1] / "data"
PLAN = DATA / "raw" / "bench" / "real-scan" / "plan.json"
OUT = DATA / "eval" / "results" / "ocr-real-scan.md"


def main(pdf: Path) -> None:
    plan = json.loads(PLAN.read_text("utf-8"))
    ocr = CachedOcr(BedrockVisionOcr(settings.ocr_model, settings.aws_region), OCR_CACHE)
    rows = []
    for p in plan:
        res = ocr.transcribe(render_page(pdf, p["sheet"]))
        o, t = norm(res.text), norm(p["truth"])
        common = sum((Counter(o) & Counter(t)).values())
        rows.append({**{k: p[k] for k in ("sheet", "doc_id", "page", "kind", "how")},
                     "cer": Levenshtein.distance(o, t) / len(t), "recall": common / len(t),
                     "extra": 1 - common / len(o) if o else 0.0, "split": res.split,
                     "seconds": res.seconds, "text": res.text})  # fmt: skip
        r = rows[-1]
        print(f"{r['sheet']} {r['doc_id']:28} p{r['page']:<3} {r['how']:8} "
              f"CER {r['cer']:6.1%}  recall {r['recall']:6.1%}  extra {r['extra']:5.1%}")  # fmt: skip
    (OUT.with_suffix(".json")).write_text(json.dumps(rows, ensure_ascii=False, indent=1), "utf-8")

    def mean(xs):
        return f"{sum(xs) / len(xs):.1%}"

    lines = [
        "# OCR on a real phone scan (`eval/real_scan.py`)",
        "",
        (f"Engine {settings.ocr_model}. 9 pages printed at 100% on A4 and scanned with an "
         "iPhone (Notes, document scan, its automatic crop and deskew left on), some on "
         "purpose badly. Truth: the page's text in the source PDF. CER counts reading order, "
         "so table pages score worse on it than on recall."),
        "",
        "| sheet | document | page | content | scanned | CER | recall | extra |",
        "|---|---|---|---|---|---|---|---|",
        *[f"| {r['sheet']} | {r['doc_id']} | {r['page']} | {r['kind']} | {r['how']} | "
          f"{r['cer']:.1%} | {r['recall']:.1%} | {r['extra']:.1%} |" for r in rows],
        (f"| **all** | | | | | **{mean([r['cer'] for r in rows])}** | "
         f"{mean([r['recall'] for r in rows])} | {mean([r['extra'] for r in rows])} |"),
    ]  # fmt: skip
    OUT.write_text("\n".join(lines) + "\n", "utf-8")


if __name__ == "__main__":
    main(Path(sys.argv[1]).resolve())
