"""Shared pieces of the retrieval evaluation: corpus texts, gold spans, scoring.

An evaluation item is a question and its gold spans. A gold span is a document and a
character range [start, end) in that document's *canonical text* (chunk.canonical_text:
the parsed blocks joined by blank lines), plus the quoted text itself. Both chunking
strategies cut the same canonical text and every indexed chunk records its own range,
so one gold span scores any strategy: a retrieved chunk is relevant when its range
overlaps a gold range of the same document.

The quote makes the set survive parser changes: when a document's canonical text no
longer holds the quote at the stored offsets, ``anchor`` finds it again (nearest
occurrence to the old offset) or reports the item as broken.

Canonical texts are cached per document (``doc_texts``) so building and scoring the
set does not re-parse 70 files, and scanned pages come from the OCR cache: what the
index holds is what the gold spans point into.
"""

import json
import math
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

from sdrag.common.config import settings
from sdrag.ingest import layout
from sdrag.ingest.chunk import canonical_text
from sdrag.ingest.corpus import CorpusDoc, load_corpus
from sdrag.ingest.ocr import BedrockVisionOcr, CachedOcr
from sdrag.ingest.parse import parse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
# every cache under data/raw/ (ingest/layout.py); the OCR and embedding ones can be moved
# with SDRAG_OCR_CACHE_DIR / SDRAG_EMBED_CACHE_DIR, as for ingestion
CACHE = layout.cache(DATA, "eval")
LLM_CACHE = CACHE / "llm"  # model replies of the evaluation scripts (CachedChat)
OCR_CACHE = Path(settings.ocr_cache_dir or layout.cache(DATA, "ocr"))
EMBED_CACHE = Path(settings.embed_cache_dir or layout.cache(DATA, "embed"))


@dataclass
class BlockInfo:
    start: int
    end: int
    kind: str  # text | table
    heading: str | None
    page: int | None


@dataclass
class DocText:
    id: str
    lang: str
    title: str
    file_type: str
    text: str
    blocks: list[BlockInfo]

    def block_at(self, offset: int) -> BlockInfo:
        for b in self.blocks:
            if b.start <= offset < b.end + 2:  # +2: the separator belongs to the block before
                return b
        return self.blocks[-1]


def _parse_doc(doc: CorpusDoc, ocr) -> DocText:
    parsed = parse(doc.path, ocr=ocr)
    text, starts = canonical_text(parsed)
    blocks = [
        BlockInfo(s, s + len(b.text), b.kind, b.heading, b.page)
        for s, b in zip(starts, parsed.blocks, strict=True)
    ]
    return DocText(doc.id, doc.lang, doc.title, doc.file_type, text, blocks)


def doc_texts(data: Path = DATA, refresh: bool = False) -> dict[str, DocText]:
    """Canonical text of every corpus document, parsed once and cached as JSON."""
    out_dir = CACHE / "canonical"
    out_dir.mkdir(parents=True, exist_ok=True)
    ocr = None
    out: dict[str, DocText] = {}
    for doc in load_corpus(data):
        path = out_dir / f"{doc.id}.json"
        if path.exists() and not refresh:
            d = json.loads(path.read_text(encoding="utf-8"))
            d["blocks"] = [BlockInfo(**b) for b in d["blocks"]]
            out[doc.id] = DocText(**d)
            continue
        if ocr is None:  # only built when a document has to be parsed
            ocr = CachedOcr(
                BedrockVisionOcr(settings.ocr_model, settings.aws_region),
                OCR_CACHE,
            )
        dt = _parse_doc(doc, ocr)
        path.write_text(json.dumps(asdict(dt), ensure_ascii=False), encoding="utf-8")
        out[doc.id] = dt
    return out


# ---------- gold spans ----------


@dataclass
class Gold:
    doc_id: str
    start: int
    end: int
    quote: str  # text[start:end] when written


@dataclass
class Item:
    qid: str
    question: str
    q_lang: str  # language of the question
    gold: list[Gold]
    kind: str  # fact | table | multi | real (a question written by people)
    source: str  # generated:<model> | easylaw | dol-whd
    meta: dict = field(default_factory=dict)
    # other spans that answer the question just as well (the same rule in another
    # statute, found by pooling); a hit on one counts like a hit on the gold
    also: list[Gold] = field(default_factory=list)

    # the answer's language and file types are those of the gold documents
    def answer_langs(self, texts: dict[str, DocText]) -> set[str]:
        return {texts[g.doc_id].lang for g in self.gold}

    def file_types(self, texts: dict[str, DocText]) -> set[str]:
        return {texts[g.doc_id].file_type for g in self.gold}


_TEXTS: dict[str, "DocText"] | None = None


def load_items(path: Path, anchored: bool = True) -> list[Item]:
    """The items of a set file, their spans re-anchored in the current canonical texts
    (``anchor``): a parser change that moves text (a table read differently) moves the
    stored offsets with it instead of scoring against the wrong place. A quote no longer
    in its document stops here rather than being scored silently wrong."""
    global _TEXTS
    if anchored and _TEXTS is None:
        _TEXTS = doc_texts()
    items = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            d = json.loads(line)
            spans = {k: [Gold(**g) for g in d.get(k, [])] for k in ("gold", "also")}
            if anchored:
                for k, gs in spans.items():
                    moved = [anchor(_TEXTS[g.doc_id].text, g) for g in gs]
                    if None in moved:
                        bad = gs[moved.index(None)]
                        raise ValueError(
                            f"{d['qid']}: quote not found in {bad.doc_id}: {bad.quote[:60]!r}"
                        )
                    spans[k] = moved
            d["gold"], d["also"] = spans["gold"], spans["also"]
            items.append(Item(**d))
    return items


