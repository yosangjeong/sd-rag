from PIL import Image

from sdrag.ingest.ocr import (
    BedrockVisionOcr,
    CachedOcr,
    OcrResult,
    halves,
    ocr_pages,
    split_markdown,
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
