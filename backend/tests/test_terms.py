import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "eval"))

from evalset import CACHE

from sdrag.retrieval.terms import EN, KO, STATUTE_WORD, expand


def test_expand_appends_statute_terms_once():
    q = "집주인이 월세를 올려 달래요"
    assert expand(q) == q + " 임대인 차임"
    assert expand("What does RESPA Section 8 prohibit?").endswith("unearned fees")
    assert expand("해고 예고 기간") == "해고 예고 기간"  # nothing to add


def _corpus(prefix: str) -> str:
    files = sorted((CACHE / "canonical").glob(f"{prefix}*.json"))
    return " ".join(json.loads(p.read_text("utf-8"))["text"] for p in files)


def test_listed_words_are_rare_in_the_statutes():
    ko, en = _corpus("kr-"), _corpus("us-").lower()
    if not ko or not en:
        pytest.skip("parsed corpus cache not present (eval/evalset.py doc_texts)")
    common = [k for k in KO if ko.count(k) >= STATUTE_WORD]
    common += [k for k in EN if len(re.findall(rf"\b{re.escape(k)}", en)) >= STATUTE_WORD]
    assert common == []
