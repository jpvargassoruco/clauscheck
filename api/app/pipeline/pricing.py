"""Per-provider/model USD pricing table (HLD §5 "record ... costo_usd").

Prices are USD per 1,000,000 tokens, approximate (checked 2026-09), used only
for cost tracking/estimates — never for billing. Unknown provider/model
combinations cost 0 USD so the pipeline never blocks on a missing price.
"""

# (provider_code, model) -> (usd_per_1m_input, usd_per_1m_output)
_PRICING: dict[tuple[str, str], tuple[float, float]] = {
    ("deepseek", "deepseek-chat"): (0.27, 1.10),
    ("deepseek", "deepseek-reasoner"): (0.55, 2.19),
    ("moonshot", "moonshot-v1-8k"): (0.20, 2.00),
    ("moonshot", "moonshot-v1-32k"): (0.24, 2.40),
    ("moonshot", "moonshot-v1-128k"): (0.60, 3.00),
    ("anthropic", "claude-3-5-haiku-latest"): (0.80, 4.00),
    ("anthropic", "claude-3-5-sonnet-latest"): (3.00, 15.00),
    ("fake", "fake-model"): (0.0, 0.0),
}


def cost_usd(provider_code: str, model: str, tokens_in: int, tokens_out: int) -> float:
    """Return the USD cost for `tokens_in`/`tokens_out` on `provider_code`/`model`.

    Defaults to 0.0 for OpenRouter (its price varies per upstream model, not
    worth hardcoding) and any other unlisted provider/model.
    """
    price_in, price_out = _PRICING.get((provider_code, model), (0.0, 0.0))
    return round((tokens_in / 1_000_000) * price_in + (tokens_out / 1_000_000) * price_out, 6)


def estimate_tokens_from_palabras(palabras: int) -> int:
    """Rough end-to-end token estimate for a full 7-stage analysis run.

    The document text/clauses are read by several LLM stages (2, 3, 4, 5,
    7), so total input token volume is a multiple of a single ~1.3
    tokens/word pass — used only for the pre-flight `GET
    /documents/{id}/estimate`, never for billing.
    """
    return int(palabras * 1.3 * 3)


def estimate_cost_usd(provider_code: str, model: str, palabras: int) -> float:
    tokens = estimate_tokens_from_palabras(palabras)
    tokens_in = int(tokens * 0.85)
    tokens_out = tokens - tokens_in
    return cost_usd(provider_code, model, tokens_in, tokens_out)


def costo_bs(costo_usd: float, usd_bob: float) -> float:
    return round(costo_usd * usd_bob, 4)
