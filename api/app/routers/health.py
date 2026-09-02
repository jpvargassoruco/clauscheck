import httpx
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db
from app.queue import get_arq_pool

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(db: AsyncSession = Depends(get_db)) -> dict:
    checks: dict[str, str] = {}

    try:
        await db.execute(text("SELECT 1"))
        checks["db"] = "ok"
    except Exception as exc:
        checks["db"] = f"error: {exc}"

    try:
        pool = await get_arq_pool()
        await pool.ping()
        checks["redis"] = "ok"
    except Exception as exc:
        checks["redis"] = f"error: {exc}"

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.PAPERLESS_URL}/api/")
        checks["paperless"] = "ok" if resp.status_code < 500 else f"error: HTTP {resp.status_code}"
    except Exception as exc:
        checks["paperless"] = f"error: {exc}"

    status_ok = all(v == "ok" for v in checks.values())
    return {"status": "ok" if status_ok else "degraded", "checks": checks}
