"""Flag the evaluation items whose answer depends on the date: their gold lies in an
amended article that was not yet in force when the answers were graded.

law.go.kr's statutes carry amendments not yet in force next to the version in force
(ingest/parse.py mark_versions). A question written from the amended text has a
reference answer that is only right from its effective date on; before it, the right
answer is the version in force. Such items are added to data/eval/item_flags.json
(part "date"), so answer results can be given without them. Retrieval scoring is
unaffected (the gold span is where it was).

    cd backend && uv run python ../eval/version_flags.py [--on 2026-11-13]
"""

import argparse
import datetime as dt
import json

from evalset import DATA, load_items
from opensearchpy import OpenSearch

from sdrag.common import versions
from sdrag.common.config import settings

SETS = ("test", "dev", "real", "test_re", "dev_re", "real_re")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--on", default="2026-11-13", help="the date the answers were graded")
    on = dt.date.fromisoformat(ap.parse_args().on)
    client = OpenSearch(hosts=[settings.opensearch_url])

    def heading(doc_id: str, pos: int) -> str:
        q = {"bool": {"filter": [{"term": {"doc_id": doc_id}}, {"range": {"start": {"lte": pos}}},
                                 {"range": {"end": {"gt": pos}}}]}}  # fmt: skip
        hits = client.search(index="chunks-structure", body={"size": 1, "_source": ["heading"],
                             "query": q})["hits"]["hits"]  # fmt: skip
        return (hits[0]["_source"].get("heading") or "") if hits else ""

    path = DATA / "eval" / "item_flags.json"
    flags = json.loads(path.read_text("utf-8"))
    added = 0
    for name in SETS:
        for it in load_items(DATA / "eval" / f"{name}.jsonl"):
            spans = [*it.gold, *it.also]
            future = []
            for g in spans:
                _, kind, day = versions.parse(heading(g.doc_id, g.start))
                future.append(day if kind == "amended" and day > on else None)
            # every gold span is in a version not yet in force on the grading date
            if spans and all(future) and it.qid not in flags["flags"]:
                flags["flags"][it.qid] = {"part": "date", "reason": (
                    f"the gold is an amended article in force from {min(future)}; on {on} the "
                    "version before it applies, so the reference answer is not yet right")}  # fmt: skip
                added += 1
    path.write_text(json.dumps(flags, ensure_ascii=False, indent=1) + "\n", "utf-8")
    print(f"{added} date-dependent items flagged (graded on {on})")


if __name__ == "__main__":
    main()
