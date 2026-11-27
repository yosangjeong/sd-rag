import pytest
from PIL import Image

from sdrag.ingest.ocr import (
    BedrockVisionOcr,
    CachedOcr,
    CheckedOcr,
    OcrError,
    OcrResult,
    halves,
    layout_text,
    ocr_pages,
    split_markdown,
    tidy,
)
from sdrag.ingest.parse import parse


def test_split_markdown_tables_and_text():
    answer = (
        "■ 시행령 [별표 1]\n과태료의 부과기준\n"
        "| 위반행위 | 과태료 |\n| --- | --- |\n| 가. 법 제10조 위반 | 300 |\n| 나. 법 제12조 위반 |\n"
        "비고: 금액은 만원 단위"
    )
    assert split_markdown(answer) == [
        ("text", "■ 시행령 [별표 1]\n과태료의 부과기준"),
        (
            "table",
            [["위반행위", "과태료"], ["가. 법 제10조 위반", "300"], ["나. 법 제12조 위반", ""]],
        ),
        ("text", "비고: 금액은 만원 단위"),
    ]


def test_halves_cut_at_a_blank_row():
    page = Image.new("L", (100, 200), 0)  # all "ink"
    page.paste(255, (0, 95, 100, 105))  # one blank band near the middle
    top, bottom = halves(page)
    assert (top.size[1], bottom.size[1]) == (95, 105)


class FakeClient:
    """Bedrock runtime stand-in: answers are taken from a list, calls recorded."""

    def __init__(self, answers):
        self.answers, self.calls = list(answers), []

    def converse(self, **kw):
        self.calls.append(kw)
        text, stop = self.answers.pop(0)
        return {
            "output": {"message": {"content": [{"text": text}]}},
            "usage": {"inputTokens": 100, "outputTokens": 10},
            "stopReason": stop,
        }


def test_answer_cut_by_token_limit_is_read_again_in_halves():
    client = FakeClient(
        [("1818181818", "max_tokens"), ("윗부분", "end_turn"), ("아랫부분", "end_turn")]
    )
    ocr = BedrockVisionOcr("qwen.test", "ap-southeast-2", client=client)
    res = ocr.transcribe(Image.new("L", (100, 200), 255))
    assert (res.text, res.split) == ("윗부분\n아랫부분", True)
    assert (res.input_tokens, res.output_tokens) == (300, 30)  # all three calls counted
    assert len(client.calls) == 3
    assert client.calls[0]["inferenceConfig"]["maxTokens"] > 0  # never left to the default


def test_cache_pays_once(tmp_path):
    class Counting:
        name, calls = "fake", 0

        def transcribe(self, image):
            Counting.calls += 1
            return OcrResult("본문", 1, 1)

    cached = CachedOcr(Counting(), tmp_path)
    image = Image.new("L", (50, 50), 255)
    assert cached.transcribe(image).text == cached.transcribe(image).text == "본문"
    assert Counting.calls == 1


def image_only_pdf(path, pages):
    images = [Image.new("L", (300, 400), 255) for _ in range(pages)]
    images[0].save(path, "PDF", save_all=True, append_images=images[1:])
    return path


class PageOcr:
    """OCR engine stand-in: the n-th call returns the n-th text."""

    name = "fake"

    def __init__(self, texts):
        self.texts = list(texts)

    def transcribe(self, image):
        return OcrResult(self.texts.pop(0))


def test_scanned_pages_are_read_by_ocr_and_parsed_like_text(tmp_path):
    pdf = image_only_pdf(tmp_path / "scan.pdf", 1)
    page = (
        "제1조(목적) 이 영은 법에서 위임된 사항을\n규정함을 목적으로 한다.\n"
        "■ 시행령 [별표 1]\n| 위반행위 | 과태료 |\n| --- | --- |\n| 가. 법 제10조 위반 | 300 |"
    )
    doc = parse(pdf, ocr=PageOcr([page]))
    assert (doc.ocr_pages, doc.needs_ocr_pages) == ([1], [])
    text, annex, table = doc.blocks
    assert text.heading == "제1조(목적)" and text.page == 1
    assert annex.heading == table.heading == "[별표 1]"
    assert table.kind == "table" and table.rows == [
        ["위반행위", "과태료"],
        ["가. 법 제10조 위반", "300"],
    ]


def test_without_ocr_scanned_pages_are_only_flagged(tmp_path):
    doc = parse(image_only_pdf(tmp_path / "scan.pdf", 2))
    assert (doc.blocks, doc.needs_ocr_pages, doc.ocr_pages) == ([], [1, 2], [])


def test_pages_render_safely_in_parallel(tmp_path):
    # PDFium is not thread-safe; unguarded, this crashed or failed to load the PDF
    pdf = tmp_path / "blank.pdf"
    images = [Image.new("L", (1650, 2330), 255) for _ in range(16)]
    images[0].save(pdf, "PDF", save_all=True, append_images=images[1:])
    for _ in range(3):
        assert sorted(ocr_pages(pdf, list(range(1, 17)), PageOcr(["x"] * 16))) == list(range(1, 17))


class Fixed:
    """OCR engine stand-in with one answer (or one error) for every page."""

    def __init__(self, name, text=None, error=None):
        self.name, self.text, self.error, self.calls = name, text, error, 0

    def transcribe(self, image):
        self.calls += 1
        if self.error:
            raise self.error
        return OcrResult(self.text, 1, 1)


