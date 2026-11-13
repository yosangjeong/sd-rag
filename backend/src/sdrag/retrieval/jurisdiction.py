"""Which country's law a question is about, so retrieval can leave out the other's.

The public corpus holds Korean and US statutes on the same subjects (dismissal,
wages, leases). A legal question that names no country means the asker's own: a
Korean question means Korean law, an English one US law (the corpus's two
jurisdictions). Without a filter an English question on, say, paid leave still got
Korean articles ranked first, and the answer step had to sort them out
(docs/decisions.md, jurisdiction).

One short LLM call answers KR, US, BOTH or NONE:
- the question names a country, its law or one of its statutes -> that country
- a legal question naming none -> the country of the question's language
- comparing the two, or asking about both -> BOTH (no filter)
- not about law (a question on an uploaded report, a manual) -> NONE (no filter)

Only public statutes are filtered: the user's own uploads are always searched,
whatever their language or country.
"""

import re

from sdrag.retrieval.rerank import is_korean

JURISDICTION_SYSTEM = """You route questions for a search engine whose shared collection holds Korean law and US federal law (labor, employment, workplace safety, real estate, leases, housing). Users also search documents they uploaded, on any topic.
Decide which country's law the question is about:
- KR or US: the question names that country, its government or agencies, its law or one of its statutes (근로기준법, FLSA, OSHA, 주택임대차보호법, the Fair Housing Act, ...).
- If it names none but is a legal question (rights, duties, rules, penalties, procedures, amounts, deadlines set by law, workplace or property matters), answer the country of its language: {own} for this question.
- BOTH: it compares the two countries or asks about both.
- NONE: it is not about law (a question about a specific report, manual, paper, product, or general knowledge).
Answer with one word: KR, US, BOTH or NONE."""

LABELS = {"KR": "kr", "US": "us"}


def jurisdiction(chat, question: str) -> str | None:
    """ "kr" | "us": search only that country's public statutes; None: no filter."""
    own = (
        "KR (the question is in Korean)"
        if is_korean(question)
        else "US (the question is in English)"
    )
    c = chat.complete(JURISDICTION_SYSTEM.format(own=own), question, max_tokens=300)
    text = re.sub(r"<think>.*?</think>", "", c.text, flags=re.DOTALL)
    words = re.findall(r"\b(KR|US|BOTH|NONE)\b", text)  # upper case: not "let us"
    return LABELS.get(words[-1]) if words else None  # a reply we cannot read: no filter
