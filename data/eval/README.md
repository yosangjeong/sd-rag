# Retrieval evaluation set

Questions paired with gold answers, as (document, character range) in the document's
canonical text (the parsed blocks joined by blank lines; `eval/evalset.py`). Every
indexed chunk records its own range in the same text, so one gold span scores any
chunking strategy: a retrieved chunk is relevant when its range overlaps a gold range.

| File | Items | Use |
|---|---|---|
| `test.jsonl` | generated, 80% | reported once per system; never used for tuning |
| `dev.jsonl` | generated, 20% | tuning (prompts, weights, thresholds) |
| `real.jsonl` | real user questions | reported next to `test`; never used for tuning |
| `real_unanswerable.jsonl` | real questions the corpus does not answer | the agent should say it does not know |
| `real_questions_candidates.csv` | the real questions as collected | input of `real.jsonl` |
| `SHA256SUMS` | hashes of the four sets | committed before any system is tuned on `dev` |

Counts and breakdowns: see "Composition" below (filled by `eval/finalize_qa.py`).

## Item format (one JSON object per line)

```json
{"qid": "g0164", "question": "In Korea, when must a company establish a labor-management council ...",
 "q_lang": "en",
 "gold": [{"doc_id": "kr-worker-participation-dec", "start": 812, "end": 941, "quote": "제2조(설치범위) ..."}],
 "also": [],
 "kind": "fact", "source": "generated:qwen.qwen3-next-80b-a3b",
 "meta": {"style": "question", "answer": "...", "answer_lang": "ko", "file_type": "pdf", "overlap": 0.0}}
```

- `gold`: spans the answer needs. One for most items; two for `multi` items (an act's
  article and the decree / rule article it delegates to), and both must be found.
- `also`: other spans that answer as fully (the same rule repeated in another statute),
  found by pooling; retrieving one counts like retrieving the gold.
- `quote`: the gold text itself. If a parser change moves the text, `evalset.anchor`
  finds the quote again; an item whose quote is gone is reported, not silently scored.
- `kind`: `fact`, `table` (the value is in a table row), `multi`, `real`.
- `meta.overlap`: share of the question's word (Korean: character) bigrams found in the
  passage, a measure of how much the question copies the text.

## How the generated items were made

1. **Answer first** (`eval/sample_passages.py`): passages are drawn from the canonical
   text (not from the index, which would favor one chunking), per (answer language,
   file type) cell, round-robin over the cell's documents; front matter, 부칙 and
   repealed sections are skipped. 15% table rows, 12% act + decree pairs (Korean),
   and a third (Korean answers) to 45% (English answers) are asked in the other
   language.
2. **Question** (`eval/generate_qa.py`, `qwen.qwen3-next-80b-a3b`): one question per
   passage in a given language and style (full question 50%, 2-6 word query 20%, a
   described situation 30%), in its own words, without article numbers; the country
   is named only when asking in the other language. The model also quotes the
   shortest evidence, which becomes the gold span (located exactly, ignoring
   whitespace and amendment notes, or at least 90% similar).
3. **Check** (`deepseek.v3.2`, another model family): answerable from the passage(s)?
   unambiguous? for `multi`, needs both? Anything short of "yes" is dropped.
4. **Pooling** (`eval/finalize_qa.py`): the top 5 of each of 8 systems (bm25, dense,
   hybrid, per_language x two chunkings) are judged (`deepseek.v3.2`) against the
   reference answer; candidates giving the same answer become `also`.
5. **Cleaning**: an OCR error the generator copied from a scan into its question
   ("용자" for 융자) is fixed, and logged in `meta.edited`; Korean questions with
   Chinese characters (a generation slip) are dropped; a question with the same answer
   as an earlier one in the same language is dropped.
6. **Split**: 20% of each cell to `dev`, 80% to `test` (seeded).

All prompts are in the scripts named above; all model calls are cached under
`data/raw/eval-cache/llm/` (not committed), so the set is reproducible from the cache.

## The real questions

Question titles (no answers) from public FAQ pages, kept verbatim:

- 법제처 찾기쉬운 생활법령정보, 백문백답 (easylaw.go.kr): 9 topics, 92 questions. Free
  use including commercial; source credited here and in `data/SOURCES.md`.
- U.S. Department of Labor, Wage and Hour Division, FMLA and FLSA FAQs (dol.gov): 72
  questions (FMLA questions longer than 125 characters were left out). Public domain.

The pages were read with a fetching tool that returns page text through a summarizing
model; spot checks against the pages matched character for character (including a
typo of the source, "알르바이트"), but not every title was checked by hand.

Gold spans: the same 8-system pool (top 10 each) is judged with the source's
jurisdiction stated (easylaw: Korean law, dol.gov: US federal law; the other
country's law never counts). The best answering passage is `gold`, others `also`.
Questions nothing in the corpus answers (court cases, guidance, laws not in the
corpus) go to `real_unanswerable.jsonl`. Every real question is in its source's own
language, so the real set has no cross-lingual items; cross-lingual retrieval is
measured on the generated set.

## Known limits

- **Pooling**: an answer that no system retrieved stays unknown, so absolute recall
  is an upper bound; comparisons between the pooled systems are fair, a new system
  that finds unpooled answers is underrated.
- **Model-written and model-judged**: generation, check and pooling are models (two
  families); the real set is the check on it: if systems rank the same on both, the
  generated set reflects real questions.
- **English tables**: the only English table is in one Federal Register notice; CFR
  tables have no ruling lines and are parsed as text.
- **English scan**: one document (a short notice), so few items.

## Composition

| | test | dev | real | real_unanswerable |
|---|---|---|---|---|
| items | 338 | 85 | 137 | 27 |
| question -> answer: en -> en | 68 | 16 | 60 | 0 |
| question -> answer: en -> ko | 66 | 21 | 0 | 0 |
| question -> answer: ko -> en | 49 | 13 | 0 | 0 |
| question -> answer: ko -> ko | 155 | 35 | 77 | 0 |
| answer file type: docx | 57 | 15 | 22 | 0 |
| answer file type: docx+hwpx | 3 | 1 | 0 | 0 |
| answer file type: docx+pdf | 4 | 1 | 0 | 0 |
| answer file type: hwpx | 58 | 14 | 17 | 0 |
| answer file type: hwpx+pdf | 2 | 1 | 0 | 0 |
| answer file type: pdf | 160 | 39 | 98 | 0 |
| answer file type: scan | 54 | 14 | 0 | 0 |
| kind: fact | 293 | 75 | 0 | 0 |
| kind: multi | 9 | 3 | 0 | 0 |
| kind: real | 0 | 0 | 137 | 0 |
| kind: table | 36 | 7 | 0 | 0 |
| style: keywords | 66 | 22 | 0 | 0 |
| style: question | 183 | 44 | 0 | 0 |
| style: real | 0 | 0 | 137 | 0 |
| style: situation | 89 | 19 | 0 | 0 |
| with also-spans | 78 | 20 | 57 | 0 |
| gold annotated by hand | 0 | 0 | 4 | 0 |

A real question's language is its source's: easylaw questions are Korean, dol.gov questions English, so the real set has no cross-lingual items.
