"""Copy the files that are indexed (70) into data/corpus/<id>.<ext>, for the repository.

data/raw/ holds the downloads and everything built from them (annex conversions,
merged HWPX, generated DOCX, synthetic scans, caches) and is not committed. The files
the pipeline actually indexes are copied here so the corpus ships with the code:
Korean statutes are not protected works (Copyright Act art. 7) and US federal works
are in the public domain (data/SOURCES.md). ingest/corpus.py reads data/corpus/ when
data/raw/corpus/ is absent.

    python data/scripts/pack_corpus.py
"""

import hashlib
import shutil
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DATA.parent / "backend" / "src"))
from sdrag.ingest.corpus import corpus_path, load_corpus  # noqa: E402

OUT = DATA / "corpus"


def main() -> None:
    OUT.mkdir(exist_ok=True)
    lines = []
    for d in load_corpus(DATA):
        src = corpus_path(DATA, d.id, d.file_type, d.tags, packed=False)
        dst = OUT / f"{d.id}{src.suffix}"
        shutil.copyfile(src, dst)
        lines.append(f"{hashlib.sha256(dst.read_bytes()).hexdigest()}  {dst.name}")
    (OUT / "SHA256SUMS").write_text("\n".join(lines) + "\n")
    size = sum(p.stat().st_size for p in OUT.iterdir())
    print(f"{len(lines)} files, {size / 2**20:.1f} MB -> {OUT}")


if __name__ == "__main__":
    main()
