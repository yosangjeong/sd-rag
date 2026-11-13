"""Real questions for the real-estate statutes: gold by pooling, as for the labor ones.

Question titles (no answers) from public FAQ pages, kept verbatim
(data/eval/real_re_questions_candidates.csv; sources in data/eval/README.md):
easylaw.go.kr 백문백답 (주택임대차, 상가임대차, 공인중개사, 부동산 매매), the CFPB's
RESPA and mortgage servicing FAQs, and the HUD / DOJ joint statement on reasonable
modifications under the Fair Housing Act.

Same procedure and models as the labor real set (finalize_qa.py): the 8-system pool
(top 10, then 25 when nothing answers) is judged with the source's jurisdiction stated;
the best answering passage is the gold, others confirmed by a third family are
``also``. The judge prompts say "real-estate law" where the labor ones say "labor law";
nothing else differs, and the labor sets are not touched. Gold for questions the judge
missed although the corpus answers them: ``real_re_manual_gold.json``. Questions nothing
in the corpus answers go to ``real_re_unanswerable.jsonl``.

    cd backend && AWS_PROFILE=<profile> SDRAG_EMBED_CACHE_DIR=../data/raw/cache/embed \\
        uv run python ../eval/real_re.py
"""

import csv
import json
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

from evalset import CACHE, EMBED_CACHE, Gold, Item, doc_texts, save_items
from finalize_qa import (
    CONFIRM_MODEL,
    CONFIRM_SYSTEM,
    JUDGE_MODEL,
    OUT,
    POOL_DEPTH,
    POOL_SYSTEMS,
    REAL_SYSTEM,
    confirm,
    judge_real,
    pool,
    sha256,
)  # fmt: skip
from opensearchpy import OpenSearch

from sdrag.common.config import settings
from sdrag.common.llm import BedrockChat, CachedChat
from sdrag.retrieval.embed import CachedEmbedder, TitanEmbedder
from sdrag.retrieval.search import Searcher

REAL_RE_SYSTEM = REAL_SYSTEM.replace("labor law", "real-estate law")
CONFIRM_RE_SYSTEM = CONFIRM_SYSTEM.replace("labor law", "real-estate law")
SOURCES = {"elr": "easylaw", "cfpb": "cfpb", "hud": "hud-doj"}
NAMES = ("real_re.jsonl", "real_re_unanswerable.jsonl")


def main() -> None:
    texts = doc_texts()
    client = OpenSearch(hosts=[settings.opensearch_url], timeout=60)
    emb = TitanEmbedder(settings.embed_model, settings.aws_region, settings.embed_dims)
    emb = CachedEmbedder(emb, EMBED_CACHE)
    searchers = [(Searcher(client, idx, emb), mode) for mode, idx in POOL_SYSTEMS]
    judge = CachedChat(BedrockChat(JUDGE_MODEL, settings.aws_region), CACHE / "llm")
    confirmer = CachedChat(BedrockChat(CONFIRM_MODEL, settings.aws_region), CACHE / "llm")
    with (OUT / "real_re_questions_candidates.csv").open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    def one(r):
        args = (judge, texts, r["qid"], r["question"])
        best, also, info = judge_real(*args, pool(searchers, r["question"], POOL_DEPTH["real"]),
                                      system=REAL_RE_SYSTEM)  # fmt: skip
        if best is None:  # a deeper pool before calling it unanswerable
            cands = pool(searchers, r["question"], POOL_DEPTH["real_retry"])
            best, also, info = judge_real(*args, cands, system=REAL_RE_SYSTEM)
            info["retry"] = True
        if best:
            also = [g for g in also
                    if confirm(confirmer, r["question"], best.quote, g, texts, CONFIRM_RE_SYSTEM)]  # fmt: skip
        return r, best, also, info

    with ThreadPoolExecutor(6) as ex:
        out = list(ex.map(one, rows))
    manual_path = OUT / "real_re_manual_gold.json"
    manual = json.loads(manual_path.read_text("utf-8"))["gold"] if manual_path.exists() else {}
    real, unanswerable, log = [], [], []
    for r, best, also, info in out:
        if best is None and r["qid"] in manual:
            best, info["manual"] = Gold(**manual[r["qid"]][0]), True
        meta = {"topic": r["topic"], "url": r["url"], "license": r["license"],
                "judge_note": info.get("note", ""), "manual": info.get("manual", False)}  # fmt: skip
        src = SOURCES[r["qid"].split("-")[0]]
        it = Item(
            r["qid"], r["question"], r["lang"], [best] if best else [], "real", src, meta, also
        )
        (real if best else unanswerable).append(it)
        log.append({"qid": r["qid"], **info})
    save_items(OUT / NAMES[0], real)
    save_items(OUT / NAMES[1], unanswerable)
    (CACHE / "qa" / "real_re_log.jsonl").write_text(
        "".join(json.dumps(x, ensure_ascii=False) + "\n" for x in log), "utf-8"
    )
    sums = {ln.split()[1]: ln for ln in (OUT / "SHA256SUMS").read_text().splitlines() if ln}
    sums |= {n: f"{sha256(OUT / n)}  {n}" for n in NAMES}
    (OUT / "SHA256SUMS").write_text("".join(v + "\n" for v in sums.values()))
    print(f"real_re {len(real)} (+{len(unanswerable)} unanswerable)")
    print("answered by language:", Counter(i.q_lang for i in real),
          "unanswerable:", Counter(i.q_lang for i in unanswerable))  # fmt: skip
    print("gold documents:", Counter(i.gold[0].doc_id for i in real).most_common())


if __name__ == "__main__":
    main()
