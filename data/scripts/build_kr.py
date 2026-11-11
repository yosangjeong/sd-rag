"""Turn the manually downloaded Korean statutes into one file per statute.

Input (downloaded from law.go.kr by hand, file names untouched):

    data/raw/kr-inbox/<family>/{law,dec,rul}/
        *.pdf   statutes assigned PDF (body + annexes already in one file)
        *.zip   statutes assigned HWPX or DOCX: law.go.kr's HWPX download is a
                zip of the body .hwpx plus one file per annex (별표), and the
                annexes are usually HWP 5.x, not HWPX
        *.hwpx  a statute without annexes is downloaded as a single .hwpx

Format per statute comes from data/kr_families.csv. For HWPX/DOCX statutes:

    1. unzip (entry names are CP949 unless the UTF-8 flag is set)
    2. annex HWP -> HWPX with hwp2hwpx (data/scripts/hwp2hwpx, Java)
    3. body + annexes -> one HWPX              (hwpx_merge.py)
    4. DOCX statutes only: HWPX -> DOCX        (hwpx_to_docx.py)
    5. verify: merged text == body + annex text; DOCX text == HWPX text
       (page headers/footers excluded), same number of tables

Outputs are written next to the zip with the body's file name, so each folder
ends up holding its source and the generated file(s). Folders whose outputs
are newer than their zip are skipped unless --force is given.

    bash data/scripts/hwp2hwpx/build.sh            # once
    uv run --no-project --python 3.12 --with lxml --with python-docx \
        python data/scripts/build_kr.py [--force] [family ...]
"""

import argparse
import csv
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from lxml import etree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hwpx_merge  # noqa: E402
import hwpx_to_docx  # noqa: E402

DATA = Path(__file__).resolve().parent.parent
INBOX = DATA / "raw" / "kr-inbox"
FAMILIES = DATA / "kr_families.csv"
CLASSES = Path(
    os.environ.get(
        "HWP2HWPX_CLASSES",
        Path(__file__).resolve().parent / "hwp2hwpx" / "build" / "classes",
    )
)
JAVA = os.environ.get("JAVA", "/opt/homebrew/opt/openjdk@21/bin/java")
KINDS = ("law", "dec", "rul")

HP = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
RE_ANNEX = re.compile(r"^\[별표\s*(\d+)?(?:의\s*(\d+))?\]")


class BuildError(Exception):
    pass


# ---------- helpers ----------


def magic(path: Path) -> str:
    head = path.read_bytes()[:4]
    if head.startswith(b"%PDF"):
        return "pdf"
    if head == b"PK\x03\x04":
        return "zip"  # HWPX, DOCX and plain zips all start like this
    if head == b"\xd0\xcf\x11\xe0":
        return "ole"  # HWP 5.x (and legacy .doc)
    return "unknown"


def annex_key(name: str) -> tuple[int, int]:
    m = RE_ANNEX.match(name)
    return (int(m.group(1) or 0), int(m.group(2) or 0)) if m else (10**6, 0)


def unzip(zpath: Path, out: Path) -> list[Path]:
    files = []
    with zipfile.ZipFile(zpath) as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            name = (
                info.filename
                if info.flag_bits & 0x800
                else info.filename.encode("cp437").decode("cp949")
            )
            target = out / Path(name).name  # flatten; never write outside out/
            target.write_bytes(z.read(info))
            files.append(target)
    return files


def hwpx_sections(path: Path):
    z = zipfile.ZipFile(path)
    names = sorted(
        (n for n in z.namelist() if re.match(r"Contents/section\d+\.xml$", n)),
        key=lambda n: int(re.search(r"\d+", n).group()),
    )
    return [etree.fromstring(z.read(n)) for n in names]


def hwpx_text(path: Path, skip_header_footer: bool = False) -> tuple[str, int]:
    text, tables = [], 0
    for root in hwpx_sections(path):
        if skip_header_footer:
            for el in list(root.iter(f"{HP}header", f"{HP}footer")):
                el.clear()
        text += ["".join(t.itertext()) for t in root.iter(f"{HP}t")]
        tables += sum(1 for _ in root.iter(f"{HP}tbl"))
    return re.sub(r"\s+", "", "".join(text)), tables


def docx_text(path: Path) -> tuple[str, int]:
    root = etree.fromstring(zipfile.ZipFile(path).read("word/document.xml"))
    text = "".join(t.text or "" for t in root.iter(f"{W}t"))
    return re.sub(r"\s+", "", text), sum(1 for _ in root.iter(f"{W}tbl"))


def hwp_to_hwpx(pairs: list[tuple[Path, Path]]) -> None:
    if not pairs:
        return
    if not (CLASSES / "Convert.class").exists():
        raise BuildError(
            f"converter not built: run  bash data/scripts/hwp2hwpx/build.sh  ({CLASSES})"
        )
    args = [str(p) for pair in pairs for p in pair]
    r = subprocess.run(
        [JAVA, "-cp", str(CLASSES), "Convert", *args], capture_output=True, text=True
    )
    if r.returncode != 0:
        raise BuildError(f"hwp2hwpx failed: {r.stderr.strip()[-500:]}")


# ---------- one statute ----------


