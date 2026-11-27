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

A generative model can write characters that are not on the page. ``CheckedOcr``
reads each page with Amazon Textract at the same time (it only writes what it
recognizes) and keeps Textract's text for a page where the model's text has many
characters Textract does not (eval/textract_bench.py). ``build_ocr`` puts it together.
"""

import hashlib
import io
import json
import logging
import re
import threading
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, replace
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
# the longest side of a rendered page: A4 at RENDER_DPI (842 pt). An iPhone scan's PDF
# page is about 1815 x 2633 pt; at 200 dpi its image was over Bedrock's request limit
# ("length limit exceeded", eval/real_scan.py). A4 and Letter pages render as before.
MAX_SIDE = round(842 * RENDER_DPI / 72)
MAX_TOKENS = 6000  # a dense page needs ~2,000; more only feeds a repetition loop


# Bedrock answers that mean "busy, try later", not "this page cannot be read"
TRANSIENT_CODES = ("ThrottlingException", "ServiceUnavailableException", "ModelNotReadyException",
                   "InternalServerException", "ModelTimeoutException", "ServiceUnavailable")  # fmt: skip


class OcrError(Exception):
    def __init__(self, message: str, transient: bool = False) -> None:
        super().__init__(message)
        self.transient = transient  # the document is worth another try later


@dataclass
class OcrResult:
    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    seconds: float = 0.0
    split: bool = False  # read as two halves after a repetition loop
    missing: float | None = None  # share of the characters the check (Textract) lacked
    replaced: bool = False  # the check's text was used: the reader had invented text


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
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            raise OcrError(f"{self.model_id}: {e}", code in TRANSIENT_CODES) from e
        except BotoCoreError as e:  # connection or read timeout: the service, not the page
            raise OcrError(f"{self.model_id}: {e}", True) from e
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


def _children(block: dict) -> list[str]:
    return [i for r in block.get("Relationships", []) if r["Type"] == "CHILD" for i in r["Ids"]]


def table_rows(blocks: dict[str, dict], resp: dict) -> tuple[dict[str, int], list[str]]:
    """Textract's TABLE blocks as "| a | b |" rows, and which table each word sits in."""
    word_table: dict[str, int] = {}
    tables: list[str] = []
    for t in (b for b in resp["Blocks"] if b["BlockType"] == "TABLE"):
        rows: dict[int, dict[int, str]] = defaultdict(dict)
        for c in (blocks[i] for i in _children(t) if blocks[i]["BlockType"] == "CELL"):
            words = [blocks[i] for i in _children(c) if blocks[i]["BlockType"] == "WORD"]
            for w in words:
                word_table[w["Id"]] = len(tables)
            rows[c["RowIndex"]][c["ColumnIndex"]] = " ".join(w["Text"] for w in words)
        width = max((max(r) for r in rows.values()), default=0)
        tables.append("\n".join(
            "| " + " | ".join(rows[i].get(j, "") for j in range(1, width + 1)) + " |"
            for i in sorted(rows)
        ))  # fmt: skip
    return word_table, tables


def layout_text(resp: dict) -> str:
    """An AnalyzeDocument answer as text: lines in the order of the LAYOUT blocks
    (Textract's reading-order analysis; nested ones such as list items are followed),
    a LAYOUT_TABLE written as its TABLE's rows. Lines no layout block covers go last.
    Each line is written once."""
    blocks = {b["Id"]: b for b in resp["Blocks"]}
    word_table, tables = table_rows(blocks, resp)

    def lines_of(b) -> list[str]:
        out = []
        for i in _children(b):
            c = blocks.get(i)
            if c is None:
                continue
            if c["BlockType"] == "LINE":
                out.append(i)
            elif c["BlockType"].startswith("LAYOUT_"):
                out += lines_of(c)
        return out

    out, done, placed = [], set(), set()
    for b in resp["Blocks"]:
        if not b["BlockType"].startswith("LAYOUT_"):
            continue
        ids = [i for i in lines_of(b) if i not in done]
        if not ids:
            continue
        done.update(ids)
        if b["BlockType"] == "LAYOUT_TABLE":
            inside = {word_table[w] for i in ids for w in _children(blocks[i]) if w in word_table}
            new = sorted(inside - placed)
            if new:
                placed.update(new)
                out += [tables[k] for k in new]
                continue
        out += [blocks[i]["Text"] for i in ids]
    # a TABLE outside any LAYOUT_TABLE stays as its lines (adding it too wrote them twice)
    out += [b["Text"] for b in resp["Blocks"] if b["BlockType"] == "LINE" and b["Id"] not in done]
    return "\n".join(out)


