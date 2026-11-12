"""Bedrock spend since a point in time, from CloudWatch token metrics (AWS/Bedrock).

Billing data arrives hours late; the token counts are near real time.
Prices: US on-demand list prices per 1M tokens (input, output), as in run_retrieval.

    cd backend && AWS_PROFILE=... uv run python ../eval/spend.py --since "2026-11-12T13:10:00Z"
"""

import argparse
import datetime as dt

import boto3

PRICES = {
    "zai.glm-4.7": (0.60, 2.20),
    "deepseek.v3.2": (0.62, 1.85),
    "qwen.qwen3-next-80b-a3b": (0.15, 1.20),
    "openai.gpt-oss-120b-1:0": (0.15, 0.60),
    "amazon.titan-embed-text-v2:0": (0.02, 0.0),
    "qwen.qwen3-vl-235b-a22b": (0.53, 2.66),
    "amazon.nova-lite-v1:0": (0.06, 0.24),
}


def spend(since: dt.datetime, region: str = "ap-southeast-2") -> dict[str, float]:
    cw = boto3.client("cloudwatch", region_name=region)
    end = dt.datetime.now(dt.UTC)
    out = {}
    for model, (pin, pout) in PRICES.items():
        tokens = {}
        for metric in ("InputTokenCount", "OutputTokenCount"):
            r = cw.get_metric_statistics(Namespace="AWS/Bedrock", MetricName=metric,
                                         Dimensions=[{"Name": "ModelId", "Value": model}],
                                         StartTime=since, EndTime=end, Period=3600,
                                         Statistics=["Sum"])  # fmt: skip
            tokens[metric] = sum(p["Sum"] for p in r["Datapoints"])
        out[model] = (tokens["InputTokenCount"] * pin + tokens["OutputTokenCount"] * pout) / 1e6
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", required=True, help="ISO time, UTC")
    a = ap.parse_args()
    since = dt.datetime.fromisoformat(a.since)
    s = spend(since)
    for m, v in sorted(s.items(), key=lambda x: -x[1]):
        if v > 0.005:
            print(f"{m:32} ${v:6.2f}")
    print(f"{'total':32} ${sum(s.values()):6.2f}")


if __name__ == "__main__":
    main()
