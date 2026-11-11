"""Split a ParsedDocument into chunks for indexing.

Two strategies, compared in the ablation:

- ``structure``: one chunk per statute article / annex / US section (the block
  ``heading`` from parse.py). Units over the size limit are split at the most
  meaningful boundary that works: paragraph (①, (a)) > item (1., (1)) > line >
  sentence > hard cut. Tables are split by rows and every piece after the first
  repeats the header row, so a cell still reads against its column name.
- ``fixed``: fixed-size windows with overlap over the whole text, ignoring
  structure (the usual baseline).

Both cut the same *canonical text*: the document's blocks joined by "\\n\\n".
Every chunk records its [start, end) offsets in that text, so an eval answer
span (document + character range) is written once and scored against either
strategy by overlap, instead of being tied to one strategy's chunk ids.

Sizes are in *estimated tokens* (``est_tokens``), not characters: a Hangul
syllable is about one token while English averages about four characters per
token, so a character budget would give Korean chunks ~3x the tokens of
English ones.
"""

import bisect
import math
import re
from dataclasses import dataclass
from typing import Literal

from sdrag.ingest.parse import ParsedDocument

SEP = "\n\n"

# split levels for an over-long unit, most meaningful first; each matches the
# whitespace a cut may replace, and the cut goes right after it
LEVELS = [
    re.compile(r"\n(?=\s*[①-⑳])|\n(?=\s*\([a-z]\)\s)"),  # 항 ① / US (a)
    re.compile(r"\n(?=\s*\d+\.\s)|\n(?=\s*\(\d+\)\s)"),  # 호 1. / US (1)
    re.compile(r"\n"),
    re.compile(r"(?<=[.?!다])\s"),  # sentence end (Korean statutes end in "~다.")
]


def _cost(c: str) -> float:
    return 1.0 if "가" <= c <= "힣" else 0.25  # Hangul syllables U+AC00..U+D7A3


MIN_TOKENS = 40  # pieces below this are joined to a neighbour when possible


def est_tokens(text: str) -> int:
    return math.ceil(sum(_cost(c) for c in text))


def _advance(text: str, pos: int, end: int, tokens: int) -> int:
    """Furthest offset (<= end) such that text[pos:offset] fits in `tokens`."""
    used = 0.0
    while pos < end and used + _cost(text[pos]) <= tokens:
        used += _cost(text[pos])
        pos += 1
    return pos


def _snap_back(text: str, lo: int, i: int) -> int:
    """Move cut i back to just after the last whitespace, if that loses at most a fifth."""
    j = max(text.rfind(" ", lo, i), text.rfind("\n", lo, i))
    return j + 1 if j >= 0 and j + 1 >= lo + (i - lo) * 4 // 5 else i


@dataclass
class Chunk:
    doc_id: str
    index: int
    text: str  # canonical[start:end]; table pieces after the first also repeat the header row
    start: int
    end: int
    kind: Literal["text", "table"]
    heading: str | None  # 제N조(...), [별표 N], § 541.100 ... (heading of the first block)
    page_start: int | None = None  # PDF only
    page_end: int | None = None

    @property
    def id(self) -> str:
        return f"{self.doc_id}#{self.index}"


def canonical_text(doc: ParsedDocument) -> tuple[str, list[int]]:
    """The blocks joined by SEP, and each block's start offset in it."""
    starts, pos = [], 0
    for b in doc.blocks:
        starts.append(pos)
        pos += len(b.text) + len(SEP)
    return SEP.join(b.text for b in doc.blocks), starts


def embed_input(chunk: Chunk, title: str) -> str:
    """Text sent to the embedding model (and to BM25): statute bodies rarely name their
    statute, so without this header '시행령 제4조' and '시행규칙 제4조' look the same."""
    head = f"{title} > {chunk.heading}" if chunk.heading else title
    return f"{head}\n{chunk.text}"


