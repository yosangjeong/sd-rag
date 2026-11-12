"""Parse and chunk documents unlike the corpus, to find what breaks before a live test.

    cd backend && AWS_PROFILE=... uv run python ../eval/robustness.py ../data/raw/robustness/*

Per file: format, pages OCR'd, blocks, tables, headings, chunks, largest chunk in
estimated tokens, characters kept, time, and the first chunk's opening, so empty or
garbled output shows at a glance. Files are test inputs only, not committed.
"""

import sys
import time
from pathlib import Path

from sdrag.common.config import settings
from sdrag.ingest.chunk import chunk_structure, est_tokens
from sdrag.ingest.ocr import BedrockVisionOcr, CachedOcr
from sdrag.ingest.parse import parse


def main() -> None:
    ocr = CachedOcr(BedrockVisionOcr(settings.ocr_model, settings.aws_region),
                    Path(settings.ocr_cache_dir or "../data/raw/ocr-cache"))  # fmt: skip
    for path in map(Path, sys.argv[1:]):
        t = time.perf_counter()
        try:
            doc = parse(path, ocr=ocr)
            chunks = chunk_structure(doc, path.stem)
        except Exception as e:  # noqa: BLE001 - report and go on to the next file
            print(f"{path.name:32} FAILED {type(e).__name__}: {e}")
            continue
        s = time.perf_counter() - t
        heads = {b.heading for b in doc.blocks if b.heading}
        tables = sum(b.kind == "table" for b in doc.blocks)
        chars = sum(len(b.text) for b in doc.blocks)
        biggest = max((est_tokens(c.text) for c in chunks), default=0)
        first = (chunks[0].text[:80] if chunks else "").replace("\n", " / ")
        print(f"{path.name:32} {doc.format:5} ocr={len(doc.ocr_pages):3} blocks={len(doc.blocks):4} "
              f"tables={tables:3} headings={len(heads):4} chunks={len(chunks):4} max_tok={biggest:4} "
              f"chars={chars:7} {s:5.1f}s | {first}")  # fmt: skip


if __name__ == "__main__":
    main()
