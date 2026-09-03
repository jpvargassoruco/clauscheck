import json
import re
from abc import ABC, abstractmethod
from typing import Any

import jsonschema

_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


class LLMError(Exception):
    pass


def extract_json(raw: str) -> dict | None:
    """Best-effort extraction of a JSON object from an LLM response."""
    raw = raw.strip()
    candidates: list[str] = [raw]

    fence_match = _FENCE_RE.search(raw)
    if fence_match:
        candidates.insert(0, fence_match.group(1).strip())

    first, last = raw.find("{"), raw.rfind("}")
    if first != -1 and last != -1 and last > first:
        candidates.append(raw[first : last + 1])

    for candidate in candidates:
        try:
            obj = json.loads(candidate)
        except (json.JSONDecodeError, ValueError):
            continue
        if isinstance(obj, dict):
            return obj
    return None


class LLMProviderBase(ABC):
    """Common interface implemented by every LLM provider adapter."""

    code: str = "base"
    model: str = ""
    # Real token usage (`{"tokens_in": int, "tokens_out": int}`) from the
    # provider for the most recent `chat_json` call (summed across the
    # repair retry, if any), or `None` when the provider did not report it
    # (the pipeline then falls back to its own char-based estimate).
    last_usage: dict[str, int] | None = None

    async def chat_json(
        self, system: str, user: str, schema: dict[str, Any], max_tokens: int = 2048
    ) -> dict[str, Any]:
        """Call the chat model and return a dict validated against `schema`.

        Performs one repair retry if the first response is not valid JSON or
        fails schema validation.
        """
        cumulative = {"tokens_in": 0, "tokens_out": 0}
        have_usage = False

        raw, usage = await self._send(system, user, max_tokens)
        if usage:
            have_usage = True
            cumulative["tokens_in"] += usage.get("tokens_in", 0)
            cumulative["tokens_out"] += usage.get("tokens_out", 0)
        data = self._parse_and_validate(raw, schema)
        if data is not None:
            self.last_usage = cumulative if have_usage else None
            return data

        repair_user = (
            f"{user}\n\n---\n"
            "Tu respuesta anterior no era JSON válido o no cumplía el schema requerido. "
            "Responde ÚNICAMENTE con un objeto JSON válido que cumpla este JSON Schema:\n"
            f"{json.dumps(schema, ensure_ascii=False)}\n\n"
            f"Respuesta anterior:\n{raw}"
        )
        raw2, usage2 = await self._send(system, repair_user, max_tokens)
        if usage2:
            have_usage = True
            cumulative["tokens_in"] += usage2.get("tokens_in", 0)
            cumulative["tokens_out"] += usage2.get("tokens_out", 0)
        data2 = self._parse_and_validate(raw2, schema)
        self.last_usage = cumulative if have_usage else None
        if data2 is not None:
            return data2

        raise LLMError("La respuesta del proveedor no es JSON válido tras el reintento de reparación")

    @abstractmethod
    async def _send(
        self, system: str, user: str, max_tokens: int
    ) -> tuple[str, dict[str, int] | None]:
        """Send the chat request; return `(raw_text, usage)`.

        `usage` is `{"tokens_in": int, "tokens_out": int}` when the provider
        reports it, else `None`.
        """
        raise NotImplementedError

    @staticmethod
    def _parse_and_validate(raw: str, schema: dict[str, Any]) -> dict[str, Any] | None:
        obj = extract_json(raw)
        if obj is None:
            return None
        try:
            jsonschema.validate(obj, schema)
        except jsonschema.ValidationError:
            return None
        return obj
