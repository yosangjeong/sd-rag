"""The correctness judge's prompts, shared by answers.py, single_file.py and rejudge.py.

v1 graded every answer version until 2026-11-13. Reading its 11 non-correct grades on
the single-file questions showed five where the answer was right and the judge took
off for extra correct detail (another fine the same article sets, a fuller list) or
for a detail the question did not ask (a start date when asked how often), although
the prompt said extra correct detail is fine; and items whose reference answer
misreads the passage (data/eval/item_flags.json). v2 says what the key fact is, that
more correct detail never lowers a grade, and that the passage, not the reference
answer, decides. It was fixed before the Claude and ChatGPT answers were collected,
and every answer version was re-graded with it (eval/rejudge.py), so all systems and
versions are graded by the same text. Judge model: DeepSeek V3.2 (neither the answer
model's family nor the question writer's).
"""

CORRECT_V1 = """You grade answers to questions about Korean and US labor law documents.
Given the question, the reference answer, the passage it comes from, and a candidate answer, decide:
- "correct": the candidate states the same key fact as the reference (number, period, condition, procedure); extra correct detail is fine.
- "partial": it states part of it, or the right fact with a wrong condition.
- "wrong": it states something else, or contradicts the reference.
- "no_answer": it says it cannot find the answer, or answers nothing.
Judge the content, not the language or style.
Return only JSON: {"grade": "correct" | "partial" | "wrong" | "no_answer", "why": "<one sentence>"}"""

CORRECT_V2 = """You grade answers to questions about Korean and US statutes ({field}).
Given the question, a reference answer, the passage it was written from, and a candidate answer, decide whether the candidate gives the asker the right answer.
First name the key fact: what the question asks for (a number, period, amount, condition, procedure, body or list), as the passage states it. Then:
- "correct": the candidate states the key fact. Further correct detail, other cases or conditions the law also sets, or a fuller list never lower the grade; leaving out a detail the question did not ask for is fine.
- "partial": part of the key fact is missing (an item of a requested list, a condition that changes the answer), or it comes with a wrong condition.
- "wrong": it gives a different key fact, or contradicts the passage.
- "no_answer": it says the documents do not answer, or answers nothing.
The passage is the authority: where the reference answer and the passage disagree, follow the passage. Judge the content, not the language or style. Whether the extra statements are supported by the candidate's sources is checked separately; here only a statement that contradicts the passage counts against it.
Return only JSON: {{"key_fact": "<a few words>", "grade": "correct" | "partial" | "wrong" | "no_answer", "why": "<one sentence>"}}"""


CORRECT_V3 = """You grade answers to questions about Korean and US statutes ({field}).
Given the question, a reference answer, the passage it was written from, today's date, a candidate answer and the sources the candidate cites, decide whether the candidate gives the asker the right answer.
First name the key fact: what the question asks for (a number, period, amount, condition, procedure, body or list), as the passage states it. Then:
- "correct": the candidate states the key fact. Further detail stated in the passage or in the candidate's cited sources (other cases or conditions the law also sets, deadlines, a fuller list, the decree's figures) never lowers the grade; leaving out a detail the question did not ask for is fine.
A question that asks for one item of a list the law sets ("one of the cases ...", "one reason ...", "중 하나") is answered by any item of that list, not only the one the reference names.
- "partial": part of the key fact is missing (an item of a requested list, a condition that changes the answer), it comes with a wrong condition, or a yes/no question is answered with a conclusion the rest of the answer contradicts.
- "wrong": it gives a different key fact, or contradicts the passage or its own sources.
- "no_answer": it says the documents do not answer, or answers nothing.
The passage is the authority: where the reference answer and the passage disagree, follow the passage. A statute can have two versions, one in force today and an amended one in force later (or the reverse); the version in force on today's date is the right answer, and naming the other with its date is correct detail, even when the reference was written from the other version. Judge the content, not the language or style.
Return only JSON: {{"key_fact": "<a few words>", "grade": "correct" | "partial" | "wrong" | "no_answer", "why": "<one sentence>"}}"""


def correct_prompt(field: str = "labor", version: int = 2) -> str:
    """field: "labor" or "real-estate" (the set the item comes from)."""
    if version == 1:
        return (
            CORRECT_V1 if field == "labor" else CORRECT_V1.replace("labor law", "real-estate law")
        )
    text = CORRECT_V3 if version == 3 else CORRECT_V2
    return text.format(field="labor law" if field == "labor" else "real-estate law")


def correct_user(question: str, reference: str, passage: str, candidate: str) -> str:
    return (f"Question: {question}\nReference answer: {reference}\n"
            f"Passage: {passage}\n\nCandidate answer: {candidate}")  # fmt: skip


def correct_user_v3(question: str, reference: str, passage: str, candidate: str,
                    sources: list[tuple[int, str]], today: str) -> str:  # fmt: skip
    """sources: (the number the answer cites it by, its text)."""
    cited = "\n\n".join(f"[{n}] {s[:2000]}" for n, s in sources) or "(none)"
    return (f"Question: {question}\nReference answer: {reference}\nPassage: {passage}\n"
            f"Today: {today}\n\nCandidate answer: {candidate}\n\nCandidate's cited sources:\n{cited}")  # fmt: skip
