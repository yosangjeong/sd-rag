"""On-demand list prices for the cost estimate in the logs: USD per 1M tokens
(input, output), ap-southeast-2, AWS Price List API, 2026-11-14 (the same table as
eval/run_retrieval.py). An estimate: the bill is in AWS Billing; tokens are logged too."""

PRICES = {
    "zai.glm-4.7": (0.62, 2.27),
    "amazon.titan-embed-text-v2:0": (0.02, 0.0),
    "qwen.qwen3-vl-235b-a22b": (0.53, 2.66),  # OCR
}


def cost_usd(model: str, input_tokens: int, output_tokens: int) -> float | None:
    """None for a model not in the table (it is not guessed)."""
    if model not in PRICES:
        return None
    pin, pout = PRICES[model]
    return round((input_tokens * pin + output_tokens * pout) / 1e6, 6)
