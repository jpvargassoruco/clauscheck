"""arq worker: job queue for analysis + embeddings.

`analyze` is currently a STUB: it marks the analysis running -> done with a
minimal valid dictamen (v1.0). The real 7-stage pipeline lives in
`app/pipeline/` and will replace this stub's body without changing the job
signature or the `analyses` row contract.
"""

import logging
from datetime import UTC, datetime

from arq.connections import RedisSettings
from sqlalchemy import select

from app.config import settings
from app.db import async_session_maker
from app.embeddings import embed_passages
from app.models import Analysis, AnalysisStatus, Articulo
from app.schemas.dictamen import Dictamen, Resumen, ResumenPorNivel

logger = logging.getLogger("clauscheck.worker")


def _stub_dictamen() -> dict:
    dictamen = Dictamen(
        indice_riesgo=0,
        nivel="informativo",
        confianza=0.0,
        resumen=Resumen(hallazgos=0, omisiones=0, por_nivel=ResumenPorNivel()),
        sintesis="Análisis pendiente de implementación del pipeline completo.",
        partes=[],
        hallazgos=[],
        omisiones=[],
        recomendaciones=[],
    )
    return dictamen.model_dump(mode="json")


async def analyze(ctx, analysis_id: str) -> None:
    async with async_session_maker() as db:
        analysis = await db.get(Analysis, analysis_id)
        if analysis is None:
            logger.warning("analyze: analysis %s not found", analysis_id)
            return

        analysis.status = AnalysisStatus.running
        analysis.etapa = 1
        analysis.started_at = datetime.now(UTC)
        await db.commit()

        try:
            analysis.etapa = 7
            analysis.dictamen = _stub_dictamen()
            analysis.status = AnalysisStatus.done
            analysis.finished_at = datetime.now(UTC)
            await db.commit()
        except Exception as exc:  # pragma: no cover - defensive
            await db.rollback()
            analysis.status = AnalysisStatus.failed
            analysis.error = str(exc)
            analysis.finished_at = datetime.now(UTC)
            await db.commit()
            raise


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
