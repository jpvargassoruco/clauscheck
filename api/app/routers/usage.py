from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import get_current_org
from app.models import Org, Plan, Usage
from app.schemas.api import UsageOut

router = APIRouter(prefix="/usage", tags=["usage"])


@router.get("", response_model=UsageOut)
async def get_usage(org: Org = Depends(get_current_org), db: AsyncSession = Depends(get_db)) -> UsageOut:
    periodo = datetime.now(UTC).strftime("%Y-%m")
    usage = await db.get(Usage, {"org_id": org.id, "periodo": periodo})
    plan = await db.get(Plan, org.plan_code)

    return UsageOut(
        periodo=periodo,
        analisis_count=usage.analisis_count if usage else 0,
        analisis_mes=plan.analisis_mes if plan else 0,
        plan_code=org.plan_code,
    )
