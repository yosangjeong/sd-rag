# OCR on a real phone scan (`eval/real_scan.py`)

Engine qwen.qwen3-vl-235b-a22b. 9 pages printed at 100% on A4 and scanned with an iPhone (Notes, document scan, its automatic crop and deskew left on), some on purpose badly. Truth: the page's text in the source PDF. CER counts reading order, so table pages score worse on it than on recall.

| sheet | document | page | content | scanned | CER | recall | extra |
|---|---|---|---|---|---|---|---|
| 1 | kr-labor-standards-law | 4 | 일반 조문 (제26조 해고의 예고) | 반듯하게 | 2.4% | 99.9% | 0.1% |
| 2 | kr-labor-standards-law | 14 | 일반 조문 (제60조 연차 유급휴가) | 조금 비뚤게 | 2.6% | 99.5% | 0.2% |
| 3 | kr-housing-lease-dec | 10 | 표 (별표 1 조정위원회 관할) | 반듯하게 | 0.0% | 100.0% | 0.0% |
| 4 | kr-housing-lease-dec | 11 | 표 (별표 1 이어짐) | 그림자 지게 | 0.0% | 100.0% | 0.0% |
| 5 | kr-occupational-safety-rul | 68 | 표 (별표 2 사업 종류) | 반듯하게 | 15.6% | 99.6% | 13.5% |
| 6 | kr-occupational-safety-rul | 71 | 표 (별표) | 조금 비뚤게 | 0.2% | 99.8% | 0.2% |
| 7 | us-cfr29-825 | 31 | 영어 2단 편집 (§ 825.200) | 반듯하게 | 3.4% | 96.6% | 0.0% |
| 8 | us-usc29-ch8 | 18 | 영어 조문 (§ 207 초과근무) | 어둡게 | 0.7% | 99.3% | 0.1% |
| 9 | kr-labor-standards-law | 28 | 표 (별표, 마지막 쪽) | 반듯하게 | 0.0% | 100.0% | 0.0% |
| **all** | | | | | **2.8%** | 99.4% | 1.6% |
