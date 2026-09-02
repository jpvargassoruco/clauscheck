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

    async def chat_json(
        self, system: str, user: str, schema: dict[str, Any], max_tokens: int = 2048
    ) -> dict[str, Any]:
        """Call the chat model and return a dict validated against `schema`.

        Performs one repair retry if the first response is not valid JSON or
        fails schema validation.
        """
        raw = await self._send(system, user, max_tokens)
        data = self._parse_and_validate(raw, schema)
        if data is not None:
            return data

        repair_user = (
            f"{user}\n\n---\n"
            "Tu respuesta anterior no era JSON válido o no cumplía el schema requerido. "
            "Responde ÚNICAMENTE con un objeto JSON válido que cumpla este JSON Schema:\n"
            f"{json.dumps(schema, ensure_ascii=False)}\n\n"
            f"Respuesta anterior:\n{raw}"
        )
        raw2 = await self._send(system, repair_user, max_tokens)
        data2 = self._parse_and_validate(raw2, schema)
        if data2 is not None:
            return data2

        raise LLMError("La respuesta del proveedor no es JSON válido tras el reintento de reparación")

    @abstractmethod
    async def _send(self, system: str, user: str, max_tokens: int) -> str:
        """Send the chat request and return the raw text response."""
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
