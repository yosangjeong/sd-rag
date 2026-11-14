"""doc2query: questions in everyday words, written per statute chunk, added to BM25.

Real questions say "집주인이 계약기간을 1년으로 하재요" where the article says 임대인 and
임대차기간; BM25 then misses the article, and the reranker never sees it. terms.py
maps a list of everyday words to statute terms; doc2query does the same from the other
side, for every chunk: an LLM writes 3 questions a layperson would ask that the passage
answers, and they are appended to the chunk's search_text in a copy of the index (the
embedding, the text shown and the reranker's passage are unchanged).

The questions are written by gpt-oss-120b, not by Qwen, which wrote the generated
evaluation sets: questions by the same model would match those sets' wording and
inflate them. Decisions are made on the real-question sets only.

    cd backend && AWS_PROFILE=<profile> uv run python ../eval/doc2query.py generate
    cd backend && uv run python ../eval/doc2query.py build      # chunks-structure -> chunks-d2q
"""

import argparse
import json
from concurrent.futures import ThreadPoolExecutor

from evalset import DATA, LLM_CACHE
from opensearchpy import OpenSearch, helpers

from sdrag.common.config import settings
from sdrag.common.llm import BedrockChat, CachedChat, parse_json

MODEL = "openai.gpt-oss-120b-1:0"
SOURCE, TARGET = "chunks-structure", "chunks-d2q"
OUT = DATA / "raw" / "d2q" / "questions.jsonl"
SYSTEM = """You help a search engine over statutes match the questions ordinary people ask. Given one passage of a statute, write 3 short questions that a worker, employer, tenant or landlord with no legal training would ask and that this passage answers. Use everyday words and situations, not the statute's own terms (e.g. "집주인" rather than "임대인", "my boss" rather than "employer"). Write them in {lang}. If the passage answers nothing a person would ask (a table of contents, a deleted article, amendment history), return []. Return only a JSON list of strings."""


def public_chunks(client) -> list[dict]:
    q = {"query": {"term": {"owner": "public"}},
         "_source": ["chunk_id", "title", "heading", "text", "lang"]}  # fmt: skip
    return [h["_source"] for h in helpers.scan(client, index=SOURCE, query=q, size=500)]


def generate() -> None:
    client = OpenSearch(hosts=[settings.opensearch_url], timeout=60)
    chat = CachedChat(BedrockChat(MODEL, settings.aws_region), LLM_CACHE)
    chunks = public_chunks(client)

    def one(c: dict) -> dict:
        lang = "English" if (c.get("lang") or "ko") == "en" else "Korean"
        user = f"{c['title']} > {c.get('heading') or ''}\n{c['text'][:1200]}"
        out = parse_json(chat.complete(SYSTEM.format(lang=lang), user, max_tokens=800).text)
        qs = (
            [q.strip() for q in out if isinstance(q, str) and q.strip()]
            if isinstance(out, list)
            else []
        )
        return {"chunk_id": c["chunk_id"], "questions": qs[:3]}

    with ThreadPoolExecutor(8) as ex:
        rows = list(ex.map(one, chunks))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), "utf-8")
    inner = chat.inner
    print(f"{len(rows)} chunks, {sum(bool(r['questions']) for r in rows)} with questions; "
          f"tokens {inner.input_tokens} in / {inner.output_tokens} out (uncached calls)")  # fmt: skip


def build() -> None:
    client = OpenSearch(hosts=[settings.opensearch_url], timeout=600)
    qs = {
        r["chunk_id"]: r["questions"] for r in map(json.loads, OUT.read_text("utf-8").splitlines())
    }
    if client.indices.exists(index=TARGET):
        client.indices.delete(index=TARGET)
    src = client.indices.get(index=SOURCE)[SOURCE]
    settings_ = {k: v for k, v in src["settings"]["index"].items()
                 if k in ("analysis", "knn", "number_of_shards", "number_of_replicas")}  # fmt: skip
    client.indices.create(
        index=TARGET, body={"settings": {"index": settings_}, "mappings": src["mappings"]}
    )
    client.reindex(body={"source": {"index": SOURCE}, "dest": {"index": TARGET}},
                   wait_for_completion=True, request_timeout=3600)  # fmt: skip
    client.indices.refresh(index=TARGET)
    q = {"query": {"term": {"owner": "public"}}, "_source": ["chunk_id", "search_text"]}
    actions = [
        {"_op_type": "update", "_index": TARGET, "_id": h["_id"],
         "doc": {"search_text": h["_source"]["search_text"] + "\n" + "\n".join(qs[h["_source"]["chunk_id"]])}}
        for h in helpers.scan(client, index=TARGET, query=q, size=500)
        if qs.get(h["_source"]["chunk_id"])
    ]  # fmt: skip
    helpers.bulk(client, actions, chunk_size=500, request_timeout=600)
    client.indices.refresh(index=TARGET)
    print(f"{TARGET}: {client.count(index=TARGET)['count']} chunks, {len(actions)} with questions")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=("generate", "build"))
    {"generate": generate, "build": build}[ap.parse_args().stage]()
