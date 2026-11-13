"""Make awkward test inputs from the public test documents in data/raw/bench/robustness/.

    cd backend && uv run python ../eval/robustness_files.py

- rotated.pdf      every page of the press release turned 90 degrees
- encrypted.pdf    the same, with an open password (should fail with a clear reason)
- truncated.pdf    the first 40% of the bytes of a PDF (a broken download)
- nested.docx      a DOCX with a table inside a table cell and a merged header
- empty.docx       a DOCX with no text at all
- big.pdf          three public PDFs joined (about 150 pages)
"""

from pathlib import Path

import pypdf
from docx import Document

DIR = Path(__file__).resolve().parents[1] / "data" / "raw" / "bench" / "robustness"


def main() -> None:
    press = DIR / "moel-press.pdf"
    w = pypdf.PdfWriter()
    for p in pypdf.PdfReader(press).pages:
        w.add_page(p.rotate(90))
    w.write(DIR / "rotated.pdf")

    w = pypdf.PdfWriter(clone_from=press)
    w.encrypt(user_password="secret", owner_password="owner")
    w.write(DIR / "encrypted.pdf")

    data = (DIR / "fomcminutes20240131.pdf").read_bytes()
    (DIR / "truncated.pdf").write_bytes(data[: int(len(data) * 0.4)])

    d = Document()
    d.add_heading("분기 실적 요약", 1)
    t = d.add_table(rows=2, cols=2)
    t.style = "Table Grid"
    head = t.rows[0].cells
    head[0].merge(head[1]).text = "2026년 3분기"
    t.rows[1].cells[0].text = "매출"
    inner = t.rows[1].cells[1].add_table(rows=2, cols=2)
    for r, (k, v) in enumerate([("국내", "120억 원"), ("해외", "85억 원")]):
        inner.rows[r].cells[0].text, inner.rows[r].cells[1].text = k, v
    d.add_paragraph("해외 매출은 전년 대비 18% 늘었다.")
    d.save(DIR / "nested.docx")
    Document().save(DIR / "empty.docx")

    w = pypdf.PdfWriter()
    for name in ("p15.pdf", "NIST.SP.800-63b.pdf", "fomcminutes20240131.pdf"):
        for p in pypdf.PdfReader(DIR / name).pages:
            w.add_page(p)
    w.write(DIR / "big.pdf")
    print("written:", ", ".join(p.name for p in sorted(DIR.iterdir())))


if __name__ == "__main__":
    main()
