"""worker/main.handle: what happens to the message and the record after a job."""

from types import SimpleNamespace
from unittest import mock

from sdrag.api.store import MemoryStore
from sdrag.worker import main as w


class Sqs:
    def __init__(self) -> None:
        self.deleted, self.later = [], []

    def delete_message(self, QueueUrl, ReceiptHandle):
        self.deleted.append(ReceiptHandle)

    def change_message_visibility(self, QueueUrl, ReceiptHandle, VisibilityTimeout):
        self.later.append(VisibilityTimeout)


def _run(receives: int, result: dict | None):
    store = MemoryStore()
    store.put_document("u1", {"id": "d1", "status": "processing", "stage": "parsing"})
    deps = SimpleNamespace(store=store, client=mock.Mock(), index="i")
    sqs, s3 = Sqs(), mock.Mock()
    m = {"Body": '{"user": "u1", "doc_id": "d1", "filename": "a.pdf", "key": "k"}',
         "ReceiptHandle": "r", "Attributes": {"ApproximateReceiveCount": str(receives)}}  # fmt: skip
    with mock.patch.object(w, "process", return_value=result) as process, \
         mock.patch.object(w, "protect"):  # fmt: skip
        w.handle(m, sqs, s3, deps)
    doc = next(d for d in store.documents("u1") if d["id"] == "d1")
    doc["removed"] = [c.kwargs["body"]["query"] for c in deps.client.delete_by_query.call_args_list]
    return doc, sqs, process


def test_done_deletes_the_message():
    doc, sqs, _ = _run(1, {"status": "done"})
    assert sqs.deleted == ["r"] and doc["removed"] == []


def test_a_passing_failure_is_tried_again_in_a_minute():
    _, sqs, _ = _run(1, {"status": "retrying", "error": "x"})
    assert sqs.deleted == [] and sqs.later == [60]


def test_the_last_try_marks_failed_and_deletes():
    doc, sqs, _ = _run(w.MAX_TRIES, {"status": "retrying", "error": "바쁨"})
    assert doc["status"] == "failed" and doc["error"].endswith("(재시도 끝)")
    assert sqs.deleted == ["r"]
    # what a busy index took before it refused is removed, and no stage is left
    assert doc["removed"] == [{"term": {"doc_id": "u-d1"}}] and doc["stage"] == ""


def test_a_delivery_after_every_try_died_marks_failed_without_running():
    doc, sqs, process = _run(w.MAX_TRIES + 1, None)
    process.assert_not_called()
    assert doc["status"] == "failed" and "멈췄습니다" in doc["error"]
    assert sqs.deleted == ["r"] and doc["removed"] == [{"term": {"doc_id": "u-d1"}}]


def test_a_final_failure_writes_the_ingest_line_like_every_outcome():
    for receives, result in (
        (w.MAX_TRIES, {"status": "retrying", "error": "바쁨"}),
        (w.MAX_TRIES + 1, None),
    ):
        with mock.patch.object(w, "log") as log:
            _run(receives, result)
        ingest = [c.kwargs for c in log.call_args_list if c.args == ("ingest",)]
        assert len(ingest) == 1 and ingest[0]["status"] == "failed" and ingest[0]["doc_id"] == "d1"
