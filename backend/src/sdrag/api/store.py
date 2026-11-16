"""Per-user records: conversations and uploaded documents.

DynamoDB in AWS (one table, partition key = the user, so a query can only ever read
one user's items: user isolation is in the key, not in a filter that could be
forgotten); a dict in memory for local runs and tests. Both implement Store.

Items (pk = "USER#<user id>"):
- sk = "CONV#<id>": title, ts (started), updated
- sk = "MSG#<conversation id>#<ms time>#<rand>": one message {role, text, citations,
  mode, ts}. One item per message, so a long conversation never meets DynamoDB's
  400 KB item limit (one growing list did); a query by prefix reads them in order.
- sk = "DOC#<id>": file name, status (queued | processing | done | failed), chunk
  count, timings, error
"""

import json
import threading
import time
import uuid
from decimal import Decimal
from typing import Protocol

import boto3


class Store(Protocol):
    def add_message(self, user: str, conv_id: str | None, message: dict) -> str: ...
    def conversations(self, user: str) -> list[dict]: ...
    def conversation(self, user: str, conv_id: str) -> dict | None: ...
    def put_document(self, user: str, doc: dict) -> None: ...
    def update_document(self, user: str, doc_id: str, **fields) -> None: ...
    def documents(self, user: str) -> list[dict]: ...


def new_id() -> str:
    return uuid.uuid4().hex[:16]


_last = [0]
_lock = threading.Lock()


def _order() -> int:
    """Nanoseconds since the epoch, strictly increasing within the process: messages
    sort in the order they were written even when two fall in the same tick."""
    with _lock:
        _last[0] = max(time.time_ns(), _last[0] + 1)
        return _last[0]


class MemoryStore:
    def __init__(self) -> None:
        self.items: dict[tuple[str, str], dict] = {}

    def add_message(self, user, conv_id, message):
        conv_id = conv_id or new_id()
        key = (user, f"CONV#{conv_id}")
        item = self.items.setdefault(
            key, {"id": conv_id, "title": message["text"][:60], "messages": [], "ts": time.time()}
        )
        item["messages"].append(message)
        return conv_id

    def conversations(self, user):
        return [{"id": v["id"], "title": v["title"], "ts": v["ts"]}
                for (u, k), v in self.items.items() if u == user and k.startswith("CONV#")]  # fmt: skip

    def conversation(self, user, conv_id):
        return self.items.get((user, f"CONV#{conv_id}"))

    def put_document(self, user, doc):
        self.items[(user, f"DOC#{doc['id']}")] = dict(doc)

    def update_document(self, user, doc_id, **fields):
        self.items[(user, f"DOC#{doc_id}")].update(fields)

    def documents(self, user):
        return [v for (u, k), v in self.items.items() if u == user and k.startswith("DOC#")]


def _ddb(value):
    """DynamoDB takes no floats: numbers go in as Decimal (a JSON round trip)."""
    return json.loads(json.dumps(value, default=str), parse_float=Decimal)


class DynamoStore:
    def __init__(self, table: str, region: str) -> None:
        self.table = boto3.resource("dynamodb", region_name=region).Table(table)

    @staticmethod
    def _pk(user: str) -> str:
        return f"USER#{user}"

    def add_message(self, user, conv_id, message):
        new = conv_id is None
        conv_id = conv_id or new_id()
        key = {"pk": self._pk(user), "sk": f"CONV#{conv_id}"}
        now = int(time.time())
        if new:
            self.table.put_item(Item=key | {"id": conv_id, "title": message["text"][:60],
                                            "ts": now, "updated": now})  # fmt: skip
        else:
            self.table.update_item(
                Key=key,
                UpdateExpression="SET updated = :t",
                ExpressionAttributeValues={":t": now},
                ConditionExpression="attribute_exists(pk)",  # someone else's id fails here
            )
        sk = f"MSG#{conv_id}#{_order():020d}#{new_id()[:4]}"
        self.table.put_item(Item={"pk": self._pk(user), "sk": sk} | _ddb(message))
        return conv_id

    def _query(self, user: str, prefix: str, fields: tuple[str, ...] = ()) -> list[dict]:
        """Every item of the user under `prefix`, page by page (a query returns at most 1 MB);
        `fields`: only these attributes (the conversation list needs no messages)."""
        from boto3.dynamodb.conditions import Key

        args = {
            "KeyConditionExpression": Key("pk").eq(self._pk(user)) & Key("sk").begins_with(prefix)
        }
        if fields:  # attribute names through placeholders: some are DynamoDB reserved words
            args["ProjectionExpression"] = ", ".join(f"#f{i}" for i in range(len(fields)))
            args["ExpressionAttributeNames"] = {f"#f{i}": f for i, f in enumerate(fields)}
        items, start = [], {}
        while True:
            r = self.table.query(**args, **start)
            items += r["Items"]
            if "LastEvaluatedKey" not in r:
                return items
            start = {"ExclusiveStartKey": r["LastEvaluatedKey"]}

    def conversations(self, user):
        return [{"id": i["id"], "title": i["title"], "ts": i["ts"]}
                for i in self._query(user, "CONV#", ("id", "title", "ts"))]  # fmt: skip

    def conversation(self, user, conv_id):
        r = self.table.get_item(Key={"pk": self._pk(user), "sk": f"CONV#{conv_id}"})
        item = r.get("Item")
        if not item:
            return None
        msgs = [{k: v for k, v in m.items() if k not in ("pk", "sk")}
                for m in self._query(user, f"MSG#{conv_id}#")]  # fmt: skip
        # items written before 2026-11-16 kept their messages in the conversation item
        return item | {"messages": list(item.get("messages", [])) + msgs}

    def put_document(self, user, doc):
        self.table.put_item(Item={"pk": self._pk(user), "sk": f"DOC#{doc['id']}"} | _ddb(doc))

    def update_document(self, user, doc_id, **fields):
        names = {f"#{k}": k for k in fields}
        values = {f":{k}": v for k, v in _ddb(fields).items()}
        self.table.update_item(
            Key={"pk": self._pk(user), "sk": f"DOC#{doc_id}"},
            UpdateExpression="SET " + ", ".join(f"#{k} = :{k}" for k in fields),
            ExpressionAttributeNames=names,
            ExpressionAttributeValues=values,
        )

    def documents(self, user):
        return self._query(user, "DOC#")