PAGE = Image.new("L", (50, 50), 255)
READ = "제1조(목적) 이 법은 근로조건의 기준을 정함을 목적으로 한다."


def test_check_keeps_the_reader_when_it_agrees():
    res = CheckedOcr(
        Fixed("qwen", READ), Fixed("textract", READ.replace("목적", "목 적"))
    ).transcribe(PAGE)
    assert (res.text, res.replaced, res.missing) == (READ, False, 0.0)  # spacing does not count


def test_check_replaces_a_page_with_invented_text():
    invented = READ + " 다만, 대통령령으로 정하는 사업장은 예외로 한다."  # not on the page
    res = CheckedOcr(Fixed("qwen", invented), Fixed("textract", READ)).transcribe(PAGE)
    assert res.replaced and res.text == READ and res.missing > 0.05


def test_a_failing_check_never_fails_the_page():
    res = CheckedOcr(Fixed("qwen", READ), Fixed("textract", error=RuntimeError("down"))).transcribe(
        PAGE
    )
    assert (res.text, res.replaced, res.missing) == (READ, False, None)


def test_reader_errors_are_not_hidden_by_the_check():
    busy = OcrError("throttled", transient=True)
    with pytest.raises(OcrError):
        CheckedOcr(Fixed("qwen", error=busy), Fixed("textract", READ)).transcribe(PAGE)


def test_each_engine_keeps_its_own_cache(tmp_path):
    qwen, textract = Fixed("qwen", READ), Fixed("textract", READ)
    CachedOcr(qwen, tmp_path).transcribe(PAGE)  # read before the check existed
    checked = CheckedOcr(CachedOcr(qwen, tmp_path), CachedOcr(textract, tmp_path))
    checked.transcribe(PAGE)
    checked.transcribe(PAGE)
    assert (qwen.calls, textract.calls) == (1, 1)  # the old reader entry still hits


def test_replaced_pages_are_listed_by_the_parser(tmp_path):
    pdf = image_only_pdf(tmp_path / "scan.pdf", 2)

    class SecondInvented:
        name = "qwen"

        def __init__(self):
            self.n = 0

        def transcribe(self, image):
            self.n += 1
            return OcrResult(READ + (" 지어낸 문장이 길게 붙어 있다." if self.n == 2 else ""))

    ocr = CheckedOcr(SecondInvented(), Fixed("textract", READ))
    doc = parse(pdf, ocr=ocr)
    assert (doc.ocr_pages, doc.ocr_replaced_pages) == ([1, 2], [2])


def test_textract_layout_order_and_tables():
    def b(id, kind, text=None, children=(), **kw):
        out = {"Id": id, "BlockType": kind, **kw}
        if text is not None:
            out["Text"] = text
        if children:
            out["Relationships"] = [{"Type": "CHILD", "Ids": list(children)}]
        return out

    resp = {"Blocks": [
        b("p", "PAGE", children=["L2", "L1", "T"]),
        b("lay1", "LAYOUT_TITLE", children=["L1"]),  # layout says L1 comes first
        b("lay2", "LAYOUT_TEXT", children=["L2"]),
        b("lay3", "LAYOUT_TABLE", children=["L3", "L4"]),
        b("L1", "LINE", "제1조(목적)", ["w1"]), b("L2", "LINE", "이 법은", ["w2"]),
        b("L3", "LINE", "구분 금액", ["w3", "w4"]), b("L4", "LINE", "가 300", ["w5", "w6"]),
        b("T", "TABLE", children=["c1", "c2", "c3", "c4"]),
        b("c1", "CELL", children=["w3"], RowIndex=1, ColumnIndex=1),
        b("c2", "CELL", children=["w4"], RowIndex=1, ColumnIndex=2),
        b("c3", "CELL", children=["w5"], RowIndex=2, ColumnIndex=1),
        b("c4", "CELL", children=["w6"], RowIndex=2, ColumnIndex=2),
        *[b(w, "WORD", t) for w, t in zip(["w1", "w2", "w3", "w4", "w5", "w6"],
                                         ["제1조(목적)", "이 법은", "구분", "금액", "가", "300"])],
    ]}  # fmt: skip
    assert layout_text(resp) == "제1조(목적)\n이 법은\n| 구분 | 금액 |\n| 가 | 300 |"


def test_br_tags_from_the_model_are_not_kept():
    answer = "제1조(목적)<br>이 영은\n| 가. 사업주가 법 제14조를 위<br>반한 경우 | 500만원 |"
    assert (
        tidy(answer) == "제1조(목적)\n이 영은\n| 가. 사업주가 법 제14조를 위 반한 경우 | 500만원 |"
    )


def test_br_in_a_scanned_table_is_cleaned_before_parsing(tmp_path):
    pdf = image_only_pdf(tmp_path / "scan.pdf", 1)
    doc = parse(
        pdf, ocr=PageOcr(["[별표 1]\n| 위반행위 | 과태료 |\n| 가. 법 제10조<br>위반 | 300 |"])
    )
    assert doc.blocks[-1].rows[-1] == ["가. 법 제10조 위반", "300"]


def test_check_does_not_count_br_tags_as_invented():
    res = CheckedOcr(
        Fixed("qwen", "| 가. 위<br>반 | 300 |" * 3), Fixed("textract", "| 가. 위 반 | 300 |" * 3)
    ).transcribe(PAGE)
    assert not res.replaced
