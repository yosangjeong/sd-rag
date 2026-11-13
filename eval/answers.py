"""Answer quality: correct, grounded in what it cites, citing the gold, declining when
the corpus has no answer.

Runs the served pipeline (service.RagService, basic mode) on a stratified sample of
the test set and on every real question the corpus cannot answer (``--set labor``),
or on the real-estate test set and its unanswerable real questions (``--set re``), then:

- correctness (judge vs the reference answer): correct | partial | wrong | no_answer
- groundedness (judge vs the cited sources' text): supported | partly | unsupported,
  i.e. does the answer say anything its citations do not
- citation hit (computed): does a cited chunk overlap a gold or also span
- unanswerable questions: does the answer decline (judge: declined | answered)

The judge is DeepSeek V3.2, of neither the answer model's (GLM) nor the question
writer's (Qwen) family; its prompts are below. Outputs per item and a summary go to
data/eval/results/answers/<version>/ (one folder per measured version).

    cd backend && AWS_PROFILE=... uv run python ../eval/answers.py --version v6-country-filter [--n 100]
"""

import argparse
import json
import random
import statistics
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

from evalset import DATA, doc_texts, load_items, overlaps

from sdrag.common.config import settings
from sdrag.common.llm import BedrockChat, CachedChat, parse_json
from sdrag.common.search_client import make_client
from sdrag.retrieval.embed import TitanEmbedder
from sdrag.service import RagService

RESULTS = DATA / "eval" / "results" / "answers"
JUDGE_MODEL = "deepseek.v3.2"
SEED = 20261112

CORRECT_SYSTEM = """You grade answers to questions about Korean and US labor law documents.
Given the question, the reference answer, the passage it comes from, and a candidate answer, decide:
- "correct": the candidate states the same key fact as the reference (number, period, condition, procedure); extra correct detail is fine.
- "partial": it states part of it, or the right fact with a wrong condition.
- "wrong": it states something else, or contradicts the reference.
- "no_answer": it says it cannot find the answer, or answers nothing.
Judge the content, not the language or style.
Return only JSON: {"grade": "correct" | "partial" | "wrong" | "no_answer", "why": "<one sentence>"}"""

GROUNDED_SYSTEM = """You check whether an answer is supported by the sources it cites.
Given an answer with [n] citations and the text of those sources, decide:
- "supported": every factual statement in the answer is stated in the cited sources.
- "partly": most is, but at least one statement is not in any cited source.
- "unsupported": the main claim is not in the cited sources.
A statement that the documents do not answer the question counts as supported.
Return only JSON: {"grade": "supported" | "partly" | "unsupported", "why": "<one sentence>"}"""

DECLINE_SYSTEM = """A user asked a question that the document collection cannot answer. Did the answer decline (say the documents do not answer it, possibly pointing to related provisions), or did it answer as if the documents did?
Return only JSON: {"grade": "declined" | "answered", "why": "<one sentence>"}"""


def sample(items, texts, n: int):
    """n items spread over (question language, answer language, file type)."""
    rng = random.Random(SEED)
    cells: dict[tuple, list] = {}
    for it in sorted(items, key=lambda i: i.qid):
        key = (
            it.q_lang,
            "+".join(sorted(it.answer_langs(texts))),
            "+".join(sorted(it.file_types(texts))),
        )
        cells.setdefault(key, []).append(it)
    for v in cells.values():
        rng.shuffle(v)
    out = []
    while len(out) < n and any(cells.values()):
        for k in sorted(cells):
            if cells[k] and len(out) < n:
                out.append(cells[k].pop())
    return out


