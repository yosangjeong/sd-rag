import zipfile

import pytest
from docx import Document

from sdrag.ingest.parse import (
    HeadingTracker,
    KoreanSpacing,
    _pdf_cell,
    dehyphenate,
    parse,
    split_statute_text,
    strip_running_lines,
)

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


def test_us_section_headings_need_a_capitalised_title():
    assert headings(
        [
            "§ 203. Definitions\nAs used in this chapter",
            "§ 825.102 of this part. For purposes of",  # wrapped cross-reference
            "§ 215(a), Sept. 23, 1966, 80 Stat. 830",  # amendment note
            "§ 541.4 Other laws and collective bar-",
            "§ 825.103 [Reserved]",
        ]
    ) == [
        "§ 203 Definitions",
        "§ 203 Definitions",
        "§ 203 Definitions",
        "§ 541.4 Other laws and collective bar",
        "§ 825.103 [Reserved]",
    ]


def test_wrapped_section_titles_are_rejoined():
    assert headings(
        [
            "§ 825.401 Filing a complaint with the\nFederal Government.\n(a) A complaint",
            "§ 651 Congressional statement of findings and\ndeclaration of purpose and policy\n(a)",
            "§ 652 Definitions\nFor the purposes of this chapter",  # complete: next line is body
        ]
    ) == [
        "§ 825.401 Filing a complaint with the Federal Government.",
        "§ 651 Congressional statement of findings and declaration of purpose and policy",
        "§ 652 Definitions",
    ]


def test_federal_register_headings():
    assert headings(
        [
            "AGENCY: Employment and Training Administration, Labor.",
            "ACTION: Final rule.",
            "SUMMARY: The Department rescinds ...",
            "I. Background and History",
            "IV. Procedural and Other Matters",
            "A. Review Under Executive Order 12866",
            "V. P. Loftis Co., 167 F. (2d) 286.",  # a case citation, not a heading
            "AGENCY: Institute of Museum and Library Services.",  # next notice on the page
            "A. Background",
        ]
    ) == [
        "AGENCY",
        "AGENCY",
        "SUMMARY",
        "I. Background and History",
        "IV. Procedural and Other Matters",
        "IV. Procedural and Other Matters / A. Review Under Executive Order 12866",
        "IV. Procedural and Other Matters / A. Review Under Executive Order 12866",
        "AGENCY",
        "A. Background",
    ]


def test_split_statute_text_on_us_sections():
    page = "end of the last one.\n§ 541.100 General rule for executive\nemployees."
    assert split_statute_text(page) == [
        "end of the last one.",
        "§ 541.100 General rule for executive\nemployees.",
    ]


# ---------- PDF cleanup ----------


def test_running_headers_and_footers_are_dropped_by_position():
    words = "가나다라마"
    pages = [
        "\n".join(
            [
                f"법제처 {i} 국가법령정보센터",
                "근로기준법",
                f"사용자는 {w}에 관하여",
                f"<개정 20{i}0. 5. 26.>",  # recurs on every page (digits aside), mid-page
                f"② 다만, {w}의 경우",
                f"{w}한다.",
                f"VerDate Sep<11>2014 Frm 0{i}",
            ]
        )
        for i, w in enumerate(words, start=1)
    ]
    out = strip_running_lines(pages)
    assert out[0].split("\n") == [
        "사용자는 가에 관하여",
        "<개정 2010. 5. 26.>",
        "② 다만, 가의 경우",
        "가한다.",
    ]
    assert strip_running_lines(pages[:2]) == pages[:2]  # too few pages to tell


def test_body_lines_repeating_at_page_ends_are_kept():
    # a fine table running over pages 4-7 of 10 ends every page with an amount
    pages = [f"법제처 {i} 국가법령정보센터\n본문 {i}쪽\n가나다\n라마바" for i in range(1, 11)]
    for i, amount in zip(range(3, 7), ("500만원", "300만원", "500만원", "200만원")):
        pages[i] += f"\n{amount}"
    out = strip_running_lines(pages)
    assert [p.split("\n")[-1] for p in out[3:7]] == ["500만원", "300만원", "500만원", "200만원"]
    assert all(not p.startswith("법제처") for p in out)


def test_dehyphenate_rejoins_soft_hyphens_only():
    assert dehyphenate("knowl-\nedge") == "knowledge"
    assert dehyphenate("commod -\nities") == "commodities"  # US Code typesetting
    assert dehyphenate("non- \nmanagement") == "non-management"
    assert dehyphenate("Subpart H-\nDefinitions") == "Subpart H-\nDefinitions"
    assert dehyphenate("근로-\n계약") == "근로-\n계약"


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


def test_pdf_cell_lines_rejoin_korean_words_but_keep_items_apart():
    assert (
        _pdf_cell("작업발판 일체형 거푸집 조\n립 및 해체") == "작업발판 일체형 거푸집 조립 및 해체"
    )
    assert _pdf_cell("1. 가설공사\n2. 굴착 및 발\n파 공사") == "1. 가설공사 2. 굴착 및 발파 공사"
    assert _pdf_cell("Nitro\nmethane") == "Nitro methane"
    assert _pdf_cell(None) == ""  # covered by a merged cell


def test_korean_line_wraps_are_rejoined_from_the_documents_own_words():
    body = [
        "이 규칙은 산업안전보건법 시행에 필요한 사항을 규정함을 목적으로 한다.",
        "사업주는 근로자의 안전을 위하여 필요한 사항을 정한다.",
        "고용노동부장관은 목적으로 정한 사항을 공표한다.",
    ]
    spacing = KoreanSpacing(["\n".join(body)])
    wrapped = "필요한 사항을 규정함을 목\n적으로 한다. 그 밖에 필요한\n사항을 정한다.\n① 사업주는"
    assert spacing.reflow(wrapped) == (
        "필요한 사항을 규정함을 목적으로 한다. 그 밖에 필요한 사항을 정한다.\n① 사업주는"
    )


def test_docx_heading_styles_become_headings(tmp_path):
    from docx import Document

    d = Document()
    d.add_heading("Guide", 0)
    d.add_heading("1. Leave", 1)
    d.add_heading("1.1 Annual", 2)
    d.add_paragraph("15 days after one year.")
    d.add_heading("2. Pay", 1)
    d.add_paragraph("Monthly.")
    d.save(tmp_path / "g.docx")
    heads = [(b.heading, b.text) for b in parse(tmp_path / "g.docx").blocks]
    assert heads[3] == ("1. Leave / 1.1 Annual", "15 days after one year.")
    assert heads[5] == ("2. Pay", "Monthly.")
