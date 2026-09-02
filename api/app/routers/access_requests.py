"""Endpoints públicos (sin auth) de solicitudes de acceso e invitaciones.

CLAUDE.md tarea 2: registro por solicitud. `POST /public/access-requests` es
el formulario público (`/solicitar-acceso` en la web); las decisiones
(aprobar/rechazar) viven en `app.routers.admin` (superadmin). La aceptación
de invitación aquí es la variante SIN sesión previa (crea o adjunta el
usuario) — distinta de `POST /invitations/{token}/accept` en `app.routers.orgs`,
que exige un usuario ya autenticado.
"""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import mail
from app.config import settings
from app.db import get_db
from app.models import AccessRequest, AccessRequestStatus, Invitation, Membership, Org, User
from app.schemas.api import (
    AccessRequestCreate,
    InvitationAcceptRequest,
    InvitationPreviewOut,
    PublicConfigOut,
    TokenResponse,
)
from app.security import create_access_token, create_refresh_token, hash_password

router = APIRouter(prefix="/public", tags=["access-requests"])

# Rate limit en memoria (5/IP/hora). Suficiente para un solo proceso api;
# no sobrevive un reinicio ni se comparte entre réplicas, pero cumple el
# objetivo de frenar abuso trivial del formulario público.
_rate_limit_state: dict[str, list[datetime]] = {}
_RATE_LIMIT_MAX = 5
_RATE_LIMIT_WINDOW = timedelta(hours=1)


def _check_rate_limit(ip: str) -> None:
    now = datetime.now(UTC)
    timestamps = [t for t in _rate_limit_state.get(ip, []) if now - t < _RATE_LIMIT_WINDOW]
    if len(timestamps) >= _RATE_LIMIT_MAX:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, detail="Demasiadas solicitudes, intente más tarde"
        )
    timestamps.append(now)
    _rate_limit_state[ip] = timestamps


@router.get("/config", response_model=PublicConfigOut)
async def get_public_config() -> PublicConfigOut:
    return PublicConfigOut(registration_mode=settings.REGISTRATION_MODE)


@router.post("/access-requests", status_code=status.HTTP_201_CREATED)
async def create_access_request(
    payload: AccessRequestCreate, request: Request, db: AsyncSession = Depends(get_db)
) -> dict:
    if payload.website:
        # Honeypot: se responde éxito sin persistir nada ni avisar al bot.
        return {"ok": True}

    ip = request.client.host if request.client else "unknown"
    _check_rate_limit(ip)

    access_request = AccessRequest(
        nombre=payload.nombre,
        email=payload.email,
        organizacion=payload.organizacion,
        telefono=payload.telefono,
        motivo=payload.motivo,
        status=AccessRequestStatus.pending,
    )
    db.add(access_request)
    await db.commit()

    await mail.send_solicitud_recibida(payload.email, payload.nombre)
    if settings.ADMIN_NOTIFY_EMAIL:
        approve_url = f"{settings.APP_BASE_URL}/admin/solicitudes"
        await mail.send_nueva_solicitud_admin(
            settings.ADMIN_NOTIFY_EMAIL,
            payload.nombre,
            payload.email,
            payload.organizacion,
            payload.motivo,
            approve_url,
        )

    return {"ok": True}


@router.get("/invitations/{token}", response_model=InvitationPreviewOut)
async def preview_invitation(
    token: str, db: AsyncSession = Depends(get_db)
) -> InvitationPreviewOut:
    result = await db.execute(select(Invitation).where(Invitation.token == token))
    invitation = result.scalars().first()
    if invitation is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Invitación no encontrada")

    org = await db.get(Org, invitation.org_id)
    return InvitationPreviewOut(
        org_nombre=org.nombre if org else "",
        email=invitation.email,
        role=invitation.role,
        expired=invitation.expires_at < datetime.now(UTC),
        accepted=invitation.accepted_at is not None,
    )


@router.post("/invitations/{token}/accept", response_model=TokenResponse)
async def accept_public_invitation(
    token: str, payload: InvitationAcceptRequest, db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    result = await db.execute(select(Invitation).where(Invitation.token == token))
    invitation = result.scalars().first()
    if invitation is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Invitación no encontrada")
    if invitation.accepted_at is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invitación ya aceptada")
    if invitation.expires_at < datetime.now(UTC):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invitación expirada")

    result = await db.execute(select(User).where(User.email == invitation.email))
    user = result.scalars().first()
    if user is None:
        user = User(
            email=invitation.email,
            password_hash=hash_password(payload.password),
            nombre=payload.nombre,
        )
        db.add(user)
        await db.flush()

    existing = await db.get(Membership, {"user_id": user.id, "org_id": invitation.org_id})
    if existing is None:
        db.add(Membership(user_id=user.id, org_id=invitation.org_id, role=invitation.role))
    else:
        existing.role = invitation.role

    invitation.accepted_at = datetime.now(UTC)
    await db.commit()

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )
