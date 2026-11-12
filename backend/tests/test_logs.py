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
