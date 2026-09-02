"""Deterministic fake LLM provider used in tests (no network calls)."""

from typing import Any

from app.llm.base import LLMProviderBase


class FakeProvider(LLMProviderBase):
    code = "fake"
    model = "fake-model"

    def __init__(self, response: dict[str, Any] | None = None):
        self._response = response or {}

    async def _send(self, system: str, user: str, max_tokens: int) -> str:  # pragma: no cover
        raise NotImplementedError("FakeProvider overrides chat_json directly")

    async def chat_json(
        self, system: str, user: str, schema: dict[str, Any], max_tokens: int = 2048
    ) -> dict[str, Any]:
        return self._response

    async def test_connection(self) -> str:
        return "ok"