class TextractOcr:
    """Amazon Textract (AnalyzeDocument with tables and layout) as OCR engine. It
    recognizes characters and does not write any it did not see, but its reading order
    is weaker than Qwen3-VL's on Korean tables (eval/textract_bench.py), so the service
    uses it as a check (CheckedOcr), not as the reader."""

    name = "textract-analyze-tables-layout"
    FEATURES = ("TABLES", "LAYOUT")

    def __init__(self, region: str, client=None) -> None:
        self.client = client or boto3.client(
            "textract", region_name=region,
            config=Config(retries={"max_attempts": 8, "mode": "adaptive"}),
        )  # fmt: skip

    def analyze(self, image: Image.Image) -> dict:
        try:
            resp = self.client.analyze_document(
                Document={"Bytes": jpeg(image)}, FeatureTypes=list(self.FEATURES)
            )
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            raise OcrError(f"textract: {e}", code in TRANSIENT_CODES) from e
        except BotoCoreError as e:
            raise OcrError(f"textract: {e}", True) from e
        resp.pop("ResponseMetadata", None)
        return resp

    def transcribe(self, image: Image.Image) -> OcrResult:
        t = time.perf_counter()
        text = layout_text(self.analyze(image))
        return OcrResult(text, seconds=round(time.perf_counter() - t, 2))


BR = re.compile(r"<br\s*/?>", re.IGNORECASE)


def tidy(text: str) -> str:
    """Qwen3-VL writes a line break inside a table cell as HTML "<br>", which is not on
    the page: in a "| a | b |" row it becomes a space, elsewhere a line break. (Done after
    the cache, so cached answers stay as the model gave them.)"""
    if "<" not in text:
        return text
    return "\n".join(
        BR.sub(" " if TABLE_ROW.match(line) else "\n", line) for line in text.split("\n")
    )


LEADER = re.compile(r"[.…·]{3,}")  # leader dots: the prompt asks for '...'
TABLE_RULE_LINES = re.compile(r"^\s*\|?[\s|:-]*-{3,}[\s|:-]*$", re.MULTILINE)


def norm(text: str) -> str:
    """Text as the OCR benchmarks compare it: no table rule lines, leader dots as '...',
    no whitespace or table bars (eval/ocr_bench.py uses the same)."""
    text = LEADER.sub("...", re.sub(r"(?<=[.…·])\s+(?=[.…·])", "", TABLE_RULE_LINES.sub("", text)))
    return re.sub(r"[\s|]", "", text)


def missing_share(text: str, check: str) -> float:
    """Share of `text`'s characters that `check` does not have (order not counted): a
    page where the reader wrote characters the check never saw was probably invented."""
    a, b = norm(text), norm(check)
    if not a:
        return 0.0
    return 1 - sum((Counter(a) & Counter(b)).values()) / len(a)


