# Unseen-document check (2026-11-12)

A rehearsal of the interview's live test: documents unlike the corpus, uploaded
through the API (`POST /api/documents`, all 8 at once) and asked about with the
default retrieval over everything the user can see (corpus + uploads). The files are
public documents used as test inputs only and are not in the repository.

| File | Kind | Processing | Chunks | Question | Answer, citation |
|---|---|---|---|---|---|
| 1706.03762.pdf (Attention Is All You Need) | two-column paper, tables | 4.7 s | 25 | How many attention heads does the base Transformer model use? / 트랜스포머 논문에서 base 모델의 head 수는? | 8, p.5 (both) |
| fomcminutes20240131.pdf | minutes, long prose | 4.1 s | 29 | What target range for the federal funds rate did the FOMC decide in January 2024? | 5¼-5½ %, p.10 |
| p15.pdf (IRS Circular E) | 70 pages, many tables | 14.3 s | 183 | What is the social security tax rate for employees in 2024? | 6.2 %, p.39 |
| NIST.SP.800-63b.pdf | standard, long | 11.4 s | 109 | What is the minimum length of a memorized secret chosen by the subscriber? | 8 characters, p.24 |
| moel-press.pdf | Korean press release, boxed tables | 0.7 s | 10 | 권리 밖 노동 원탁회의에는 몇 명이 참여했나요? | 605명, p.1 |
| moel-press-scan.pdf | the same, synthetic scan (OCR) | 14.7 s | 9 | (same) | 605명, p.1 (cited with the digital one) |
| benefits-guide.docx | DOCX with heading styles, merged cells | 0.7 s | 4 | 리프레시 휴가는 며칠 주나요? | 10일, "1. 휴가 제도" |
| fw4.pdf (Form W-4) | form | 2.5 s | 16 | W-4 Step 2는 어떤 사람이 작성해야 하나요? | two jobs / both spouses work, p.2 |

8 of 8 correct, 2.7-4.2 s per answer.

Found and fixed by this check (`eval/robustness.py` prints per-file parse stats):

- **Text lost in a boxed table** (press release): pdfplumber found the box but put
  most of its text in no cell; the box was then also excluded from the page text, so
  1,300 of 3,560 characters were missing. Tables whose cells hold under 80% of the
  characters inside them are now read as text (`parse._pdf_tables`). The statute
  table benchmark is unchanged (95.7% / 67.1% in-table, 100% kept) and no corpus
  document's text changed.
- **No headings outside statutes**: DOCX heading styles (Title, Heading N, 제목 N)
  now give the heading path ("1. Leave / 1.1 Annual"). PDFs without statute
  structure are cited by page.
