# Amazon Textract against Qwen3-VL on the OCR bench (`eval/textract_bench.py`, 2026-11-27)

Evaluation only: the service OCR engine stays Qwen3-VL 235B (`ingest/ocr.py`). Textract
AnalyzeDocument, ap-southeast-2, on the same page images ingestion renders (200 dpi,
grayscale JPEG): the 12 synthetic-scan pages of `eval/ocr_bench.py` at both quality levels
and the 9 sheets of the real iPhone scan (`eval/real_scan.py`), 33 pages. Two calls per
page: `FeatureTypes=["TABLES"]` (about $0.5) and, the same day, `["TABLES", "LAYOUT"]`
(about $0.66 at most). Same normalization and scores as the Qwen3-VL rows (which are the
cached transcriptions those scripts measured).

- `textract-lines`: the LINE blocks in the order Textract returns them (the same text
  detection as DetectDocumentText).
- `textract-tables`: the same, with lines inside a detected table replaced by the table as
  `| a | b |` rows.
- `textract-layout`: lines in the order of the LAYOUT blocks (Textract's reading-order
  analysis), a LAYOUT_TABLE as its table's `| a | b |` rows.

CER counts reading order; recall and extra (characters in the output not in the truth)
do not.

### Synthetic scans, office quality (CER / recall / extra, page-weighted mean)

| engine | ko-body | ko-table | en-2col | en-3col | en-table | s/page |
|---|---|---|---|---|---|---|
| qwen3-vl-235b | 2.3% / 99.2% / 0.8% | 0.4% / 99.8% / 0.4% | 3.9% / 97.0% / 0.3% | 7.1% / 97.4% / 0.3% | 9.0% / 96.4% / 0.4% | 14.4 |
| textract-lines | 3.1% / 98.2% / 1.6% | 30.1% / 99.5% / 0.2% | 75.5% / 96.9% / 0.4% | 79.4% / 97.3% / 0.3% | 73.8% / 95.6% / 0.5% | 6.2 |
| textract-tables | 3.1% / 98.2% / 1.6% | 12.3% / 99.5% / 0.2% | 58.7% / 96.9% / 0.4% | 7.2% / 97.3% / 0.3% | 72.4% / 95.6% / 0.5% | 6.2 |
| textract-layout | 3.1% / 98.2% / 1.6% | 12.3% / 99.5% / 0.2% | 3.6% / 96.9% / 0.4% | 7.2% / 97.3% / 0.3% | 9.1% / 95.6% / 0.5% | 6.4 |

### Synthetic scans, poor quality (CER / recall / extra, page-weighted mean)

| engine | ko-body | ko-table | en-2col | en-3col | en-table | s/page |
|---|---|---|---|---|---|---|
| qwen3-vl-235b | 2.8% / 98.4% / 1.4% | 0.4% / 99.6% / 0.4% | 3.9% / 96.7% / 0.3% | 7.1% / 97.4% / 0.3% | 9.1% / 95.7% / 0.1% | 13.8 |
| textract-lines | 4.4% / 97.0% / 1.9% | 31.3% / 98.6% / 1.2% | 76.1% / 95.8% / 1.6% | 79.4% / 97.1% / 0.5% | 73.8% / 94.0% / 1.2% | 4.9 |
| textract-tables | 5.1% / 97.0% / 1.9% | 11.3% / 98.6% / 1.2% | 58.1% / 95.8% / 1.6% | 7.4% / 97.1% / 0.5% | 73.3% / 94.0% / 1.2% | 4.9 |
| textract-layout | 4.4% / 97.0% / 1.9% | 11.3% / 98.6% / 1.2% | 5.6% / 95.8% / 1.6% | 7.4% / 97.1% / 0.5% | 12.5% / 94.0% / 1.2% | 5.1 |

### Real iPhone scan, 9 sheets (CER / extra)

| sheet | content | scanned | qwen3-vl-235b | textract-lines | textract-tables | textract-layout |
|---|---|---|---|---|---|---|
| 1 | 일반 조문 (제26조 해고의 예고) | 반듯하게 | 2.4% / 0.1% | 3.2% / 1.3% | 3.2% / 1.3% | 3.2% / 1.3% |
| 2 | 일반 조문 (제60조 연차 유급휴가) | 조금 비뚤게 | 2.6% / 0.2% | 3.5% / 0.9% | 3.5% / 0.9% | 3.5% / 0.9% |
| 3 | 표 (별표 1 조정위원회 관할) | 반듯하게 | 0.0% / 0.0% | 7.4% / 0.0% | 5.5% / 0.0% | 5.5% / 0.0% |
| 4 | 표 (별표 1 이어짐) | 그림자 지게 | 0.0% / 0.0% | 1.2% / 0.0% | 1.2% / 0.0% | 1.2% / 0.0% |
| 5 | 표 (별표 2 사업 종류) | 반듯하게 | 15.6% / 13.5% | 9.9% / 0.4% | 0.8% / 0.4% | 0.8% / 0.4% |
| 6 | 표 (별표) | 조금 비뚤게 | 0.2% / 0.2% | 31.7% / 0.2% | 24.9% / 0.2% | 24.9% / 0.2% |
| 7 | 영어 2단 편집 (§ 825.200) | 반듯하게 | 3.4% / 0.0% | 73.9% / 0.1% | 73.9% / 0.1% | 3.5% / 0.1% |
| 8 | 영어 조문 (§ 207 초과근무) | 어둡게 | 0.7% / 0.1% | 72.8% / 0.2% | 0.5% / 0.2% | 0.5% / 0.2% |
| 9 | 표 (별표, 마지막 쪽) | 반듯하게 | 0.0% / 0.0% | 0.6% / 0.0% | 0.6% / 0.0% | 0.6% / 0.0% |
| **all** | | | **2.8%** / 1.6% | **22.7%** / 0.3% | **12.7%** / 0.3% | **4.9%** / 0.3% |

