import uuid
from datetime import UTC, datetime

from arq import ArqRedis
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import get_current_org, get_current_user
from app.models import Analysis, Document, Org, Plan, Usage, User
from app.queue import get_arq_pool
from app.schemas.api import AnalysisCreate, AnalysisDetailOut, AnalysisOut, AnalysisQueuedOut

router = APIRouter(prefix="/analyses", tags=["analyses"])


def _current_periodo() -> str:
    return datetime.now(UTC).strftime("%Y-%m")


@router.post("", response_model=AnalysisQueuedOut, status_code=status.HTTP_201_CREATED)
async def create_analysis(
    payload: AnalysisCreate,
    org: Org = Depends(get_current_org),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    arq_pool: ArqRedis = Depends(get_arq_pool),
) -> Analysis:
    document = await db.get(Document, payload.document_id)
    if document is None or document.org_id != org.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Documento no encontrado")

    plan = await db.get(Plan, org.plan_code)
    periodo = _current_periodo()
    usage = await db.get(Usage, {"org_id": org.id, "periodo": periodo})
    used = usage.analisis_count if usage else 0
    limit = plan.analisis_mes if plan else 0

    if used >= limit:
        raise HTTPException(status.HTTP_402_PAYMENT_REQUIRED, detail="Cuota de análisis agotada")

    if usage is None:
        usage = Usage(org_id=org.id, periodo=periodo, analisis_count=1)
        db.add(usage)
    else:
        usage.analisis_count = used + 1

    analysis = Analysis(
        org_id=org.id,
        document_id=document.id,
        status="queued",
        etapa=0,
        created_by=user.id,
    )
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)

    await arq_pool.enqueue_job("analyze", str(analysis.id))

    return AnalysisQueuedOut(id=analysis.id, status=analysis.status)


@router.get("", response_model=list[AnalysisOut])
async def list_analyses(
    limit: int = 20,
    offset: int = 0,
    org: Org = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
) -> list[Analysis]:
    result = await db.execute(
        select(Analysis)
        .where(Analysis.org_id == org.id)
        .order_by(Analysis.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


@router.get("/{analysis_id}", response_model=AnalysisDetailOut)
async def get_analysis(
    analysis_id: uuid.UUID, org: Org = Depends(get_current_org), db: AsyncSession = Depends(get_db)
) -> Analysis:
    analysis = await db.get(Analysis, analysis_id)
    if analysis is None or analysis.org_id != org.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Análisis no encontrado")
    return analysis


@router.delete("/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_analysis(
    analysis_id: uuid.UUID, org: Org = Depends(get_current_org), db: AsyncSession = Depends(get_db)
) -> None:
    analysis = await db.get(Analysis, analysis_id)
    if analysis is None or analysis.org_id != org.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Análisis no encontrado")
    await db.delete(analysis)
    await db.commit()
