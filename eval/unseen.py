"""Retrieval on documents the system was never built or tuned on.

Everything else in eval/ measures the 70 statutes, and several retrieval steps are
specific to them (cross-references between a law and its decree, definition articles,
statute terms). A user (or an interviewer) uploads other things: press releases,
guides, reports, tables, scans. This set measures that case:

- documents: public files downloaded on 2026-11-14, unrelated to the corpus: Korean
  government press releases from korea.kr (KOGL type 1, attribution: see
  data/eval/unseen_docs.json), the NIST Cybersecurity Framework 2.0 and IRS
  Publication 15 (US government works, public domain), and one simulated scan (a
  press release rendered to images with a slight skew and noise, no text layer);
- ingestion: the upload path itself (worker/job.py process: parse, OCR for the scan,
  chunk, embed, index), owned by a test user;
- questions: sampled chunks of each document, written by Qwen and checked by DeepSeek
  with the prompts of generate_qa.py made field-neutral; 30% asked in the other
  language;
- search: as the service searches for that user, over their uploads and the public
  statutes (the statutes are distractors here).

    cd backend && AWS_PROFILE=<profile> uv run python ../eval/unseen.py prepare
    ... ingest | generate | measure
"""

import argparse
import json
import random
import shutil
import statistics
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace

from evalset import (
    DATA,
    EMBED_CACHE,
    LLM_CACHE,
    Gold,
    Item,
    load_items,
    locate,
    save_items,
    score,
)
from generate_qa import CHECK_MODEL, GEN_MODEL, LANG_NAME, STYLE_WEIGHTS, STYLES, overlap
from opensearchpy import OpenSearch

from sdrag.api.store import MemoryStore
from sdrag.common.config import settings
from sdrag.common.llm import BedrockChat, CachedChat, parse_json
from sdrag.retrieval.embed import CachedEmbedder, TitanEmbedder
from sdrag.retrieval.index import PUBLIC
from sdrag.retrieval.jurisdiction import jurisdiction
from sdrag.retrieval.rerank import LlmReranker, LlmTranslator
from sdrag.retrieval.search import Searcher

USER = "unseen-eval"
RAW = DATA / "raw" / "unseen"
DOCS = RAW / "docs"
MANIFEST = DATA / "eval" / "unseen_docs.json"
SET = DATA / "eval" / "unseen.jsonl"
OUT = DATA / "eval" / "results" / "unseen"
PER_DOC = 6
SEED = 20261114
KOGL = "KOGL type 1 (공공누리 제1유형, 출처표시): 대한민국 정책브리핑 www.korea.kr"
PD = "US government work, public domain (17 U.S.C. 105)"

# (id, downloaded file, title, source, license)
DOCUMENTS = [
    ("kr-policy-meeting", "kr/f_198589845", "hwpx", "제17회 국가정책조정회의 보도자료",
     "https://www.korea.kr/briefing/pressReleaseView.do?newsId=156789192", KOGL),
    ("kr-fuel-price-cap", "kr/f_198590117", "hwpx", "12차 석유 최고가격, 11차 수준으로 동결",
     "https://www.korea.kr/briefing/pressReleaseView.do?newsId=156789230", KOGL),
    ("kr-cocoa-recall", "kr/f_198589956", "hwpx", "금속성 이물 혼입된 수입 코코아분말 회수 조치",
     "https://www.korea.kr/briefing/pressReleaseView.do?newsId=156789212", KOGL),
    ("kr-medical-data", "kr/f_198590115", "pdf", "AI 기반 의료데이터 표준화로 기관 간 정보 연계·활용 확대",
     "https://www.korea.kr/briefing/pressReleaseView.do?newsId=156789187", KOGL),
    ("kr-law-portal", "kr/f_198589884", "pdf", "국가법령정보센터, 국민 눈높이에 맞춰 새 단장",
     "https://www.korea.kr/briefing/pressReleaseView.do?newsId=156789202", KOGL),
    ("kr-marine-park-scan", "kr/f_198589976", "scan", "호미반도 국가해양생태공원 조성 사업 예비타당성조사 통과 (모의 스캔)",
     "https://www.korea.kr/briefing/pressReleaseView.do?newsId=156789211", KOGL),
    ("us-nist-csf", "NIST.CSWP.29.pdf", "pdf", "The NIST Cybersecurity Framework (CSF) 2.0",
     "https://nvlpubs.nist.gov/nistpubs/CSWP/NIST.CSWP.29.pdf", PD),
    ("us-irs-p15", "irs-p15.pdf", "pdf", "IRS Publication 15 (Circular E), Employer's Tax Guide",
     "https://www.irs.gov/pub/irs-pdf/p15.pdf", PD),
]  # fmt: skip

