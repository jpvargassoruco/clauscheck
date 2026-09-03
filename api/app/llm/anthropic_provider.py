from anthropic import AsyncAnthropic

from app.llm.base import LLMError, LLMProviderBase


class AnthropicProvider(LLMProviderBase):
    """Adapter for the Anthropic Messages API. JSON is requested via the system prompt."""

    code = "anthropic"

    def __init__(self, api_key: str, model: str):
        self.model = model
        self._client = AsyncAnthropic(api_key=api_key)

    async def _send(
        self, system: str, user: str, max_tokens: int
    ) -> tuple[str, dict[str, int] | None]:
        system_json = (
            f"{system}\n\n"
            "Responde ÚNICAMENTE con un objeto JSON válido, sin texto adicional, "
            "sin markdown ni bloques de código."
        )
        try:
            resp = await self._client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system_json,
                messages=[{"role": "user", "content": user}],
            )
        except Exception as exc:  # anthropic.APIError and friends
            raise LLMError(f"anthropic: {exc}") from exc

        parts = [block.text for block in resp.content if getattr(block, "type", None) == "text"]
        text = "".join(parts)

        usage = None
        raw_usage = getattr(resp, "usage", None)
        if raw_usage is not None:
            usage = {
                "tokens_in": int(getattr(raw_usage, "input_tokens", 0) or 0),
                "tokens_out": int(getattr(raw_usage, "output_tokens", 0) or 0),
            }
        return text, usage

    async def test_connection(self) -> str:
        try:
            await self._client.messages.create(
                model=self.model,
                max_tokens=1,
                messages=[{"role": "user", "content": "ping"}],
            )
        except Exception as exc:
            raise LLMError(str(exc)) from exc
        return "ok"
