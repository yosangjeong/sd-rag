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
words hyphenated at line ends are re-joined (``knowl-``/``edge``).

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
    needs_ocr_pages: list[int] = field(default_factory=list)


class HeadingTracker:
    """Remember the current article / annex while walking a statute in reading order."""

    def __init__(self) -> None:
        self.article: str | None = None
        self.annex: str | None = None
        self.in_addenda = False
        self.fr_part: str | None = None  # current "I." part, parent of "A." headings

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


def _pdf_tables(page) -> list:
    """Ruled tables of a page, top to bottom.

    - A row cut by a page break has no rule on the cut side, so pdfplumber would drop
      it to text; a rule is assumed where the page's vertical lines start and end.
    - One-column tables are layout boxes (law.go.kr frames annexes in one), read as
      text like in HWPX and DOCX.
    - Two columns whose second one never holds more than 2 characters are a framed
      paragraph whose border clips the last letter ("...이상으로 한다 | ."), not a table.
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
        tables.append(t)
    return sorted(tables, key=lambda t: t.bbox[1])


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


def parse_pdf(path: Path) -> ParsedDocument:
    doc = ParsedDocument(str(path), "pdf")
    heads = HeadingTracker()
    raw = [page.extract_text() or "" for page in PdfReader(path).pages]
    kept = strip_running_lines(raw)
    table_end = 0  # page the last table block ends on (a block keeps its first page)
    with pdfplumber.open(path) as plumber:
        for i, (orig, text, page) in enumerate(zip(raw, kept, plumber.pages), start=1):
            if not orig.strip():
                doc.needs_ocr_pages.append(i)
                continue
            tables = _pdf_tables(page)
            if not tables:
                parts = [("text", text)]
            else:
                running = Counter(_edge_key(ln) for ln in orig.splitlines() if ln.strip())
                running.subtract(_edge_key(ln) for ln in text.splitlines() if ln.strip())
                parts = _pdf_page_parts(page, tables, {k for k, n in running.items() if n > 0})
            for kind, content in parts:
                if kind == "text":
                    for piece in split_statute_text(dehyphenate(content)):
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
