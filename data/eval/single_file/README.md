# One file: our system vs Claude and ChatGPT

The brief's target is the document search of Claude and ChatGPT on a single file.
`compare.csv` holds 30 test questions whose answer is in one document (8 cells: PDF,
HWPX, DOCX, scan x Korean / English questions; 28 different files).

| Column | Filled by |
|---|---|
| file, pages, question, reference, gold_quote | `eval/single_file.py select` |
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

| System | correct | partial | wrong | no answer | gold passage retrieved |
|---|---|---|---|---|---|
| ours (GLM-4.7 answers, 2026-11-12) | 80% | 17% | 3% | 0% | 30 / 30 in the top 6 |
| Claude | | | | | |
| ChatGPT | | | | | |
