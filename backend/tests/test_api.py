from types import SimpleNamespace
from typing import ClassVar

import pytest
from fastapi.testclient import TestClient

from sdrag.agent.answer import Answer, Citation
from sdrag.api import main
from sdrag.api.store import MemoryStore
from sdrag.service import Reply


class FakeService:
    def __init__(self):
        self.calls = []

    def ask(self, user, question, mode="basic", request_id="", history=None, scope=None):
        self.calls.append((user, question, mode))
        self.history, self.scope = history, scope
        cite = Citation(1, "kr-a-law#3", "kr-a-law", "법", "제26조", None, None, 0, 10)
        return Reply(Answer("30일 전 [1]", [cite], [cite]), mode, 12.0, 100, 20)


class FakeOpenSearch:
    """/api/source: returns the chunk only if the query's owner filter allows it."""

    chunks: ClassVar[dict] = {
        "u-x#0": {"chunk_id": "u-x#0", "doc_id": "u-x", "owner": "alice", "text": "비밀"}
    }

    def search(self, index, body):
        f = body["query"]["bool"]["filter"]
        cid, owners = f[0]["term"]["chunk_id"], f[1]["terms"]["owner"]
        c = self.chunks.get(cid)
        hits = [{"_source": c}] if c and c["owner"] in owners else []
        return {"hits": {"hits": hits}}


class FakeQueue:
    def __init__(self):
        self.sent = []

    def send(self, user, doc_id, path, filename):
        self.sent.append((user, filename))

    def wake(self):
        self.woken = True


@pytest.fixture
def api(monkeypatch):
    d = SimpleNamespace(store=MemoryStore(), service=FakeService(), client=FakeOpenSearch(),
                        index="i", queue=FakeQueue())  # fmt: skip
    monkeypatch.setattr(main, "deps", lambda: d)
    monkeypatch.setattr(main, "create_index", lambda *a, **k: None)
    with TestClient(main.app) as c:
        yield c, d


def as_user(name):
    return {"X-Dev-User": name}


def test_chat_answers_with_citations_and_keeps_the_conversation(api):
    c, d = api
    r = c.post("/api/chat", json={"message": "해고 예고?"}, headers=as_user("alice")).json()
    assert r["citations"][0]["heading"] == "제26조" and r["answer"] == "30일 전 [1]"
    conv = c.get(f"/api/conversations/{r['conversation_id']}", headers=as_user("alice")).json()
    assert [m["role"] for m in conv["messages"]] == ["user", "assistant"]
    assert d.service.calls == [("alice", "해고 예고?", "basic")]


def test_users_cannot_see_each_others_conversations(api):
    c, _ = api
    r = c.post("/api/chat", json={"message": "q"}, headers=as_user("alice")).json()
    assert (
        c.get(f"/api/conversations/{r['conversation_id']}", headers=as_user("bob")).status_code
        == 404
    )
    assert c.get("/api/conversations", headers=as_user("bob")).json() == []
    # nor continue it
    body = {"message": "q2", "conversation_id": r["conversation_id"]}
    assert c.post("/api/chat", json=body, headers=as_user("bob")).status_code == 404


def test_users_cannot_open_each_others_sources(api):
    c, _ = api
    assert (
        c.get("/api/source/u-x#0".replace("#", "%23"), headers=as_user("alice")).status_code == 200
    )
    assert c.get("/api/source/u-x%230", headers=as_user("bob")).status_code == 404


def test_upload_accepts_supported_files_and_lists_them_per_user(api):
    c, d = api
    files = [("files", ("a.pdf", b"%PDF-1.4", "application/pdf")),
             ("files", ("b.hwp", b"x", "application/octet-stream"))]  # fmt: skip
    r = c.post("/api/documents", files=files, headers=as_user("alice")).json()
    assert [a["file"] for a in r["accepted"]] == ["a.pdf"]
    assert r["rejected"][0]["file"] == "b.hwp"
    assert d.queue.sent == [("alice", "a.pdf")] and d.queue.woken
    assert len(c.get("/api/documents", headers=as_user("alice")).json()) == 1
    assert c.get("/api/documents", headers=as_user("bob")).json() == []


def test_mode_is_validated(api):
    c, _ = api
    assert c.post("/api/chat", json={"message": "q", "mode": "rm -rf"}).status_code == 422


def test_follow_ups_get_the_conversation_and_scope(api):
    c, d = api
    r = c.post("/api/chat", json={"message": "해고 예고?"}, headers=as_user("alice")).json()
    body = {
        "message": "그럼 5인 미만은?",
        "conversation_id": r["conversation_id"],
        "documents": ["kr-a-law"],
    }
    c.post("/api/chat", json=body, headers=as_user("alice"))
    assert [m["role"] for m in d.service.history] == ["user", "assistant"]
    assert d.service.scope == ["kr-a-law"]


def test_logs_are_for_evaluators_only(api, monkeypatch):
    c, _ = api
    monkeypatch.setattr(main.logs_api, "query", lambda preset, minutes, rid: [{"preset": preset}])
    assert c.get("/api/logs/recent", headers=as_user("alice")).status_code == 403
    ev = {"X-Dev-User": "eva", "X-Dev-Groups": "evaluators"}
    assert c.get("/api/logs/recent", headers=ev).json() == [{"preset": "recent"}]
    assert c.get("/api/me", headers=ev).json()["evaluator"] is True
    assert c.get("/api/me", headers=as_user("alice")).json()["evaluator"] is False


def test_log_presets_reject_unknown_names_and_bad_ids():
    from sdrag.api import logs_api

    with pytest.raises(ValueError):
        logs_api.query("drop table", 60, "")
    with pytest.raises(ValueError):
        logs_api.query("request", 60, "x' or 1=1")
