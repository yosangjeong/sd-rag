"""Pool the reported systems' results into the gold spans, as TREC does.

The `also` spans (other passages that answer as fully) were pooled once, from the top
5 of 8 first-stage systems (finalize_qa.py). Systems built later (rerank, translation
union, the wide pool, the agent) return passages none of those ranked, and an answer
there counts as a miss even when it answers the question as well as the gold: in the
2026-11-13 served run, the top passage for "the longest a worker under 20 can be paid
the youth wage" (29 U.S.C. 206(g): "during the first 90 consecutive calendar days")
was a miss because the gold is the next sentence.

This judges, with the same prompts and models as finalize_qa.py (DeepSeek V3.2 finds
the candidates that give the same answer, gpt-oss-120b confirms each), the top
`--depth` of every result file of every system in a set's results folder, so all
systems gain from it alike; then re-scores every stored result file (rebuild the
summaries after with run_retrieval.py --set <set>, which prints them). New spans are added to the set's `also`, with meta.also_repooled listing
them, so a later reader sees what came from here.

    cd backend && uv run python ../eval/repool.py --dry-run            # count only
    cd backend && AWS_PROFILE=<profile> uv run python ../eval/repool.py
"""

import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, replace

from evalset import DATA, LLM_CACHE, doc_texts, load_items, overlaps, save_items, score
from finalize_qa import CONFIRM_MODEL, JUDGE_MODEL, confirm, judge_generated, sha256
from opensearchpy import OpenSearch

from sdrag.common.config import settings
from sdrag.common.llm import BedrockChat, CachedChat

SETS = ("dev", "dev_re", "test", "real", "test_re", "real_re")
RESULTS = DATA / "eval" / "results" / "retrieval-70docs"
# the systems README.md and docs/decisions.md compare: served (now and before), the
# hybrid baseline, the agent
REPORTED = ["wide+rerank+jur@chunks-structure", "bilingual_union+rerank+jur@chunks-structure",
            "hybrid@chunks-structure", "agent+rerank@chunks-structure"]  # fmt: skip


def candidates(set_name: str, qid: str, item, depth: int, rows_by_file: dict) -> list[str]:
    """Chunk ids in any system's top `depth` for this question, not already gold/also."""
    seen, out = set(), []
    for rows in rows_by_file.values():
        r = rows.get(qid)
        for h in (r or {}).get("retrieved", [])[:depth]:
            rel = [*item.gold, *item.also]
            if h["chunk_id"] in seen or any(overlaps(h, g) for g in rel):
                continue
            seen.add(h["chunk_id"])
            out.append(h["chunk_id"])
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--depth", type=int, default=5)
    ap.add_argument(
        "--systems",
        nargs="*",
        default=REPORTED,
        help="result-file prefixes to pool (default: the systems the README reports)",
    )
    ap.add_argument("--dry-run", action="store_true", help="count the candidates only")
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    client = OpenSearch(hosts=[settings.opensearch_url], timeout=60)
    texts = doc_texts()
    judge = CachedChat(BedrockChat(JUDGE_MODEL, settings.aws_region), LLM_CACHE)
    confirmer = CachedChat(BedrockChat(CONFIRM_MODEL, settings.aws_region), LLM_CACHE)

    def chunk(cid: str) -> dict:
        body = {"size": 1, "query": {"term": {"chunk_id": cid}},
                "_source": ["doc_id", "title", "heading", "text", "start", "end"]}  # fmt: skip
        hits = client.search(index="chunks-structure", body=body)["hits"]["hits"]
        return hits[0]["_source"] | {"chunk_id": cid} if hits else None  # re-chunked since

    log = {}
    for name in SETS:
        path = DATA / "eval" / f"{name}.jsonl"
        items = load_items(path)
        files = sorted((RESULTS / name).glob("*.jsonl"))  # all are re-scored below
        pooled = [p for p in files if p.name.split("~")[0].removesuffix(".jsonl") in a.systems]
        rows_by_file = {
            p.name: {
                json.loads(x)["qid"]: json.loads(x) for x in p.read_text("utf-8").splitlines() if x
            }
            for p in pooled
        }
        todo = [
            (it, candidates(name, it.qid, it, a.depth, rows_by_file)) for it in items if it.gold
        ]
        n = sum(len(c) for _, c in todo)
        print(
            f"{name}: {len(items)} items, {len(pooled)} systems pooled, {n} candidates", flush=True
        )
        if a.dry_run:
            continue

        def judge_one(job):
            it, cids = job
            if not cids:
                return it, []
            cands = [c for c in (chunk(x) for x in cids) if c]
            if not cands:
                return it, []
            # a real question has no reference answer: its gold quote stands in, as in
            # finalize_qa.py's do_real
            ref = it.meta.get("check_answer") or it.meta.get("answer") or it.gold[0].quote
            probe = replace(it, meta=it.meta | {"check_answer": ref})
            found, _ = judge_generated(judge, texts, probe, cands)
            return it, [g for g in found if confirm(confirmer, it.question, ref, g, texts)]

        with ThreadPoolExecutor(a.workers) as ex:
            results = list(ex.map(judge_one, todo))
        added = with_new = 0
        for it, new in results:
            new = [g for g in new if not any(overlaps(vars(g), h) for h in [*it.gold, *it.also])]
            if new:
                it.also = [*it.also, *new]
                earlier = it.meta.get("also_repooled", [])
                it.meta = it.meta | {"also_repooled": [*earlier, *(asdict(g) for g in new)]}
                added += len(new)
                with_new += 1
        save_items(path, items)
        log[name] = {"candidates": n, "added": added,
                     "items_with_new_also": with_new}  # fmt: skip
        print(f"  added {added} also-spans", flush=True)

        # re-score every stored result file of this set with the new spans
        by_qid = {it.qid: it for it in items}
        for p in files:
            rows = [json.loads(x) for x in p.read_text("utf-8").splitlines() if x]
            for r in rows:
                it = by_qid.get(r["qid"])
                if it and it.gold:
                    r["scores"] = asdict(score(r["retrieved"], it.gold, it.also))
            p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), "utf-8")
    if not a.dry_run:
        sums_path = DATA / "eval" / "SHA256SUMS"  # the sets changed: their checksums too
        sums = {ln.split()[1]: ln for ln in sums_path.read_text().splitlines() if ln}
        sums |= {f"{n}.jsonl": f"{sha256(DATA / 'eval' / f'{n}.jsonl')}  {n}.jsonl" for n in SETS}
        sums_path.write_text("".join(v + "\n" for v in sums.values()))
        out = DATA / "eval" / "results" / "repool.json"
        out.write_text(json.dumps(log, indent=1), "utf-8")
        print(
            "then: uv run python ../eval/run_retrieval.py --set ../data/eval/<set>.jsonl  (summaries)"
        )


if __name__ == "__main__":
    main()
