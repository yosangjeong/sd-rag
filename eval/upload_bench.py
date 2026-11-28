"""Upload throughput: send every corpus file at once, wait until all are indexed.

The brief asks to upload 50+ PDF / DOCX / HWPX files at once and to measure ingestion
throughput and duration. This posts the corpus files (70 since the real-estate statutes; 53 before) to a
running API, polls /api/documents until no file is queued or processing, and reports wall
time, files and chunks per minute, and the stage times recorded by the worker
(worker/job.py).

The API takes at most 100 files per user per day (api/main.py MAX_DAY_FILES): a larger
set is split evenly over several accounts (--token or --user, repeated), one multipart
request each, all sent at the same time; the queue and the workers are shared. The corpus
(70) fits one account, as on 11/26.

    cd backend && uv run python ../eval/upload_bench.py --api http://127.0.0.1:8001 \
        --out ../data/eval/results/upload/upload-local.json
    # deployed: an account that is not an evaluator's (infra/scripts/id_token.sh)
    uv run python ../eval/upload_bench.py --api https://<site> --token "$T"
"""

import argparse
import json
import math
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx

from sdrag.ingest.corpus import load_corpus

DATA = Path(__file__).resolve().parents[1] / "data"


PER_ACCOUNT = 100  # the API's daily limit per user (api/main.py MAX_DAY_FILES)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default="http://127.0.0.1:8001")
    ap.add_argument(
        "--user", action="append", help="local dev user (repeat); default upload-bench-N"
    )
    ap.add_argument("--token", action="append", help="Cognito ID token, one per account (repeat)")
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    docs = load_corpus(DATA)
    files = [("files", (f"{d.id}{d.path.suffix}", d.path.read_bytes())) for d in docs]
    size = sum(len(f[1][1]) for f in files)
    if a.token:
        accounts = [{"Authorization": f"Bearer {t}"} for t in a.token]
    else:
        users = a.user or [
            f"upload-bench-{i + 1}" for i in range(math.ceil(len(files) / PER_ACCOUNT))
        ]
        accounts = [{"X-Dev-User": u} for u in users]
    n = len(accounts)
    if len(files) > n * PER_ACCOUNT:
        raise SystemExit(
            f"{len(files)} files need {math.ceil(len(files) / PER_ACCOUNT)} accounts, got {n}"
        )
    parts = [files[i::n] for i in range(n)]  # even split, at most PER_ACCOUNT each
    clients = [httpx.Client(base_url=a.api, headers=h, timeout=600) for h in accounts]
    try:
        t0 = time.time()

        def send(i: int) -> dict:
            return clients[i].post("/api/documents", files=parts[i]).json()

        with ThreadPoolExecutor(n) as pool:
            replies = list(pool.map(send, range(n)))
        t_upload = time.time() - t0
        rejected = [x for r in replies for x in r["rejected"]]
        print(
            f"sent {len(files)} files ({size / 2**20:.0f} MB) over {n} accounts in {t_upload:.1f}s;"
            f" accepted {sum(len(r['accepted']) for r in replies)}, rejected {rejected}"
        )
        ids = [{x["id"] for x in r["accepted"]} for r in replies]
        while True:
            mine = [d for c, own in zip(clients, ids, strict=True)
                    for d in c.get("/api/documents").json() if d["id"] in own]  # fmt: skip
            busy = [d for d in mine if d["status"] in ("queued", "processing")]
            print(
                f"  {time.time() - t0:6.0f}s  done {sum(d['status'] == 'done' for d in mine)}"
                f"  failed {sum(d['status'] == 'failed' for d in mine)}  waiting {len(busy)}",
                flush=True,
            )
            if not busy:
                break
            time.sleep(10)
    finally:
        for c in clients:
            c.close()
    wall = max(float(d["finished"]) for d in mine) - t0
    done = [d for d in mine if d["status"] == "done"]
    chunks = sum(int(d["chunks"]) for d in done)
    result = {
        "files": len(files), "accounts": n, "rejected": len(rejected), "megabytes": round(size / 2**20, 1), "done": len(done),
        "failed": [d["file"] + ": " + d.get("error", "") for d in mine if d["status"] == "failed"],
        "chunks": chunks, "wall_s": round(wall), "upload_s": round(t_upload, 1),
        "files_per_min": round(len(done) / wall * 60, 1), "chunks_per_min": round(chunks / wall * 60),
        "median_parse_s": statistics.median(float(d["parse_s"]) for d in done),
        "median_embed_s": statistics.median(float(d["embed_s"]) for d in done),
        "slowest": sorted(((d["file"], float(d["parse_s"]) + float(d["embed_s"]) + float(d["index_s"]))
                           for d in done), key=lambda x: -x[1])[:5],
        "ocr_pages": sum(int(d.get("ocr_pages", 0)) for d in done),
    }  # fmt: skip
    print(json.dumps(result, indent=1, ensure_ascii=False))
    if a.out:
        a.out.write_text(json.dumps(result, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
