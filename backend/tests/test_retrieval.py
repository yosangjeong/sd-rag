from sdrag.ingest.corpus import load_corpus
from sdrag.retrieval.embed import CachedEmbedder
from sdrag.retrieval.search import Hit, Searcher, rrf


def hits(*ids):
    return [Hit(i, 0.0, {"chunk_id": i}) for i in ids]


def test_rrf_favors_chunks_high_in_both_lists():
    fused = rrf(hits("a", "b", "c"), hits("c", "a", "d"), size=4)
    assert [h.chunk_id for h in fused] == ["a", "c", "b", "d"]
    assert fused[0].score == 1 / 61 + 1 / 62


def test_rrf_breaks_ties_by_id():
    assert [h.chunk_id for h in rrf(hits("b"), hits("a"))] == ["a", "b"]


def test_cached_embedder_pays_once(tmp_path):
    class Counting:
        name, dims, calls = "fake:2", 2, 0

        def embed(self, texts):
            Counting.calls += len(texts)
            return [[float(len(t)), 1.0] for t in texts]

    e = CachedEmbedder(Counting(), tmp_path)
    assert e.embed(["가", "나다"]) == [[1.0, 1.0], [2.0, 1.0]]
    assert e.embed(["나다", "라"]) == [[2.0, 1.0], [1.0, 1.0]]
    assert Counting.calls == 3  # "나다" came from the cache


class FakeClient:
    def __init__(self):
        self.bodies = []

    def search(self, index, body):
        self.bodies.append(body)
        return {"hits": {"hits": [{"_id": "x#0", "_score": 1.0, "_source": {}}]}}


class FakeEmbedder:
    name, dims = "fake", 2

    def embed(self, texts):
        return [[0.1, 0.2] for _ in texts]


def test_filters_reach_bm25_and_knn():
    client = FakeClient()
    s = Searcher(client, "chunks-structure", FakeEmbedder())
    s.hybrid("해고 예고", size=5, depth=20, langs=["ko"], doc_ids=["kr-labor-standards-law"])
    bm25, dense = client.bodies
    want = [{"terms": {"lang": ["ko"]}}, {"terms": {"doc_id": ["kr-labor-standards-law"]}}]
    assert bm25["query"]["bool"]["filter"] == want
    knn = dense["query"]["knn"]["embedding"]
    assert knn["filter"] == {"bool": {"filter": want}} and knn["k"] == 20


def test_per_language_searches_each_language_once_with_one_embedding():
    client = FakeClient()

    class Once(FakeEmbedder):
        calls = 0

        def embed(self, texts):
            Once.calls += 1
            return super().embed(texts)

    Searcher(client, "i", Once()).per_language("overtime pay")
    langs = [
        b["query"]["bool"]["filter"][0]["terms"]["lang"]
        for b in client.bodies
        if "bool" in b["query"]
    ]
    assert langs == [["ko"], ["en"]] and Once.calls == 1


def test_corpus_resolves_scans_and_skips_eval_truth(tmp_path):
    (tmp_path / "manifest.csv").write_text(
        "id,lang,source,title,url,format,tags,license,acquisition,sha256\n"
        "kr-a-law,ko,s,법,u,scan,legal;scan,KR-CA-7,manual,x\n"
        "kr-a-law-truth,ko,s,법,u,hwpx,legal;eval-truth,KR-CA-7,manual,x\n"
        "us-b,en,s,Act,u,pdf,legal,US-PD-105,auto,x\n",
        encoding="utf-8",
    )
    corpus = tmp_path / "raw" / "corpus"
    corpus.mkdir(parents=True)
    docs = load_corpus(tmp_path)
    assert [(d.id, d.file_type) for d in docs] == [("kr-a-law", "scan"), ("us-b", "pdf")]
    assert docs[0].path == corpus / "kr" / "labor" / "scans" / "kr-a-law.pdf"
    assert docs[1].path == corpus / "us" / "labor" / "us-b.pdf"
    # a fresh clone has no data/raw/: the packed copies in data/corpus/ are used
    corpus.rmdir()
    assert [d.path.name for d in load_corpus(tmp_path)] == ["kr-a-law.pdf", "us-b.pdf"]
    assert load_corpus(tmp_path)[0].path.parent == tmp_path / "corpus"


def test_owners_filter_reaches_every_query():
    client = FakeClient()
    s = Searcher(client, "i", FakeEmbedder(), owners=["user-1", "public"])
    s.hybrid("해고")
    bm25, dense = client.bodies
    want = {"terms": {"owner": ["user-1", "public"]}}
    assert bm25["query"]["bool"]["filter"] == [want]
    assert dense["query"]["knn"]["embedding"]["filter"] == {"bool": {"filter": [want]}}


def test_scope_limits_every_query_to_the_chosen_documents():
    client = FakeClient()
    Searcher(client, "i", FakeEmbedder(), owners=["u", "public"], scope=["kr-a-law"]).hybrid("해고")
    bm25, dense = client.bodies
    want = [{"terms": {"owner": ["u", "public"]}}, {"terms": {"doc_id": ["kr-a-law"]}}]
    assert bm25["query"]["bool"]["filter"] == want
    assert dense["query"]["knn"]["embedding"]["filter"] == {"bool": {"filter": want}}


def test_country_filter_drops_only_the_other_countrys_public_statutes():
    client = FakeClient()
    Searcher(
        client, "chunks-structure", FakeEmbedder(), owners=["u1", "public"], country="kr"
    ).hybrid("notice of dismissal", size=5, depth=20)
    for f in (client.bodies[0]["query"]["bool"]["filter"],
              client.bodies[1]["query"]["knn"]["embedding"]["filter"]["bool"]["filter"]):  # fmt: skip
        dropped = f[1]["bool"]["must_not"][0]["bool"]
        assert dropped["filter"] == [{"term": {"owner": "public"}}]  # uploads are kept
        assert dropped["should"] == [{"prefix": {"doc_id": "us-"}}]


class Reply:
    def __init__(self, text):
        self.text, self.input_tokens, self.output_tokens = text, 0, 0


class OneWord:
    def __init__(self, text):
        self.text, self.systems = text, []

    def complete(self, system, user, max_tokens=1024, temperature=0.0):
        self.systems.append(system)
        return Reply(self.text)


def test_jurisdiction_reads_the_label_and_defaults_to_no_filter():
    from sdrag.retrieval.jurisdiction import jurisdiction

    assert jurisdiction(OneWord("<think>maybe KR?</think>US"), "Is overtime paid?") == "us"
    assert jurisdiction(OneWord("KR"), "Severance pay in Korea?") == "kr"
    for text in ("BOTH", "NONE", "I cannot tell"):
        assert jurisdiction(OneWord(text), "question") is None
    chat = OneWord("KR")
    jurisdiction(chat, "해고 예고는 언제 해야 하나요?")
    assert "KR (the question is in Korean)" in chat.systems[0]


def test_agent_document_list_follows_the_country():
    from sdrag.service import is_other_country

    docs = [{"id": "kr-a-law", "owner": "public"}, {"id": "us-b", "owner": "public"},
            {"id": "u-x", "owner": "u1"}]  # fmt: skip
    assert [d["id"] for d in docs if not is_other_country(d, "kr")] == ["kr-a-law", "u-x"]
