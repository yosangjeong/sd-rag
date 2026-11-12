"""The RAG pipeline the API serves: retrieve, then answer with citations.

Two modes, compared in the evaluation (eval/run_retrieval.py):

- ``basic``: the question and its translation into the other corpus language, each
  searched with hybrid (BM25 + dense, RRF), fused, then the top 20 reranked by the LLM.
  Chosen on the dev set: hit@10 0.93, MRR 0.85 against 0.76 / 0.51 for hybrid alone,
  mostly from cross-lingual questions (docs/decisions.md).
- ``agent``: the tool-use agent (agent/search.py) decides the searches, then the same
  reranker orders what it found.

Both answer from the top ANSWER_SOURCES chunks (agent/answer.py). Every search is
limited to the user's own documents and the public corpus.
"""

import time
from dataclasses import dataclass, field

from sdrag.agent.answer import Answer, answer
from sdrag.agent.search import SearchAgent
from sdrag.common.logs import log
from sdrag.retrieval.index import PUBLIC, list_documents
from sdrag.retrieval.rerank import LlmReranker, LlmTranslator
from sdrag.retrieval.search import Searcher

ANSWER_SOURCES = 6
RERANK_DEPTH = 20


class RequestChat:
    """The shared chat client with token counters of its own, so concurrent requests
    each log their own usage."""

    def __init__(self, chat) -> None:
        self.inner, self.name = chat, chat.name
        self.model_id, self.client = chat.model_id, chat.client
        self.input_tokens = self.output_tokens = 0

    def complete(self, system, user, max_tokens=1024, temperature=0.0):
        c = self.inner.complete(system, user, max_tokens, temperature)
        self.input_tokens += c.input_tokens
        self.output_tokens += c.output_tokens
        return c


@dataclass
class Reply:
    answer: Answer
    mode: str
    latency_ms: float
    input_tokens: int
    output_tokens: int
    steps: list[dict] = field(default_factory=list)  # agent tool calls
    retrieved: list[str] = field(default_factory=list)  # chunk ids, in order


class RagService:
    def __init__(self, client, index: str, embedder, chat) -> None:
        self.client, self.index, self.embedder, self.chat = client, index, embedder, chat

    def ask(self, user_id: str, question: str, mode: str = "basic", request_id: str = "") -> Reply:
        t0 = time.perf_counter()
        chat = RequestChat(self.chat)
        s = Searcher(self.client, self.index, self.embedder, LlmTranslator(chat),
                     owners=[user_id, PUBLIC])  # fmt: skip
        steps: list[dict] = []
        if mode == "agent":
            docs = list_documents(self.client, self.index, [user_id, PUBLIC])
            res = SearchAgent(chat.client, chat.model_id, s, docs).run(question)
            chat.input_tokens += res.input_tokens  # the agent calls Converse directly
            chat.output_tokens += res.output_tokens
            hits, steps = res.hits[:RERANK_DEPTH], res.steps
            for st in steps:
                log("tool_call", request_id=request_id, tool=st["tool"], input=st["input"])
        else:
            hits = s.bilingual(question, size=RERANK_DEPTH)
        hits = LlmReranker(chat).rerank(question, hits)
        log("retrieval", request_id=request_id, mode=mode,
            results=[{"chunk_id": h.chunk_id, "doc_id": h.source.get("doc_id")} for h in hits[:10]])  # fmt: skip
        ans = answer(chat, question, hits[:ANSWER_SOURCES])
        ms = 1000 * (time.perf_counter() - t0)
        log("answer", request_id=request_id, mode=mode, latency_ms=round(ms),
            llm_input_tokens=chat.input_tokens, llm_output_tokens=chat.output_tokens,
            cited=[c.chunk_id for c in ans.citations])  # fmt: skip
        return Reply(ans, mode, ms, chat.input_tokens, chat.output_tokens, steps,
                     [h.chunk_id for h in hits])  # fmt: skip
