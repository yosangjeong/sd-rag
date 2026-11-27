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

PDF text is cleaned before blocks are made: running headers/footers (page
numbers, "법제처 3 국가법령정보센터", CFR "VerDate ..." lines) are dropped and
words hyphenated at line ends are re-joined (``knowl-``/``edge``). Korean lines
wrap mid-word ("목" / "적으로"), so each Hangul-Hangul line break is decided to be a
space or nothing from the document's own words (``KoreanSpacing``).

PDF text comes from pypdf, which keeps the column order of two-column pages (CFR).
pypdf knows nothing of tables, so pages with ruled tables (law.go.kr annexes) are
read with pdfplumber instead: its tables become table blocks and only the text
outside them is read as text. pdfplumber is not used everywhere because it reads
two-column pages across both columns line by line.
"""

import logging
import re
import zipfile
from collections import Counter
from dataclasses import dataclass, field
from itertools import pairwise
from pathlib import Path
from typing import Literal

import pdfplumber
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from lxml import etree
from pypdf import PdfReader

from sdrag.common import versions
from sdrag.ingest.ocr import OcrEngine, ocr_pages, split_markdown

# pypdf logs a fontTools warning for every CFF font it meets (1,500 lines for our
# US PDFs); text extraction is unaffected
logging.getLogger("pypdf").setLevel(logging.ERROR)
logging.getLogger("pdfminer").setLevel(logging.ERROR)

HP = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

# 제4조(해고 예고의 예외...) / 제12조의3(...) at the start of a paragraph or line. The
# parenthesised title is required: a wrapped line can start with "제26조에 따른 ..."
RE_ARTICLE = re.compile(r"^\s*(제\s*\d+\s*조(?:\s*의\s*\d+)?)\s*(\([^)]*\))")
# [별표 3], [별표 2의2], [별표] — law.go.kr annex header, often after "■ <title> "
RE_ANNEX = re.compile(r"\[별표\s*(\d+(?:\s*의\s*\d+)?)?\]")
# "부칙 <제18176호, 2021. 5. 18.>" starts the addenda, whose articles restart at 제1조
RE_ADDENDA = re.compile(r"^\s*부\s*칙\s*(<[^>]*>)?\s*$|^\s*부\s*칙\s*<")
# US Code "§ 203. Definitions" / CFR "§ 541.4 Other laws ..." / "§ 825.103 [Reserved]".
# A capitalised title is required: a wrapped cross-reference can start a line too
# ("§ 825.102 of this part", "§ 215(a), Sept. 23, 1966").
RE_SECTION = re.compile(
    r"^\s*§\s?(\d+(?:\.\d+)?[a-z]?)\.?\s+(\[Reserved\]|[A-Z][a-z].*)$", re.MULTILINE
)
# a section title wrapped onto the next line ends in a connector: "Filing a complaint
# with the" / "Employees employed in certain tobacco, cotton, sugar cane or"
RE_OPEN_END = re.compile(
    r"(?:[-,;]|\b(?:and|or|of|for|the|to|in|on|with|by|from|a|an|under|between|at|as))$"
)
# Federal Register notices have no § numbers. They open with "AGENCY:", "SUMMARY:", ...
# ("ACTION: Final rule." is one line under AGENCY, not a heading of its own)
# and number their discussion "I. Background", "A. Review Under ..."; a heading has no
# final period, which keeps out case citations such as "V. P. Loftis Co., 167 F. 286."
RE_FR_LABEL = re.compile(
    r"^\s*(AGENCY|SUMMARY|DATES?|ADDRESSES|FOR FURTHER INFORMATION CONTACT"
    r"|SUPPLEMENTARY INFORMATION):"
)
RE_FR_PART = re.compile(r"^\s*([IVX]+|[A-H])\.\s+([A-Z][^\n]{2,90}?)\s*$")


def _fr_part(line: str) -> re.Match | None:
    m = RE_FR_PART.match(line)
    return m if m and not m.group(2).endswith(".") else None


def starts_heading(line: str) -> bool:
    """Does this line open a new heading (used to cut PDF pages into blocks)?"""
    return bool(
        RE_ARTICLE.match(line)
        or RE_ADDENDA.match(line)
        or RE_SECTION.match(line)
        or RE_FR_LABEL.match(line)
        or _fr_part(line)
        or line.lstrip().startswith(("[별표", "■"))
    )


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
    needs_ocr_pages: list[int] = field(default_factory=list)  # no text, not (yet) OCR'd
    ocr_pages: list[int] = field(default_factory=list)  # text came from OCR
    ocr_replaced_pages: list[int] = field(default_factory=list)  # OCR check kept Textract's text


class HeadingTracker:
    """Remember the current article / annex while walking a statute in reading order."""

    def __init__(self) -> None:
        self.article: str | None = None
        self.annex: str | None = None
        self.in_addenda = False
        self.fr_part: str | None = None  # current "I." part, parent of "A." headings
        self.outline_path: list[str] = []  # style-marked headings (DOCX), outer first

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
            return
        lines = text.split("\n")
        m = RE_SECTION.match(lines[0])
        if m:
            title = m.group(2).strip()
            for nxt in lines[1:4]:  # re-join a title wrapped over lines
                if not RE_OPEN_END.search(title) or not nxt.strip():
                    break
                title = title.rstrip("-") + ("" if title.endswith("-") else " ") + nxt.strip()
            self.article = f"§ {m.group(1)} {title.rstrip('-').strip()}"
            return
        m = RE_FR_LABEL.match(lines[0])
        if m:
            if m.group(1) == "AGENCY":  # a new notice starts; FR pages hold several
                self.fr_part = None
            self.article = m.group(1)
            return
        m = _fr_part(lines[0])
        if m:
            label = f"{m.group(1)}. {m.group(2)}"
            if re.fullmatch(r"[IVX]+", m.group(1)):
                self.fr_part = self.article = label
            else:
                self.article = f"{self.fr_part} / {label}" if self.fr_part else label

    def outline(self, text: str, level: int) -> None:
        """A heading marked by the document's own styles (DOCX "Heading 2", "Title"),
        for documents that are not statutes: the heading is the path of open levels."""
        self.outline_path = self.outline_path[: max(level - 1, 0)]
        self.outline_path.append(re.sub(r"\s+", " ", text)[:100])
        self.article = " / ".join(self.outline_path)

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
    """The grid by each cell's address. rowCnt / colCnt are a starting size only: files
    from other converters put cells past them (the grid grows) or leave addresses out
    (the cell takes the next place in its row)."""
    ncol = int(tbl.get("colCnt") or 0)
    rows = [[""] * ncol for _ in range(int(tbl.get("rowCnt") or 0))]
    for i, tr in enumerate(tbl.findall(f"{HP}tr")):
        for j, tc in enumerate(tr.findall(f"{HP}tc")):
            addr = tc.find(f"{HP}cellAddr")
            r = int(addr.get("rowAddr", i)) if addr is not None else i
            c = int(addr.get("colAddr", j)) if addr is not None else j
            while len(rows) <= r:
                rows.append([""] * ncol)
            if len(rows[r]) <= c:
                rows[r] += [""] * (c + 1 - len(rows[r]))
            rows[r][c] = _hwpx_cell_text(tc)  # merged cells: text sits in the anchor cell
    width = max((len(r) for r in rows), default=0)
    return [r + [""] * (width - len(r)) for r in rows]


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
                            if rows and any(any(r) for r in rows):  # an empty table: nothing
                                add("table", table_text(rows), rows)
                    # ctrl (header/footer, page numbers), secPr, pictures: skipped
            if "".join(buf).strip():
                add("text", "".join(buf).strip())

    for name in names:
        walk(etree.fromstring(z.read(name)).findall(f"{HP}p"))
    return doc


# ---------- DOCX ----------


RE_DOCX_HEADING = re.compile(r"^(?:Heading|제목)\s*(\d)$|^(Title)$", re.IGNORECASE)


def _docx_heading_level(para) -> int | None:
    """Outline level of a paragraph styled as a heading: Title = 0, Heading N = N."""
    try:
        m = RE_DOCX_HEADING.match(para.style.name or "")
    except (KeyError, AttributeError):  # a style id missing from styles.xml
        return None
    if not m:
        return None
    return 0 if m.group(2) else int(m.group(1))


def _docx_cell_text(cell) -> str:
    """A cell's paragraphs and, in order, any table nested in it (rows "a · b", joined
    by "; "): python-docx's cell.text leaves nested tables out, and their values were
    lost (a figure table inside a summary table)."""
    parts = []
    for el in cell._tc.iterchildren():
        if el.tag == f"{W}p":
            parts.append(Paragraph(el, cell).text)
        elif el.tag == f"{W}tbl":
            inner = Table(el, cell)
            parts.append(
                "; ".join(" · ".join(_docx_cell_text(c) for c in r.cells) for r in inner.rows)
            )
    return "\n".join(p for p in parts if p.strip()).strip()


def _docx_para_text(p) -> str:
    """A paragraph's text as Word shows it with changes accepted: runs inside tracked
    insertions (w:ins), content controls and smart tags count (python-docx's
    Paragraph.text skips them); deleted text (w:delText) does not."""
    out = []
    for node in p.iter(f"{W}t", f"{W}tab", f"{W}br", f"{W}cr"):
        if node.tag == f"{W}t":
            out.append(node.text or "")
        else:
            out.append("\t" if node.tag == f"{W}tab" else "\n")
    return "".join(out)


def parse_docx(path: Path) -> ParsedDocument:
    doc = ParsedDocument(str(path), "docx")
    d = Document(str(path))
    heads = HeadingTracker()

    def walk(container_el, parent):
        for el in container_el.iterchildren():
            if el.tag in (f"{W}sdt", f"{W}customXml"):  # content controls (forms, cover pages)
                content = el.find(f"{W}sdtContent") if el.tag == f"{W}sdt" else el
                if content is not None:
                    walk(content, parent)
            elif el.tag == f"{W}p":
                para = Paragraph(el, parent)
                text = _docx_para_text(el).strip()
                if text:
                    heads.update(text)
                    if (level := _docx_heading_level(para)) is not None and heads.annex is None:
                        heads.outline(text, level)
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
                        cells.append(
                            "" if any(cell._tc is t for t in seen) else _docx_cell_text(cell)
                        )
                        seen.append(cell._tc)
                    rows.append(cells)
                if not any(c.strip() for r in rows for c in r):  # an empty table, as in HWPX
                    continue
                heads.update_annex(" ".join(rows[0]))
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
        if starts_heading(line) and cur:
            pieces.append("\n".join(cur))
            cur = []
        cur.append(line)
    if cur:
        pieces.append("\n".join(cur))
    return [p.strip() for p in pieces if p.strip()]


EDGE = (0, 1, 2, -2, -1)  # line positions where running headers/footers sit


def _edge_key(line: str) -> str:
    """Digits and all spacing ignored: page numbers change, and pypdf and pdfplumber
    space the same header differently ("§ 778.311" / "§778.311")."""
    return re.sub(r"\s+", "", re.sub(r"\d+", "#", line))


def strip_running_lines(pages: list[str]) -> list[str]:
    """Drop running headers/footers: a line whose text (digits aside) sits at the same
    line position (EDGE) on at least 3 pages and on

    - 20% of the pages for the top 3 lines: law.go.kr prints no header on annex
      pages, which are most of some statutes;
    - 50% of the pages for the bottom 2 lines, which is where body text repeats:
      every article of 직업안정법 ends in "[전문개정 2009. 10. 9.]" (6 of 16 page
      ends), a fine table's last row ends 4 pages running ("500만원"). The only real
      footer in the corpus (GPO's "VerDate ...") is on every page.

    At least 3 pages: in a 5-page statute two "[별표 N] 삭제 <...>" pages match too.
    Position-bound so that body lines that merely recur mid-page are never touched."""
    if len(pages) < 3:
        return pages
    lines = [[ln for ln in p.splitlines() if ln.strip()] for p in pages]
    counts: dict[tuple[int, str], int] = {}
    for ls in lines:
        for pos in EDGE:
            if -len(ls) <= pos < len(ls):
                key = (pos, _edge_key(ls[pos]))
                counts[key] = counts.get(key, 0) + 1
    share = {pos: 0.2 if pos >= 0 else 0.5 for pos in EDGE}
    out = []
    for ls in lines:
        drop = {
            pos % len(ls)
            for pos in EDGE
            if -len(ls) <= pos < len(ls)
            and counts[(pos, _edge_key(ls[pos]))] >= max(3, share[pos] * len(pages))
        }
        out.append("\n".join(ln for j, ln in enumerate(ls) if j not in drop))
    return out


def dehyphenate(text: str) -> str:
    """Re-join words split at line ends: "knowl-\\nedge" (also "commod -\\nities", US
    Code style) -> "knowledge"; a hyphen followed by a space is a real one: "non-
    \\nmanagement" -> "non-management". Only before a lowercase letter, so list
    dashes and Korean text are untouched."""
    text = re.sub(r"(\w)- +\n(?=[a-z])", r"\1-", text)
    return re.sub(r"(\w) ?-\n(?=[a-z])", r"\1", text)


# a line inside a table cell that starts a list item: "1. 가설공사", "가. 굴착", "※ 비고"
RE_CELL_ITEM = re.compile(r"^(\d+\.|[가-하]\.|\d+\)|[가-하]\)|\(\d+\)|[※ㆍ·-])")


def _pdf_cell(cell: str | None) -> str:
    """PDF cells wrap lines wherever the column ends, mid-word in Korean ("조\n립"):
    re-join without a space, except before a list item or between English words."""
    if not cell:
        return ""  # None = covered by a merged cell
    lines = [ln.strip() for ln in cell.split("\n") if ln.strip()]
    out = lines[0] if lines else ""
    for ln in lines[1:]:
        english = out[-1:].isascii() and ln[0].isascii() and out[-1:].isalnum()
        out += " " + ln if RE_CELL_ITEM.match(ln) or english else ln
    return out


MIN_CELL_COVERAGE = 0.8


def _pdf_tables(page) -> list:
    """Ruled tables of a page, top to bottom.

    - A row cut by a page break has no rule on the cut side, so pdfplumber would drop
      it to text; a rule is assumed where the page's vertical lines start and end.
    - One-column tables are layout boxes (law.go.kr frames annexes in one), read as
      text like in HWPX and DOCX.
    - Two columns whose second one never holds more than 2 characters are a framed
      paragraph whose border clips the last letter ("...이상으로 한다 | ."), not a table.
    - A table whose cells hold less than MIN_CELL_COVERAGE of the characters inside its
      box lost text to cells pdfplumber could not assign (seen on a ministry press
      release: quotes in a 3-column box came out empty); its area is read as text.
    - A table with no characters at all (a blank form's grid) is dropped, as HWPX and
      DOCX drop theirs: it made a chunk of empty cells.
    """
    v = [e for e in page.edges if e["orientation"] == "v"]
    settings = (
        {"explicit_horizontal_lines": [min(e["top"] for e in v), max(e["bottom"] for e in v)]}
        if v
        else {}
    )
    tables = []
    for t in page.find_tables(settings):
        rows = t.extract()
        cols = max((len(r) for r in rows), default=0)
        if cols < 2 or (cols == 2 and all(len((r[-1] or "").strip()) <= 2 for r in rows)):
            continue
        inside = sum(not c["text"].isspace() for c in page.within_bbox(t.bbox).chars)
        kept = sum(len(re.sub(r"\s", "", cell or "")) for r in rows for cell in r)
        if not kept or kept < MIN_CELL_COVERAGE * inside:  # empty (as in HWPX and DOCX) or lossy
            continue
        tables.append(_widen_unruled(page, t))
    return sorted(tables, key=lambda t: t.bbox[1])


class _Table:
    """A table read again from text positions: what _pdf_page_parts needs of one."""

    def __init__(self, bbox, rows) -> None:
        self.bbox, self.rows = bbox, rows

    def extract(self):
        return self.rows


def _latin_page(page) -> bool:
    chars = [c["text"] for c in page.chars if not c["text"].isspace()]
    latin = sum(c.isascii() for c in chars)
    return bool(chars) and latin / len(chars) > 0.9


def _widen_unruled(page, t):
    """An English table without row rules (CFR: rules only around a few heads) comes out
    of pdfplumber's line strategy as the ruled middle only, every column's values
    stacked in one cell ("0\n130\n130 ..."), the columns beside it read as text. When
    every filled cell of a row holds the same number (3+) of lines, the table's band of
    its page column is read again by text alignment and kept if it has more columns.
    Korean pages are left as they are (law.go.kr tables are ruled)."""
    rows = t.extract()
    stacked = any(
        len({(c or "").count("\n") for c in r if c}) == 1
        and max((c or "").count("\n") for c in r) >= 2
        for r in rows
    )
    if not stacked or not _latin_page(page):
        return t
    x0, _, x1, _ = page.bbox
    cx = (t.bbox[0] + t.bbox[2]) / 2
    col = next(((a, b) for a, b in _pdf_columns(page, x0, x1) if a <= cx < b), (x0, x1))
    band = page.crop((col[0], t.bbox[1], min(col[1], x1), t.bbox[3]))
    text_rows = band.extract_table({"vertical_strategy": "text", "horizontal_strategy": "text"})
    width = max((len(r) for r in rows), default=0)
    if not text_rows or max(len(r) for r in text_rows) <= width or len(text_rows) <= len(rows):
        return t
    text_rows = [
        [_unruled_cell(c) for c in r] for r in text_rows if any((c or "").strip() for c in r)
    ]
    return _Table((col[0], t.bbox[1], min(col[1], x1), t.bbox[3]), text_rows)


def _unruled_cell(cell: str | None) -> str:
    """A cell of a re-read CFR table: leader dots dropped ("Jun ......" -> "Jun") and the
    minus sign, which GPO's font maps to the code of "¥" ("¥370"), restored."""
    cell = re.sub(r"\s*[.…]{3,}\s*", " ", cell or "").strip()
    return re.sub(r"¥(?=\d)", "−", cell)


def _center(obj) -> tuple[float, float]:
    return (obj["x0"] + obj["x1"]) / 2, (obj["top"] + obj["bottom"]) / 2


def _pdf_columns(page, x0: float, x1: float) -> list[tuple[float, float]]:
    """Column ranges of a page, cut at vertical gutters: x bands at least 4pt wide, in
    the middle 70% of the page, that almost no character overlaps. CFR pages have 2
    columns, Federal Register pages 3. Characters, not words: CFR's gutter is so
    narrow (8pt) that pdfplumber glues words across it ("compensa"+"amount"). A
    full-width line (a table title, the top of a page shared with the last notice)
    overlaps a gutter, hence "almost": up to 25% of the busiest 1pt band. Two checks
    keep single-column pages whole:

    - the 6pt right of the band must be dense (50% of the busiest band): a column's
      lines all start at one x. Where lines of one column merely end raggedly (a
      law.go.kr annex page) the band has no such edge (measured 0.22-0.28 there,
      0.62-0.80 at real CFR and Federal Register gutters);
    - a cut must leave 20% of the characters on each side (not the page margin)."""
    chars = page.chars
    if len(chars) < 500:
        return [(x0, x1)]
    n = int(x1 - x0) + 1
    cover = [0] * n
    for c in chars:
        for b in range(max(0, int(c["x0"] - x0)), min(n, int(c["x1"] - x0) + 1)):
            cover[b] += 1
    low = max(cover) * 0.25
    cuts, run = [], []
    for b in range(int(n * 0.15), int(n * 0.85)):
        if cover[b] <= low:
            run.append(b)
            continue
        if len(run) >= 4 and sum(cover[b : b + 6]) / 6 >= 0.5 * max(cover):
            cut = x0 + (run[0] + run[-1] + 1) / 2
            left = sum(1 for c in chars if _center(c)[0] < cut)
            if 0.2 <= left / len(chars) <= 0.8:
                cuts.append(cut)
        run = []
    edges = [x0, *cuts, x1 + 1]
    return list(pairwise(edges))


def _is_running(key: str, running: set[str]) -> bool:
    """Is a pdfplumber line one of the header/footer keys found in pypdf's text? Page
    numbers dropped first: the engines put them at opposite ends of the Federal
    Register header. A prefix is enough: pypdf glues GPO's sideways stamp onto the
    "VerDate ..." footer, pdfplumber does not."""
    key = key.replace("#", "")
    return any(
        key == r or (min(len(key), len(r)) >= 8 and r.startswith(key))
        for r in (r.replace("#", "") for r in running)
    )


def _pdf_page_parts(page, tables, running: set[str]) -> list[tuple[str, object]]:
    """("text", str) and ("table", rows) in reading order for a page with tables:
    column by column, top to bottom. Each character goes to exactly one region by its
    center, so nothing is lost or doubled at a border; text beside a table (same
    height) follows the table. Left out of the text: characters inside tables, rotated
    ones (GPO's sideways margin stamp), and the page's header/footer lines (`running`:
    the keys strip_running_lines dropped from pypdf's text of this page), which are
    removed over the full width before the page is cut into columns."""
    x0, top, x1, bottom = page.bbox

    def in_table(obj) -> bool:
        cx, cy = _center(obj)
        return any(t.bbox[0] <= cx <= t.bbox[2] and t.bbox[1] <= cy <= t.bbox[3] for t in tables)

    base = page.filter(lambda o: o.get("upright", True) and not in_table(o))
    lines = base.extract_text_lines()
    drop = [
        (ln["top"], ln["bottom"])
        for ln in [*lines[:3], *lines[-2:]]
        if _is_running(_edge_key(ln["text"]), running)
    ]
    if drop:
        base = base.filter(lambda o: not any(t <= _center(o)[1] <= b for t, b in drop))
    parts: list[tuple[str, object]] = []
    for cx0, cx1 in _pdf_columns(base, x0, x1):
        col_tables = sorted(
            (t for t in tables if cx0 <= (t.bbox[0] + t.bbox[2]) / 2 < cx1),
            key=lambda t: t.bbox[1],
        )
        bounds = [top, *(t.bbox[1] for t in col_tables), bottom + 1]
        for k, (y0, y1) in enumerate(pairwise(bounds)):
            if k:  # region k follows table k-1
                rows = col_tables[k - 1].extract()
                parts.append(("table", [[_pdf_cell(c) for c in row] for row in rows]))
            region = base.filter(
                lambda o, a=(cx0, cx1, y0, y1): (
                    a[0] <= _center(o)[0] < a[1] and a[2] <= _center(o)[1] < a[3]
                )
            )
            text = region.extract_text() or ""
            if text.strip():
                parts.append(("text", text))
    return parts


# a line that starts something (an item, an article, a note) is a real break, not a wrap
RE_LINE_OPENER = re.compile(
    r"^\s*([①-⑳]|\d+\.|[가-하]\.|\d+\)|[가-하]\)|\(\d+\)|제\s*\d+\s*조|부\s*칙|[<\[※■○ㆍ·-])"
)
WORD_EDGE_PUNCT = "「」『』“”‘’\"'(),.:;·ㆍ<>[]"


class KoreanSpacing:
    """Was a Korean PDF line break a space? Korean wraps lines anywhere, mid-word
    included ("목" / "적으로"), and pypdf keeps no trace of a space at the break.
    Measured against the same statutes' HWPX text: 36% of Hangul-Hangul wraps are
    spaces, so neither "always space" nor "always join" is right.

    The document teaches its own words: words in the middle of a line have real
    spacing, so they make a vocabulary. For a break between fragments L and R:

    1. L+R is a word at least as frequent as L or R alone -> join ("목적으로")
    2. L and R are both words -> space ("사항을" "규정함을")
    3. else boundary statistics: how often words start with R's first 3 syllables
       and end with L's last 3, relative to how often those occur at all

    88% / 85% correct on the two statutes with HWPX ground truth (36% before;
    eval/pdf_spacing.py). A
    corpus-wide vocabulary scored 2-4 points more but would tie every upload to the
    public corpus's vocabulary.
    """

    def __init__(self, texts: list[str]) -> None:
        self.words: Counter = Counter()
        for text in texts:
            for line in text.split("\n"):
                for w in line.split()[1:-1]:  # line-edge words may be fragments
                    if w := w.strip(WORD_EDGE_PUNCT):
                        self.words[w] += 1
        self.starts: Counter = Counter()
        self.ends: Counter = Counter()
        self.within: Counter = Counter()
        for w, n in self.words.items():
            for k in range(1, min(3, len(w)) + 1):
                self.starts[w[:k]] += n
                self.ends[w[-k:]] += n
            for sub in {w[a : a + k] for k in (1, 2, 3) for a in range(len(w) - k + 1)}:
                self.within[sub] += n

    def is_space(self, left: str, right: str) -> bool:
        L, R = left.strip(WORD_EDGE_PUNCT), right.strip(WORD_EDGE_PUNCT)
        if not L or not R:
            return True
        joined, l_n, r_n = self.words[L + R], self.words[L], self.words[R]
        if joined and joined >= min(l_n, r_n):
            return False
        if l_n and r_n:
            return True
        l3, r3 = L[-3:], R[:3]
        start = self.starts[r3] / (self.within[r3] or 1)
        end = self.ends[l3] / (self.within[l3] or 1)
        return start * end >= 0.2

    def reflow(self, text: str) -> str:
        """Join wrapped Hangul lines (with a space or not); keep every other break."""
        lines = text.split("\n")
        out = [lines[0]]
        for line in lines[1:]:
            prev = out[-1].rstrip()
            nxt = line.lstrip()
            if (
                prev
                and nxt
                and "가" <= prev[-1] <= "힣"
                and "가" <= nxt[0] <= "힣"
                and not RE_LINE_OPENER.match(nxt)
            ):
                space = self.is_space(prev.split()[-1], nxt.split()[0])
                out[-1] = prev + (" " if space else "") + nxt
            else:
                out.append(line)
        return "\n".join(out)


# a longer scan is refused with a message: about 14 s a page on 4 threads makes 300
# pages ~18 minutes, well inside the worker's 120-minute scale-in protection (the
# message's visibility is extended while it runs, worker/main.py Heartbeat)
MAX_OCR_PAGES = 300


def _stamped_scan(text: str, page) -> bool:
    """A page with under 50 characters of text and an image over half of it: a scan
    whose text layer is only a stamp or a page number."""
    if len("".join(text.split())) >= 50:
        return False
    w, h = float(page.width), float(page.height)
    covered = sum(max(0.0, min(im["x1"], w) - max(im["x0"], 0.0))
                  * max(0.0, min(im["bottom"], h) - max(im["top"], 0.0)) for im in page.images)  # fmt: skip
    return covered >= 0.5 * w * h


class UnreadableFile(ValueError):
    """A file that cannot be read at all; the message is shown to the user as is."""


def _open_pdf(path: Path) -> PdfReader:
    try:
        reader = PdfReader(path)
        if reader.is_encrypted and not reader.decrypt(""):  # an empty open password is common
            raise UnreadableFile(
                "암호가 걸린 PDF라 읽을 수 없습니다 (암호를 풀고 다시 올려 주세요)"
            )
        _ = len(reader.pages)  # a broken page tree fails here
        return reader
    except UnreadableFile:
        raise
    except Exception as e:  # pypdf raises several types for a damaged file
        raise UnreadableFile(f"손상되었거나 끝까지 받지 못한 PDF입니다 ({type(e).__name__})") from e


def _pdf_page(i, orig, text, page, blank, rotated, doc) -> list[tuple[str, object]] | None:
    """One page's parts for parse_pdf, or None for a page with no text (recorded)."""
    if not orig.strip() or (i in blank and i not in doc.ocr_pages):
        doc.needs_ocr_pages.append(i)  # no text, or OCR failed on it
        return None
    if i in doc.ocr_pages:
        return split_markdown(text)
    # a turned page: pdfplumber's boxes come back in unturned coordinates and the
    # table and column logic garbled the text; pypdf's text reads it in order
    tables = [] if i in rotated else _pdf_tables(page)
    if not tables:
        return [("text", text)]
    running = Counter(_edge_key(ln) for ln in orig.splitlines() if ln.strip())
    running.subtract(_edge_key(ln) for ln in text.splitlines() if ln.strip())
    return _pdf_page_parts(page, tables, {k for k, n in running.items() if n > 0})


def parse_pdf(path: Path, ocr: OcrEngine | None = None, progress=None) -> ParsedDocument:
    """Pages without a text layer are read by `ocr` when given; their text then goes
    through the same clean-up as extracted text (headers, line wraps, headings), and
    their "| a | b |" tables become table blocks. Without `ocr` (or if it fails on a
    page) such pages are only listed in needs_ocr_pages."""
    doc = ParsedDocument(str(path), "pdf")
    heads = HeadingTracker()
    reader = _open_pdf(path)
    raw = [page.extract_text() or "" for page in reader.pages]
    rotated = {i for i, page in enumerate(reader.pages, start=1) if page.rotation % 360}
    blank = [i for i, t in enumerate(raw, start=1) if not t.strip()]
    if ocr is not None:
        # a scan stamped with a little text ("Scanned with CamScanner", a page number,
        # a fax header) is a scan too: OCR it (no corpus page qualifies, 2026-11-16)
        with pdfplumber.open(path, password="") as plumber:
            stamped = set()
            for i, (t, page) in enumerate(zip(raw, plumber.pages), 1):
                if t.strip() and _stamped_scan(t, page):
                    stamped.add(i)
                page.close()  # pdfplumber keeps every parsed page until closed: ~9 MB each
            blank = sorted(set(blank) | stamped)
        if len(blank) > MAX_OCR_PAGES:
            raise UnreadableFile(
                f"스캔 쪽이 {len(blank)}쪽으로 한 번에 처리할 수 있는 {MAX_OCR_PAGES}쪽을 넘습니다 "
                "(나눠서 올려 주세요)"
            )
    if ocr is not None and blank:
        for i, res in ocr_pages(path, blank, ocr, progress=progress).items():
            raw[i - 1] = res.text
            if not res.text.strip():  # read but empty: still a page with no text
                continue
            doc.ocr_pages.append(i)
            if res.replaced:
                doc.ocr_replaced_pages.append(i)
        doc.ocr_pages.sort()
        doc.ocr_replaced_pages.sort()
    kept = strip_running_lines(raw)
    pages: list[tuple[int, list[tuple[str, object]]]] = []
    with pdfplumber.open(path, password="") as plumber:
        for i, (orig, text, page) in enumerate(zip(raw, kept, plumber.pages), start=1):
            try:
                parts = _pdf_page(i, orig, text, page, blank, rotated, doc)
            finally:
                page.close()  # 113 pages held 1 GB at the peak; closed one by one, 91 MB
            if parts is not None:
                pages.append((i, parts))

    spacing = KoreanSpacing([c for _, parts in pages for k, c in parts if k == "text"])
    table_end = 0  # page the last table block ends on (a block keeps its first page)
    for i, parts in pages:
        for kind, content in parts:
            if kind == "text":
                for piece in split_statute_text(spacing.reflow(dehyphenate(content))):
                    heads.update(piece)
                    doc.blocks.append(
                        Block("text", piece, len(doc.blocks), page=i, heading=heads.current)
                    )
                continue
            rows = content
            prev = doc.blocks[-1] if doc.blocks else None
            if (
                prev is not None
                and prev.kind == "table"
                and table_end == i - 1
                and parts[0] == (kind, content)
                and len(prev.rows[0]) == len(rows[0])
            ):
                # the page opens with the rest of the last page's table: one table.
                # A first row with an empty first cell is the second half of a row
                # cut by the page break ("번호" is printed on the first half only)
                if not rows[0][0] and prev.rows[-1][0]:
                    last = prev.rows[-1]
                    prev.rows[-1] = [
                        (x + " " + y).strip() for x, y in zip(last, rows[0], strict=True)
                    ]
                    rows = rows[1:]
                prev.rows += rows
                prev.text = table_text(prev.rows)
                table_end = i
                continue
            heads.update_annex(" ".join(rows[0]))
            table_end = i
            doc.blocks.append(
                Block(
                    "table",
                    table_text(rows),
                    len(doc.blocks),
                    page=i,
                    heading=heads.current,
                    rows=rows,
                )
            )
    return doc


OLE = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"  # old binary HWP / DOC, and encrypted DOCX
MAX_UNZIPPED = 200 * 2**20  # a 50 MB upload that inflates past this is refused (zip bomb;
# lxml and python-docx hold the whole XML, several times its size, on the 4 GB worker)


def sniff_format(path: Path) -> str:
    """The format by content, not extension. A file that is not one of the three gets
    an UnreadableFile with a message for the user (an old .hwp renamed .hwpx, a
    password-protected .docx, a damaged zip)."""
    with path.open("rb") as f:
        head = f.read(1024)
    if b"%PDF" in head:  # the header may follow some junk bytes (PDF spec: first 1 KB)
        return "pdf"
    if head.startswith(OLE[:4]):
        raise UnreadableFile("한글 구버전(HWP)·DOC 파일이거나 암호가 걸린 문서입니다. "
                             "HWPX, DOCX 또는 PDF로 저장해 올려 주세요")  # fmt: skip
    if head.startswith(b"PK\x03\x04"):
        try:
            with zipfile.ZipFile(path) as z:
                infos = z.infolist()
                names = {i.filename for i in infos}
                if sum(i.file_size for i in infos) > MAX_UNZIPPED:
                    raise UnreadableFile("압축을 푼 크기가 너무 큰 파일입니다")
                if "word/document.xml" in names:
                    return "docx"
                mimetype = z.read("mimetype")[:64] if "mimetype" in names else b""
                if "Contents/header.xml" in names or mimetype.startswith(b"application/hwp"):
                    return "hwpx"
        except zipfile.BadZipFile as e:
            raise UnreadableFile("파일이 손상되어 열 수 없습니다") from e
    raise UnreadableFile(f"{path.name}: PDF, DOCX, HWPX만 읽을 수 있습니다")


def parse(path: str | Path, ocr: OcrEngine | None = None, progress=None) -> ParsedDocument:
    """Parse by content, not extension (an uploaded .hwpx may really be an HWP file).
    `ocr` reads scanned PDF pages (see parse_pdf); progress(done, total) follows them."""
    path = Path(path)
    fmt = sniff_format(path)
    if fmt == "pdf":
        doc = parse_pdf(path, ocr, progress)
    else:
        doc = {"hwpx": parse_hwpx, "docx": parse_docx}[fmt](path)
    return mark_versions(doc)


# law.go.kr's "현행 법령" carries amendments not yet in force: the article appears twice,
# the version in force first, then the amended one ending in "[시행일: 2026. 11. 27.]
# 제18조의3". Both share a heading, so they were chunked together and an answer gave
# the two rules side by side, dating the amendment by its <개정 ...> date (the date it
# was enacted, not the one it takes effect). 87 such markers in 14 corpus statutes, in
# every format; many take effect on 2026-12-08.
RE_EFFECTIVE = re.compile(r"\[시행일\s*:\s*(\d{4})\.\s*(\d{1,2})\.\s*(\d{1,2})\.?\s*\]([^\n]*)")
RE_ARTICLE_ID = re.compile(r"제\s*(\d+)\s*조(?:\s*의\s*(\d+))?")


def _article_id(heading: str | None) -> str | None:
    m = RE_ARTICLE_ID.match(heading or "")
    return f"제{m.group(1)}조" + (f"의{m.group(2)}" if m.group(2) else "") if m else None


def mark_versions(doc: ParsedDocument) -> ParsedDocument:
    """Give the two versions of an amended article headings of their own.

    For each "[시행일: D] 제N조 ..." marker, the amended version runs from the last block
    that starts article 제N조 up to the marker; it gets "<heading> [D 시행]". The version
    before it (the previous run of 제N조) gets "<heading> [개정 전, D 전까지]". Both
    labels are facts that hold on any day; which one is in force is decided when a
    question is answered (agent/answer.py gets today's date). Distinct headings also
    keep the versions in separate chunks."""
    blocks = doc.blocks

    def starts(i: int, aid: str) -> bool:
        m = RE_ARTICLE.match(blocks[i].text)
        return bool(m) and _article_id(re.sub(r"\s+", "", m.group(1))) == aid

    marks: dict[str, list[tuple[int, str]]] = {}  # article -> (block, date) of its markers
    for k, b in enumerate(blocks):
        for m in RE_EFFECTIVE.finditer(b.text):  # a block can hold several markers
            date = f"{m.group(1)}. {int(m.group(2))}. {int(m.group(3))}."
            for x in RE_ARTICLE_ID.finditer(m.group(4)):
                aid = f"제{x.group(1)}조" + (f"의{x.group(2)}" if x.group(2) else "")
                if (k, date) not in marks.setdefault(aid, []):
                    marks[aid].append((k, date))
    for aid, ms in marks.items():
        last = max(k for k, _ in ms)
        new = next((i for i in range(last, -1, -1) if starts(i, aid)), None)
        if new is None or "[" in (blocks[new].heading or "").split(")")[-1]:
            continue  # article not found before the marker, or already labelled
        # the version before it: the run of the same article right before (its title may
        # differ: "근로감독관의 권한" -> "노동감독관의 권한"); one further away is another
        # article of that number (a 부칙's 제1조)
        old = next((i for i in range(new - 1, -1, -1) if starts(i, aid)), None)
        if old is not None and any(
            blocks[i].heading != blocks[old].heading for i in range(old, new)
        ):
            old = None
        # the amended version's date: a marker the version before it does not carry too
        # (근로기준법 제116조: both carry "[시행일: 2027. 1. 1.] 제116조제1항제2호", only the
        # second "[시행일: 2026. 12. 8.] 제116조제2항제1호")
        dates = [d for k, d in ms if new <= k <= last]
        before = {d for k, d in ms if old is not None and old <= k < new}
        if not dates:
            continue
        # several of its own: the earliest, when the version starts to apply (제72조 from
        # 2027. 4. 28., only its 제5항 from 2027. 10. 28.)
        own = [d for d in dates if d not in before] or dates
        date = min(own, key=lambda d: tuple(int(x) for x in d.rstrip(".").split(". ")))
        base = blocks[new].heading
        for i in range(new, last + 1):
            if blocks[i].heading == base:
                blocks[i].heading = versions.amended(base, date)
        if old is not None:
            prev = blocks[old].heading
            for i in range(old, new):
                blocks[i].heading = versions.before(prev, date)
    return doc
