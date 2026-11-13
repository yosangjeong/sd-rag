"""Measure how well Korean PDF line wraps are re-joined, against the same statute's HWPX.

Korean PDF lines wrap anywhere, mid-word included, and parse.KoreanSpacing decides for
each Hangul-Hangul wrap whether it was a space. The HWPX edition of the statute has
the real spacing, so it is the ground truth:

- break accuracy: every wrap in the PDF text (parsed with re-joining switched off) is
  located in the HWPX text by the 8 non-space characters on each side, which says
  whether a space was there; KoreanSpacing's decision is compared with that. Wraps
  before an item / article / note (RE_LINE_OPENER) stay line breaks and are left out.
- eojeol match: share of the Hangul words in the PDF's text blocks that are words of
  the HWPX text (multiset), with re-joining off and on. A wrongly joined or split word
  is no word of the HWPX.

    cd backend && uv run python ../eval/pdf_spacing.py
"""

import re
import sys
from collections import Counter
from contextlib import contextmanager
from itertools import pairwise
from pathlib import Path

from sdrag.ingest import layout
from sdrag.ingest import parse as P

DATA = Path(__file__).resolve().parent.parent / "data"
RAW = DATA / "raw"


def corpus_pair(pair: str) -> Path:
    """<family>/<kind> folder of a Korean statute, in whichever field holds it."""
    return next(r / pair for r in layout.kr_family_roots(DATA) if (r / pair).is_dir())


PAIRS = ["kr-occupational-safety/rul", "kr-industrial-accident/dec"]
HANGUL = re.compile("[가-힣]")


@contextmanager
def no_reflow():
    """Parse with re-joining switched off (eval only: the parser has no such option)."""
    original = P.KoreanSpacing.reflow
    P.KoreanSpacing.reflow = lambda self, text: text
    try:
        yield
    finally:
        P.KoreanSpacing.reflow = original


def truth_spacing(truth) -> tuple[str, list[bool]]:
    """The HWPX text without spaces, and whether a space follows each character."""
    chars: list[str] = []
    space_after: list[bool] = []
    for ch in re.sub(r"\s+", " ", " ".join(b.text for b in truth.blocks)):
        if ch == " ":
            if space_after:
                space_after[-1] = True
        else:
            chars.append(ch)
            space_after.append(False)
    return "".join(chars), space_after


def labelled_wraps(pdf, truth) -> list[tuple[str, str, bool]]:
    """(line, next line, truth: space at the wrap) for Hangul-Hangul wraps found once."""
    ns, space_after = truth_spacing(truth)
    out = []
    for b in pdf.blocks:
        if b.kind != "text":
            continue
        lines = b.text.split("\n")
        for a, c in pairwise(lines):
            a, c = a.rstrip(), c.lstrip()
            if not (a and c and HANGUL.match(a[-1]) and HANGUL.match(c[0])):
                continue
            if P.RE_LINE_OPENER.match(c):
                continue
            left, right = re.sub(r"\s", "", a)[-8:], re.sub(r"\s", "", c)[:8]
            i = ns.find(left + right)
            if len(left) < 4 or len(right) < 4 or i < 0 or ns.find(left + right, i + 1) >= 0:
                continue  # too short to locate, not found, or ambiguous
            out.append((a, c, space_after[i + len(left) - 1]))
    return out


def eojeol_match(pdf, truth) -> float:
    punct = P.WORD_EDGE_PUNCT

    def words(doc, text_only):
        return Counter(
            w.strip(punct)
            for b in doc.blocks
            if b.kind == "text" or not text_only
            for w in b.text.split()
            if w.strip(punct) and (not text_only or HANGUL.search(w))
        )

    got, want = words(pdf, True), words(truth, False)
    return sum((got & want).values()) / sum(got.values())


def main() -> None:
    for pair in PAIRS:
        truth = P.parse(next((RAW / "truth" / pair).glob("*.hwpx")))
        pdf_path = next(corpus_pair(pair).glob("*.pdf"))
        with no_reflow():
            raw = P.parse(pdf_path)
        spacing = P.KoreanSpacing([b.text for b in raw.blocks if b.kind == "text"])
        wraps = labelled_wraps(raw, truth)
        right = sum(spacing.is_space(a.split()[-1], c.split()[0]) == s for a, c, s in wraps)
        spaces = sum(s for *_, s in wraps)
        print(
            f"{pair:28} wraps {len(wraps):4} (spaces {spaces / len(wraps):5.1%})  "
            f"break accuracy {right / len(wraps):5.1%}  "
            f"eojeol match {eojeol_match(raw, truth):5.1%} -> "
            f"{eojeol_match(P.parse(pdf_path), truth):5.1%}"
        )


if __name__ == "__main__":
    sys.exit(main())
