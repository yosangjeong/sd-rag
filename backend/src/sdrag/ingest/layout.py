"""Where things live under data/raw/ (not committed): one place for every path.

    data/raw/
      corpus/<kr|us>/<labor|realestate>/   the documents, by country and field
        <family>/<law|dec|rul>/            Korean statutes: the download and what
                                           data/scripts/build_kr.py builds from it
        <id>.pdf                           US documents
        scans/<id>.pdf                     synthetic scans (data/scripts/make_scans.py)
      truth/<family>/<kind>/               HWPX editions used as ground truth for PDFs
      cache/ocr, cache/embed, cache/eval   OCR results, embeddings, evaluation caches
      bench/ocr, bench/embed, bench/robustness
                                           inputs and outputs of the benchmarks
      deploy/                              deploy outputs, rehearsal accounts (secrets)
      logs/                                run logs

The field comes from the manifest tags ("realestate", otherwise labor); the country
from the id (kr-*, us-*). Standard library only: data scripts that run outside the
backend environment import it too.
"""

from pathlib import Path

FIELDS = ("labor", "realestate")


def raw(data: Path) -> Path:
    return data / "raw"


def country(doc_id: str) -> str:
    return doc_id.split("-", 1)[0]  # kr | us


def field(tags) -> str:
    tags = tags.split(";") if isinstance(tags, str) else tags
    return "realestate" if "realestate" in tags else "labor"


def corpus_dir(data: Path, doc_id: str, tags) -> Path:
    return raw(data) / "corpus" / country(doc_id) / field(tags)


def kr_dir(data: Path, doc_id: str, tags) -> Path:
    """Folder of one Korean statute: .../<family>/<kind>/ (kind = law | dec | rul)."""
    family, _, kind = doc_id.rpartition("-")
    return corpus_dir(data, doc_id, tags) / family / kind


def scan_path(data: Path, doc_id: str, tags) -> Path:
    return corpus_dir(data, doc_id, tags) / "scans" / f"{doc_id}.pdf"


def truth_dir(data: Path, doc_id: str) -> Path:
    family, _, kind = doc_id.rpartition("-")
    return raw(data) / "truth" / family / kind


def kr_family_roots(data: Path) -> list[Path]:
    """Folders that hold Korean statute families, one per field."""
    return [raw(data) / "corpus" / "kr" / f for f in FIELDS]


def cache(data: Path, name: str) -> Path:  # ocr | embed | eval
    return raw(data) / "cache" / name


def bench(data: Path, name: str) -> Path:  # ocr | embed | robustness
    return raw(data) / "bench" / name


def deploy(data: Path) -> Path:
    return raw(data) / "deploy"


def logs(data: Path) -> Path:
    return raw(data) / "logs"
