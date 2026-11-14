"""Re-grade a stored answer run with judge v3 (eval/judges.py): the cited sources and
the run's date go to the judge too. Writes `correct_v3` into each row of
results/answers/<version>/{test_sample,test_re}.jsonl and prints v2 vs v3.

    cd backend && AWS_PROFILE=<profile> uv run python ../eval/rejudge_v3.py v8-figure-check 2026-11-13
"""

import json
import re
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

from evalset import DATA, LLM_CACHE, load_items
from judges import correct_prompt, correct_user_v3
from opensearchpy import OpenSearch

from sdrag.common.config import settings
from sdrag.common.llm import BedrockChat, CachedChat, parse_json

RESULTS = DATA / "eval" / "results" / "answers"
SETS = {"test_sample": ("test", "labor"), "test_re": ("test_re", "real-estate")}


def main() -> None:
    version, today = sys.argv[1], sys.argv[2]
    client = OpenSearch(hosts=[settings.opensearch_url], timeout=60)
    judge = CachedChat(BedrockChat("deepseek.v3.2", settings.aws_region), LLM_CACHE)

    def text(cid: str) -> str:
        body = {"size": 1, "_source": ["text"], "query": {"term": {"chunk_id": cid}}}
        h = client.search(index="chunks-structure", body=body)["hits"]["hits"]
        return h[0]["_source"]["text"] if h else ""

    for name, (set_name, field) in SETS.items():
        path = RESULTS / version / f"{name}.jsonl"
        rows = [json.loads(x) for x in path.read_text("utf-8").splitlines() if x]
        items = {i.qid: i for i in load_items(DATA / "eval" / f"{set_name}.jsonl")}
        system = correct_prompt(field, 3)

        def grade(row: dict, items=items, system=system) -> dict:
            it = items[row["qid"]]
            ref = it.meta.get("check_answer") or it.meta.get("answer", "")
            # runs before citation renumbering (v1-v7) have no cited_n; their answer text
            # cites by position among the sources given, and "cited" lists the cited
            # sources in the order of those numbers
            nums = row.get("cited_n") or sorted(
                {int(n) for n in re.findall(r"\[(\d+)\]", row["answer"])}
            )
            if len(nums) != len(row["cited"]):
                return {
                    "grade": "skipped",
                    "why": "citation numbers do not match the cited sources",
                }
            sources = [(n, text(c)) for n, c in zip(nums, row["cited"], strict=True)]
            user = correct_user_v3(
                it.question, ref, it.gold[0].quote, row["answer"], sources, today
            )
            out = parse_json(judge.complete(system, user, max_tokens=400).text) or {}
            return {"grade": out.get("grade", "unparsed"), "why": out.get("why", "")}

        with ThreadPoolExecutor(4) as pool:
            grades = list(pool.map(grade, rows))
        for r, g in zip(rows, grades, strict=True):
            r["correct_v3"] = g
        path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), "utf-8")
        v2 = Counter(r.get("correct_v2", r["correct"])["grade"] for r in rows)
        v3 = Counter(r["correct_v3"]["grade"] for r in rows)
        print(name, len(rows), "v2", dict(v2), "v3", dict(v3))


if __name__ == "__main__":
    main()
