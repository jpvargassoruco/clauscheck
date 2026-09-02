from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.crypto import decrypt
from app.llm.anthropic_provider import AnthropicProvider
from app.llm.base import LLMError, LLMProviderBase
from app.llm.openai_compat import OpenAICompatProvider
from app.models import LLMProvider, LLMProviderKind

_ENV_FALLBACKS = {
    "deepseek": lambda: OpenAICompatProvider(
        code="deepseek",
        base_url=settings.DEEPSEEK_BASE_URL,
        api_key=settings.DEEPSEEK_API_KEY,
        model=settings.DEEPSEEK_MODEL,
    ),
    "moonshot": lambda: OpenAICompatProvider(
        code="moonshot",
        base_url=settings.MOONSHOT_BASE_URL,
        api_key=settings.MOONSHOT_API_KEY,
        model=settings.MOONSHOT_MODEL,
    ),
    "openrouter": lambda: OpenAICompatProvider(
        code="openrouter",
        base_url=settings.OPENROUTER_BASE_URL,
        api_key=settings.OPENROUTER_API_KEY,
        model=settings.OPENROUTER_MODEL,
    ),
    "anthropic": lambda: AnthropicProvider(
        api_key=settings.ANTHROPIC_API_KEY, model=settings.ANTHROPIC_MODEL
    ),
}


def build_provider(row: LLMProvider) -> LLMProviderBase:
    api_key = decrypt(row.api_key_enc) if row.api_key_enc else ""
    if row.kind == LLMProviderKind.anthropic:
        return AnthropicProvider(api_key=api_key, model=row.model or settings.ANTHROPIC_MODEL)
    return OpenAICompatProvider(
        code=row.code, base_url=row.base_url, api_key=api_key, model=row.model
    )


async def get_default_provider(db: AsyncSession) -> LLMProviderBase:
    """Resolve the default LLM provider: DB `llm_providers.is_default=true`, else env fallback."""
    result = await db.execute(
        select(LLMProvider).where(LLMProvider.enabled.is_(True), LLMProvider.is_default.is_(True))
    )
    row = result.scalars().first()
    if row is not None:
        return build_provider(row)

    for code, factory in _ENV_FALLBACKS.items():
        provider = factory()
        api_key = getattr(settings, f"{code.upper()}_API_KEY", "")
        if api_key:
            return provider

    raise LLMError("No hay proveedor LLM configurado (ni en BD ni en variables de entorno)")