class _Doc:
    """Offset lookups shared by both strategies."""

    def __init__(self, doc: ParsedDocument, doc_id: str):
        self.doc, self.doc_id = doc, doc_id
        self.text, self.starts = canonical_text(doc)
        self.chunks: list[Chunk] = []

    def block_at(self, offset: int) -> int:
        return max(0, bisect.bisect_right(self.starts, offset) - 1)

    def emit(self, s: int, e: int, prefix: str = "", heading: str | None = None) -> None:
        # trim whitespace (block separators) at the edges so spans hold content only
        while s < e and self.text[s].isspace():
            s += 1
        while e > s and self.text[e - 1].isspace():
            e -= 1
        if s == e:
            return
        first, last = self.doc.blocks[self.block_at(s)], self.doc.blocks[self.block_at(e - 1)]
        self.chunks.append(
            Chunk(
                self.doc_id,
                len(self.chunks),
                prefix + self.text[s:e],
                s,
                e,
                first.kind,
                heading or first.heading,
                first.page,
                last.page,
            )
        )


# ---------- structure ----------


def _hard_cut(text: str, s: int, e: int, max_tokens: int) -> list[tuple[int, int]]:
    out = []
    while s < e:
        cut = max(_advance(text, s, e, max_tokens), s + 1)
        out.append((s, cut))
        s = cut
    return out


def split_span(text: str, s: int, e: int, max_tokens: int, level: int = 0) -> list[tuple[int, int]]:
    """Cut text[s:e] into consecutive spans of at most max_tokens, preferring LEVELS[level]
    boundaries and falling back to finer ones only for pieces that are still too long."""
    if est_tokens(text[s:e]) <= max_tokens:
        return [(s, e)]
    if level == len(LEVELS):
        return _hard_cut(text, s, e, max_tokens)
    cuts = [m.end() for m in LEVELS[level].finditer(text, s, e) if s < m.end() < e]
    if not cuts:
        return split_span(text, s, e, max_tokens, level + 1)
    segments = list(zip([s, *cuts], [*cuts, e]))
    out: list[tuple[int, int]] = []
    cur_s, cur_e = segments[0]
    for seg_s, seg_e in segments[1:]:
        if (
            est_tokens(text[cur_s:seg_e]) <= max_tokens
            or est_tokens(text[cur_s:cur_e]) < MIN_TOKENS
        ):
            # greedy: grow the current piece while it fits; a tiny piece (a section's
            # title line before a long "(a)") is never left alone: it goes with the next
            # segment, and the finer level below splits the two where they fit
            cur_e = seg_e
        else:
            out += split_span(text, cur_s, cur_e, max_tokens, level + 1)
            cur_s, cur_e = seg_s, seg_e
    return out + split_span(text, cur_s, cur_e, max_tokens, level + 1)


def _units(d: _Doc) -> list[tuple[int, int, bool]]:
    """(first block, last block, is_table): consecutive text blocks under the same heading
    form one unit; each table is a unit of its own."""
    units: list[tuple[int, int, bool]] = []
    for i, b in enumerate(d.doc.blocks):
        prev = d.doc.blocks[i - 1] if i else None
        if (
            b.kind == "text"
            and prev is not None
            and prev.kind == "text"
            and prev.heading == b.heading
            and not units[-1][2]
        ):
            units[-1] = (units[-1][0], i, False)
        else:
            units.append((i, i, b.kind == "table"))
    return units


def header_rows(rows: list[list[str]]) -> int:
    """How many leading rows to repeat: the first, plus the next while the row above has
    empty (merged) cells, i.e. its heading continues below: a title row spanning the
    table, or "과태료 금액(만원)" over "1차 위반 | 2차 위반 | 3차 이상 위반". At most 3,
    and at least one data row is left."""
    k = 1
    while k < min(3, len(rows) - 1) and "" in rows[k - 1]:
        k += 1
    return k


