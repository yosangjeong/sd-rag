"""OCR for PDF pages without a text layer (scans).

An engine turns a page image into text: ``OcrEngine`` is that one call, so engines
can be swapped. The default, ``BedrockVisionOcr``, asks a vision-language model on
Amazon Bedrock to transcribe the page. Qwen3-VL was chosen by eval/ocr_bench.py on
synthetic scans of corpus pages (CER 0.4-9% by page type, under 1% invented text,
about 14 s and $0.005 per page); the prompt and the two guards below come from it:

- leader dots ("Renewal Request ........") are to be written as '...': the model
  otherwise repeated dots until the token limit (45k characters) and lost the rest
  of the page;
- an answer cut by the token limit still means the model got stuck repeating
  itself, so the page is read again as two halves cut at its blankest row.

Tables come back as "| a | b |" rows; ``split_markdown`` turns them into table
parts so a scanned table is chunked like a born-digital one.
"""

import hashlib
import io
import json
import logging
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol

import boto3
import pypdfium2 as pdfium
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from PIL import Image

log = logging.getLogger(__name__)

PROMPT = (
    "Transcribe all text on this scanned page exactly as printed, in reading order "
    "(on multi-column pages, column by column). Do not translate, correct, summarize "
    "or add anything. Keep line breaks. Write tables as rows like | cell | cell |. "
    "Write a run of leader dots or dashes as '...'. Output only the transcription."
)
PROMPT_VERSION = "1"  # bump when PROMPT changes: cached results are keyed on it
RENDER_DPI = 200  # what the bench used; scans are 150-300 dpi
MAX_TOKENS = 6000  # a dense page needs ~2,000; more only feeds a repetition loop


class OcrError(Exception):
    pass


@dataclass
class OcrResult:
    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    seconds: float = 0.0
    split: bool = False  # read as two halves after a repetition loop


class OcrEngine(Protocol):
    name: str

    def transcribe(self, image: Image.Image) -> OcrResult: ...


def jpeg(image: Image.Image) -> bytes:
    buf = io.BytesIO()
    image.convert("L").save(buf, "JPEG", quality=90)
    return buf.getvalue()


def halves(image: Image.Image) -> list[Image.Image]:
    """Cut a page in two at the blankest pixel row of its middle fifth, so no text line
    is cut: the band is averaged per row and the brightest (emptiest) row wins."""
    gray = image.convert("L")
    w, h = gray.size
    top, bottom = int(h * 0.4), int(h * 0.6)
    rows = list(gray.crop((0, top, w, bottom)).resize((1, bottom - top)).get_flattened_data())
    cut = top + max(range(len(rows)), key=rows.__getitem__)
    return [image.crop((0, 0, w, cut)), image.crop((0, cut, w, h))]


class BedrockVisionOcr:
    """A vision-language model on Bedrock (Converse API) as OCR engine."""

    def __init__(self, model_id: str, region: str, client=None) -> None:
        if client is None:
            client = boto3.client(
                "bedrock-runtime",
                region_name=region,
                # a dense page takes 20-30 s; botocore's 60 s default cut some in the bench
                config=Config(retries={"max_attempts": 6, "mode": "adaptive"}, read_timeout=300),
            )
        self.client, self.model_id, self.name = client, model_id, model_id

    def _call(self, image: Image.Image) -> tuple[str, dict, str]:
        try:
            r = self.client.converse(
                modelId=self.model_id,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"image": {"format": "jpeg", "source": {"bytes": jpeg(image)}}},
                            {"text": PROMPT},
                        ],
                    }
                ],
                inferenceConfig={"maxTokens": MAX_TOKENS, "temperature": 0},
            )
        except (ClientError, BotoCoreError) as e:
            raise OcrError(f"{self.model_id}: {e}") from e
        text = "".join(b.get("text", "") for b in r["output"]["message"]["content"])
        return text, r["usage"], r["stopReason"]

    def transcribe(self, image: Image.Image) -> OcrResult:
        t = time.perf_counter()
        text, usage, stop = self._call(image)
        res = OcrResult(text, usage["inputTokens"], usage["outputTokens"])
        if stop == "max_tokens":
            texts = []
            for half in halves(image):
                part, u, _ = self._call(half)
                texts.append(part)
                res.input_tokens += u["inputTokens"]
                res.output_tokens += u["outputTokens"]
            res.text, res.split = "\n".join(texts), True
        res.seconds = round(time.perf_counter() - t, 2)
        return res


class CachedOcr:
    """Keep results on disk keyed by engine, prompt version and image bytes, so
    re-ingesting a document does not pay for its OCR again."""

    def __init__(self, engine: OcrEngine, cache_dir: Path) -> None:
        self.engine, self.dir, self.name = engine, Path(cache_dir), engine.name

    def transcribe(self, image: Image.Image) -> OcrResult:
        key = hashlib.sha256(
            f"{self.engine.name}\n{PROMPT_VERSION}\n".encode() + jpeg(image)
        ).hexdigest()
        path = self.dir / key[:2] / f"{key}.json"
        if path.exists():
            return OcrResult(**json.loads(path.read_text(encoding="utf-8")))
        res = self.engine.transcribe(image)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(res), ensure_ascii=False), encoding="utf-8")
        return res


# PDFium is not thread-safe: concurrent calls crashed the bench (segfault) and broke
# document loading ("Data format error"). Rendering takes ~0.2 s against ~14 s of OCR,
# so serializing it costs next to nothing.
_PDFIUM = threading.Lock()


def render_page(pdf: Path, page: int, dpi: int = RENDER_DPI) -> Image.Image:
    with _PDFIUM:
        doc = pdfium.PdfDocument(pdf)
        try:
            return doc[page - 1].render(scale=dpi / 72).to_pil().convert("L")
        finally:
            doc.close()


def ocr_pages(
    pdf: Path, pages: list[int], engine: OcrEngine, workers: int = 4
) -> dict[int, OcrResult]:
    """Transcribe pages (1-based) in parallel; a page that fails is left out and logged,
    so one bad page does not stop the document."""

    def one(page: int) -> tuple[int, OcrResult | None]:
        try:
            return page, engine.transcribe(render_page(pdf, page))
        except OcrError as e:
            log.warning("OCR failed on %s page %d: %s", pdf.name, page, e)
            return page, None

    with ThreadPoolExecutor(workers) as pool:
        return {p: r for p, r in pool.map(one, pages) if r is not None}


TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$")
TABLE_RULE = re.compile(r"^\s*\|?[\s|:-]*-{3,}[\s|:-]*$")  # | --- | --- |


def split_markdown(text: str) -> list[tuple[str, object]]:
    """("text", str) and ("table", rows) parts of an OCR answer, in order: runs of
    "| a | b |" lines are tables (their "| --- |" rule lines dropped), the rest text."""
    parts: list[tuple[str, object]] = []
    buf: list[str] = []
    rows: list[list[str]] = []

    def flush_text():
        if "".join(buf).strip():
            parts.append(("text", "\n".join(buf)))
        buf.clear()

    def flush_table():
        if rows:
            width = max(len(r) for r in rows)
            parts.append(("table", [r + [""] * (width - len(r)) for r in rows]))
        rows.clear()

    for line in text.split("\n"):
        if TABLE_ROW.match(line):
            flush_text()
            if not TABLE_RULE.match(line):
                rows.append([c.strip() for c in line.strip().strip("|").split("|")])
        else:
            flush_table()
            buf.append(line)
    flush_text()
    flush_table()
    return parts
