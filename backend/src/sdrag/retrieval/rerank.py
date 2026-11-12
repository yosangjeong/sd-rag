"""Second-stage ranking and query translation, both done by a text LLM on Bedrock.

Reranker: the first stage (hybrid search) returns ~20 candidates; the reranker reads
the question and all of them in one call and returns them in order of relevance.
Bedrock's rerank models (Cohere Rerank, Amazon Rerank) are not offered in
ap-southeast-2, and a cross-encoder of our own would be another service to run, so a
listwise LLM call is used: one request per question, candidates numbered, the model
answers with the numbers in order. Candidates it leaves out keep their first-stage
order after the ones it ranked.

Translation: Korean and English chunks sit in one index and both embedding models
favor the query's language (docs/decisions.md), so a question is also searched in
the other language. The LLM translates it literally, keeping legal terms.
"""

import re

from sdrag.common.llm import parse_json
from sdrag.retrieval.search import Hit

RERANK_SYSTEM = """You rank search results for a legal search engine over Korean and US labor law.
Given a question and numbered passages, order the passages by how well each answers the question: a passage that states the rule, condition, number or procedure asked about comes first; passages only on the same topic come after; unrelated ones last. Passages may be in Korean or English; the question may be in either language.
Return only JSON: {"ranking": [<passage numbers, best first>]}"""

TRANSLATE_SYSTEM = """Translate the user's search query into {target}. Translate literally and keep it a search query of the same kind (a question stays a question, keywords stay keywords). Use the standard legal term of {target_law} where one exists. Return only the translation."""

MAX_PASSAGE_CHARS = 1200  # a long chunk is cut for the reranker only; ~20 x 1,200 chars fits easily


def is_korean(text: str) -> bool:
    hangul = len(re.findall(r"[가-힣]", text))
    latin = len(re.findall(r"[A-Za-z]", text))
    return hangul > latin / 3


class LlmReranker:
    def __init__(self, chat, max_tokens: int = 400) -> None:
        self.chat, self.max_tokens, self.name = chat, max_tokens, f"llm:{chat.name}"

    def rerank(self, question: str, hits: list[Hit]) -> list[Hit]:
        if len(hits) < 2:
            return hits
        blocks = []
        for n, h in enumerate(hits, 1):
            s = h.source
            head = f"{s.get('title', '')} > {s.get('heading') or ''}".rstrip(" >")
            blocks.append(f"[{n}] {head}\n{s.get('text', '')[:MAX_PASSAGE_CHARS]}")
        user = f"Question: {question}\n\nPassages:\n\n" + "\n\n".join(blocks)
        out = parse_json(self.chat.complete(RERANK_SYSTEM, user, max_tokens=self.max_tokens).text)
        order = out.get("ranking", []) if isinstance(out, dict) else []
        seen: list[int] = []
        for n in order:
            if isinstance(n, int) and 1 <= n <= len(hits) and n - 1 not in seen:
                seen.append(n - 1)
        rest = [i for i in range(len(hits)) if i not in seen]  # unranked keep their order
        return [hits[i] for i in seen + rest]


class LlmTranslator:
    def __init__(self, chat) -> None:
        self.chat, self.name = chat, f"llm:{chat.name}"

    def to_other_language(self, query: str) -> tuple[str, str]:
        """(translation, its language)."""
        if is_korean(query):
            target, law, lang = "English", "US federal labor law", "en"
        else:
            target, law, lang = "Korean", "Korean labor law (법령 용어)", "ko"
        system = TRANSLATE_SYSTEM.format(target=target, target_law=law)
        c = self.chat.complete(system, query, max_tokens=400)
        text = re.sub(r"<think>.*?</think>", "", c.text, flags=re.DOTALL).strip()
        return text.strip('"'), lang


CONDENSE_SYSTEM = """You turn the user's last message in a conversation about Korean and US labor law into a standalone search question.
Use the earlier turns only to resolve what the last message refers to: omitted subjects, "that", "그 경우", "what about ...", and "the opposite" / "그 반대" (spell out who does what to whom, e.g. the employer notifying the worker instead of the worker notifying the employer).
Drop conversational openers ("그럼", "그러면", "so", "then"). Keep the language of the last message. If it is already a complete question on its own, return it unchanged. Do not answer it.
Return only the question."""

HISTORY_TURNS = 6  # the last three exchanges
HISTORY_CHARS = 600  # per turn: an answer's first lines carry its subject


def condense(chat, history: list[dict], question: str) -> str:
    """The follow-up question made standalone, for retrieval and the answer.

    Retrieval sees one query, so "그럼 5인 미만은?" after a question on dismissal
    notice has to become "5인 미만 사업장도 해고 예고를 해야 하나요?" first. History
    entries are {"role": "user" | "assistant", "text": ...}."""
    if not history:
        return question
    turns = "\n".join(f"{m['role']}: {m['text'][:HISTORY_CHARS]}" for m in history[-HISTORY_TURNS:])
    c = chat.complete(CONDENSE_SYSTEM, f"Conversation:\n{turns}\n\nLast message: {question}",
                      max_tokens=300)  # fmt: skip
    text = re.sub(r"<think>.*?</think>", "", c.text, flags=re.DOTALL).strip().strip('"')
    return text or question
