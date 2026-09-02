import httpx

from app.llm.base import LLMError, LLMProviderBase

# Providers that reliably honour `response_format={"type":"json_object"}`.
_SUPPORTS_JSON_MODE = {"deepseek", "openrouter"}


class OpenAICompatProvider(LLMProviderBase):
    """Adapter for any OpenAI-chat-completions-compatible API (DeepSeek, Moonshot, OpenRouter)."""

    def __init__(self, code: str, base_url: str, api_key: str, model: str, timeout: float = 60.0):
        self.code = code
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    async def _send(self, system: str, user: str, max_tokens: int) -> str:
        payload: dict = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "max_tokens": max_tokens,
        }
        if self.code in _SUPPORTS_JSON_MODE:
            payload["response_format"] = {"type": "json_object"}

        headers = {"Authorization": f"Bearer {self.api_key}"}

        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            resp = await client.post("/chat/completions", json=payload, headers=headers)
        if resp.status_code >= 400:
            raise LLMError(f"{self.code}: HTTP {resp.status_code}: {resp.text[:500]}")

        data = resp.json()
        try:
            return data["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError(f"{self.code}: respuesta inesperada: {data}") from exc

    async def test_connection(self) -> str:
        """Minimal 1-token call used by the admin `test` endpoint."""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 1,
        }
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            resp = await client.post("/chat/completions", json=payload, headers=headers)
        if resp.status_code >= 400:
            raise LLMError(f"HTTP {resp.status_code}: {resp.text[:500]}")
        return "ok"
