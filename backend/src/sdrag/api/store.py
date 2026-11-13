"""Per-user records: conversations and uploaded documents.

DynamoDB in AWS (one table, partition key = the user, so a query can only ever read
one user's items: user isolation is in the key, not in a filter that could be
forgotten); a dict in memory for local runs and tests. Both implement Store.

Items (pk = "USER#<user id>"):
- sk = "CONV#<id>": title, messages [{role, text, citations, mode, ts}]
- sk = "DOC#<id>": file name, status (queued | processing | done | failed), chunk
  count, timings, error
"""

import json
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
        if new:
            self.table.put_item(Item=key | _ddb({"id": conv_id, "title": message["text"][:60],
                                                 "messages": [message], "ts": int(time.time())}))  # fmt: skip
        else:
            self.table.update_item(
                Key=key,
                UpdateExpression="SET messages = list_append(messages, :m)",
                ExpressionAttributeValues={":m": _ddb([message])},
                ConditionExpression="attribute_exists(pk)",  # someone else's id fails here
            )
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
        return r.get("Item")

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
