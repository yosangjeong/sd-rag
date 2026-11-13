"""Small text helpers shared by the pipeline: the question's language, model replies.

One rule for "is this Korean" everywhere: the answer language, the translation
direction, the jurisdiction default and an upload's language all use it.
"""

import re

RE_THINK = re.compile(r"<think>.*?</think>", re.DOTALL)


def is_korean(text: str) -> bool:
    """More than one Hangul syllable per three Latin letters ("FMLA 휴가는 며칠?" is Korean)."""
    hangul = len(re.findall(r"[가-힣]", text))
    latin = len(re.findall(r"[A-Za-z]", text))
    return hangul > latin / 3


def strip_think(text: str) -> str:
    """A reasoning model's reply without its <think> ... </think> block."""
    return RE_THINK.sub("", text).strip()
