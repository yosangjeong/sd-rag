# One file: our system vs Claude and ChatGPT

The brief's target is the document search of Claude and ChatGPT on a single file.
`compare.csv` holds 50 test questions whose answer is in one document, each set
spread over 8 cells (PDF, HWPX, DOCX, scan x Korean / English questions): 30 labor
(qid g..., 28 files) and 20 real estate (qid r..., 16 files). `file` is the committed
copy in `data/corpus/` (scans there are image-only PDFs).

| Column | Filled by |
|---|---|
| file, pages, question, reference, gold_quote | `eval/single_file.py select` (labor), `select-re` (real estate, appended) |
| ours, ours_gold_in_sources | `eval/single_file.py ours` (search scoped to the file) |
| claude, chatgpt | by hand, below |

## Filling in Claude and ChatGPT

Fill the 20 rows listed in `subset20.json` (chosen on 2026-11-16 before any Claude or ChatGPT answer was seen: one per field x file type x question language, plus one labor row per file type; flagged items left out). The other 30 can stay empty.

For each row: open a new chat (claude.ai and chatgpt.com, default model), attach the
file in `file` (paths are relative to the repository root), paste `question`
exactly, and copy the reply into the `claude` / `chatgpt` column. One chat per row,
so no answer sees another file. Re-running `select-re` keeps every filled answer. Note the model names and date at the bottom.

Then: `cd backend && uv run python ../eval/single_file.py grade` grades all three
columns with the same judge (`JUDGE_SYSTEM` in the script, DeepSeek V3.2, a family
used neither for our answers nor for writing the questions).

## Results

| System | set | correct | partial | wrong | no answer | gold passage retrieved |
|---|---|---|---|---|---|---|
| ours (GLM-4.7 answers, served prompts, 2026-11-13) | labor (30) | 77% | 17% | 7% | 0% | 30 / 30 in the top 6 |
| ours | real estate (20) | 80% | 20% | 0% | 0% | 20 / 20 in the top 6 |

### The 20 rows answered by all (2026-11-16)

Claude: claude.ai, Sonnet 5.5; ChatGPT: chatgpt.com, GPT-6; default model, one new chat
per row, the file attached, on 2026-11-16 (Monday). The 20 rows were chosen before any of
their answers was seen (`subset20.json`).

Steps, all reproducible from the files here:

1. References checked against the whole articles before grading (`fixes20.json`): 5 of 20
   corrected (g0597 answered a question its sentence does not govern; r0176 was written
   from the association-inspection article for a broker-inspection question: already noted
   in the judge check of 2026-11-13 (`judge-agreement.md`, v6 item 1) but never applied to
   the set; missed in today's audit, applied after the answers came in, so shown both ways; g0276 벌금 -> 과태료; r0037 and g0274 completed).
2. `ours_now`: the served code path (`service.RagService.ask`, scoped to the file), code
   as committed before the Claude / ChatGPT answers were seen (`ours20_now.json`). The
   `ours` column is the 2026-11-13 run through the older retrieval path, kept as it was.
3. `grade-full`: judge v2 with the corrected reference and the whole articles as the
   passage (`grades20.json`; `--skip-fix r0176` gives the grades before that fix,
   `grades20-skip-r0176.json`).
4. Every item with a non-correct grade re-read against the statutes by Claude Code (not
   blind: it knew which system wrote which answer), all four answers of it (`regrade20.json`: 15 of 80 grades changed, each with its reason).

correct / partial / wrong of 20:

| System | judge, r0176 as first written | judge | after the re-read |
|---|---|---|---|
| ours, 2026-11-13 run | 15 / 4 / 1 | 16 / 3 / 1 | **20 / 0 / 0** |
| ours, served code (2026-11-16) | 14 / 4 / 2 | 15 / 3 / 2 | **19 / 1 / 0** |
| Claude (Sonnet 5.5) | 16 / 1 / 3 | 17 / 1 / 2 | **20 / 0 / 0** |
| ChatGPT (GPT-6) | 16 / 2 / 2 | 16 / 3 / 1 | **19 / 0 / 1** |

On one file all four answer nearly every question; with 20 questions a difference of one is
noise. What remains: ChatGPT gave the amount of the next row of a fine table (g0276, 200만원
for 300만원); our served answer opened a yes/no question with "No" against its own body
(g0143, the reversal pattern also seen in r0082), and glossed 권리금 as "Jeonsegeum" (r0037).
The judge's 15 errors came from the passage it sees (a table split over chunks, a
neighbouring article such as an exemption or Article 16), not from the answers. Claude's and
ChatGPT's answers are much longer (median characters: Claude 1,065, ChatGPT 624, ours 157 /
175) and add context from outside the file (Claude cited web pages for r0037's thresholds).

