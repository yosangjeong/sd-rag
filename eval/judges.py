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


def correct_prompt(field: str = "labor", version: int = 2) -> str:
    """field: "labor" or "real-estate" (the set the item comes from)."""
    if version == 1:
        return (
            CORRECT_V1 if field == "labor" else CORRECT_V1.replace("labor law", "real-estate law")
        )
    return CORRECT_V2.format(field="labor law" if field == "labor" else "real-estate law")


def correct_user(question: str, reference: str, passage: str, candidate: str) -> str:
    return (f"Question: {question}\nReference answer: {reference}\n"
            f"Passage: {passage}\n\nCandidate answer: {candidate}")  # fmt: skip
