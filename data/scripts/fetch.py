"""Fetch and verify the document corpus listed in data/manifest.csv.

  python data/scripts/fetch.py            # download 'auto' docs, check 'manual' docs
  python data/scripts/fetch.py --record   # also write missing sha256 values back
  python data/scripts/fetch.py --sources  # regenerate data/SOURCES.md from the manifest

Files land in data/raw/corpus/<country>/<field>/ (gitignored; paths in
backend/src/sdrag/ingest/layout.py): US documents as <id>.pdf, Korean statutes in
<family>/<kind>/ (see build_kr.py). 'manual' documents (e.g. from law.go.kr, whose
download flow needs a browser) must be saved there by hand; this script then
verifies them by SHA-256 so everyone gets the same bytes.

For Korean statutes and the recorded SHA-256 is that of the file as downloaded
(the zip, or the single PDF/HWPX), not of the merged HWPX or generated DOCX.
Those derived files are rebuilt by build_kr.py, which checks their text and
table count against the source instead; their bytes vary between builds
(zip timestamps), so hashing them would not be reproducible.

Rows with format "scan" are corpus documents served as a synthetic scan: the hashed
file is the source PDF (downloaded or saved as above), and make_scans.py writes the
image-only scan of it to .../<field>/scans/<id>.pdf. Their text PDF is not indexed.

Rows tagged eval-truth (ids ending in -truth) are not part of the corpus: they are
the HWPX edition of a statute the corpus holds as PDF, kept in
data/raw/truth/<family>/<kind>/ as ground truth for eval/pdf_tables.py. Build
their HWPX with build_kr.build_hwpx_kind; never index them (the statute would
appear twice).

Uses only the standard library (layout.py included).
"""

import argparse
import csv
import hashlib
import sys
import time
import urllib.request
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DATA.parent / "backend" / "src"))
from sdrag.ingest import layout  # noqa: E402  (standard library only)

MANIFEST = DATA / "manifest.csv"
TRUTH_SUFFIX = "-truth"
USER_AGENT = "sd-rag-dataset-fetch/0.1"

LICENSES = {
    "US-PD-105": "Public domain - work of the U.S. Government (17 U.S.C. 105)",
    "KR-CA-7": "Not protected - Korean Copyright Act Art. 7 (statutes, notices, court decisions)",
    "KOGL-1": "Korea Open Government License Type 1 (attribution required)",
    "MOLEG-EASYLAW": "Free use including commercial, source must be credited: "
    "법제처 찾기쉬운 생활법령정보 (https://easylaw.go.kr/CSP/InfoCopyright.laf)",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def download(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    tmp = dest.with_suffix(dest.suffix + ".part")
    with urllib.request.urlopen(req, timeout=120) as resp, tmp.open("wb") as out:
        while chunk := resp.read(1 << 16):
            out.write(chunk)
    tmp.rename(dest)


def local_path(row: dict) -> Path:
    """Where a document's hashed file lives (see the module docstring, layout.py)."""
    doc_id = row["id"]
    if doc_id.endswith(TRUTH_SUFFIX):
        folder = layout.truth_dir(DATA, doc_id.removesuffix(TRUTH_SUFFIX))
    elif doc_id.startswith("kr-"):
        folder = layout.kr_dir(DATA, doc_id, row["tags"])
    else:
        return layout.corpus_dir(DATA, doc_id, row["tags"]) / f"{doc_id}.pdf"  # scans: a PDF
    if folder.is_dir():
        files = {f.suffix.lower(): f for f in folder.iterdir() if f.is_file()}
        # the download is the zip if there is one, else the single PDF/HWPX
        for ext in (".zip", ".pdf", ".hwpx"):
            if ext in files:
                return files[ext]
    return folder / f"{doc_id}.{row['format']}"


def load() -> tuple[list[str], list[dict]]:
    with MANIFEST.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


def fetch(record: bool) -> int:
    fields, rows = load()
    problems = 0
    for row in rows:
        dest = local_path(row)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists():
            if row["acquisition"] == "auto":
                print(f"download {row['id']}")
                download(row["url"], dest)
                time.sleep(1)  # be polite to the source server
            else:
                print(f"MISSING  {row['id']}: save it manually from {row['url']}")
                problems += 1
                continue
        digest = sha256(dest)
        if not row["sha256"]:
            row["sha256"] = digest if record else ""
            print(f"new      {row['id']} {digest[:12]}" + (" (recorded)" if record else ""))
        elif row["sha256"] != digest:
            print(f"CHANGED  {row['id']}: expected {row['sha256'][:12]}, got {digest[:12]}")
            problems += 1
        else:
            print(f"ok       {row['id']}")
    if record:
        with MANIFEST.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
            w.writeheader()
            w.writerows(rows)
    return problems


def write_sources() -> None:
    _, rows = load()
    lines = [
        "# Document sources and licenses",
        "",
        "Generated from `data/manifest.csv` by `data/scripts/fetch.py --sources`. Do not edit by hand.",
        "",
        "## Licenses",
        "",
    ]
    lines += [f"- **{k}**: {v}" for k, v in LICENSES.items()]
    lines += [
        "",
        "## Documents",
        "",
        "| ID | Lang | Title | Source | Format | Tags | License |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['id']} | {r['lang']} | [{r['title']}]({r['url']}) | {r['source']} "
            f"| {r['format']} | {r['tags']} | {r['license']} |"
        )
    lines += [
        "",
        "## Evaluation questions",
        "",
        "Real questions in `data/eval/real_questions_candidates.csv` (question titles only, "
        "no answers) are quoted from:",
        "",
        "- 출처: 법제처 찾기쉬운 생활법령정보, 백문백답 (easylaw.go.kr) - MOLEG-EASYLAW",
        "- U.S. Department of Labor, Wage and Hour Division: FMLA and FLSA FAQs (dol.gov) - US-PD-105",
        "",
        "Real-estate real questions in `data/eval/real_re_questions_candidates.csv` (titles only):",
        "",
        "- 출처: 법제처 찾기쉬운 생활법령정보, 백문백답 - 부동산/임대차 (easylaw.go.kr) - MOLEG-EASYLAW",
        "- Consumer Financial Protection Bureau: RESPA FAQs and Mortgage Servicing FAQs (2021) "
        "(consumerfinance.gov) - US-PD-105",
        "- HUD and DOJ: Joint Statement, Reasonable Modifications under the Fair Housing Act (2008) "
        "(justice.gov) - US-PD-105",
        "",
        "Generated questions are written by a model from the corpus above; see `data/eval/README.md`.",
    ]
    (DATA / "SOURCES.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote SOURCES.md ({len(rows)} documents)")


def main() -> None:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument(
        "--record",
        action="store_true",
        help="write missing sha256 values to the manifest",
    )
    p.add_argument("--sources", action="store_true", help="regenerate SOURCES.md and exit")
    args = p.parse_args()
    if args.sources:
        write_sources()
        return
    sys.exit(1 if fetch(args.record) else 0)


if __name__ == "__main__":
    main()
