"""Stage 1.5 — pseudonymization (never let the LLM provider see real identities).

`anonymize(text, mapping=None)` scans `text` for Bolivian PII via regex and
replaces every match with a stable token (`PARTE_1`, `CI_1`, `NIT_1`,
`TEL_1`, `EMAIL_1`, `CUENTA_1`, `DIRECCION_1`, `EMPRESA_1`, `PLACA_1`, ...),
returning `(pseudonymized_text, mapping)` where `mapping` is `token ->
real_value`. Passing back a previously-returned `mapping` (e.g. loaded from
`documents.pseudonyms`) makes repeated calls over the same values reuse the
same tokens (idempotent, deterministic — no randomness is involved, so two
independent calls over the same text produce the same mapping regardless).

`restore(obj, mapping)` walks any JSON-able structure (dict/list/str, and
Pydantic-dumped dicts) and replaces tokens back with their real values —
call it right before persisting/returning anything a human will read
(`clausulas`, `partes`, `ficha`, the final `dictamen`).

Amounts, dates and clause numbering ("PRIMERA", "SEGUNDA"...) are legally
significant and are never touched. City names (Santa Cruz, Cochabamba, La
Paz, ...) are left as-is too — jurisdiction depends on them — only exact
street addresses are tokenized.

PII categories detected (regex, in this order — person names go first
because one of their anchors is the literal text "con C.I.", which the CI
pattern below would otherwise consume):
  1. email                          -> EMAIL_n
  2. nombre de persona ("señor/a X", "Sr./Sra. X", "X con C.I.") -> PARTE_n
  3. cédula de identidad (CI)       -> CI_n
  4. NIT                            -> NIT_n
  5. cuenta bancaria                -> CUENTA_n
  6. placa (vehicle plate)          -> PLACA_n
  7. teléfono (+591 / 6xxxxxxx / 7xxxxxxx) -> TEL_n
  8. dirección (street address)     -> DIRECCION_n
  9. razón social (S.R.L./S.A./LTDA) -> EMPRESA_n
"""

from __future__ import annotations

import re
from typing import Any

_TOKEN_RE_CACHE: dict[tuple[str, ...], re.Pattern[str]] = {}


def _next_index(mapping: dict[str, str], prefix: str) -> int:
    best = 0
    for token in mapping:
        if token.startswith(prefix + "_"):
            suffix = token[len(prefix) + 1 :]
            if suffix.isdigit():
                best = max(best, int(suffix))
    return best + 1


def _make_replacer(mapping: dict[str, str], prefix: str):
    """Return a `re.sub` callback that assigns/reuses a stable `PREFIX_n`
    token for each distinct matched value (case/whitespace-insensitive
    dedup so "Juan Perez" and "juan  perez" collapse to the same token).
    """
    reverse = {v.strip().lower(): tok for tok, v in mapping.items() if tok.startswith(prefix + "_")}

    def _sub(m: re.Match[str]) -> str:
        value = m.group(0)
        key = value.strip().lower()
        token = reverse.get(key)
        if token is None:
            token = f"{prefix}_{_next_index(mapping, prefix)}"
            mapping[token] = value
            reverse[key] = token
        return token

    return _sub


# --- detection patterns (order matters) -------------------------------

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")

_CI_RE = re.compile(
    r"(?:C[ée]dula\s+de\s+[Ii]dentidad|C\.?I\.?)\s*(?:N[°ºo]\.?)?\s*[:\-]?\s*"
    r"\d{5,9}(?:\s?-?\s?[A-Z]{2,3}\b)?"
)

_NIT_RE = re.compile(r"\bNIT\.?\s*(?:N[°ºo]\.?)?\s*[:\-]?\s*\d{5,15}\b")

_CUENTA_RE = re.compile(
    r"(?:[Cc]uenta(?:\s+(?:bancaria|corriente|de\s+ahorros?))?)\s*"
    r"(?:N[°ºo]\.?)?\s*[:\-]?\s*\d{6,20}\b"
)

_PLACA_RE = re.compile(
    r"[Pp]laca\s*(?:de\s+control)?\s*(?:N[°ºo]\.?)?\s*[:\-]?\s*[A-Z0-9]{3,4}[\s-]?[A-Z0-9]{2,4}\b"
)

_TEL_RE = re.compile(r"(?:\+591[\s-]?)?\b[67]\d{7}\b")

_DIRECCION_RE = re.compile(
    r"(?:Av(?:enida)?\.?|Calle|C\.|Urbanizaci[oó]n|Urb\.)\s+"
    r"[A-ZÁÉÍÓÚÑa-záéíóúñ0-9°ºNn.'\-]+(?:\s+[A-ZÁÉÍÓÚÑa-záéíóúñ0-9°ºNn.'\-]+){0,5}"
    r"(?:\s*,?\s*[Nn][°ºo]?\.?\s*\d+\w*)?"
)

