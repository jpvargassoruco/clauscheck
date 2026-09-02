"""arq worker: job queue for analysis + embeddings.

`analyze` resolves the org's LLM provider and document, then delegates the
real 7-stage analysis to `app.pipeline.run_pipeline` (HLD §5), handling the
`queued -> running -> done|failed` status transitions and recording a
human-readable Spanish `error` on failure.
"""

import logging
from datetime import UTC, datetime

from arq.connections import RedisSettings
from sqlalchemy import select

from app.config import settings
from app.db import async_session_maker
from app.embeddings import embed_passages
from app.llm.registry import get_default_provider
from app.models import Analysis, AnalysisStatus, Articulo, Document
from app.pipeline import run_pipeline

logger = logging.getLogger("clauscheck.worker")


async def analyze(ctx, analysis_id: str) -> None:
    async with async_session_maker() as db:
        analysis = await db.get(Analysis, analysis_id)
        if analysis is None:
            logger.warning("analyze: analysis %s not found", analysis_id)
            return

        analysis.status = AnalysisStatus.running
        analysis.etapa = 0
        analysis.started_at = datetime.now(UTC)
        await db.commit()

        try:
            document = await db.get(Document, analysis.document_id)
            if document is None:
                raise ValueError("El documento del análisis ya no existe.")

            provider = await get_default_provider(db)
            analysis.provider_code = provider.code
            analysis.model = provider.model
            await db.commit()

            await run_pipeline(db, analysis, document, provider)
        except Exception as exc:
            logger.exception("analyze: fallo en analysis %s", analysis_id)
            await db.rollback()
            analysis.status = AnalysisStatus.failed
            analysis.error = str(exc)
            analysis.finished_at = datetime.now(UTC)
            await db.commit()


async def reembed_articulos(ctx, articulo_ids: list[str] | None = None) -> int:
    """Recompute embeddings for articulos (all, or a given id subset)."""
    async with async_session_maker() as db:
        stmt = select(Articulo)
        if articulo_ids:
            stmt = stmt.where(Articulo.id.in_(articulo_ids))
        result = await db.execute(stmt)
        rows = list(result.scalars().all())
        if not rows:
            return 0

        vectors = embed_passages([r.texto for r in rows])
        for row, vec in zip(rows, vectors, strict=True):
            row.embedding = vec
        await db.commit()
        return len(rows)


class WorkerSettings:
    functions = [analyze, reembed_articulos]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
