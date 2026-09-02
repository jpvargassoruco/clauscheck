"""Lazy-loaded sentence-transformers embeddings (intfloat/multilingual-e5-small, 384 dims).

e5 models expect a `query: ` / `passage: ` prefix on their inputs.
"""

from functools import lru_cache

from app.config import settings


@lru_cache
def _get_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(settings.EMBEDDING_MODEL)


def embed_query(text: str) -> list[float]:
    model = _get_model()
    vec = model.encode(f"query: {text}", normalize_embeddings=True)
    return vec.tolist()


def embed_passages(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    model = _get_model()
    vecs = model.encode([f"passage: {t}" for t in texts], normalize_embeddings=True)
    return [v.tolist() for v in vecs]