def _split_table(d: _Doc, i: int, max_tokens: int) -> None:
    """Rows are the lines of the block text (parse.table_text writes one row per line)."""
    s0 = d.starts[i]
    block = d.doc.blocks[i]
    text = block.text
    if est_tokens(text) <= max_tokens:
        d.emit(s0, s0 + len(text))
        return
    lines = text.split("\n")
    header = "".join(ln + "\n" for ln in lines[: header_rows(block.rows or [[]])])
    if est_tokens(header) > max_tokens // 2:
        header = ""  # a huge header is a title box, not column names; don't repeat it
    budget = max_tokens - est_tokens(header)
    row_starts = [s0]
    for ln in lines:
        row_starts.append(row_starts[-1] + len(ln) + 1)
    cur_s = row_starts[0]
    for r in range(1, len(lines) + 1):
        piece_end = row_starts[r] - 1  # end of row r-1, without its newline
        if r < len(lines) and est_tokens(d.text[cur_s : row_starts[r + 1] - 1]) <= budget:
            continue  # row r still fits in the current piece
        for ps, pe in split_span(d.text, cur_s, piece_end, budget, level=3):
            d.emit(ps, pe, prefix="" if ps == s0 else header)
        cur_s = row_starts[r]


def chunk_structure(doc: ParsedDocument, doc_id: str, max_tokens: int = 500) -> list[Chunk]:
    d = _Doc(doc, doc_id)
    for first, last, is_table in _units(d):
        if is_table:
            _split_table(d, first, max_tokens)
            continue
        s = d.starts[first]
        e = d.starts[last] + len(doc.blocks[last].text)
        for ps, pe in split_span(d.text, s, e, max_tokens):
            d.emit(ps, pe)
    return _merge_neighbours(d, max_tokens)


def _norm(x: str | None) -> str:
    return re.sub(r"\W+", "", x or "")


def _merge_neighbours(d: _Doc, max_tokens: int) -> list[Chunk]:
    """Re-join neighbouring pieces under the same heading when together they still fit.
    Splitting is recursive, so leftovers from different levels are never packed together
    (제2조: the tail of ① split by items, then ②); and an annex's title line is a text
    unit while its table is a unit of its own. Pieces that repeat a table header row
    can only absorb what follows them, never be absorbed.

    A chunk that is nothing but its heading line ("IV. Procedural and Other Matters"
    right before "A. Review ...", "SUPPLEMENTARY INFORMATION:") is joined to the next
    chunk whatever that one's heading, and the merged chunk takes the next heading,
    which names the parent anyway ("IV. ... / A. Review ...")."""
    out: list[Chunk] = []
    for c in d.chunks:
        prev = out[-1] if out else None
        plain = c.text == d.text[c.start : c.end]
        if prev is not None and plain:
            heading_only = prev.heading is not None and _norm(prev.text) == _norm(prev.heading)
            text = prev.text + d.text[prev.end : c.end]
            if (prev.heading == c.heading or heading_only) and est_tokens(text) <= max_tokens:
                prev.text, prev.end, prev.page_end = text, c.end, c.page_end
                prev.heading = c.heading
                if c.kind == "table":
                    prev.kind = "table"
                continue
        out.append(c)
    for i, c in enumerate(out):
        c.index = i
    return out


# ---------- fixed ----------


def chunk_fixed(
    doc: ParsedDocument, doc_id: str, size: int = 400, overlap: int = 60
) -> list[Chunk]:
    """Windows of `size` tokens, each starting `size - overlap` tokens after the previous
    one; cuts snap back to whitespace so words stay whole."""
    d = _Doc(doc, doc_id)
    text, n, pos = d.text, len(d.text), 0
    while pos < n:
        end = _advance(text, pos, n, size)
        if end < n:
            end = _snap_back(text, pos, end)
        d.emit(pos, end)
        if end >= n:
            break
        nxt = _snap_back(text, pos, _advance(text, pos, n, size - overlap))
        pos = nxt if nxt > pos else end  # always make progress
    return d.chunks


STRATEGIES = {"structure": chunk_structure, "fixed": chunk_fixed}