def save_items(path: Path, items: list[Item]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(asdict(it), ensure_ascii=False) + "\n")


def anchor(text: str, g: Gold) -> Gold | None:
    """The gold span in the current text: as stored if the quote is still there,
    otherwise the occurrence of the quote nearest the old offset; None if it is gone."""
    if text[g.start : g.end] == g.quote:
        return g
    hits, i = [], text.find(g.quote)
    while i >= 0:
        hits.append(i)
        i = text.find(g.quote, i + 1)
    if not hits:
        return None
    s = min(hits, key=lambda h: abs(h - g.start))
    return Gold(g.doc_id, s, s + len(g.quote), g.quote)


FUZZY_MIN = 90  # rapidfuzz partial_ratio, 0-100
# amendment notes inside Korean statutes ("<개정 2010. 7. 12.>", "[본조신설 2009. 3. 12.]"):
# models leave them out when they quote
RE_NOTE = re.compile(
    r"<(?:개정|신설|전문개정|타법개정)[^>]*>|\[(?:본조|전문|제목)[^\]]*\d{4}\.[^\]]*\]"
)


def _squeeze(s: str) -> tuple[str, list[int]]:
    """s without whitespace and amendment notes, and each kept character's offset in s."""
    drop = set()
    for m in RE_NOTE.finditer(s):
        drop.update(range(m.start(), m.end()))
    keep = [i for i, c in enumerate(s) if not c.isspace() and i not in drop]
    return "".join(s[i] for i in keep), keep


def locate(text: str, quote: str) -> tuple[int, int] | None:
    """Where an LLM-quoted passage sits in the text: exact first, then ignoring
    whitespace and amendment notes, then the best approximate match on that squeezed
    form (models drop a parenthesis or swap in a defined term) if it is at least
    FUZZY_MIN similar. The span returned is always the text's own. None when not
    found."""
    i = text.find(quote)
    if i >= 0:
        return i, i + len(quote)
    sq_text, idx = _squeeze(text)
    sq_quote, _ = _squeeze(quote)
    if not sq_quote:
        return None
    j = sq_text.find(sq_quote)
    if j >= 0:
        return idx[j], idx[j + len(sq_quote) - 1] + 1
    if len(sq_quote) < 20:
        return None  # too short to match approximately without false hits
    from rapidfuzz import fuzz  # dev dependency: only the evaluation uses it

    al = fuzz.partial_ratio_alignment(sq_quote, sq_text)
    if al is None or al.score < FUZZY_MIN or al.dest_end <= al.dest_start:
        return None
    return idx[al.dest_start], idx[al.dest_end - 1] + 1


# ---------- scoring ----------


def overlaps(src: dict, g: Gold) -> bool:
    return src["doc_id"] == g.doc_id and src["start"] < g.end and g.start < src["end"]


@dataclass
class Scores:
    """Per-question metrics at two granularities.

    span level: a retrieved chunk is relevant when it overlaps a gold span or an
    ``also`` span. What has to be found is the *units*: a question with one gold span
    has one unit, answered by the gold span or any ``also`` span; a multi question
    has one unit per gold span, each of which has to be found (``also`` spans then
    count as relevant but stand for no unit). Each unit counts once, however many
    chunks cover it.
    doc level: a retrieved chunk is relevant when it is from a gold or ``also`` document.
    """

    span_recall: dict[int, float]  # k -> share of units found in the top k
    span_hit: dict[int, float]  # k -> 1 if a relevant chunk is in the top k
    span_mrr: float  # 1 / rank of the first relevant chunk (0 if none in the list)
    span_ndcg10: float  # binary gain per unit, at the rank it is first found
    doc_hit: dict[int, float]


KS = (1, 3, 5, 10, 20)


def score(retrieved: list[dict], gold: list[Gold], also: list[Gold] = (), ks=KS) -> Scores:
    relevant = [*gold, *also]
    units = [relevant] if len(gold) == 1 else [[g] for g in gold]
    found_at = [  # rank at which each unit is first found
        next((r for r, s in enumerate(retrieved, 1) if any(overlaps(s, g) for g in u)), None)
        for u in units
    ]
    first = next(
        (r for r, s in enumerate(retrieved, 1) if any(overlaps(s, g) for g in relevant)), None
    )
    docs = {g.doc_id for g in relevant}
    doc_rank = next((r for r, s in enumerate(retrieved, 1) if s["doc_id"] in docs), None)
    dcg = sum(found_at.count(r) / math.log2(r + 1) for r in range(1, 11))
    idcg = sum(1 / math.log2(r + 1) for r in range(1, min(len(units), 10) + 1))
    return Scores(
        span_recall={k: sum(1 for f in found_at if f and f <= k) / len(units) for k in ks},
        span_hit={k: float(bool(first and first <= k)) for k in ks},
        span_mrr=1 / first if first else 0.0,
        span_ndcg10=dcg / idcg,
        doc_hit={k: float(bool(doc_rank and doc_rank <= k)) for k in ks},
    )
