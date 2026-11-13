"""The document corpus as listed in data/manifest.csv, resolved to files on disk.

The file that gets indexed is not always the downloaded one (data/scripts/fetch.py
pins those): Korean statutes live in data/raw/corpus/kr/<field>/<family>/<kind>/ next
to the HWPX/DOCX built from them, and "scan" documents are the synthetic scans in
.../<field>/scans/ (paths: layout.py). Rows tagged eval-truth are ground truth for evaluation, never
corpus. A clone of the repository has no downloads in data/raw/; the indexed files
are then read from data/corpus/ (data/scripts/pack_corpus.py).
"""

import csv
from dataclasses import dataclass
from pathlib import Path

from sdrag.ingest import layout


@dataclass(frozen=True)
class CorpusDoc:
    id: str
    lang: str  # ko | en
    title: str
    file_type: str  # pdf | hwpx | docx | scan: what the evaluation reports by
    tags: tuple[str, ...]
    path: Path


EXT = {"pdf": ".pdf", "scan": ".pdf", "hwpx": ".hwpx", "docx": ".docx"}


def corpus_path(data: Path, doc_id: str, fmt: str, tags=(), packed: bool | None = None) -> Path:
    """The file indexed for a document (layout.py). packed: the copy in data/corpus/
    (data/scripts/pack_corpus.py), used by default when data/raw/corpus/ is absent,
    i.e. in a fresh clone of the repository."""
    if packed is None:
        packed = not (data / "raw" / "corpus").exists()
    if packed:
        return data / "corpus" / f"{doc_id}{EXT[fmt]}"
    if fmt == "scan":
        return layout.scan_path(data, doc_id, tags)
    if doc_id.startswith("kr-"):
        folder = layout.kr_dir(data, doc_id, tags)
        found = sorted(folder.glob(f"*.{fmt}"))
        if len(found) != 1:
            raise FileNotFoundError(f"{doc_id}: expected one .{fmt} in {folder}, found {found}")
        return found[0]
    return layout.corpus_dir(data, doc_id, tags) / f"{doc_id}.{fmt}"


def load_corpus(data: Path) -> list[CorpusDoc]:
    with (data / "manifest.csv").open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    return [
        CorpusDoc(
            r["id"],
            r["lang"],
            r["title"],
            r["format"],
            tuple(r["tags"].split(";")),
            corpus_path(data, r["id"], r["format"], r["tags"]),
        )
        for r in rows
        if "eval-truth" not in r["tags"].split(";")
    ]
