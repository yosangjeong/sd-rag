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

    def ask(self, user, question, mode="basic", request_id="", history=None, scope=None,
            on_event=None):  # fmt: skip
        self.calls.append((user, question, mode))
        self.history, self.scope = history, scope
        if on_event:
            on_event({"type": "stage", "stage": "writing"})
            for piece in ("30일 ", "전 [1]"):
                on_event({"type": "delta", "text": piece})
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

    def wake(self, files=1):
        self.woken = files


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
    assert d.queue.sent == [("alice", "a.pdf")] and d.queue.woken == 1
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


def test_dynamo_store_reads_every_page_and_lists_without_messages():
    from sdrag.api.store import DynamoStore

    class Table:
        def __init__(self):
            self.calls = []

        def query(self, **kw):
            self.calls.append(kw)
            page = [{"id": "c1", "title": "a", "ts": 1}] if "ExclusiveStartKey" not in kw else [
                {"id": "c2", "title": "b", "ts": 2}]  # fmt: skip
            return {"Items": page} | (
                {} if "ExclusiveStartKey" in kw else {"LastEvaluatedKey": {"k": 1}}
            )

    store = DynamoStore.__new__(DynamoStore)
    store.table = Table()
    assert [c["id"] for c in store.conversations("u")] == ["c1", "c2"]
    first = store.table.calls[0]
    assert set(first["ExpressionAttributeNames"].values()) == {"id", "title", "ts"}  # no messages


def test_a_token_with_an_unknown_key_id_is_401_not_500(monkeypatch):
    import jwt
    import pytest
    from fastapi import HTTPException

    from sdrag.api import auth

    monkeypatch.setattr(auth.settings, "auth_mode", "cognito")

    def unknown_kid(token):
        raise jwt.PyJWKClientError('Unable to find a signing key that matches: "x"')

    monkeypatch.setattr(auth, "claims_of", unknown_kid)
    with pytest.raises(HTTPException) as e:
        auth._claims("Bearer abc.def.ghi", None, None)
    assert e.value.status_code == 401


def test_dev_auth_is_refused_inside_an_ecs_task(monkeypatch):
    import pytest

    from sdrag.common.config import Settings

    monkeypatch.setenv("ECS_CONTAINER_METADATA_URI_V4", "http://169.254.170.2/v4/x")
    with pytest.raises(ValueError):
        Settings(auth_mode="dev")


def test_upload_refuses_a_renamed_file_and_one_over_the_limit(api, monkeypatch):
    c, _ = api
    monkeypatch.setattr(main, "MAX_FILE_MB", 1)
    files = [("files", ("old.hwpx", b"\xd0\xcf\x11\xe0 binary hwp", "application/octet-stream")),
             ("files", ("fake.pdf", b"hello", "application/pdf")),
             ("files", ("big.pdf", b"%PDF-1.4" + b"0" * (2**20 + 10), "application/pdf")),
             ("files", ("ok.docx", b"PK\x03\x04 rest", "application/octet-stream"))]  # fmt: skip
    r = c.post("/api/documents", files=files, headers=as_user("alice")).json()
    assert [a["file"] for a in r["accepted"]] == ["ok.docx"]
    reasons = {x["file"]: x["reason"] for x in r["rejected"]}
    assert (
        "HWPX" in reasons["old.hwpx"]
        and "PDF" in reasons["fake.pdf"]
        and "MB" in reasons["big.pdf"]
    )


def test_a_file_the_queue_refuses_is_marked_failed_and_may_be_sent_again(api, monkeypatch):
    c, d = api
    pdf = ("files", ("a.pdf", b"%PDF-1.4 x", "application/pdf"))

    def refuse(*a):
        raise RuntimeError("SQS unavailable")

    monkeypatch.setattr(d.queue, "send", refuse)
    r = c.post("/api/documents", files=[pdf], headers=as_user("alice")).json()
    assert r["accepted"] == [] and "queued" in r["rejected"][0]["reason"]
    [doc] = d.store.documents("alice")
    assert doc["status"] == "failed" and doc["error"]  # not left "queued" forever
    monkeypatch.undo()
    monkeypatch.setattr(main, "deps", lambda: d)
    assert c.post("/api/documents", files=[pdf], headers=as_user("alice")).json()["accepted"]


