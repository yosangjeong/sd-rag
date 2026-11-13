"""CI gate: fail when retrieval on a dev set falls below the committed baseline.

    python eval/gate.py <summary.json of this run> data/eval/baseline-dev.json
    python eval/gate.py <summary.json of this run> data/eval/baseline-dev_re.json

The baseline holds, per system, the metrics and optionally a tolerance. One labor dev
question is 1/85 = 0.012 of hit@10, and LLM reranking varies a little between runs,
so a drop counts only beyond TOLERANCE; the real-estate dev set has 21 questions
(0.048 each), so its baseline allows one question. Raise the baseline (commit a new
one) when a change improves it.
"""

import json
import sys
from pathlib import Path

TOLERANCE = 0.03
METRICS = ("span_hit@10", "span_mrr")


def main() -> None:
    run, base = (json.loads(Path(p).read_text("utf-8")) for p in sys.argv[1:3])
    failed = False
    for system, metrics in base.items():
        got = run.get(system, {}).get("all=all")
        if got is None:
            print(f"FAIL {system}: not in this run")
            failed = True
            continue
        tolerance = metrics.get("tolerance", TOLERANCE)
        for m in METRICS:
            ok = got[m] >= metrics[m] - tolerance
            failed |= not ok
            print(
                f"{'ok  ' if ok else 'FAIL'} {system} {m}: {got[m]:.3f} (baseline {metrics[m]:.3f})"
            )
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