GEN_SYSTEM = """You write test questions for a document search engine. Users upload their own documents (reports, press releases, guides, manuals, tables) and ask about them.
You are given one passage from an uploaded document. Write ONE question that a reader of such a document could ask and that the passage answers.

Rules:
- Write the question in {q_lang}. Style: {style}.
- Do not quote the passage and do not cite section or page numbers: use your own words for the same idea.
- {lang_rule}
- The question must have one clear answer in the passage, and must make sense on its own to someone who has not seen it (name the program, product or subject it is about).
- "evidence": copy, character for character, the shortest part of the passage that answers the question (usually one sentence, one list item or one table row; at most about 300 characters). Give a list with one string.
- "answer": the answer in one short sentence, in {q_lang}.
- If the passage holds nothing a reader would ask about (only a heading, contact details, a table of contents, unreadable text), return {{"skip": true, "reason": "..."}}.

Return only JSON: {{"question": "...", "evidence": [...], "answer": "..."}}"""

CHECK_SYSTEM = """You review test questions for a document search engine. Given a question and the passage it was written from, judge strictly.
- "answerable": "yes" if the passage fully answers the question, "partial" if only in part, "no" otherwise.
- "ambiguous": true if the question is unclear, or could just as well be about something else, or depends on context the asker did not give.
- "answer": the answer from the passage, one sentence.
Return only JSON: {"answerable": "...", "ambiguous": false, "answer": "..."}"""


def simulated_scan(src: Path, dst: Path, dpi: int = 150) -> None:
    """A press release rendered page by page to grey images with a slight rotation and
    noise, saved as an image-only PDF: what a scanner returns (no text layer)."""
    import pypdfium2 as pdfium
    from PIL import Image, ImageFilter

    rng = random.Random(SEED)
    pages = []
    for page in pdfium.PdfDocument(str(src)):
        img = page.render(scale=dpi / 72).to_pil().convert("L")
        img = img.rotate(rng.uniform(-1.2, 1.2), expand=True, fillcolor=255)
        noise = Image.effect_noise(img.size, 18).convert("L")
        img = Image.blend(img, noise, 0.08).filter(ImageFilter.GaussianBlur(0.4))
        pages.append(img.convert("RGB"))
    pages[0].save(dst, "PDF", save_all=True, append_images=pages[1:], resolution=dpi)


def prepare() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    manifest = []
    for doc_id, file, kind, title, url, lic in DOCUMENTS:
        src = RAW / "download" / file
        ext = "pdf" if kind == "scan" else kind
        dst = DOCS / f"{doc_id}.{ext}"
        if kind == "scan":
            simulated_scan(src, dst)
        else:
            shutil.copyfile(src, dst)
        manifest.append({"id": doc_id, "file": dst.name, "title": title, "source": url,
                         "license": lic, "kind": kind})  # fmt: skip
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", "utf-8")
    print(f"{len(manifest)} documents in {DOCS}")


def ingest() -> None:
    from evalset import OCR_CACHE

    from sdrag.common.search_client import make_client
    from sdrag.ingest.ocr import BedrockVisionOcr, CachedOcr
    from sdrag.worker.job import process

    client = make_client(settings.opensearch_url, settings.aws_region)
    emb = TitanEmbedder(settings.embed_model, settings.aws_region, settings.embed_dims)
    ocr = CachedOcr(BedrockVisionOcr(settings.ocr_model, settings.aws_region), OCR_CACHE)
    deps = SimpleNamespace(store=MemoryStore(), client=client, index=settings.index,
                           embedder=CachedEmbedder(emb, EMBED_CACHE), ocr=ocr)  # fmt: skip
    client.delete_by_query(index=settings.index, refresh=True,
                           body={"query": {"term": {"owner": USER}}})  # fmt: skip
    for d in json.loads(MANIFEST.read_text("utf-8")):
        path = DOCS / d["file"]
        deps.store.put_document(USER, {"id": d["id"], "file": d["title"], "status": "queued"})
        r = process(USER, d["id"], path, f"{d['title']}.{path.suffix[1:]}", deps)
        print(d["id"], r.get("status"), r.get("chunks"), r.get("error", ""), flush=True)
    client.indices.refresh(index=settings.index)


def chunks_of(client, doc_id: str) -> list[dict]:
    body = {"size": 1000, "query": {"term": {"doc_id": f"u-{doc_id}"}},
            "_source": ["chunk_id", "doc_id", "title", "heading", "text", "start", "end", "lang"]}  # fmt: skip
    return [h["_source"] for h in client.search(index=settings.index, body=body)["hits"]["hits"]]


