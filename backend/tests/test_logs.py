import json

from sdrag.common.logs import log, mask, user_hash


def test_mask_hides_personal_data_and_secrets():
    s = mask("hong@example.com 900101-1234567 010-1234-5678 AKIAABCDEFGHIJKLMNOP Bearer abc.def")
    assert s == "<email> <rrn> <phone> <aws-key> Bearer <token>"


def test_mask_keeps_statute_numbers():
    s = "근로기준법 제26조, 29 CFR 825.110, 2026. 10. 8., 30일"
    assert mask(s) == s


def test_log_writes_masked_json(capsys):
    log("request", user=user_hash("u-1"), question="제 번호는 010 1234 5678 이에요", n=3)
    rec = json.loads(capsys.readouterr().out)
    assert rec["event"] == "request" and rec["n"] == 3
    assert rec["question"] == "제 번호는 <phone> 이에요" and len(rec["user"]) == 12


def test_mask_numbers_next_to_hangul_and_other_forms():
    cases = {
        "전화는 010-1234-5678입니다": "전화는 <phone>입니다",
        "연락처010-1234-5678": "연락처<phone>",
        "900101-1234567번": "<rrn>번",
        "+82 10-1234-5678": "<phone>",
        "사무실 02-123-4567로": "사무실 <phone>로",
        "031-123-4567": "<phone>",
        "010.1234.5678": "<phone>",
        "password=hunter2 다음": "password=<secret> 다음",
        "aws_secret_access_key = abcDEF123/xyz": "aws_secret_access_key = <secret>",
        "key sk-abcdefghijklmnopqrstu": "key <api-key>",
        "카드 4111 1111 1111 1111로": "카드 <card>로",
        "4111-1111-1111-1111": "<card>",
    }
    assert {k: mask(k) for k in cases} == cases


def test_mask_keeps_statute_and_document_numbers():
    for s in [
        "2026-20646",
        "제12조의3제2항",
        "29 U.S.C. 2614(c)(3)",
        "O10-O16, O20-O48",
        "1억6천500만원",
        "2025. 2. 21.",
        "| 0 0 0 0 0 0 0 0 0 0 0 0 0 0 |",
        "별지 제26호서식",
        "I00-I02",
        "법률 제20520호",
    ]:
        assert mask(s) == s
