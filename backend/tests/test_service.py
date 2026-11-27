"""The served question path end to end, with fakes for OpenSearch and the LLM:
jurisdiction, translation and the statute-terms query at once, the wide pool, the
reranker, the answer with its citations numbered from 1."""

from sdrag.common.llm import Completion
from sdrag.retrieval.jurisdiction import JURISDICTION_SYSTEM
from sdrag.retrieval.rerank import RERANK_SYSTEM, STATUTE_TERMS_SYSTEM
from sdrag.service import RagService

CHUNKS = {
    "kr-housing-lease-law#18": {"doc_id": "kr-housing-lease-law", "title": "주택임대차보호법",
                                "heading": "제4조(임대차기간 등)", "start": 0, "end": 40,
                                "text": "기간을 정하지 아니하거나 2년 미만으로 정한 임대차는 그 기간을 2년으로 본다."},
    "kr-housing-lease-law#19": {"doc_id": "kr-housing-lease-law", "title": "주택임대차보호법",
                                "heading": "제5조", "start": 41, "end": 60, "text": "다른 조문"},
}  # fmt: skip


class FakeOpenSearch:
    def __init__(self):
        self.bodies = []

    def search(self, index, body):
        self.bodies.append(body)
        hits = [{"_id": cid, "_score": 1.0, "_source": src | {"chunk_id": cid, "owner": "public"}}
                for cid, src in CHUNKS.items()]  # fmt: skip
        return {"hits": {"hits": hits}}


class FakeEmbedder:
    name, dims = "fake", 2

    def embed(self, texts):
        return [[0.1, 0.2] for _ in texts]


class FakeChat:
    """Answers by the system prompt, as the real model would be asked."""

    name, model_id, client = "fake", "fake", None

    def __init__(self):
        self.systems = []

    def complete(self, system, user, max_tokens=1024, temperature=0.0):
        self.systems.append(system)
        if system.startswith(JURISDICTION_SYSTEM[:60]):
            text = "KR"
        elif system == STATUTE_TERMS_SYSTEM:
            text = "주택임대차보호법 임대차기간 2년 미만"
        elif system == RERANK_SYSTEM:
            text = '{"ranking": [2, 1]}'
        elif "Translate" in system:
            text = "lease term one year"
        else:  # the answer: cites the second source only
            text = "2년 미만으로 정한 기간은 2년으로 봅니다 [2]."
        return Completion(text, 10, 5, "end_turn")


def test_basic_question_runs_every_step_and_numbers_citations_from_one():
    client, chat = FakeOpenSearch(), FakeChat()
    reply = RagService(client, "chunks-structure", FakeEmbedder(), chat).ask(
        "user-1", "집주인이 계약기간을 1년으로 하재요"
    )
    asked = set(chat.systems)
    assert {STATUTE_TERMS_SYSTEM, RERANK_SYSTEM} <= asked
    assert any(s.startswith(JURISDICTION_SYSTEM[:60]) for s in asked)
    # the reranker put #18 (the lease-term article) second -> it is the answer's [2],
    # shown as [1] after renumbering
    assert reply.answer.text.endswith("[1].")
    assert [(c.n, c.chunk_id) for c in reply.answer.citations] == [(1, "kr-housing-lease-law#18")]
    assert reply.answer.unchecked_figures == []  # "2년" is in the cited article
    # "KR": the US statutes were left out of the searches
    assert any("us-" in str(b) and "must_not" in str(b) for b in client.bodies)
    # every search was limited to the user's and the public documents
    assert all("owner" in str(b) and "user-1" in str(b) for b in client.bodies)
    # BM25 got the statute's term for the everyday word (집주인 -> 임대인)
    assert any("임대인" in str(b) for b in client.bodies)


def test_a_failing_optional_step_is_skipped_not_fatal():
    class Flaky(FakeChat):
        def complete(self, system, user, max_tokens=1024, temperature=0.0):
            if system == RERANK_SYSTEM or "Translate" in system or system == STATUTE_TERMS_SYSTEM:
                self.systems.append(system)
                raise TimeoutError("model busy")
            return super().complete(system, user, max_tokens, temperature)

    reply = RagService(FakeOpenSearch(), "chunks-structure", FakeEmbedder(), Flaky()).ask(
        "user-1", "집주인이 계약기간을 1년으로 하재요"
    )
    assert reply.answer.text  # answered from the first-stage order


def test_a_failing_condense_or_agent_falls_back_not_fatal(monkeypatch):
    class Flaky(FakeChat):
        def complete(self, system, user, max_tokens=1024, temperature=0.0):
            if user.startswith("Conversation:"):  # condense
                raise TimeoutError("model busy")
            return super().complete(system, user, max_tokens, temperature)

    history = [{"role": "user", "text": "해고 예고는?"}, {"role": "assistant", "text": "30일 전"}]
    svc = RagService(FakeOpenSearch(), "chunks-structure", FakeEmbedder(), Flaky())
    assert svc.ask("user-1", "집주인이 계약기간을 1년으로 하재요", history=history).answer.text
    # agent mode: FakeChat has no Converse client, so the agent fails; the wide pool stands
    monkeypatch.setattr("sdrag.service.list_documents", lambda *a, **k: [])
    reply = svc.ask("user-1", "집주인이 계약기간을 1년으로 하재요", mode="agent")
    assert reply.answer.text and reply.retrieved


def test_an_amended_article_comes_with_its_other_version():
    from sdrag.retrieval.search import Hit
    from sdrag.service import with_versions

    def hit(cid, heading, text="휴가 15일"):
        return Hit(cid, 1.0, {"doc_id": "kr-law", "heading": heading, "text": text})

    new = hit("kr-law#98", "제60조(연차 유급휴가) [2027. 6. 10. 시행]")
    old = hit("kr-law#96", "제60조(연차 유급휴가) [개정 전, 2027. 6. 10. 전까지]")
    other = hit("kr-law#5", "제5조(근로조건의 준수)")
    # the sibling is in the pool but not among the sources: it is put right after
    out = with_versions(None, "i", ["public"], [new, other], [new, other, old])
    assert [h.chunk_id for h in out] == ["kr-law#98", "kr-law#96", "kr-law#5"]
    # both versions present, or no versions at all: unchanged
    assert with_versions(None, "i", ["public"], [new, old], [new, old]) == [new, old]
    assert with_versions(None, "i", ["public"], [other], [other]) == [other]

    class Index:  # the sibling only in the index
        def search(self, index, body):
            assert {"term": {"doc_id": "kr-law"}} in body["query"]["bool"]["filter"]
            return {"hits": {"hits": [{"_id": old.chunk_id, "_source": old.source}]}}

    assert [h.chunk_id for h in with_versions(Index(), "i", ["public"], [new], [new])] == [
        "kr-law#98",
        "kr-law#96",
    ]
