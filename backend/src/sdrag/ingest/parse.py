"""Parse PDF, HWPX and DOCX files into a flat list of blocks (paragraphs and tables).

Every block carries a location the chat UI can show as the answer's source:

- PDF: page number (pages are fixed in a PDF)
- HWPX / DOCX: no fixed pages (pagination depends on the renderer), so the
  location is structural; the block index plus the nearest heading
- all formats: ``heading`` = the statute article (제N조) or annex ([별표 N]) the
  block belongs to, so a citation reads the same whatever the file format

Tables are rendered as ``| a | b |`` rows so that row/column relations survive
into the text that gets embedded. PDF pages with no extractable text are
flagged ``needs_ocr`` (scanned pages); OCR happens in a later stage.
"""

import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from lxml import etree
from pypdf import PdfReader

HP = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

# 제4조(해고 예고의 예외...) / 제12조의3(...) at the start of a paragraph or line. The
# parenthesised title is required: a wrapped line can start with "제26조에 따른 ..."
RE_ARTICLE = re.compile(r"^\s*(제\s*\d+\s*조(?:\s*의\s*\d+)?)\s*(\([^)]*\))")
# [별표 3], [별표 2의2], [별표] — law.go.kr annex header, often after "■ <title> "
RE_ANNEX = re.compile(r"\[별표\s*(\d+(?:\s*의\s*\d+)?)?\]")
# "부칙 <제18176호, 2021. 5. 18.>" starts the addenda, whose articles restart at 제1조
RE_ADDENDA = re.compile(r"^\s*부\s*칙\s*(<[^>]*>)?\s*$|^\s*부\s*칙\s*<")


@dataclass
class Block:
    kind: Literal["text", "table"]
    text: str
    index: int  # order within the document
    page: int | None = None  # PDF only, 1-based
    heading: str | None = (
        None  # e.g. "제4조(해고 예고의 예외가 되는 근로자의 귀책사유)", "[별표 3]"
    )
    rows: list[list[str]] | None = None  # tables only: cell texts per row


@dataclass
class ParsedDocument:
    path: str
    format: Literal["pdf", "hwpx", "docx"]
    blocks: list[Block] = field(default_factory=list)
    needs_ocr_pages: list[int] = field(default_factory=list)


class HeadingTracker:
    """Remember the current article / annex while walking a statute in reading order."""

    def __init__(self) -> None:
        self.article: str | None = None
        self.annex: str | None = None
        self.in_addenda = False

    def update_annex(self, text: str) -> bool:
        """Annex header: starts the text, possibly after "■ <statute title> "."""
        head = text.lstrip()[:80]
        m = RE_ANNEX.search(head)
        if m and head.startswith(("[별표", "■")):
            self.annex, self.article = re.sub(r"\s+", " ", m.group(0)), None
            return True
        return False

    def update(self, text: str) -> None:
        if self.update_annex(text) or self.annex is not None:
            return
        if RE_ADDENDA.match(text):
            self.in_addenda, self.article = True, "부칙"
            return
        m = RE_ARTICLE.match(text)
        if m:
            article = re.sub(r"\s+", "", m.group(1)) + m.group(2)
            self.article = f"부칙 {article}" if self.in_addenda else article

    @property
    def current(self) -> str | None:
        return self.annex or self.article


def table_text(rows: list[list[str]]) -> str:
    return "\n".join("| " + " | ".join(c.replace("\n", " ") for c in r) + " |" for r in rows)


# ---------- HWPX ----------


def _hwpx_t(t_el) -> str:
    parts = [t_el.text or ""]
    for child in t_el:
        name = etree.QName(child).localname
        parts.append("\t" if name == "tab" else "\n" if name == "lineBreak" else "")
        parts.append(child.tail or "")
    return "".join(parts)


def _hwpx_cell_text(tc) -> str:
    """All text inside a cell, nested tables included, paragraphs joined by spaces."""
    texts = []
    for p in tc.iter(f"{HP}p"):
        line = "".join(_hwpx_t(t) for r in p.findall(f"{HP}run") for t in r.findall(f"{HP}t"))
        if line.strip():
            texts.append(line.strip())
    return " ".join(texts)


def _hwpx_table(tbl) -> list[list[str]]:
    rows = [[""] * int(tbl.get("colCnt")) for _ in range(int(tbl.get("rowCnt")))]
    for tr in tbl.findall(f"{HP}tr"):
        for tc in tr.findall(f"{HP}tc"):
            addr = tc.find(f"{HP}cellAddr")
            r, c = int(addr.get("rowAddr")), int(addr.get("colAddr"))
            rows[r][c] = _hwpx_cell_text(tc)  # merged cells: text sits in the anchor cell
    return rows


