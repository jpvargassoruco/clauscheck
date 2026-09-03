"""arq worker: job queue for analysis + embeddings.

`analyze` resolves the org's LLM provider and document, then delegates the
real 7-stage analysis to `app.pipeline.run_pipeline` (HLD §5), handling the
`queued -> running -> done|failed` status transitions and recording a
human-readable Spanish `error` on failure. `POST /analyses` reserves 1
análisis + the document's word count against the org's monthly quota
up-front (see `app.routers.analyses`); if the job fails, that reservation
is refunded here so a failed run never counts against the quota.
"""

import logging
from datetime import UTC, datetime

from arq.connections import RedisSettings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import async_session_maker
from app.embeddings import embed_passages
from app.llm.registry import get_default_provider
from app.models import Analysis, AnalysisStatus, Articulo, Document, Usage
from app.periodo import current_periodo
from app.pipeline import run_pipeline
from app.pipeline.words import contar_palabras

logger = logging.getLogger("clauscheck.worker")


async def _refund_usage(db: AsyncSession, org_id, periodo: str, palabras: int) -> None:
    """Undo the POST /analyses reservation (1 análisis + `palabras`) after a
    failed job, so a failed run doesn't count against the org's quota."""
    usage = await db.get(Usage, {"org_id": org_id, "periodo": periodo})
    if usage is None:
        return
    usage.analisis_count = max(usage.analisis_count - 1, 0)
    usage.palabras_count = max(usage.palabras_count - palabras, 0)


async def analyze(ctx, analysis_id: str) -> None:
    async with async_session_maker() as db:
        analysis = await db.get(Analysis, analysis_id)
        if analysis is None:
            logger.warning("analyze: analysis %s not found", analysis_id)
            return

        org_id = analysis.org_id  # captured before any rollback expires it below

        analysis.status = AnalysisStatus.running
        analysis.etapa = 0
        analysis.started_at = datetime.now(UTC)
        await db.commit()

        periodo = current_periodo()
        palabras_reservadas = 0

        try:
            document = await db.get(Document, analysis.document_id)
            if document is None:
                raise ValueError("El documento del análisis ya no existe.")

            # Mirrors what POST /analyses reserved (see routers.analyses),
            # for the refund below if this run fails.
            palabras_reservadas = document.palabras or contar_palabras(document.texto)

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
            await _refund_usage(db, org_id, periodo, palabras_reservadas)
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
