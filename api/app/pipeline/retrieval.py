"""Stage 5 (retrieval half) — contrastar norma: pgvector top-k per candidate.

HLD §5: `embed(cláusula + problema)` with `embed_query`, then pgvector
cosine top-8 `articulos` where `vigente`. The LLM step (see `prompts.py` /
`__init__.py`) may then choose applicable articles ONLY from this set.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.embeddings import embed_query
from app.models import Articulo

TOP_K = 8


async def retrieve_articulos(db: AsyncSession, query_text: str, k: int = TOP_K) -> list[Articulo]:
    vector = embed_query(query_text)
    stmt = (
        select(Articulo)
        .where(Articulo.vigente.is_(True), Articulo.embedding.is_not(None))
        .options(selectinload(Articulo.cuerpo))
        .order_by(Articulo.embedding.cosine_distance(vector))
        .limit(k)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


def articulo_to_dict(art: Articulo) -> dict:
    return {
        "id": str(art.id),
        "cuerpo": art.cuerpo.code if art.cuerpo is not None else "",
        "numero": art.numero,
        "inciso": art.inciso,
        "texto": art.texto,
        "fuente_url": art.fuente_url,
    }