def judge(llm, system: str, user: str) -> dict:
    return parse_json(llm.complete(system, user, max_tokens=300).text) or {"grade": "unparsed"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--version", required=True, help="folder name under results/answers/")
    ap.add_argument("--set", choices=("labor", "re"), default="labor")
    ap.add_argument("--reuse", action="store_true",
                    help="keep the version's existing result files, run only what is missing")  # fmt: skip
    a = ap.parse_args()
    texts = doc_texts()
    if a.set == "labor":
        test = sample(load_items(DATA / "eval" / "test.jsonl"), texts, a.n)
        unanswerable = load_items(DATA / "eval" / "real_unanswerable.jsonl")
        correct_system = CORRECT_SYSTEM
    else:
        test = sample(load_items(DATA / "eval" / "test_re.jsonl"), texts, a.n)
        unanswerable = load_items(DATA / "eval" / "real_re_unanswerable.jsonl")
        correct_system = CORRECT_SYSTEM.replace("labor law", "real-estate law")

    client = make_client(settings.opensearch_url, settings.aws_region)
    emb = TitanEmbedder(settings.embed_model, settings.aws_region, settings.embed_dims)
    service = RagService(
        client, settings.index, emb, BedrockChat(settings.llm_model, settings.aws_region)
    )
    jllm = CachedChat(
        BedrockChat(JUDGE_MODEL, settings.aws_region), DATA / "raw" / "cache" / "eval" / "llm"
    )

    def run(it, answerable: bool) -> dict:
        reply = service.ask("eval", it.question)
        ans = reply.answer
        row = {"qid": it.qid, "question": it.question, "answer": ans.text,
               "cited": [c.chunk_id for c in ans.citations], "latency_ms": round(reply.latency_ms),
               "tokens": [reply.input_tokens, reply.output_tokens]}  # fmt: skip
        if not answerable:
            row["decline"] = judge(
                jllm, DECLINE_SYSTEM, f"Question: {it.question}\n\nAnswer: {ans.text}"
            )
            return row
        g = it.gold[0]
        row["citation_hit"] = any(
            overlaps(vars(c), s) for c in ans.citations for s in [*it.gold, *it.also]
        )
        ref = it.meta.get("check_answer") or it.meta.get("answer", "")
        row["correct"] = judge(jllm, correct_system, f"Question: {it.question}\nReference answer: {ref}\n"
                               f"Passage: {g.quote}\n\nCandidate answer: {ans.text}")  # fmt: skip
        cited = "\n\n".join(
            f"[{c.n}] {texts[c.doc_id].text[c.start : c.end][:2000]}" for c in ans.citations
        )
        row["grounded"] = judge(
            jllm, GROUNDED_SYSTEM, f"Answer: {ans.text}\n\nCited sources:\n{cited or '(none)'}"
        )
        return row

    OUT = RESULTS / a.version
    OUT.mkdir(parents=True, exist_ok=True)
    names = ("test_sample", "unanswerable") if a.set == "labor" else ("test_re", "unanswerable_re")

    def kept(name: str) -> list[dict] | None:
        path = OUT / f"{name}.jsonl"
        if a.reuse and path.exists():
            return [json.loads(x) for x in path.read_text("utf-8").splitlines() if x]
        return None

    with ThreadPoolExecutor(a.workers) as ex:
        rows = kept(names[0]) or list(ex.map(lambda it: run(it, True), test))
        un = kept(names[1]) or list(ex.map(lambda it: run(it, False), unanswerable))
    for name, rs in zip(names, (rows, un), strict=True):
        (OUT / f"{name}.jsonl").write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rs), "utf-8"
        )

    def share(rs, key):
        if not rs:
            return "-"
        c = Counter(r[key]["grade"] for r in rs)
        return ", ".join(f"{k} {v / len(rs):.0%}" for k, v in c.most_common())

    lines = [
        "# Answer quality (served pipeline: translation union + rerank + GLM-4.7 answers)",
        "",
        (
            f"{'Test' if a.set == 'labor' else 'Real-estate test'} sample: {len(rows)} items "
            f"spread over language and file type; unanswerable: {len(un)} real questions the "
            f"corpus does not answer. Judge: {JUDGE_MODEL} (prompts in eval/answers.py)."
        ),
        "",
        "| Measure | Result |",
        "|---|---|",
        f"| correctness (vs reference) | {share(rows, 'correct')} |",
        f"| groundedness (vs cited sources) | {share(rows, 'grounded')} |",
        f"| a citation overlaps the gold | {sum(r['citation_hit'] for r in rows) / len(rows):.0%} |",
        f"| unanswerable: declined | {share(un, 'decline')} |",
        f"| latency p50 | {statistics.median(r['latency_ms'] for r in rows + un) / 1000:.1f} s |",
    ]
    summary = "summary.md" if a.set == "labor" else "summary-re.md"
    (OUT / summary).write_text("\n".join(lines) + "\n", "utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
