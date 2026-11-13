# OCR on the corpus scans (`eval/ocr_corpus.py`)

Engine qwen.qwen3-vl-235b-a22b, cached transcriptions the index was built from, against the source page text; page-weighted means. CER counts reading order, so table pages score worse on it than on recall.

| field | document | lang | pages | CER | recall | extra |
|---|---|---|---|---|---|---|
| labor | us-fr-2026-20646 | en | 3 | 9.5% | 96.8% | 0.3% |
| real estate | us-cfr24-100 | en | 25 | 1.4% | 99.8% | 0.0% |
| labor | kr-minimum-wage-rul | ko | 5 | 2.1% | 99.4% | 0.8% |
| labor | kr-equal-employment-dec | ko | 16 | 4.5% | 99.2% | 1.8% |
| labor | kr-wage-claim-rul | ko | 10 | 5.3% | 99.2% | 0.7% |
| real estate | kr-real-estate-transaction-rul | ko | 11 | 3.4% | 99.1% | 0.7% |
| real estate | kr-commercial-lease-dec | ko | 8 | 3.9% | 99.3% | 1.4% |
| **labor** | all | | 34 | **4.8%** | 99.0% | 1.2% |
| **real estate** | all | | 44 | **2.4%** | 99.5% | 0.4% |