_EMPRESA_RE = re.compile(
    r"\b[A-ZÁÉÍÓÚÑ0-9][\w.&Á-Úá-ú'-]*(?:\s+[A-ZÁÉÍÓÚÑ0-9&][\w.&Á-Úá-ú'-]*){0,5}"
    r"\s+(?:S\.?R\.?L\.?|S\.?A\.?|LTDA\.?)\b"
)

# A "name word": starts with an uppercase letter, followed by any mix of
# letters — matches both Title Case ("Pérez") and ALL CAPS ("PÉREZ"), since
# Bolivian contracts use either depending on the section (prose vs. the
# comparecientes header).
_NAME = r"[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ'-]*"
_PERSONA_SENOR_RE = re.compile(
    rf"\b[Ss]e[ñn]or(?:a)?\.?\s+({_NAME}(?:\s+{_NAME}){{1,3}})"
)
_PERSONA_ABREV_RE = re.compile(rf"\b(?:Sr|Sra)\.\s+({_NAME}(?:\s+{_NAME}){{1,3}})")
_PERSONA_CON_CI_RE = re.compile(rf"\b({_NAME}(?:\s+{_NAME}){{1,3}}),?\s+con\s+C\.?I\.?")


def anonymize(text: str, mapping: dict[str, str] | None = None) -> tuple[str, dict[str, str]]:
    """Pseudonymize Bolivian PII in `text`. Returns `(text, mapping)` with
    `mapping` extended (existing entries in the passed-in `mapping` are
    reused/kept, never re-tokenized).
    """
    mapping = dict(mapping or {})

    text = _EMAIL_RE.sub(_make_replacer(mapping, "EMAIL"), text)

    # Person names first: one anchor is the literal text "con C.I.", which
    # the CI pattern below would otherwise consume before we get to look
    # for it. Unlike the categories below, the value to dedupe/store is
    # capture group 1 (the bare name) — the anchor word ("señor", "con
    # C.I.") must stay in the text — so these are driven directly instead
    # of via `_make_replacer` (which keys off the whole match, group 0).
    def _tokenize_name(name: str) -> str:
        key = name.strip().lower()
        reverse = {v.strip().lower(): tok for tok, v in mapping.items() if tok.startswith("PARTE_")}
        token = reverse.get(key)
        if token is None:
            token = f"PARTE_{_next_index(mapping, 'PARTE')}"
            mapping[token] = name
        return token

    def _sub_name_group(pattern: re.Pattern[str]) -> None:
        nonlocal text

        def _sub(m: re.Match[str]) -> str:
            name = m.group(1)
            token = _tokenize_name(name)
            return m.group(0).replace(name, token)

        text = pattern.sub(_sub, text)

    _sub_name_group(_PERSONA_SENOR_RE)
    _sub_name_group(_PERSONA_ABREV_RE)
    _sub_name_group(_PERSONA_CON_CI_RE)

    text = _CI_RE.sub(_make_replacer(mapping, "CI"), text)
    text = _NIT_RE.sub(_make_replacer(mapping, "NIT"), text)
    text = _CUENTA_RE.sub(_make_replacer(mapping, "CUENTA"), text)
    text = _PLACA_RE.sub(_make_replacer(mapping, "PLACA"), text)
    text = _TEL_RE.sub(_make_replacer(mapping, "TEL"), text)
    text = _DIRECCION_RE.sub(_make_replacer(mapping, "DIRECCION"), text)
    text = _EMPRESA_RE.sub(_make_replacer(mapping, "EMPRESA"), text)

    return text, mapping


def restore(obj: Any, mapping: dict[str, str]) -> Any:
    """Walk `obj` (str/dict/list, recursively — e.g. a dictamen dict) and
    replace every pseudonymization token with its real value. Tokens are
    matched case-insensitively on word boundaries so an LLM that reproduces
    a token in a different case (`parte_1`) still gets restored.
    """
    if not mapping:
        return obj

    if isinstance(obj, dict):
        return {k: restore(v, mapping) for k, v in obj.items()}
    if isinstance(obj, list):
        return [restore(v, mapping) for v in obj]
    if isinstance(obj, str):
        return _restore_text(obj, mapping)
    return obj


def _restore_text(text: str, mapping: dict[str, str]) -> str:
    if not text or "_" not in text:
        return text

    key = tuple(sorted(mapping))
    pattern = _TOKEN_RE_CACHE.get(key)
    if pattern is None:
        tokens_by_len = sorted(mapping, key=len, reverse=True)
        pattern = re.compile(
            r"\b(" + "|".join(re.escape(t) for t in tokens_by_len) + r")\b", re.IGNORECASE
        )
        _TOKEN_RE_CACHE[key] = pattern

    upper_mapping = {tok.upper(): val for tok, val in mapping.items()}
    return pattern.sub(lambda m: upper_mapping.get(m.group(0).upper(), m.group(0)), text)
