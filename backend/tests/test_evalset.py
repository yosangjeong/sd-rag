import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "eval"))

from evalset import Gold, anchor, locate, score

from sdrag.common.llm import parse_json


def chunk(doc, start, end):
    return {"doc_id": doc, "start": start, "end": end}


def test_span_scores_count_each_gold_span_once():
    gold = [Gold("a", 100, 150, ""), Gold("b", 0, 10, "")]
    retrieved = [chunk("c", 0, 50), chunk("a", 90, 120), chunk("a", 120, 200), chunk("b", 5, 8)]
    s = score(retrieved, gold, ks=(1, 3, 5))
    assert s.span_hit == {1: 0.0, 3: 1.0, 5: 1.0}
    assert s.span_recall == {1: 0.0, 3: 0.5, 5: 1.0}  # the second "a" chunk adds nothing
    assert s.span_mrr == 0.5
    assert s.doc_hit[1] == 0.0 and s.doc_hit[3] == 1.0
    # gains at ranks 2 and 4 against an ideal of ranks 1 and 2
    assert round(s.span_ndcg10, 4) == round((1 / 1.585 + 1 / 2.3219) / (1 + 1 / 1.585), 4)


def test_an_also_span_answers_a_single_gold_question():
    gold, also = [Gold("a", 0, 10, "")], [Gold("b", 0, 10, "")]
    s = score([chunk("b", 0, 5), chunk("a", 0, 5)], gold, also, ks=(1,))
    assert s.span_hit[1] == 1.0 and s.span_recall[1] == 1.0 and s.span_ndcg10 == 1.0


def test_a_multi_question_needs_every_gold_span():
    gold, also = [Gold("a", 0, 10, ""), Gold("b", 0, 10, "")], [Gold("c", 0, 10, "")]
    s = score([chunk("c", 0, 5), chunk("a", 0, 5)], gold, also, ks=(2,))
    assert s.span_mrr == 1.0 and s.span_recall[2] == 0.5


def test_touching_ranges_do_not_overlap():
    assert score([chunk("a", 0, 100)], [Gold("a", 100, 120, "")]).span_mrr == 0.0


def test_locate_tolerates_reflowed_whitespace():
    text = "제26조(해고의 예고) 사용자는 근로자를 해고하려면\n적어도 30일 전에 예고를 하여야 한다."
    s, e = locate(text, "근로자를 해고하려면 적어도 30일 전에")
    assert text[s:e] == "근로자를 해고하려면\n적어도 30일 전에"
    assert locate(text, "60일 전에") is None


def test_locate_skips_amendment_notes():
    text = "제출해야 한다.<개정 2010. 7. 12.>\n\n1. 제정하거나 변경된 협의회규정"
    s, e = locate(text, "제출해야 한다. 1. 제정하거나 변경된 협의회규정")
    assert (s, e) == (0, len(text))


def test_anchor_follows_a_moved_quote():
    g = Gold("a", 5, 8, "xyz")
    assert anchor("abcdexyz", g) == g  # still in place
    assert anchor(".......xyz.xyz", g) == Gold("a", 7, 10, "xyz")  # nearest to the old 5
    assert anchor("nothing here", g) is None


def test_parse_json_strips_fences_and_thinking():
    assert parse_json('<think>hmm {"a": 0}</think>Sure:\n```json\n{"a": 1}\n```') == {"a": 1}
    assert parse_json("Here: [1, 2] and more") == [1, 2]
    assert parse_json("no json") is None
