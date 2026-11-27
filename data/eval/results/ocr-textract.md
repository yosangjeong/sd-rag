# Amazon Textract against Qwen3-VL on the OCR bench (`eval/textract_bench.py`, 2026-11-27)

Evaluation only: the service OCR engine stays Qwen3-VL 235B (`ingest/ocr.py`). Textract
AnalyzeDocument with `FeatureTypes=["TABLES"]`, ap-southeast-2, one call per page on the
same page images ingestion renders (200 dpi, grayscale JPEG): the 12 synthetic-scan pages
of `eval/ocr_bench.py` at both quality levels and the 9 sheets of the real iPhone scan
(`eval/real_scan.py`), 33 pages, about $0.5-0.65. Same normalization and scores as the
Qwen3-VL rows (which are the cached transcriptions those scripts measured).

- `textract-lines`: the LINE blocks in the order Textract returns them (the same text
  detection as DetectDocumentText).
- `textract-tables`: the same, with lines inside a detected table replaced by the table as
  `| a | b |` rows.

CER counts reading order; recall and extra (characters in the output not in the truth)
do not. LAYOUT analysis (Textract's reading-order feature) was not used.

### Synthetic scans, office quality (CER / recall / extra, page-weighted mean)

| engine | ko-body | ko-table | en-2col | en-3col | en-table | s/page |
|---|---|---|---|---|---|---|
| qwen3-vl-235b | 2.3% / 99.2% / 0.8% | 0.4% / 99.8% / 0.4% | 3.9% / 97.0% / 0.3% | 7.1% / 97.4% / 0.3% | 9.0% / 96.4% / 0.4% | 14.4 |
| textract-lines | 3.1% / 98.2% / 1.6% | 30.1% / 99.5% / 0.2% | 75.5% / 96.9% / 0.4% | 79.4% / 97.3% / 0.3% | 73.8% / 95.6% / 0.5% | 6.2 |
| textract-tables | 3.1% / 98.2% / 1.6% | 12.3% / 99.5% / 0.2% | 58.7% / 96.9% / 0.4% | 7.2% / 97.3% / 0.3% | 72.4% / 95.6% / 0.5% | 6.2 |

### Synthetic scans, poor quality (CER / recall / extra, page-weighted mean)

| engine | ko-body | ko-table | en-2col | en-3col | en-table | s/page |
|---|---|---|---|---|---|---|
| qwen3-vl-235b | 2.8% / 98.4% / 1.4% | 0.4% / 99.6% / 0.4% | 3.9% / 96.7% / 0.3% | 7.1% / 97.4% / 0.3% | 9.1% / 95.7% / 0.1% | 13.8 |
| textract-lines | 4.4% / 97.0% / 1.9% | 31.3% / 98.6% / 1.2% | 76.1% / 95.8% / 1.6% | 79.4% / 97.1% / 0.5% | 73.8% / 94.0% / 1.2% | 4.9 |
| textract-tables | 5.1% / 97.0% / 1.9% | 11.3% / 98.6% / 1.2% | 58.1% / 95.8% / 1.6% | 7.4% / 97.1% / 0.5% | 73.3% / 94.0% / 1.2% | 4.9 |

### Real iPhone scan, 9 sheets (CER / extra)

| sheet | content | scanned | qwen3-vl-235b | textract-lines | textract-tables |
|---|---|---|---|---|---|
| 1 | 일반 조문 (제26조 해고의 예고) | 반듯하게 | 2.4% / 0.1% | 3.2% / 1.3% | 3.2% / 1.3% |
| 2 | 일반 조문 (제60조 연차 유급휴가) | 조금 비뚤게 | 2.6% / 0.2% | 3.5% / 0.9% | 3.5% / 0.9% |
| 3 | 표 (별표 1 조정위원회 관할) | 반듯하게 | 0.0% / 0.0% | 7.4% / 0.0% | 5.5% / 0.0% |
| 4 | 표 (별표 1 이어짐) | 그림자 지게 | 0.0% / 0.0% | 1.2% / 0.0% | 1.2% / 0.0% |
| 5 | 표 (별표 2 사업 종류) | 반듯하게 | 15.6% / 13.5% | 9.9% / 0.4% | 0.8% / 0.4% |
| 6 | 표 (별표) | 조금 비뚤게 | 0.2% / 0.2% | 31.7% / 0.2% | 24.9% / 0.2% |
| 7 | 영어 2단 편집 (§ 825.200) | 반듯하게 | 3.4% / 0.0% | 73.9% / 0.1% | 73.9% / 0.1% |
| 8 | 영어 조문 (§ 207 초과근무) | 어둡게 | 0.7% / 0.1% | 72.8% / 0.2% | 0.5% / 0.2% |
| 9 | 표 (별표, 마지막 쪽) | 반듯하게 | 0.0% / 0.0% | 0.6% / 0.0% | 0.6% / 0.0% |
| **all** | | | **2.8%** / 1.6% | **22.7%** / 0.3% | **12.7%** / 0.3% |

Textract 2.1 s/page on the real scan (Qwen3-VL: 11.3 s).

## What it shows

- **Characters are recognized about as well**: recall 94-99.5% for Textract against
  95.7-99.8% for Qwen3-VL on every page type. Korean body CER is a little higher with
  Textract (office 3.1% vs 2.3%, poor 4.4-5.1% vs 2.8%; real-scan articles 3.2-3.5% vs 2.4-2.6%).
- **Reading order is where Textract loses**: on English two-column pages its lines run
  across both columns, CER 58-76% (Qwen3-VL 3.9%; real-scan sheet 7: 73.9% vs 3.4%).
  Korean tables in table form: CER 11-12% against 0.4% (cell order and merged cells).
- **It invents less and is faster**: extra 0.3% on the real scan against 1.6% (Qwen3-VL's
  13.5% on sheet 5, a table page, where Textract has 0.4%); 2-6 s per page against 11-14 s.
- **Decision (criteria set before the run)**: mixed, so the engine is kept. Textract is
  better on invented text and speed, worse on reading order, Korean body and Korean tables.
  Improvement on record: Textract with LAYOUT for reading order, or Qwen3-VL as the reader
  with Textract as a check (pages where the two disagree, or Qwen3-VL outputs characters
  Textract does not see, flagged for a second read).
