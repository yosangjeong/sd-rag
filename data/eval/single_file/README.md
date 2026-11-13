# One file: our system vs Claude and ChatGPT

The brief's target is the document search of Claude and ChatGPT on a single file.
`compare.csv` holds 40 test questions whose answer is in one document, each set
spread over 8 cells (PDF, HWPX, DOCX, scan x Korean / English questions): 30 labor
(qid g..., 28 files) and 10 real estate (qid r..., 9 files). `file` is the committed
copy in `data/corpus/` (scans there are image-only PDFs).

| Column | Filled by |
|---|---|
| file, pages, question, reference, gold_quote | `eval/single_file.py select` (labor), `select-re` (real estate, appended) |
| ours, ours_gold_in_sources | `eval/single_file.py ours` (search scoped to the file) |
| claude, chatgpt | by hand, below |

## Filling in Claude and ChatGPT

For each row: open a new chat (claude.ai and chatgpt.com, default model), attach the
file in `file` (paths are relative to the repository root), paste `question`
exactly, and copy the reply into the `claude` / `chatgpt` column. One chat per row,
so no answer sees another file. Note the model names and date at the bottom.

Then: `cd backend && uv run python ../eval/single_file.py grade` grades all three
columns with the same judge (`JUDGE_SYSTEM` in the script, DeepSeek V3.2, a family
used neither for our answers nor for writing the questions).

## Results

| System | set | correct | partial | wrong | no answer | gold passage retrieved |
|---|---|---|---|---|---|---|
| ours (GLM-4.7 answers, served prompts, 2026-11-13) | labor (30) | 77% | 17% | 7% | 0% | 30 / 30 in the top 6 |
| ours | real estate (10) | 80% | 20% | 0% | 0% | 10 / 10 in the top 6 |
| Claude | labor | | | | | |
| Claude | real estate | | | | | |
| ChatGPT | labor | | | | | |
| ChatGPT | real estate | | | | | |