def build_hwpx_kind(folder: Path, fmt: str, force: bool) -> str:
    files = [f for f in folder.iterdir() if f.is_file() and not f.name.startswith(".")]
    zips = [f for f in files if f.suffix.lower() == ".zip"]
    pdfs = [f for f in files if f.suffix.lower() == ".pdf"]
    if pdfs:
        raise BuildError(f"assigned {fmt} but found a PDF: {pdfs[0].name}")

    if not zips:
        # no annexes: law.go.kr gives a single .hwpx, which is already final
        sources = [
            f
            for f in files
            if f.suffix.lower() == ".hwpx" and not RE_ANNEX.match(f.name)
        ]
        loose_annexes = [f for f in files if RE_ANNEX.match(f.name)]
        if loose_annexes:
            raise BuildError(
                "annex files found without a zip; please put the downloaded zip here as is"
            )
        if len(sources) != 1 or magic(sources[0]) != "zip":
            raise BuildError(
                f"expected one zip or one .hwpx, found {[f.name for f in files]}"
            )
        merged, n_annex = sources[0], 0
    else:
        if len(zips) != 1:
            raise BuildError(f"expected one zip, found {len(zips)}")
        zpath = zips[0]
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / "src").mkdir()
            extracted = unzip(zpath, tmp / "src")
            bodies = [
                f
                for f in extracted
                if not RE_ANNEX.match(f.name) and not f.name.startswith("[별지")
            ]
            annexes = sorted(
                (f for f in extracted if RE_ANNEX.match(f.name)),
                key=lambda f: annex_key(f.name),
            )
            forms = [f for f in extracted if f.name.startswith("[별지")]
            if forms:
                print(
                    f"    note: skipping {len(forms)} form(s) (별지); 서식 should be unchecked when saving"
                )
            if len(bodies) != 1 or magic(bodies[0]) != "zip":
                raise BuildError(
                    f"zip should hold one body .hwpx, found {[f.name for f in bodies]}"
                )
            body = bodies[0]
            merged = folder / (body.stem + ".hwpx")
            n_annex = len(annexes)
            if (
                not force
                and merged.exists()
                and merged.stat().st_mtime >= zpath.stat().st_mtime
            ):
                if fmt != "docx" or merged.with_suffix(".docx").exists():
                    return f"up to date ({n_annex} annexes)"

            # annexes: HWP 5.x -> HWPX; real HWPX annexes are used as they are
            (tmp / "hwpx").mkdir()
            ready, pairs = [], []
            for a in annexes:
                kind = magic(a)
                if kind == "ole":
                    out = tmp / "hwpx" / (a.stem + ".hwpx")
                    pairs.append((a, out))
                    ready.append(out)
                elif kind == "zip":
                    ready.append(a)
                else:
                    raise BuildError(f"{a.name}: unknown format")
            hwp_to_hwpx(pairs)

            tmp_out = tmp / "merged.hwpx"
            hwpx_merge.merge(tmp_out, body, ready)
            got, _ = hwpx_text(tmp_out)
            want = hwpx_text(body)[0] + "".join(hwpx_text(a)[0] for a in ready)
            if got != want:
                raise BuildError("merged HWPX text differs from body + annexes")
            shutil.copyfile(tmp_out, merged)

    status = f"hwpx ok ({n_annex} annexes)"
    if fmt == "docx":
        docx = merged.with_suffix(".docx")
        hwpx_to_docx.convert(merged, docx)
        (ht, htab), (dt, dtab) = (
            hwpx_text(merged, skip_header_footer=True),
            docx_text(docx),
        )
        if ht != dt or htab != dtab:
            raise BuildError(
                f"DOCX differs from HWPX (chars {len(ht)} vs {len(dt)}, tables {htab} vs {dtab})"
            )
        status += f", docx ok ({dtab} tables)"
    return status


KIND_SUFFIX = {"law": "", "dec": " 시행령", "rul": " 시행규칙"}


def check_title(folder: Path, title: str, kind: str) -> None:
    """law.go.kr names files '<title>(<type>)(제N호)(YYYYMMDD).ext'; catch files put in the wrong folder."""
    expected = f"{title}{KIND_SUFFIX[kind]}("
    for f in folder.iterdir():
        if f.name.startswith(".") or RE_ANNEX.match(f.name):
            continue
        if not f.name.startswith(expected):
            raise BuildError(
                f"{f.name}: expected a file named '{expected}...' in {kind}/"
            )


def build_kind(folder: Path, fmt: str, force: bool, title: str, kind: str) -> str:
    if not folder.exists() or not any(
        f for f in folder.iterdir() if not f.name.startswith(".")
    ):
        return "not downloaded"
    check_title(folder, title, kind)
    if fmt == "pdf":
        files = [
            f for f in folder.iterdir() if f.is_file() and not f.name.startswith(".")
        ]
        pdfs = [f for f in files if f.suffix.lower() == ".pdf"]
        if len(pdfs) != 1 or len(files) != 1:
            raise BuildError(
                f"assigned pdf: expected exactly one PDF, found {[f.name for f in files]}"
            )
        if magic(pdfs[0]) != "pdf":
            raise BuildError(f"{pdfs[0].name} is not a PDF")
        return "pdf ok"
    return build_hwpx_kind(folder, fmt, force)


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("families", nargs="*", help="only these families (default: all)")
    ap.add_argument(
        "--force", action="store_true", help="rebuild even if outputs are up to date"
    )
    args = ap.parse_args()

    with FAMILIES.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    known = {r["family"] for r in rows}
    for d in sorted(p for p in INBOX.iterdir() if p.is_dir()):
        if d.name not in known:
            print(f"!! {d.name}: folder not listed in {FAMILIES.name}")

    errors = 0
    for row in rows:
        if args.families and row["family"] not in args.families:
            continue
        print(f"== {row['family']} ({row['title']})")
        for kind in KINDS:
            try:
                status = build_kind(
                    INBOX / row["family"] / kind,
                    row[kind],
                    args.force,
                    row["title"],
                    kind,
                )
                print(f"  {kind} [{row[kind]}] {status}")
            except BuildError as e:
                errors += 1
                print(f"  {kind} [{row[kind]}] !! {e}")
    print(f"\n{errors} error(s)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
