"""Convert an HWPX document (paragraphs + tables) into a DOCX file.

Used for statutes assigned the DOCX format: law.go.kr offers no real DOCX
export (its "DOC" is RTF with annexes embedded as images), so the DOCX is
generated from the official HWPX. What is carried over:

- paragraph text (tabs and line breaks included)
- tables, including merged cells (hp:cellSpan) and tables nested in cells
- one page break per HWPX section, so each annex (별표) starts on a new page

What is dropped on purpose: page headers/footers, images (QR code, logos),
and character/paragraph styling. None of it affects the searchable content.

    uv run --no-project --python 3.12 --with lxml --with python-docx \
        python data/scripts/hwpx_to_docx.py IN.hwpx OUT.docx
"""

import re
import sys
import zipfile
from pathlib import Path

from docx import Document
from docx.enum.text import WD_BREAK
from lxml import etree

HP = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"


def run_text(t_el) -> str:
    """Text of one <hp:t>, which may contain <hp:tab/>, <hp:lineBreak/> etc."""
    parts = [t_el.text or ""]
    for child in t_el:
        name = etree.QName(child).localname
        if name == "tab":
            parts.append("\t")
        elif name == "lineBreak":
            parts.append("\n")
        parts.append(child.tail or "")
    return "".join(parts)


def emit_paragraphs(p_elements, container) -> None:
    """Write HWPX <hp:p> elements into a python-docx container (document or cell)."""
    for p in p_elements:
        buf: list[str] = []

        def flush():
            text = "".join(buf)
            buf.clear()
            if text.strip():
                para = container.add_paragraph()
                lines = text.split("\n")
                for i, line in enumerate(lines):
                    run = para.add_run(line)
                    if i < len(lines) - 1:
                        run.add_break()

        for run in p.findall(f"{HP}run"):
            for child in run:
                name = etree.QName(child).localname
                if name == "t":
                    buf.append(run_text(child))
                elif name == "tbl":
                    flush()
                    emit_table(child, container)
                # ctrl (header/footer/page number), secPr, pic, etc. are skipped
        flush()


def emit_table(tbl, container) -> None:
    rows, cols = int(tbl.get("rowCnt")), int(tbl.get("colCnt"))
    table = container.add_table(rows=rows, cols=cols)
    table.style = "Table Grid"
    for tc in tbl.iter(f"{HP}tc"):
        if tc.getparent().getparent() is not tbl:  # cell of a nested table
            continue
        addr, span = tc.find(f"{HP}cellAddr"), tc.find(f"{HP}cellSpan")
        r, c = int(addr.get("rowAddr")), int(addr.get("colAddr"))
        rs = int(span.get("rowSpan")) if span is not None else 1
        cs = int(span.get("colSpan")) if span is not None else 1
        cell = table.cell(r, c)
        if rs > 1 or cs > 1:
            cell = cell.merge(table.cell(r + rs - 1, c + cs - 1))
        # a new cell starts with one empty paragraph; reuse it for the first line
        first = cell.paragraphs[0]
        sub = tc.find(f"{HP}subList")
        emit_paragraphs(sub.findall(f"{HP}p") if sub is not None else [], cell)
        if len(cell.paragraphs) > 1 and not first.text:
            first._element.getparent().remove(first._element)


def convert(src: Path, dst: Path) -> None:
    z = zipfile.ZipFile(src)
    names = sorted(
        (n for n in z.namelist() if re.match(r"Contents/section\d+\.xml$", n)),
        key=lambda n: int(re.search(r"\d+", n).group()),
    )
    doc = Document()
    for i, name in enumerate(names):
        if i:
            doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
        sec = etree.fromstring(z.read(name))
        emit_paragraphs(sec.findall(f"{HP}p"), doc)
    doc.save(dst)


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    convert(src, dst)
    print(f"wrote {dst}")


if __name__ == "__main__":
    main()