class CheckedOcr:
    """Read a page with `primary` (Qwen3-VL) and, at the same time, with `check`
    (Textract). If more than `threshold` of the primary's characters are missing from
    the check's text, the primary invented them: the page keeps the check's text and
    is marked replaced. On 33 benchmark pages a 5% threshold flagged the one page with
    invented text and no good page (eval/textract_bench.py --agree; a small sample).
    The check never fails a page: if it errors, the primary's text is kept."""

    _pool = ThreadPoolExecutor(4)  # the checks run beside ocr_pages' own 4 readers

    def __init__(self, primary: OcrEngine, check: OcrEngine, threshold: float = 0.05) -> None:
        self.primary, self.check, self.threshold = primary, check, threshold
        self.name = primary.name

    def transcribe(self, image: Image.Image) -> OcrResult:
        checked = self._pool.submit(self.check.transcribe, image)
        res = self.primary.transcribe(image)  # its errors stay as they are (retry, skip)
        try:
            other = checked.result()
        except Exception as e:  # noqa: BLE001 - the check is extra; the page is still read
            log.warning("OCR check failed, keeping the reader's text: %s: %s", type(e).__name__, e)
            return res
        share = missing_share(tidy(res.text), tidy(other.text))
        if share <= self.threshold:
            return replace(res, missing=round(share, 4))
        log.warning("OCR check: %.1f%% of the reader's characters are not on the page "
                    "(Textract); using Textract's text", share * 100)  # fmt: skip
        return replace(res, text=other.text, missing=round(share, 4), replaced=True)


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


def build_ocr(model_id: str, region: str, check: bool, cache_dir: Path | None = None) -> OcrEngine:
    """The service's OCR: Qwen3-VL, checked by Textract when `check` (SDRAG_OCR_CHECK).
    With a cache directory each engine keeps its own results there, so a page already
    read (by either) is not paid for again."""

    def cached(engine: OcrEngine) -> OcrEngine:
        return CachedOcr(engine, cache_dir) if cache_dir else engine

    reader = cached(BedrockVisionOcr(model_id, region))
    return CheckedOcr(reader, cached(TextractOcr(region))) if check else reader


# PDFium is not thread-safe: concurrent calls crashed the bench (segfault) and broke
# document loading ("Data format error"). Rendering takes ~0.2 s against ~14 s of OCR,
# so serializing it costs next to nothing.
_PDFIUM = threading.Lock()


def render_page(pdf: Path, page: int, dpi: int = RENDER_DPI) -> Image.Image:
    with _PDFIUM:
        doc = pdfium.PdfDocument(pdf)
        try:
            p = doc[page - 1]
            scale = min(dpi / 72, MAX_SIDE / max(p.get_size()))
            return p.render(scale=scale).to_pil().convert("L")
        finally:
            doc.close()


def ocr_pages(
    pdf: Path, pages: list[int], engine: OcrEngine, workers: int = 4, progress=None
) -> dict[int, OcrResult]:
    """Transcribe pages (1-based) in parallel; a page that fails is left out and logged,
    so one bad page does not stop the document (the caller lists it as unread). A busy
    service (throttling after the retries) is not a bad page: it is raised, so the whole
    upload is retried later instead of being indexed with pages missing. progress(done,
    total) is called as pages finish (the upload status shows it: a 50-page scan takes
    minutes); an error in it does not stop the OCR."""
    done = [0]
    lock = threading.Lock()

    def one(page: int) -> tuple[int, OcrResult | None]:
        try:
            res = engine.transcribe(render_page(pdf, page))
            return page, replace(res, text=tidy(res.text))
        except OcrError as e:
            if e.transient:
                raise
            log.warning("OCR failed on %s page %d: %s", pdf.name, page, e)
            return page, None
        except Exception as e:  # noqa: BLE001 - a page that cannot be rendered
            log.warning("OCR failed on %s page %d: %s: %s", pdf.name, page, type(e).__name__, e)
            return page, None
        finally:
            if progress:
                with lock:
                    done[0] += 1
                    try:
                        progress(done[0], len(pages))
                    except Exception as e:  # noqa: BLE001 - a status write is not the OCR
                        log.warning("OCR progress update failed: %s", e)

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
