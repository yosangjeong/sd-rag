"""Upload throughput: send every corpus file in one request, wait until all are indexed.

The brief asks to upload 50+ PDF / DOCX / HWPX files at once and to measure ingestion
throughput and duration. This posts the 53 corpus files (4 of them scans) to a
running API as one multipart request, polls /api/documents until no file is queued
or processing, and reports wall time, files and chunks per minute, and the stage
times recorded by the worker (worker/job.py).

    python eval/upload_bench.py --api http://127.0.0.1:8001 --out data/eval/results/upload-local.json
"""

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend" / "src"))
from sdrag.ingest.corpus import load_corpus  # noqa: E402

DATA = Path(__file__).resolve().parents[1] / "data"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default="http://127.0.0.1:8001")
    ap.add_argument("--user", default="upload-bench")
    ap.add_argument("--token", help="Cognito ID token (deployed API)")
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    headers = {"Authorization": f"Bearer {a.token}"} if a.token else {"X-Dev-User": a.user}
    docs = load_corpus(DATA)
    files = [("files", (f"{d.id}{d.path.suffix}", d.path.read_bytes())) for d in docs]
    size = sum(len(f[1][1]) for f in files)
    with httpx.Client(base_url=a.api, headers=headers, timeout=600) as c:
        t0 = time.time()
        r = c.post("/api/documents", files=files).json()
        t_upload = time.time() - t0
        print(
            f"sent {len(files)} files ({size / 2**20:.0f} MB) in {t_upload:.1f}s; accepted {len(r['accepted'])}"
        )
        ids = {x["id"] for x in r["accepted"]}
        while True:
            mine = [d for d in c.get("/api/documents").json() if d["id"] in ids]
            busy = [d for d in mine if d["status"] in ("queued", "processing")]
            print(
                f"  {time.time() - t0:6.0f}s  done {sum(d['status'] == 'done' for d in mine)}"
                f"  failed {sum(d['status'] == 'failed' for d in mine)}  waiting {len(busy)}",
                flush=True,
            )
            if not busy:
                break
            time.sleep(10)
    wall = max(float(d["finished"]) for d in mine) - t0
    done = [d for d in mine if d["status"] == "done"]
    chunks = sum(int(d["chunks"]) for d in done)
    result = {
        "files": len(files), "megabytes": round(size / 2**20, 1), "done": len(done),
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
