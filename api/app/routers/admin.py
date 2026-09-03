import csv
import io
import secrets
import uuid
from datetime import UTC, date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import mail
from app.config import settings
from app.crypto import encrypt
from app.db import get_db
from app.deps import require_superadmin
from app.embeddings import embed_passages
from app.llm.base import LLMError
from app.llm.registry import build_provider
from app.models import (
    AccessRequest,
    AccessRequestStatus,
    Analysis,
    Articulo,
    CuerpoLegal,
    Document,
    Invitation,
    LLMProvider,
    LLMProviderKind,
    Org,
    Plan,
    Usage,
    User,
)
from app.normativa_import import import_normativa
from app.paperless import provision_org
from app.periodo import current_periodo
from app.pipeline.pricing import costo_bs
from app.routers.auth import _slugify, _unique_slug
from app.schemas.api import (
    AccessRequestApprove,
    AccessRequestOut,
    AccessRequestReject,
    ArticuloIn,
    ArticuloOut,
    ConsumoDiaRow,
    ConsumoOrgRow,
    ConsumoOut,
    ConsumoTotales,
    CuerpoLegalIn,
    CuerpoLegalOut,
    NormativaImportResult,
    OrgAdminUpdate,
    OrgOut,
    PlanOut,
    PlanUpdate,
    ProviderCreate,
    ProviderOut,
    ProviderTestResult,
    ProviderUpdate,
)

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_superadmin)])


# --- providers ----------------------------------------------------------


@router.get("/providers", response_model=list[ProviderOut])
async def list_providers(db: AsyncSession = Depends(get_db)) -> list[LLMProvider]:
    result = await db.execute(select(LLMProvider))
    return list(result.scalars().all())


@router.post("/providers", response_model=ProviderOut, status_code=status.HTTP_201_CREATED)
async def create_provider(
    payload: ProviderCreate, db: AsyncSession = Depends(get_db)
) -> LLMProvider:
    if payload.is_default:
        await db.execute(LLMProvider.__table__.update().values(is_default=False))
    provider = LLMProvider(
        code=payload.code,
        kind=LLMProviderKind(payload.kind),
        base_url=payload.base_url,
        model=payload.model,
        api_key_enc=encrypt(payload.api_key or ""),
        enabled=payload.enabled,
        is_default=payload.is_default,
        params=payload.params,
    )
    db.add(provider)
    await db.commit()
    await db.refresh(provider)
    return provider


async def _get_provider_or_404(db: AsyncSession, provider_id: uuid.UUID) -> LLMProvider:
    provider = await db.get(LLMProvider, provider_id)
    if provider is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Proveedor no encontrado")
    return provider


@router.patch("/providers/{provider_id}", response_model=ProviderOut)
async def update_provider(
    provider_id: uuid.UUID, payload: ProviderUpdate, db: AsyncSession = Depends(get_db)
) -> LLMProvider:
    provider = await _get_provider_or_404(db, provider_id)
    data = payload.model_dump(exclude_unset=True)
    if data.get("is_default"):
        await db.execute(LLMProvider.__table__.update().values(is_default=False))
    if "api_key" in data:
        provider.api_key_enc = encrypt(data.pop("api_key") or "")
    for field, value in data.items():
        setattr(provider, field, value)
    await db.commit()
    await db.refresh(provider)
    return provider


