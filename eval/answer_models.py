"""Which answer model: the same sources, only the model that writes the answer changes.

For each of the 50 single-file questions (data/eval/single_file/compare.csv) the retrieval
(bilingual_union + GLM-4.7 rerank, as served before 2026-11-13 and as single_file.py
records it; not the wide pool; search scoped to the file) runs once and its
top 6 sources go to every candidate answer model with the served answer prompt
(sdrag.agent.answer). The same judge as single_file.py (DeepSeek V3.2, judge v2) grades
each answer against the reference answer and the gold text. DeepSeek is not a
candidate (the judge's family); Claude is not one (cross-Region inference only).

Every model reply is cached (CachedChat), so a re-run costs nothing.
Writes data/eval/answer_models.json.

    cd backend && AWS_PROFILE=... uv run python ../eval/answer_models.py [--budget N] [model ...]
"""

import datetime as dt
import json
import sys
import threading
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

from evalset import DATA, LLM_CACHE, load_items
from judges import correct_prompt, correct_user
from single_file import CSV, JUDGE_MODEL

from sdrag.agent.answer import answer
from sdrag.common.config import settings
from sdrag.common.llm import BedrockChat, CachedChat, parse_json
from sdrag.common.search_client import make_client
from sdrag.retrieval.embed import TitanEmbedder
from sdrag.retrieval.index import PUBLIC
from sdrag.retrieval.rerank import LlmReranker, LlmTranslator
from sdrag.retrieval.search import Searcher

MODELS = [
    "zai.glm-4.7",  # served
    "zai.glm-5",
    "qwen.qwen3-235b-a22b-2507-v1:0",
    "openai.gpt-oss-120b-1:0",
    "moonshotai.kimi-k2.5",
    "mistral.mistral-large-3-675b-instruct",
    "minimax.minimax-m2.5",
]
TODAY = dt.date(2026, 11, 15)  # fixed, so the answer prompts (and the cache keys) hold
OUT = DATA / "eval" / "answer_models.json"


class Recording:
    """Wraps a chat and remembers the stop reasons (a reasoning model can spend the
    token budget before the answer: stop reason max_tokens)."""

    def __init__(self, inner) -> None:
        self.inner, self.name, self.stops = inner, inner.name, []
        self._lock = threading.Lock()

    def complete(self, system, user, max_tokens=1024, temperature=0.0):
        c = self.inner.complete(system, user, max_tokens, temperature)
        with self._lock:
            self.stops.append(c.stop_reason)
        return c


def sources_for(rows, items):
    client = make_client(settings.opensearch_url, settings.aws_region)
    emb = TitanEmbedder(settings.embed_model, settings.aws_region, settings.embed_dims)
    chat = CachedChat(BedrockChat(settings.llm_model, settings.aws_region), LLM_CACHE)

    def one(r):
        it = items[r["qid"]]
        s = Searcher(client, settings.index, emb, LlmTranslator(chat), owners=[PUBLIC],
                     scope=[it.gold[0].doc_id])  # fmt: skip
        return LlmReranker(chat).rerank(it.question, s.bilingual_union(it.question, 20, 10))[:6]

    with ThreadPoolExecutor(8) as ex:
        return dict(zip([r["qid"] for r in rows], ex.map(one, rows), strict=True))


def main(models: list[str], budget: int = 1200) -> None:
    import csv

    rows = list(csv.DictReader(CSV.open(encoding="utf-8")))
    items = {
        i.qid: i for s in ("test.jsonl", "test_re.jsonl") for i in load_items(DATA / "eval" / s)
    }
    sources = sources_for(rows, items)
    judge = CachedChat(BedrockChat(JUDGE_MODEL, settings.aws_region), LLM_CACHE)
    results = json.loads(OUT.read_text("utf-8")) if OUT.exists() else {}
    for model in models:
        label = model if budget == 1200 else f"{model}@{budget}"
        raw = BedrockChat(model, settings.aws_region)
        chat = Recording(CachedChat(raw, LLM_CACHE))

        def one(r, chat=chat):
            field = "real-estate" if r["qid"].startswith("r") else "labor"
            a = answer(chat, r["question"], sources[r["qid"]], max_tokens=budget, today=TODAY)
            if not a.text.strip():
                # the judge graded empty answers "correct" (it read the reference as the
                # answer): a reasoning model that spent its budget thinking, 2026-11-15
                out = {"grade": "no_answer", "why": "empty answer (not sent to the judge)"}
            else:
                user = correct_user(r["question"], r["reference"], r["gold_quote"], a.text)
                reply = judge.complete(correct_prompt(field, 2), user, max_tokens=400)
                out = parse_json(reply.text) or {}
            return {"qid": r["qid"], "field": field, "answer": a.text,
                    "grade": out.get("grade", "unparsed"), "why": out.get("why", ""),
                    "unchecked_figures": a.unchecked_figures}  # fmt: skip

        with ThreadPoolExecutor(6) as ex:
            graded = list(ex.map(one, rows))
        stops = Counter(chat.stops)
        results[label] = {"grades": graded, "stop_reasons": dict(stops),
                          "new_tokens": [raw.input_tokens, raw.output_tokens]}  # fmt: skip
        OUT.write_text(json.dumps(results, ensure_ascii=False, indent=1), "utf-8")
        report(label, results[label])


def report(model: str, r: dict) -> None:
    for field in ("labor", "real-estate", None):
        sel = [g for g in r["grades"] if field is None or g["field"] == field]
        c, n = Counter(g["grade"] for g in sel), len(sel)
        print(f"{model:40} {field or 'all':12} n={n:2}  correct {c['correct'] / n:4.0%}  "
              f"partial {c['partial'] / n:4.0%}  wrong {c['wrong'] / n:4.0%}  "
              f"no answer {c['no_answer'] / n:4.0%}")  # fmt: skip
    print(f"{'':40} stop reasons {r['stop_reasons']}  new tokens in/out {r['new_tokens']}")


if __name__ == "__main__":
    args = sys.argv[1:]
    # --budget N: the answer's max_tokens (served: 1200); reasoning models think inside it
    budget = int(args.pop(args.index("--budget") + 1)) if "--budget" in args else 1200
    if "--budget" in args:
        args.remove("--budget")
    main(args or MODELS, budget)
