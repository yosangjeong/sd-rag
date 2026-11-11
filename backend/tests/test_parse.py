import zipfile

import pytest
from docx import Document

from sdrag.ingest.parse import HeadingTracker, parse, split_statute_text

# ---------- headings ----------


def headings(texts):
    h, out = HeadingTracker(), []
    for t in texts:
        h.update(t)
        out.append(h.current)
    return out


def test_article_heading_needs_title():
    assert headings(["제4조(해고 예고의 예외) 법 제26조에서 ...", "제26조에 따른 사유는 ..."]) == [
        "제4조(해고 예고의 예외)",
        "제4조(해고 예고의 예외)",  # a wrapped line starting with 제26조 is not a new article
    ]


def test_article_with_branch_number():
    assert headings(["제12조의 3 (질환) 내용"]) == ["제12조의3(질환)"]


def test_addenda_articles_are_prefixed():
    got = headings(["제1조(목적) ...", "부칙 <제436호, 2025. 2. 21.>", "제1조(시행일) ..."])
    assert got == ["제1조(목적)", "부칙", "부칙 제1조(시행일)"]


def test_annex_heading_after_title_marker():
    got = headings(
        ["제7조(벌칙) ...", "■ 근로기준법 시행규칙 [별표 3] <신설 2025. 2. 21>", "1. 질환"]
    )
    assert got == ["제7조(벌칙)", "[별표 3]", "[별표 3]"]


def test_split_statute_text_on_article_starts():
    page = "제1조(목적) 이 법은\n목적으로 한다.\n제2조(정의) 이 법에서\n제26조에 따른"
    assert split_statute_text(page) == [
        "제1조(목적) 이 법은\n목적으로 한다.",
        "제2조(정의) 이 법에서\n제26조에 따른",
    ]


# ---------- DOCX ----------


def make_docx(path):
    d = Document()
    d.add_paragraph("제1조(목적) 이 규칙은 목적으로 한다.")
    box = d.add_table(rows=2, cols=1)  # single-column layout box around an annex
    box.cell(0, 0).text = "■ 시행규칙 [별표 1] <개정 2021. 11. 19.>"
    box.cell(1, 0).text = "1. 첫째 사유"
    t = d.add_table(rows=2, cols=2)
    t.cell(0, 0).merge(t.cell(0, 1)).text = "질환명과 코드"
    t.cell(1, 0).text = "고혈압"
    t.cell(1, 1).text = "O10"
    d.save(path)


def test_docx_blocks_and_tables(tmp_path):
    p = tmp_path / "a.docx"
    make_docx(p)
    doc = parse(p)
    assert doc.format == "docx"
    assert [(b.kind, b.heading) for b in doc.blocks] == [
        ("text", "제1조(목적)"),
        ("text", "[별표 1]"),
        ("text", "[별표 1]"),
        ("table", "[별표 1]"),
    ]
    assert doc.blocks[-1].rows == [["질환명과 코드", ""], ["고혈압", "O10"]]
    assert doc.blocks[-1].text == "| 질환명과 코드 |  |\n| 고혈압 | O10 |"


# ---------- HWPX ----------

SEC = (
    '<hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" '
    'xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">{}</hs:sec>'
)


def p(inner):
    return f"<hp:p><hp:run>{inner}</hp:run></hp:p>"


def tc(r, c, text, rs=1, cs=1):
    return (
        f"<hp:tc><hp:subList>{p(f'<hp:t>{text}</hp:t>')}</hp:subList>"
        f'<hp:cellAddr colAddr="{c}" rowAddr="{r}"/><hp:cellSpan colSpan="{cs}" rowSpan="{rs}"/></hp:tc>'
    )


def make_hwpx(path, sections):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("mimetype", "application/hwp+zip")
        z.writestr("Contents/header.xml", "<hh:head xmlns:hh='x'/>")
        for i, body in enumerate(sections):
            z.writestr(f"Contents/section{i}.xml", SEC.format(body))


def test_hwpx_sections_tables_and_header_skipped(tmp_path):
    header = (
        "<hp:ctrl><hp:header><hp:subList>"
        + p("<hp:t>머리말</hp:t>")
        + "</hp:subList></hp:header></hp:ctrl>"
    )
    body = p(header + "<hp:t>제4조(해고) 내용<hp:tab/>끝</hp:t>")
    table = (
        '<hp:tbl rowCnt="2" colCnt="2"><hp:tr>' + tc(0, 0, "질환명", cs=2) + "</hp:tr>"
        "<hp:tr>" + tc(1, 0, "고혈압") + tc(1, 1, "O10") + "</hp:tr></hp:tbl>"
    )
    annex = p("<hp:t>■ 시행규칙 [별표 3] &lt;신설&gt;</hp:t>") + p(table)
    path = tmp_path / "a.hwpx"
    make_hwpx(path, [body, annex])
    doc = parse(path)
    assert doc.format == "hwpx"
    assert [(b.kind, b.heading, b.text) for b in doc.blocks] == [
        ("text", "제4조(해고)", "제4조(해고) 내용\t끝"),  # header text dropped
        ("text", "[별표 3]", "■ 시행규칙 [별표 3] <신설>"),
        ("table", "[별표 3]", "| 질환명 |  |\n| 고혈압 | O10 |"),
    ]


def test_format_is_sniffed_not_taken_from_extension(tmp_path):
    p_ = tmp_path / "looks-like.hwpx"
    make_docx(p_)
    assert parse(p_).format == "docx"
    hwp = tmp_path / "annex.hwpx"
    hwp.write_bytes(b"\xd0\xcf\x11\xe0" + b"\0" * 100)  # HWP 5.x (OLE) named .hwpx
    with pytest.raises(ValueError, match="unsupported"):
        parse(hwp)
