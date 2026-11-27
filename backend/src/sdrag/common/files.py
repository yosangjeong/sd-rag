"""File helpers shared by the OCR and embedding caches."""

import os
import threading
from pathlib import Path


def write_atomic(path: Path, text: str) -> None:
    """Write a cache file whole or not at all: a reader in another thread or a later run
    never sees half of it (a temp file in the same directory, then renamed)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)
