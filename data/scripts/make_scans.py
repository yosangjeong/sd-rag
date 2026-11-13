"""Write the synthetic scans of the corpus documents whose manifest format is "scan".

The brief asks for scanned PDFs (OCR) among the document types. Real scans of our
statutes do not exist, so a few corpus documents are served as scans instead of as
text PDFs: every page of the source PDF (verified by fetch.py) goes through
scanify.py's "office" profile into data/raw/corpus/<country>/<field>/scans/<id>.pdf, an image-only PDF the
parser can only read by OCR. The text PDF of these documents is not indexed, so no
statute is in the corpus twice.

The seed comes from the document id, so a document always gets the same scan.

    cd backend && uv run python ../data/scripts/make_scans.py [--force]
"""

import argparse
import csv
import hashlib
import sys
from pathlib import Path

from pypdf import PdfReader

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch
import scanify

PROFILE = "office"


def scan_file(row: dict) -> Path:
    return fetch.layout.scan_path(fetch.DATA, row["id"], row["tags"])


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--force", action="store_true", help="rewrite existing scans")
    args = ap.parse_args()
    with fetch.MANIFEST.open(encoding="utf-8", newline="") as f:
        rows = [r for r in csv.DictReader(f) if r["format"] == "scan"]
    for row in rows:
        out = scan_file(row)
        out.parent.mkdir(parents=True, exist_ok=True)
        if out.exists() and not args.force:
            print(f"exists   {row['id']}")
            continue
        src = fetch.local_path(row)
        if not src.exists():
            print(f"MISSING  {row['id']}: run fetch.py first ({src})")
            continue
        pages = list(range(1, len(PdfReader(src).pages) + 1))
        seed = int(hashlib.sha256(row["id"].encode()).hexdigest()[:8], 16)
        scanify.scan(src, out, pages, PROFILE, seed)
        print(f"scanned  {row['id']}: {len(pages)} pages -> {out.relative_to(fetch.DATA)}")


if __name__ == "__main__":
    main()