Textract 2.1 s/page on the real scan, with LAYOUT 2.6 s (Qwen3-VL: 11.3 s).

## What it shows

- **Characters are recognized about as well**: recall 94-99.5% for Textract against
  95.7-99.8% for Qwen3-VL on every page type.
- **LAYOUT fixes most of the reading order**: English two-column CER 3.6-5.6% (without it
  58-76%; Qwen3-VL 3.9%), English tables 9.1-12.5% (Qwen3-VL 9.0-9.1%), real-scan sheet 7
  3.5% (Qwen3-VL 3.4%). Real scan overall 4.9% against 2.8%.
- **Korean is still behind**: body 3.1-4.4% against 2.3-2.8% (real-scan articles 3.2-3.5%
  against 2.4-2.6%), tables 11-12% against 0.4% (real-scan sheet 6: 24.9% against 0.2%;
  cell order and merged cells). LAYOUT changes nothing on the Korean pages.
- **It invents less and is faster**: extra 0.3% on the real scan against 1.6% (Qwen3-VL's
  13.5% on sheet 5, a table page, where Textract has 0.4%); 2-6 s per page against 11-14 s.
- **Decision (criteria set before the run)**: Qwen3-VL is ahead on the real scan, Korean
  body and Korean tables, with and without LAYOUT, so the engine is kept.

## Textract as a check on Qwen3-VL

Simulated from the outputs above, no new calls: if a page were flagged for a second read
when the two engines disagree, which of Qwen3-VL's bad pages (CER over 5%) would be caught?
33 pages is a small sample; read the counts as a direction, not a rate.

### Textract as a check on Qwen3-VL (33 pages, 9 with Qwen3-VL CER over 5%)

| flag a page when | flagged | of them Qwen3-VL CER > 5% (caught) | missed bad pages | good pages flagged |
|---|---|---|---|---|
| edit distance Qwen3-VL vs Textract > 3% | 11 | 3 | 6 | 8 |
| edit distance Qwen3-VL vs Textract > 5% | 8 | 3 | 6 | 5 |
| edit distance Qwen3-VL vs Textract > 10% | 4 | 1 | 8 | 3 |
| Qwen3-VL characters Textract lacks > 3% | 3 | 2 | 7 | 1 |
| Qwen3-VL characters Textract lacks > 5% | 1 | 1 | 8 | 0 |
| Qwen3-VL characters Textract lacks > 10% | 1 | 1 | 8 | 0 |

| page | Qwen3-VL CER | diff | only |
|---|---|---|---|
| real sheet 5 | 15.6% | 13.5% | 13.5% |
| poor us-fr-2026-20646 p1 | 12.8% | 1.8% | 1.5% |
| office us-fr-2026-20646 p1 | 12.5% | 1.6% | 1.2% |
| poor us-fr-2026-20646 p2 | 7.1% | 0.7% | 0.7% |
| office us-fr-2026-20646 p2 | 7.1% | 0.4% | 0.4% |
| poor us-cfr29-541 p4 | 6.3% | 5.4% | 2.8% |
| office us-cfr29-541 p4 | 6.2% | 2.1% | 0.7% |
| office us-cfr29-778 p36 | 5.5% | 1.9% | 1.5% |
| poor us-cfr29-778 p36 | 5.4% | 8.3% | 4.1% |
| office kr-occupational-safety-rul p71 | 0.8% | 29.9% | 0.8% |
| office kr-occupational-safety-rul p96 | 0.5% | 6.2% | 0.3% |
| poor kr-occupational-safety-rul p71 | 0.2% | 27.9% | 0.5% |
| real sheet 6 | 0.2% | 24.7% | 0.2% |
| real sheet 3 | 0.0% | 5.5% | 0.3% |

- **Order-insensitive disagreement ("Qwen3-VL characters Textract lacks") finds invented
  text**: over 5% it flags one page, real-scan sheet 5, the page where Qwen3-VL wrote 13.5%
  of characters that are not on the page, and no good page.
- **It does not find Qwen3-VL's other high-CER pages**: those are English tables and a
  three-column page where Textract reads the same characters (disagreement under 2%); their
  CER comes from the order against the source text, which Textract shares.
- **Edit-distance disagreement flags Korean table pages Qwen3-VL read correctly** (sheet 6,
  p71: 25-30% apart, Qwen3-VL CER under 1%): there Textract is the one out of order.
- So the useful check is narrow: Textract as a detector of invented characters, a second
  read when more than a few percent of Qwen3-VL's characters are not in Textract's output.
  It costs one Textract call per scanned page (2-6 s, run alongside).
