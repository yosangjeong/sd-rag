"""Everyday words -> the words the statutes use, for keyword search.

People ask "집주인이 월세를 올린대요" or "my landlord won't fix the heater"; the statutes
say 임대인, 차임, lessor. BM25 matches words, so a question in everyday words misses
the article that answers it (the embedding search is less affected). `expand` appends
the statute's terms to the query for BM25; the question itself is kept, and the
vector search embeds the question unchanged.

A word is listed only if the statutes themselves rarely use it (under
`STATUTE_WORD` times in that country's corpus, checked by tests/test_terms.py): where
the statutes use the everyday word too (퇴직금, 산재보험, 연차, landlord, tenant),
adding the formal term only blurred the query (measured on the evaluation sets: 산재 ->
"산업재해 업무상 재해" pushed the right article down in three real questions).

The table is general vocabulary of Korean labor and housing law and of the US
statutes in the corpus, written from the statutes' own terms, not from evaluation
questions. One part is different and says so: popular section names ("RESPA Section
8") mapped to their codified sections, added after two real CFPB questions asked by
those names were missed (docs/decisions.md, "Statute terms").
"""

import re

STATUTE_WORD = 10

# everyday or administrative Korean -> statute terms (주택임대차보호법, 근로기준법, ...)
KO = {
    "집주인": "임대인",
    "건물주": "임대인",
    "세입자": "임차인",
    "월세": "차임",
    "전세금": "보증금",
    "재계약": "계약갱신",
    "계약 연장": "계약갱신",
    "이사하": "인도 주민등록 대항력",
    "이사를": "인도 주민등록 대항력",
    "이사 가": "인도 주민등록 대항력",
    "전입신고": "주민등록 대항력",
    "복비": "중개보수",
    "중개수수료": "중개보수",
    "부동산 사무실": "중개사무소 개업공인중개사",
    "부동산중개업소": "중개사무소 개업공인중개사",
    "공인중개사 사무소": "중개사무소",
    "알바": "단시간근로자",
    "아르바이트": "단시간근로자",
    "파트타임": "단시간근로자",
    "계약직": "기간제근로자",
    "비정규직": "기간제근로자 단시간근로자",
    "월급": "임금",
    "봉급": "임금",
    "연봉": "임금",
    "월급이 밀": "임금 체불",
    "임금이 밀": "임금 체불",
    "못 받은 월급": "체불 임금",
    "잘렸": "해고",
    "짤렸": "해고",
    "해고 통보": "해고의 예고",
    "야근": "연장근로 야간근로",
    "잔업": "연장근로",
    "주말 근무": "휴일근로",
    "휴일 근무": "휴일근로",
    "주휴수당": "주휴일 유급휴일",
    "출산휴가": "출산전후휴가",
    "육휴": "육아휴직",
    "4대보험": "고용보험 산업재해보상보험",
    "고용센터": "직업안정기관",
    "회사가 망": "도산 대지급금",
    "외국인 노동자": "외국인근로자",
}

# everyday English -> the terms of the US statutes in the corpus (FLSA, FMLA, OSH Act,
# Fair Housing Act, RESPA / Regulation X)
EN = {
    "fired": "discharge termination",
    "laid off": "layoff termination",
    "unpaid wages": "back wages",
    "back pay": "back wages",
    "whistleblower": "discrimination complaint retaliation",
    "retaliat": "discrimination complaint",
    "mortgage company": "servicer",
    "loan servicer": "servicer",
    "kickback": "referral fee unearned fees",
    "disabled": "handicap disability",
    "wheelchair": "handicap reasonable modification accommodation",
}

# popular section names -> the codified section and its heading
SECTIONS = [
    (r"\bRESPA\s+Section\s+8\b", "12 U.S.C. 2607 prohibition against kickbacks and unearned fees"),
    (r"\bRESPA\s+Section\s+6\b", "12 U.S.C. 2605 servicing of mortgage loans"),
    (r"\bRESPA\s+Section\s+9\b", "12 U.S.C. 2608 title companies"),
    (r"\bRESPA\s+Section\s+10\b", "12 U.S.C. 2609 escrow accounts"),
    (r"\bFLSA\s+Section\s+7\b", "29 U.S.C. 207 maximum hours"),
    (r"\bFLSA\s+Section\s+6\b", "29 U.S.C. 206 minimum wage"),
    (r"\bFLSA\s+Section\s+13\b", "29 U.S.C. 213 exemptions"),
    (r"\bOSH Act\s+Section\s+11\(c\)", "29 U.S.C. 660(c) discharge or discrimination"),
]
_SECTIONS = [(re.compile(p, re.IGNORECASE), t) for p, t in SECTIONS]
_EN = [(re.compile(rf"\b{re.escape(k)}", re.IGNORECASE), v) for k, v in EN.items()]


def expand(query: str) -> str:
    """The query with the statute terms of the everyday words it contains appended."""
    add: list[str] = []
    for word, terms in KO.items():
        if word in query:
            add.append(terms)
    for pattern, terms in _EN:
        if pattern.search(query):
            add.append(terms)
    for pattern, terms in _SECTIONS:
        if pattern.search(query):
            add.append(terms)
    extra = [t for t in dict.fromkeys(" ".join(add).split()) if t.lower() not in query.lower()]
    return f"{query} {' '.join(extra)}" if extra else query