def generate() -> None:
    client = OpenSearch(hosts=[settings.opensearch_url], timeout=60)
    gen = CachedChat(BedrockChat(GEN_MODEL, settings.aws_region), LLM_CACHE)
    chk = CachedChat(BedrockChat(CHECK_MODEL, settings.aws_region), LLM_CACHE)
    rng = random.Random(SEED)
    items, dropped = [], {}
    for d in json.loads(MANIFEST.read_text("utf-8")):
        cs = [c for c in chunks_of(client, d["id"]) if len(c["text"]) >= 200]
        rng.shuffle(cs)
        made = 0
        for c in cs:
            if made >= PER_DOC:
                break
            lang = c.get("lang") or ("ko" if d["id"].startswith("kr-") else "en")
            q_lang = lang if rng.random() < 0.7 else ("en" if lang == "ko" else "ko")
            style = rng.choices(list(STYLE_WEIGHTS), weights=list(STYLE_WEIGHTS.values()))[0]
            lang_rule = ("The document is in the same language as the question." if q_lang == lang
                         else "The document is in another language than the question; ask naturally in your language.")  # fmt: skip
            system = GEN_SYSTEM.format(
                q_lang=LANG_NAME[q_lang], style=STYLES[style], lang_rule=lang_rule
            )
            passage = f"[Passage] {d['title']} > {c.get('heading') or ''}\n{c['text']}"
            out = parse_json(gen.complete(system, passage, max_tokens=800, temperature=0.5).text)
            if not isinstance(out, dict) or out.get("skip") or not out.get("question"):
                dropped["generation"] = dropped.get("generation", 0) + 1
                continue
            quote = (out.get("evidence") or [""])[0].strip()
            loc = locate(c["text"], quote)
            if loc is None:
                dropped["quote not found"] = dropped.get("quote not found", 0) + 1
                continue
            q = out["question"].strip()
            ok = parse_json(
                chk.complete(CHECK_SYSTEM, f"Question: {q}\n\n{passage}", max_tokens=400).text
            )
            if not isinstance(ok, dict) or ok.get("answerable") != "yes" or ok.get("ambiguous"):
                dropped["check"] = dropped.get("check", 0) + 1
                continue
            s, e = c["start"] + loc[0], c["start"] + loc[1]
            made += 1
            items.append(Item(f"u{len(items) + 1:03d}", q, q_lang,
                              [Gold(c["doc_id"], s, e, c["text"][loc[0]:loc[1]])], "fact",
                              f"generated:{GEN_MODEL}",
                              {"doc": d["id"], "doc_kind": d["kind"], "style": style, "answer_lang": lang,
                               "answer": out.get("answer", ""), "check_answer": ok.get("answer", ""),
                               "overlap": round(overlap(q, c["text"]), 3)}, []))  # fmt: skip
        print(d["id"], "questions", made, flush=True)
    save_items(SET, items)
    print(f"{len(items)} questions -> {SET}; dropped {dropped}")


def measure() -> None:
    client = OpenSearch(hosts=[settings.opensearch_url], timeout=60)
    emb = CachedEmbedder(
        TitanEmbedder(settings.embed_model, settings.aws_region, settings.embed_dims), EMBED_CACHE
    )
    chat = BedrockChat("zai.glm-4.7", settings.aws_region)
    cached = CachedChat(chat, LLM_CACHE)  # translation and jurisdiction: same calls as served
    items = load_items(SET, anchored=False)
    OUT.mkdir(parents=True, exist_ok=True)
    systems = {"hybrid": None, "wide+rerank+jur": True}
    summary = {}
    for name, served in systems.items():
        s = Searcher(client, settings.index, emb, LlmTranslator(cached), owners=[USER, PUBLIC])
        rows = []
        for it in items:
            if served:
                s.country = jurisdiction(cached, it.question)
                hits = s.wide(it.question)
                hits = LlmReranker(chat).rerank(it.question, hits, s.last_queries or None)
            else:
                s.country = None
                hits = s.hybrid(it.question, 20)
            got = [h.source | {"chunk_id": h.chunk_id} for h in hits]
            sc = score(got, it.gold, it.also)
            rows.append({"qid": it.qid, "question": it.question, "doc": it.meta["doc"],
                         "scores": asdict(sc), "retrieved": [{k: g.get(k) for k in ("doc_id", "start", "end", "heading", "chunk_id")} for g in got[:20]]})  # fmt: skip
        (OUT / f"{name}.jsonl").write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), "utf-8"
        )
        m = lambda f, rows=rows: statistics.mean(f(r["scores"]) for r in rows)
        summary[name] = {"n": len(rows), "hit@1": m(lambda x: x["span_hit"][1]), "hit@5": m(lambda x: x["span_hit"][5]),
                         "hit@10": m(lambda x: x["span_hit"][10]), "mrr": m(lambda x: x["span_mrr"]),
                         "doc_hit@10": m(lambda x: x["doc_hit"][10])}  # fmt: skip
        print(
            name,
            {k: round(v, 3) if isinstance(v, float) else v for k, v in summary[name].items()},
            flush=True,
        )
    (OUT / "summary.json").write_text(json.dumps(summary, indent=1), "utf-8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=("prepare", "ingest", "generate", "measure"))
    {"prepare": prepare, "ingest": ingest, "generate": generate, "measure": measure}[
        ap.parse_args().stage
    ]()