def test_the_same_file_twice_is_indexed_once(api):
    c, d = api
    pdf = ("files", ("a.pdf", b"%PDF-1.4 same", "application/pdf"))
    r = c.post("/api/documents", files=[pdf, ("files", ("copy.pdf", b"%PDF-1.4 same", "application/pdf"))],
               headers=as_user("alice")).json()  # fmt: skip
    assert [a["file"] for a in r["accepted"]] == ["a.pdf"]
    assert "already uploaded (as a.pdf)" in r["rejected"][0]["reason"]
    r = c.post("/api/documents", files=[pdf], headers=as_user("alice")).json()  # a later request
    assert r["accepted"] == [] and "already uploaded" in r["rejected"][0]["reason"]
    assert c.post("/api/documents", files=[pdf], headers=as_user("bob")).json()[
        "accepted"
    ]  # per user
    for doc in d.store.documents("alice"):  # a failed upload may be sent again
        d.store.update_document("alice", doc["id"], status="failed")
    assert c.post("/api/documents", files=[pdf], headers=as_user("alice")).json()["accepted"]


def test_dynamo_store_keeps_one_item_per_message_in_order():
    from botocore.exceptions import ClientError

    from sdrag.api.store import DynamoStore

    class Table:  # just enough of a DynamoDB table: keys, a condition, begins_with
        def __init__(self):
            self.items = {}

        def put_item(self, Item):
            self.items[(Item["pk"], Item["sk"])] = dict(Item)

        def get_item(self, Key):
            item = self.items.get((Key["pk"], Key["sk"]))
            return {"Item": dict(item)} if item else {}

        def update_item(self, Key, ConditionExpression=None, ExpressionAttributeValues=None, **kw):
            k = (Key["pk"], Key["sk"])
            if k not in self.items:
                raise ClientError(
                    {"Error": {"Code": "ConditionalCheckFailedException"}}, "UpdateItem"
                )
            self.items[k]["updated"] = ExpressionAttributeValues[":t"]

        def query(self, KeyConditionExpression, **kw):
            pk, prefix = (c._values[1] for c in KeyConditionExpression._values)
            rows = sorted(
                (k[1], v) for k, v in self.items.items() if k[0] == pk and k[1].startswith(prefix)
            )
            return {"Items": [v for _, v in rows]}

    store = DynamoStore.__new__(DynamoStore)
    store.table = Table()
    conv = store.add_message("u", None, {"role": "user", "text": "첫 질문"})
    for i in range(3):
        store.add_message("u", conv, {"role": "assistant", "text": f"답 {i}"})
    c = store.conversation("u", conv)
    assert [m["text"] for m in c["messages"]] == ["첫 질문", "답 0", "답 1", "답 2"]
    assert all("pk" not in m for m in c["messages"])
    assert [x["id"] for x in store.conversations("u")] == [conv]  # messages are not conversations
    assert store.conversation("v", conv) is None  # another user's id
    import pytest

    with pytest.raises(ClientError):
        store.add_message("v", conv, {"role": "user", "text": "x"})


def test_chat_stream_sends_stages_deltas_then_the_stored_answer(api):
    import json

    c, _ = api
    r = c.post("/api/chat/stream", json={"message": "해고 예고는?"}, headers=as_user("alice"))
    events = [json.loads(x) for x in r.text.splitlines() if x]
    kinds = [e["type"] for e in events]
    assert kinds[0] == "stage" and kinds[-1] == "done" and kinds.count("delta") == 2
    done = events[-1]
    assert done["answer"] == "30일 전 [1]" and done["citations"][0]["chunk_id"] == "kr-a-law#3"
    conv = c.get(f"/api/conversations/{done['conversation_id']}", headers=as_user("alice")).json()
    assert [m["role"] for m in conv["messages"]] == ["user", "assistant"]
    assert c.post("/api/chat/stream", json={"message": "x", "conversation_id": "nope"},
                  headers=as_user("alice")).status_code == 404  # fmt: skip


def test_upload_shortens_a_long_name_and_keeps_a_daily_limit(api, monkeypatch, tmp_path):
    c, _ = api
    monkeypatch.setattr(main.settings, "upload_dir", str(tmp_path))
    monkeypatch.setattr(main, "MAX_DAY_FILES", 2)
    long = "근로계약서" * 40 + ".pdf"  # 600 bytes: "File name too long" failed the batch
    files = [("files", (long, b"%PDF-1.4 a", "application/pdf")),
             ("files", ("b.pdf", b"%PDF-1.4 b", "application/pdf")),
             ("files", ("c.pdf", b"%PDF-1.4 c", "application/pdf"))]  # fmt: skip
    r = c.post("/api/documents", files=files, headers=as_user("alice")).json()
    assert len(r["accepted"]) == 2
    assert (
        r["accepted"][0]["file"].endswith(".pdf") and len(r["accepted"][0]["file"].encode()) <= 200
    )
    assert r["rejected"] == [{"file": "c.pdf", "reason": "daily limit of 2 files"}]
