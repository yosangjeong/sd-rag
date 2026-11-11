from itertools import pairwise

from sdrag.ingest.chunk import (
    canonical_text,
    chunk_fixed,
    chunk_structure,
    embed_input,
    est_tokens,
    split_span,
)
from sdrag.ingest.parse import Block, ParsedDocument, table_text


def make_doc(*blocks: tuple) -> ParsedDocument:
    """blocks: (kind, text, heading[, rows])"""
    doc = ParsedDocument("x.hwpx", "hwpx")
    for i, (kind, text, heading, *rows) in enumerate(blocks):
        doc.blocks.append(Block(kind, text, i, heading=heading, rows=rows[0] if rows else None))
    return doc


def assert_invariants(doc: ParsedDocument, chunks, max_tokens: int) -> None:
    text, _ = canonical_text(doc)
    covered = set()
    for c in chunks:
        assert est_tokens(c.text) <= max_tokens
        assert c.text.endswith(text[c.start : c.end])  # body is the canonical slice
        covered.update(range(c.start, c.end))
    assert all(ch.isspace() or i in covered for i, ch in enumerate(text))


def test_est_tokens_counts_hangul_as_1_4_and_other_chars_as_a_quarter():
    assert est_tokens("근로자") == 5  # ceil(3 * 1.4)
    assert est_tokens("abcd") == 1
    assert est_tokens("근로 abc") == 4  # ceil(2 * 1.4 + 4 * 0.25)


def test_short_articles_become_one_chunk_each():
    doc = make_doc(
        ("text", "근로기준법", None),
        ("text", "제1조(목적) 이 법은 근로조건의 기준을 정한다.", "제1조(목적)"),
        ("text", "제2조(정의) 이 법에서 사용하는 용어의 뜻은 다음과 같다.", "제2조(정의)"),
        ("text", "1. “근로자”란 임금을 목적으로 근로를 제공하는 사람을 말한다.", "제2조(정의)"),
    )
    chunks = chunk_structure(doc, "kr-x")
    assert [c.heading for c in chunks] == [None, "제1조(목적)", "제2조(정의)"]
    assert chunks[2].text.startswith("제2조") and chunks[2].text.endswith("말한다.")
    assert [c.id for c in chunks] == ["kr-x#0", "kr-x#1", "kr-x#2"]
    assert_invariants(doc, chunks, 500)


def test_long_article_is_cut_at_paragraph_marks():
    para = "사용자는 근로자에게 정당한 이유 없이 해고하지 못한다. " * 4  # ~140 tokens
    text = f"제23조(해고 등의 제한) ① {para}\n② {para}\n③ {para}"
    doc = make_doc(("text", text, "제23조(해고 등의 제한)"))
    chunks = chunk_structure(doc, "d", max_tokens=320)  # ①+② = 288, +③ = 426
    assert [c.text[:1] for c in chunks] == ["제", "③"]  # ①+② fit together, ③ does not
    assert all(c.heading == "제23조(해고 등의 제한)" for c in chunks)
    assert_invariants(doc, chunks, 320)


def test_split_span_falls_back_to_finer_boundaries():
    text = "가나다라마바사아 " * 30  # no newlines, no sentence ends: hard cuts only
    spans = split_span(text, 0, len(text), 50)
    assert spans[0][0] == 0 and spans[-1][1] == len(text)
    assert all(a[1] == b[0] for a, b in pairwise(spans))  # contiguous
    assert all(est_tokens(text[s:e]) <= 50 for s, e in spans)


def test_long_table_is_split_by_rows_with_the_header_repeated():
    rows = [["위반행위", "과태료(만원)"]] + [
        [f"{i}. 법 제{i}조를 위반한 경우", "100"] for i in range(40)
    ]
    doc = make_doc(
        ("text", "■ 시행령 [별표 1]", "[별표 1]"),
        ("table", table_text(rows), "[별표 1]", rows),
    )
    chunks = chunk_structure(doc, "d", max_tokens=120)
    tables = [c for c in chunks if c.kind == "table"]
    assert len(tables) > 2
    assert tables[0].text.startswith("■ 시행령 [별표 1]")  # title line merged into the table
    for c in tables[1:]:
        assert c.text.startswith("| 위반행위 | 과태료(만원) |\n| ")  # header, then whole rows
        assert c.text.endswith("|")
    assert_invariants(doc, chunks, 120)


def test_fixed_windows_overlap_and_cover_everything():
    doc = make_doc(
        ("text", "The employer shall pay overtime. " * 60, "§ 778.100 Overtime."),
        ("text", "제50조(근로시간) 1주 간의 근로시간은 40시간을 초과할 수 없다. " * 20, "제50조"),
    )
    chunks = chunk_fixed(doc, "d", size=100, overlap=20)
    assert len(chunks) > 5
    assert all(a.start < b.start < a.end for a, b in pairwise(chunks))  # overlap
    assert_invariants(doc, chunks, 100)
    assert all(not c.text[0].isspace() and not c.text[-1].isspace() for c in chunks)


def test_embed_input_prefixes_title_and_heading():
    doc = make_doc(("text", "제4조(목적) 본문", "제4조(목적)"), ("text", "앞부분", None))
    a, b = sorted(chunk_structure(doc, "d"), key=lambda c: c.start, reverse=True)
    assert (
        embed_input(b, "근로기준법 시행령") == "근로기준법 시행령 > 제4조(목적)\n제4조(목적) 본문"
    )
    assert embed_input(a, "근로기준법 시행령") == "근로기준법 시행령\n앞부분"
