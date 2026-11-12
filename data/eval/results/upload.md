# Upload throughput (`eval/upload_bench.py`)

All corpus files in one multipart request to `POST /api/documents`, then polling
`/api/documents` until nothing is queued or processing. Wall time is from the request
to the last file's finish; scanned pages are OCR'd for real (the worker has no cache).

| Run | Where | Files | Done | Wall | Files/min | OCR pages | Notes |
|---|---|---|---|---|---|---|---|
| 1 | local, 4 threads, OpenSearch in Docker | 53 (36 MB) | 53 | 154 s | 20.7 | 34 | `upload-local.json` |
| 2 | AWS, worker 0 -> 3 tasks on the queue alarm, t3.medium.search | 53 | 53 | 429 s | 7.4 | 34 | first file done at 287 s: the 5-minute queue alarm |
| 3 | AWS, + API wakes the worker | 53 | 53 (52 at 333 s) | 2,197 s | - | 34 | scale-in stopped the task holding the last file; it came back after the 30-min visibility timeout |
| 4 | AWS, + scale-in protection, up to 4 tasks, t3.small.search | 70 (66 MB) | 63 | 517 s | 7.3 | 78 | 7 failed with 429 / 502 from the search node: four bulk writers at once |

After run 4: bulk writes retry with backoff, busy failures are redelivered after a
minute (dead-letter queue after 3), at most two workers (`docs/decisions.md`,
deployment rehearsal). To be measured again on the final deployment.

Per file (run 4, median): parse 0.36 s, embed 0.55 s; the slowest files are scans
(OCR at about 14 s a page, 4 pages at a time per worker).