@router.delete("/providers/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_provider(provider_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> None:
    provider = await _get_provider_or_404(db, provider_id)
    await db.delete(provider)
    await db.commit()


@router.post("/providers/{provider_id}/test", response_model=ProviderTestResult)
async def test_provider(provider_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> ProviderTestResult:
    provider_row = await _get_provider_or_404(db, provider_id)
    provider = build_provider(provider_row)
    try:
        await provider.test_connection()
    except LLMError as exc:
        return ProviderTestResult(ok=False, detail=str(exc))
    return ProviderTestResult(ok=True)


# --- normativa: cuerpos ---------------------------------------------------


@router.get("/normativa/cuerpos", response_model=list[CuerpoLegalOut])
async def list_cuerpos(db: AsyncSession = Depends(get_db)) -> list[CuerpoLegal]:
    result = await db.execute(select(CuerpoLegal).order_by(CuerpoLegal.code))
    return list(result.scalars().all())


@router.post("/normativa/cuerpos", response_model=CuerpoLegalOut, status_code=status.HTTP_201_CREATED)
async def create_cuerpo(payload: CuerpoLegalIn, db: AsyncSession = Depends(get_db)) -> CuerpoLegal:
    cuerpo = CuerpoLegal(**payload.model_dump())
    db.add(cuerpo)
    await db.commit()
    await db.refresh(cuerpo)
    return cuerpo


@router.patch("/normativa/cuerpos/{cuerpo_id}", response_model=CuerpoLegalOut)
async def update_cuerpo(
    cuerpo_id: uuid.UUID, payload: CuerpoLegalIn, db: AsyncSession = Depends(get_db)
) -> CuerpoLegal:
    cuerpo = await db.get(CuerpoLegal, cuerpo_id)
    if cuerpo is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Cuerpo legal no encontrado")
    for field, value in payload.model_dump().items():
        setattr(cuerpo, field, value)
    await db.commit()
    await db.refresh(cuerpo)
    return cuerpo


# --- normativa: articulos --------------------------------------------------


@router.get("/normativa/articulos", response_model=list[ArticuloOut])
async def list_articulos(
    cuerpo: str | None = None,
    numero: str | None = None,
    q: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[Articulo]:
    stmt = select(Articulo)
    if cuerpo:
        stmt = stmt.join(CuerpoLegal, CuerpoLegal.id == Articulo.cuerpo_id).where(
            CuerpoLegal.code == cuerpo
        )
    if numero:
        stmt = stmt.where(Articulo.numero == numero)
    if q:
        stmt = stmt.where(Articulo.texto.ilike(f"%{q}%"))
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.post("/normativa/articulos", response_model=ArticuloOut, status_code=status.HTTP_201_CREATED)
async def create_articulo(payload: ArticuloIn, db: AsyncSession = Depends(get_db)) -> Articulo:
    articulo = Articulo(**payload.model_dump())
    db.add(articulo)
    await db.commit()
    await db.refresh(articulo)
    return articulo


@router.patch("/normativa/articulos/{articulo_id}", response_model=ArticuloOut)
async def update_articulo(
    articulo_id: uuid.UUID, payload: ArticuloIn, db: AsyncSession = Depends(get_db)
) -> Articulo:
    articulo = await db.get(Articulo, articulo_id)
    if articulo is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Artículo no encontrado")
    for field, value in payload.model_dump().items():
        setattr(articulo, field, value)
    await db.commit()
    await db.refresh(articulo)
    return articulo


@router.delete("/normativa/articulos/{articulo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_articulo(articulo_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> None:
    articulo = await db.get(Articulo, articulo_id)
    if articulo is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Artículo no encontrado")
    await db.delete(articulo)
    await db.commit()


@router.post("/normativa/import", response_model=NormativaImportResult)
async def import_normativa_endpoint(payload: dict, db: AsyncSession = Depends(get_db)) -> dict:
    try:
        return await import_normativa(db, payload)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/normativa/reembed")
async def reembed_normativa(db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(select(Articulo))
    rows = list(result.scalars().all())
    if not rows:
        return {"reembedded": 0}
    vectors = embed_passages([r.texto for r in rows])
    for row, vec in zip(rows, vectors, strict=True):
        row.embedding = vec
    await db.commit()
    return {"reembedded": len(rows)}


# --- orgs / plans ----------------------------------------------------------


@router.get("/orgs", response_model=list[OrgOut])
async def admin_list_orgs(db: AsyncSession = Depends(get_db)) -> list[Org]:
    result = await db.execute(select(Org).order_by(Org.created_at.desc()))
    return list(result.scalars().all())


@router.patch("/orgs/{org_id}", response_model=OrgOut)
async def admin_update_org(
    org_id: uuid.UUID, payload: OrgAdminUpdate, db: AsyncSession = Depends(get_db)
) -> Org:
    org = await db.get(Org, org_id)
    if org is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Organización no encontrada")
    if payload.plan_code is not None:
        org.plan_code = payload.plan_code
    await db.commit()
    await db.refresh(org)
    return org


@router.get("/plans", response_model=list[PlanOut])
async def admin_list_plans(db: AsyncSession = Depends(get_db)) -> list[Plan]:
    result = await db.execute(select(Plan))
    return list(result.scalars().all())


@router.patch("/plans/{code}", response_model=PlanOut)
async def admin_update_plan(
    code: str, payload: PlanUpdate, db: AsyncSession = Depends(get_db)
) -> Plan:
    plan = await db.get(Plan, code)
    if plan is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Plan no encontrado")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(plan, field, value)
    await db.commit()
    await db.refresh(plan)
    return plan


# --- consumo (dashboard) -----------------------------------------------------


async def _build_consumo(
    db: AsyncSession, desde: date | None, hasta: date | None, org_id: uuid.UUID | None
) -> ConsumoOut:
    hoy = datetime.now(UTC).date()
    if hasta is None:
        hasta = hoy
    if desde is None:
        desde = hasta.replace(day=1)

    start_dt = datetime.combine(desde, time.min, tzinfo=UTC)
    end_dt = datetime.combine(hasta, time.max, tzinfo=UTC)

    stmt = (
        select(Analysis, Document.palabras, Org.nombre, Org.plan_code)
        .join(Document, Analysis.document_id == Document.id)
        .join(Org, Analysis.org_id == Org.id)
        .where(Analysis.created_at >= start_dt, Analysis.created_at <= end_dt)
    )
    if org_id is not None:
        stmt = stmt.where(Analysis.org_id == org_id)
    result = await db.execute(stmt)
    rows = result.all()

    org_acc: dict[uuid.UUID, dict] = {}
    dia_acc: dict[date, dict] = {}
    for analysis, palabras, org_nombre, plan_code in rows:
        oid = analysis.org_id
        acc = org_acc.setdefault(
            oid,
            {
                "org_nombre": org_nombre,
                "plan_code": plan_code,
                "analisis": 0,
                "palabras": 0,
                "tokens_in": 0,
                "tokens_out": 0,
                "costo_usd": 0.0,
            },
        )
        acc["analisis"] += 1
        acc["palabras"] += palabras or 0
        acc["tokens_in"] += analysis.tokens_in or 0
        acc["tokens_out"] += analysis.tokens_out or 0
        acc["costo_usd"] += float(analysis.costo_usd or 0)

        dia = analysis.created_at.date()
        dacc = dia_acc.setdefault(dia, {"analisis": 0, "palabras": 0, "costo_usd": 0.0})
        dacc["analisis"] += 1
        dacc["palabras"] += palabras or 0
        dacc["costo_usd"] += float(analysis.costo_usd or 0)

    # Plan usage bars (web) compare against the *current* month, regardless
    # of the desde/hasta range being aggregated above.
    periodo = current_periodo()
    usage_by_org: dict[uuid.UUID, Usage] = {}
    if org_acc:
        result2 = await db.execute(
            select(Usage).where(Usage.org_id.in_(org_acc.keys()), Usage.periodo == periodo)
        )
        for u in result2.scalars():
            usage_by_org[u.org_id] = u

    result3 = await db.execute(select(Plan))
    plans_by_code = {p.code: p for p in result3.scalars()}

    org_rows: list[ConsumoOrgRow] = []
    for oid, acc in sorted(org_acc.items(), key=lambda kv: kv[1]["costo_usd"], reverse=True):
        plan = plans_by_code.get(acc["plan_code"])
        usage_row = usage_by_org.get(oid)
        org_rows.append(
            ConsumoOrgRow(
                org_id=oid,
                org_nombre=acc["org_nombre"],
                plan_code=acc["plan_code"],
                analisis=acc["analisis"],
                palabras=acc["palabras"],
                tokens_in=acc["tokens_in"],
                tokens_out=acc["tokens_out"],
                costo_usd=round(acc["costo_usd"], 4),
                costo_bs=costo_bs(acc["costo_usd"], settings.USD_BOB),
                analisis_mes_plan=plan.analisis_mes if plan else 0,
                palabras_mes_plan=plan.palabras_mes if plan else 0,
                analisis_mes_usado=usage_row.analisis_count if usage_row else 0,
                palabras_mes_usado=usage_row.palabras_count if usage_row else 0,
            )
        )

    serie_diaria = [
        ConsumoDiaRow(
            fecha=dia,
            analisis=v["analisis"],
            palabras=v["palabras"],
            costo_usd=round(v["costo_usd"], 4),
        )
        for dia, v in sorted(dia_acc.items())
    ]

    total_costo = sum(r.costo_usd for r in org_rows)
    totales = ConsumoTotales(
        analisis=sum(r.analisis for r in org_rows),
        palabras=sum(r.palabras for r in org_rows),
        tokens_in=sum(r.tokens_in for r in org_rows),
        tokens_out=sum(r.tokens_out for r in org_rows),
        costo_usd=round(total_costo, 4),
        costo_bs=costo_bs(total_costo, settings.USD_BOB),
    )

    return ConsumoOut(
        desde=desde,
        hasta=hasta,
        usd_bob=settings.USD_BOB,
        totales=totales,
        rows=org_rows,
        serie_diaria=serie_diaria,
    )


@router.get("/consumo", response_model=ConsumoOut)
async def admin_consumo(
    desde: date | None = None,
    hasta: date | None = None,
    org_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
) -> ConsumoOut:
    return await _build_consumo(db, desde, hasta, org_id)


@router.get("/consumo/export.csv")
async def admin_consumo_export_csv(
    desde: date | None = None,
    hasta: date | None = None,
    org_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    consumo = await _build_consumo(db, desde, hasta, org_id)

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "org_id",
            "org_nombre",
            "plan_code",
            "analisis",
            "palabras",
            "tokens_in",
            "tokens_out",
            "costo_usd",
            "costo_bs",
        ]
    )
    for r in consumo.rows:
        writer.writerow(
            [
                r.org_id,
                r.org_nombre,
                r.plan_code,
                r.analisis,
                r.palabras,
                r.tokens_in,
                r.tokens_out,
                r.costo_usd,
                r.costo_bs,
            ]
        )
    buf.seek(0)
    filename = f"consumo_{consumo.desde}_{consumo.hasta}.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# --- access requests --------------------------------------------------------


@router.get("/access-requests", response_model=list[AccessRequestOut])
async def list_access_requests(
    status_filter: AccessRequestStatus | None = Query(default=None, alias="status"),
    db: AsyncSession = Depends(get_db),
) -> list[AccessRequest]:
    stmt = select(AccessRequest).order_by(AccessRequest.created_at.desc())
    if status_filter is not None:
        stmt = stmt.where(AccessRequest.status == status_filter)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def _get_access_request_or_404(db: AsyncSession, request_id: uuid.UUID) -> AccessRequest:
    access_request = await db.get(AccessRequest, request_id)
    if access_request is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Solicitud no encontrada")
    return access_request


@router.post("/access-requests/{request_id}/approve", response_model=AccessRequestOut)
async def approve_access_request(
    request_id: uuid.UUID,
    payload: AccessRequestApprove,
    user: User = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
) -> AccessRequest:
    access_request = await _get_access_request_or_404(db, request_id)
    if access_request.status != AccessRequestStatus.pending:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Solicitud ya decidida")

    slug = await _unique_slug(db, _slugify(access_request.organizacion))
    org = Org(slug=slug, nombre=access_request.organizacion, plan_code=payload.plan_code)
    db.add(org)
    await db.flush()

    resources = await provision_org(slug, org.id)
    org.paperless_user_id = resources.user_id
    org.paperless_tag_id = resources.tag_id
    org.paperless_storage_path_id = resources.storage_path_id

    invitation = Invitation(
        org_id=org.id,
        email=access_request.email,
        role=payload.role,
        token=secrets.token_urlsafe(32),
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    db.add(invitation)

    access_request.status = AccessRequestStatus.approved
    access_request.decided_at = datetime.now(UTC)
    access_request.decided_by = user.id
    access_request.org_id = org.id

    await db.commit()
    await db.refresh(access_request)

    accept_url = f"{settings.APP_BASE_URL}/invitacion/{invitation.token}"
    await mail.send_invitacion(
        access_request.email, invitation.token, org.nombre, invitation.role.value, accept_url
    )

    return access_request


@router.post("/access-requests/{request_id}/reject", response_model=AccessRequestOut)
async def reject_access_request(
    request_id: uuid.UUID,
    payload: AccessRequestReject,
    user: User = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
) -> AccessRequest:
    access_request = await _get_access_request_or_404(db, request_id)
    if access_request.status != AccessRequestStatus.pending:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Solicitud ya decidida")

    access_request.status = AccessRequestStatus.rejected
    access_request.decided_at = datetime.now(UTC)
    access_request.decided_by = user.id
    await db.commit()
    await db.refresh(access_request)

    await mail.send_solicitud_rechazada(access_request.email, access_request.nombre, payload.motivo)

    return access_request
