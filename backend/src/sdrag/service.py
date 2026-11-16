"""The RAG pipeline the API serves: retrieve, then answer with citations.

Two modes, compared in the evaluation (eval/run_retrieval.py):

- ``basic``: Searcher.wide (served since 2026-11-13): hybrid search (BM25 + dense, RRF)
  for the question, its translation into the other corpus language and its
  statute-terms rewrite, with referenced and defining articles (about 50 candidates),
  all reranked by the LLM (docs/decisions.md, "Wider candidate pool"). Fusing the lists
  instead let the translation's results push out the question's own.
- Optional steps (country, translation, statute terms, reranking) that fail are
  skipped and logged as ``degraded``; the request goes on without them.
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
from sdrag.common.prices import cost_usd
from sdrag.retrieval.index import PUBLIC, list_documents
from sdrag.retrieval.jurisdiction import jurisdiction
from sdrag.retrieval.rerank import LlmReranker, LlmTranslator, condense
from sdrag.retrieval.search import COUNTRIES, Searcher

ANSWER_SOURCES = 6
RERANK_DEPTH = 20
TRANSLATION_EXTRA = 10


def _optional(future, step: str, request_id: str):
    """The result of an optional step, or None (logged) if it failed."""
    if future is None:
        return None
    try:
        return future.result()
    except Exception as e:  # noqa: BLE001 - see the caller
        log("degraded", request_id=request_id, step=step, error=f"{type(e).__name__}: {e}"[:300])
        return None


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
    def __init__(self, client, index: str, embedder, chat, answer_chat=None) -> None:
        """answer_chat: a different model for the answer step only (eval/answer_models.py
        compares them); translation, reranking and the agent keep ``chat``."""
        self.client, self.index, self.embedder, self.chat = client, index, embedder, chat
        self.answer_chat = answer_chat

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
            # each of these only widens or narrows the search: if one fails, the request
            # goes on without it (no country filter, no translation, no terms query)
            country = _optional(country_f, "jurisdiction", request_id)
            # "" (not None) for a failed one: Searcher.wide would ask again for None
            t = _optional(translation_f, "translation", request_id)
            translation = (t[0] if t else "") if basic else None
            terms = _optional(terms_f, "statute_terms", request_id)
            statute_terms = (terms or "") if basic else None
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
        try:
            hits = LlmReranker(chat).rerank(question, hits, s.last_queries or None)
        except Exception as e:  # noqa: BLE001 - the first-stage order is the fallback
            log(
                "degraded",
                request_id=request_id,
                step="rerank",
                error=f"{type(e).__name__}: {e}"[:300],
            )
        log("retrieval", request_id=request_id, mode=mode, country=country,
            results=[{"chunk_id": h.chunk_id, "doc_id": h.source.get("doc_id")} for h in hits[:10]])  # fmt: skip
        if self.answer_chat is None:
            ans = answer(chat, question, hits[:ANSWER_SOURCES])
        else:
            ans = answer(self.answer_chat, question, hits[:ANSWER_SOURCES])
            chat.input_tokens += ans.input_tokens
            chat.output_tokens += ans.output_tokens
        ms = 1000 * (time.perf_counter() - t0)
        # the response itself (masked, cut) and an estimated cost, besides the tokens
        cost = cost_usd(self.chat.model_id, chat.input_tokens, chat.output_tokens)
        log("answer", request_id=request_id, mode=mode, latency_ms=round(ms),
            answer=ans.text[:2000], cost_usd_est=cost,
            llm_input_tokens=chat.input_tokens, llm_output_tokens=chat.output_tokens,
            cited=[c.chunk_id for c in ans.citations], rewritten_for=ans.rewritten_for,
            unchecked_figures=ans.unchecked_figures)  # fmt: skip
        return Reply(ans, mode, ms, chat.input_tokens, chat.output_tokens, steps,
                     [h.chunk_id for h in hits], standalone)  # fmt: skip
