"""Yes/no openers: re-ask every stored answer that opens with yes/no (v11-final labor and
real estate, v14 dev, the 20 one-file served answers) with the current code, and keep
the old and the new answer side by side for reading.

Why: 5 of these 47 answers opened with the word their own body contradicts ("Yes,
employers do not owe ..."); the judge passed 2 of them (docs/decisions.md, 2026-11-16).
The answer prompt has a yes/no rule since; this shows whether the openers now agree
with their bodies, read by hand (no judge: it missed them).

    cd backend && AWS_PROFILE=... uv run python ../eval/yesno.py
"""

import csv
import json
import re
from concurrent.futures import ThreadPoolExecutor

from evalset import DATA, load_items

from sdrag.common.config import settings
from sdrag.common.llm import BedrockChat
from sdrag.common.search_client import make_client
from sdrag.retrieval.embed import TitanEmbedder
from sdrag.service import RagService

R = DATA / "eval" / "results" / "answers"
OUT = R / "yesno-check.json"
OPENER = re.compile(r"^\s*(\*\*)?(yes|no|네|아니요|아니오|예|그렇습니다|아닙니다)\b", re.IGNORECASE)
RUNS = ["v11-final/test_sample.jsonl", "v11-final/test_re.jsonl", "v14-dates-digits-dev/test_sample.jsonl"]


def main() -> None:
    old = {}  # qid -> (question, old answer, scope)
    for run in RUNS:
        for line in (R / run).open(encoding="utf-8"):
            r = json.loads(line)
            if OPENER.match(r["answer"]):
                old.setdefault(r["qid"], (r["question"], r["answer"], None))
    sf = DATA / "eval" / "single_file"
    rows = {r["qid"]: r for r in csv.DictReader((sf / "compare.csv").open(encoding="utf-8"))}
    items = {i.qid: i for s in ("test.jsonl", "test_re.jsonl") for i in load_items(DATA / "eval" / s)}
    for q, a in json.loads((sf / "ours20_now.json").read_text("utf-8"))["answers"].items():
        if OPENER.match(a["answer"]):  # asked about one file: scoped, as when it was made
            old[q + "@file"] = (rows[q]["question"], a["answer"], [items[q].gold[0].doc_id])

    client = make_client(settings.opensearch_url, settings.aws_region)
    emb = TitanEmbedder(settings.embed_model, settings.aws_region, settings.embed_dims)
    service = RagService(client, settings.index, emb, BedrockChat(settings.llm_model, settings.aws_region))

    def one(key):
        question, before, scope = old[key]
        after = service.ask("eval", question, scope=scope).answer.text
        print(key, "|", before[:50].replace("\n", " "), "->", after[:50].replace("\n", " "), flush=True)
        return key, {"question": question, "before": before, "after": after}

    with ThreadPoolExecutor(4) as ex:
        out = dict(ex.map(one, sorted(old)))
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), "utf-8")
    print(len(out), "re-asked ->", OUT)


if __name__ == "__main__":
    main()