def parse_hwpx(path: Path) -> ParsedDocument:
    doc = ParsedDocument(str(path), "hwpx")
    z = zipfile.ZipFile(path)
    names = sorted(
        (n for n in z.namelist() if re.match(r"Contents/section\d+\.xml$", n)),
        key=lambda n: int(re.search(r"\d+", n).group()),
    )
    heads = HeadingTracker()

    def add(kind, text, rows=None):
        if kind == "text":
            heads.update(text)
        else:  # annex titles often sit in the first row of the annex's table
            heads.update_annex(" ".join(rows[0]))
        doc.blocks.append(Block(kind, text, len(doc.blocks), heading=heads.current, rows=rows))

    def walk(paragraphs):
        for p in paragraphs:
            buf: list[str] = []
            for run in p.findall(f"{HP}run"):
                for child in run:
                    tag = etree.QName(child).localname
                    if tag == "t":
                        buf.append(_hwpx_t(child))
                    elif tag == "tbl":
                        if "".join(buf).strip():
                            add("text", "".join(buf).strip())
                        buf = []
                        if child.get("colCnt") == "1":
                            # a single-column table is a layout box (law.go.kr wraps annexes
                            # in one): read each cell like body text so inner tables stay tables
                            for tc in child.findall(f"{HP}tr/{HP}tc"):
                                walk(tc.findall(f"{HP}subList/{HP}p"))
                        else:
                            rows = _hwpx_table(child)
                            add("table", table_text(rows), rows)
                    # ctrl (header/footer, page numbers), secPr, pictures: skipped
            if "".join(buf).strip():
                add("text", "".join(buf).strip())

    for name in names:
        walk(etree.fromstring(z.read(name)).findall(f"{HP}p"))
    return doc


# ---------- DOCX ----------


def parse_docx(path: Path) -> ParsedDocument:
    doc = ParsedDocument(str(path), "docx")
    d = Document(str(path))
    heads = HeadingTracker()

    def walk(container_el, parent):
        for el in container_el.iterchildren():
            if el.tag == f"{W}p":
                text = Paragraph(el, parent).text.strip()
                if text:
                    heads.update(text)
                    doc.blocks.append(Block("text", text, len(doc.blocks), heading=heads.current))
            elif el.tag == f"{W}tbl":
                table = Table(el, parent)
                if all(len(tr.findall(f"{W}tc")) == 1 for tr in el.findall(f"{W}tr")):
                    # single-column table = layout box: read each cell as body text
                    for r, tc in enumerate(el.findall(f"{W}tr/{W}tc")):
                        walk(tc, table.cell(r, 0))
                    continue
                rows = []
                for row in table.rows:
                    seen, cells = [], []  # keep element refs so lxml reuses the same proxies
                    for cell in row.cells:  # python-docx repeats merged cells; keep the first
                        cells.append("" if any(cell._tc is t for t in seen) else cell.text.strip())
                        seen.append(cell._tc)
                    rows.append(cells)
                heads.update_annex(" ".join(rows[0]) if rows else "")
                doc.blocks.append(
                    Block(
                        "table", table_text(rows), len(doc.blocks), heading=heads.current, rows=rows
                    )
                )

    walk(d.element.body, d)
    return doc


# ---------- PDF ----------


def split_statute_text(text: str) -> list[str]:
    """Split one page of text at article / annex starts so each piece has one heading."""
    pieces, cur = [], []
    for line in text.splitlines():
        starts = RE_ARTICLE.match(line) or RE_ADDENDA.match(line)
        if (starts or line.lstrip().startswith(("[별표", "■"))) and cur:
            pieces.append("\n".join(cur))
            cur = []
        cur.append(line)
    if cur:
        pieces.append("\n".join(cur))
    return [p.strip() for p in pieces if p.strip()]


def parse_pdf(path: Path) -> ParsedDocument:
    doc = ParsedDocument(str(path), "pdf")
    heads = HeadingTracker()
    for i, page in enumerate(PdfReader(path).pages, start=1):
        text = page.extract_text() or ""
        if not text.strip():
            doc.needs_ocr_pages.append(i)
            continue
        for piece in split_statute_text(text):
            heads.update(piece)
            doc.blocks.append(Block("text", piece, len(doc.blocks), page=i, heading=heads.current))
    return doc


def sniff_format(path: Path) -> str:
    head = path.read_bytes()[:4]
    if head.startswith(b"%PDF"):
        return "pdf"
    if head == b"PK\x03\x04":
        names = zipfile.ZipFile(path).namelist()
        if "word/document.xml" in names:
            return "docx"
        if "Contents/header.xml" in names or "mimetype" in names:
            return "hwpx"
    raise ValueError(f"{path.name}: unsupported format (PDF, DOCX, HWPX only)")


def parse(path: str | Path) -> ParsedDocument:
    """Parse by content, not extension (an uploaded .hwpx may really be an HWP file)."""
    path = Path(path)
    fmt = sniff_format(path)
    return {"pdf": parse_pdf, "hwpx": parse_hwpx, "docx": parse_docx}[fmt](path)
