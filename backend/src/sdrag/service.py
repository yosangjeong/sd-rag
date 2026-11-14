"""The RAG pipeline the API serves: retrieve, then answer with citations.

Two modes, compared in the evaluation (eval/run_retrieval.py):

- ``basic``: hybrid search (BM25 + dense, RRF) for the question (top 20) and for its
  translation into the other corpus language (up to 10 more), all reranked by the LLM.
  Chosen on the dev set: hit@10 0.95, MRR 0.88 against 0.76 / 0.51 for hybrid alone
  (docs/decisions.md). Fusing the two lists instead let the translation's results push
  out the question's own, which cost same-language questions.
- ``agent``: the tool-use agent (agent/search.py) decides the searches, then the same
  reranker orders what it found.

Before either, a legal question is labelled with its country (retrieval/jurisdiction.py)
and the other country's public statutes are left out of every search. Both answer
from the top ANSWER_SOURCES chunks (agent/answer.py). Every search is limited to the
user's own documents and the public corpus.
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from sdrag.agent.answer import Answer, answer
from sdrag.agent.search import SearchAgent
from sdrag.common.logs import log
from sdrag.retrieval.index import PUBLIC, list_documents
from sdrag.retrieval.jurisdiction import jurisdiction
from sdrag.retrieval.rerank import LlmReranker, LlmTranslator, condense
from sdrag.retrieval.search import COUNTRIES, Searcher

ANSWER_SOURCES = 6
RERANK_DEPTH = 20
TRANSLATION_EXTRA = 10


def is_other_country(doc: dict, country: str) -> bool:
    """A public statute of another country than `country` (what Searcher leaves out)."""
    prefix = doc["id"].split("-", 1)[0]
    return doc["owner"] == PUBLIC and prefix in COUNTRIES and prefix != country


class RequestChat:
    """The shared chat client with token counters of its own, so concurrent requests
    each log their own usage."""

    def __init__(self, chat) -> None:
        self.inner, self.name = chat, chat.name
        self.model_id, self.client = chat.model_id, chat.client
        self.input_tokens = self.output_tokens = 0
        self.lock = threading.Lock()  # two calls of one request may run at once

    def complete(self, system, user, max_tokens=1024, temperature=0.0):
        c = self.inner.complete(system, user, max_tokens, temperature)
        with self.lock:
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
    question: str = ""  # what was searched: the follow-up made standalone


class RagService:
    def __init__(self, client, index: str, embedder, chat) -> None:
        self.client, self.index, self.embedder, self.chat = client, index, embedder, chat

    def ask(self, user_id: str, question: str, mode: str = "basic", request_id: str = "",
            history: list[dict] | None = None, scope: list[str] | None = None) -> Reply:  # fmt: skip
        """history: the conversation so far (follow-ups are made standalone first);
        scope: document ids to search in (none: everything the user can see)."""
        t0 = time.perf_counter()
        chat = RequestChat(self.chat)
        standalone = condense(chat, history or [], question)
        if standalone != question:
            log("rewrite", request_id=request_id, question=question, standalone=standalone)
        question = standalone
        # a legal question naming no country means its language's (jurisdiction.py);
        # a search limited to chosen documents needs no guess. The translation does
        # not depend on it, nor does the question in statute terms: the calls run at once.
        translator = LlmTranslator(chat)
        with ThreadPoolExecutor(3) as pool:
            country_f = pool.submit(jurisdiction, chat, question) if not scope else None
            basic = mode != "agent"
            translation_f = pool.submit(translator.to_other_language, question) if basic else None
            terms_f = pool.submit(translator.to_statute_terms, question) if basic else None
            country = country_f.result() if country_f else None
            translation = translation_f.result()[0] if translation_f else None
            statute_terms = terms_f.result() if terms_f else None
        s = Searcher(self.client, self.index, self.embedder, translator,
                     owners=[user_id, PUBLIC], scope=scope or None, country=country)  # fmt: skip
        steps: list[dict] = []
        if mode == "agent":
            docs = list_documents(self.client, self.index, [user_id, PUBLIC])
            if scope:
                docs = [d for d in docs if d["id"] in scope]
            if country:  # the agent's document list matches what it can search
                docs = [d for d in docs if not is_other_country(d, country)]
            res = SearchAgent(chat.client, chat.model_id, s, docs).run(question)
            chat.input_tokens += res.input_tokens  # the agent calls Converse directly
            chat.output_tokens += res.output_tokens
            hits, steps = res.hits[:RERANK_DEPTH], res.steps
            for st in steps:
                log("tool_call", request_id=request_id, tool=st["tool"], input=st["input"])
        else:
            # the wider pool (search.Searcher.wide): served retrieval since 2026-11-13
            hits = s.wide(question, size=RERANK_DEPTH, extra=TRANSLATION_EXTRA,
                          translation=translation, statute_terms=statute_terms)  # fmt: skip
        hits = LlmReranker(chat).rerank(question, hits, s.last_queries or None)
        log("retrieval", request_id=request_id, mode=mode, country=country,
            results=[{"chunk_id": h.chunk_id, "doc_id": h.source.get("doc_id")} for h in hits[:10]])  # fmt: skip
        ans = answer(chat, question, hits[:ANSWER_SOURCES])
        ms = 1000 * (time.perf_counter() - t0)
        log("answer", request_id=request_id, mode=mode, latency_ms=round(ms),
            llm_input_tokens=chat.input_tokens, llm_output_tokens=chat.output_tokens,
            cited=[c.chunk_id for c in ans.citations], rewritten_for=ans.rewritten_for,
            unchecked_figures=ans.unchecked_figures)  # fmt: skip
        return Reply(ans, mode, ms, chat.input_tokens, chat.output_tokens, steps,
                     [h.chunk_id for h in hits], standalone)  # fmt: skip
