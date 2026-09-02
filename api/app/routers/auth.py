import re
import uuid

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import mail, mfa
from app.config import settings
from app.db import get_db
from app.deps import get_current_user
from app.models import Membership, MembershipRole, Org, User
from app.paperless import provision_org
from app.schemas.api import (
    LoginRequest,
    MeResponse,
    MfaCodeRequest,
    MfaRequiredOut,
    MfaSetupOut,
    MfaVerifyRequest,
    OrgRoleOut,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slugify(text: str) -> str:
    slug = _SLUG_RE.sub("-", text.lower()).strip("-")
    return slug or "org"


async def _unique_slug(db: AsyncSession, base: str) -> str:
    slug = base
    i = 1
    while True:
        result = await db.execute(select(Org).where(Org.slug == slug))
        if result.scalars().first() is None:
            return slug
        i += 1
        slug = f"{base}-{i}"


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    if settings.REGISTRATION_MODE in ("approval", "closed"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="El registro es por solicitud")

    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalars().first() is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="El email ya está registrado")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        nombre=payload.nombre,
    )
    db.add(user)
    await db.flush()

    slug = await _unique_slug(db, _slugify(payload.org_nombre))
    org = Org(slug=slug, nombre=payload.org_nombre, plan_code="free")
    db.add(org)
    await db.flush()

    resources = await provision_org(slug, org.id)
    org.paperless_user_id = resources.user_id
    org.paperless_tag_id = resources.tag_id
    org.paperless_storage_path_id = resources.storage_path_id

    db.add(Membership(user_id=user.id, org_id=org.id, role=MembershipRole.owner))
    await db.commit()

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/login", response_model=None)
async def login(
    payload: LoginRequest, db: AsyncSession = Depends(get_db)
) -> TokenResponse | MfaRequiredOut:
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalars().first()
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")

    if user.mfa_enabled:
        return MfaRequiredOut(mfa_token=mfa.create_mfa_token(user.id))

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/mfa/verify", response_model=TokenResponse)
async def mfa_verify(payload: MfaVerifyRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    try:
        data = decode_token(payload.mfa_token)
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Token inválido") from None
    if data.get("type") != "mfa":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

    try:
        user_id = uuid.UUID(data["sub"])
    except (KeyError, ValueError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Token inválido") from None

    user = await db.get(User, user_id)
    if user is None or not user.is_active or not user.mfa_enabled:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Usuario inválido")

    secret = mfa.decrypt_secret(user.mfa_secret_enc)
    if not mfa.verify_code(secret, payload.code):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Código inválido")

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/mfa/setup", response_model=MfaSetupOut)
async def mfa_setup(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> MfaSetupOut:
    secret = mfa.generate_secret()
    user.mfa_secret_enc = mfa.encrypt_secret(secret)
    await db.commit()

    uri = mfa.provisioning_uri(secret, user.email)
    return MfaSetupOut(secret=secret, otpauth_url=uri, qr=mfa.qr_data_url(uri))


@router.post("/mfa/enable")
async def mfa_enable(
    payload: MfaCodeRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if not user.mfa_secret_enc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Primero genere un secreto MFA")
    secret = mfa.decrypt_secret(user.mfa_secret_enc)
    if not mfa.verify_code(secret, payload.code):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Código inválido")

    user.mfa_enabled = True
    await db.commit()
    await mail.send_mfa_notice(user.email, "activada")
    return {"mfa_enabled": True}


@router.post("/mfa/disable")
async def mfa_disable(
    payload: MfaCodeRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if not user.mfa_enabled:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="MFA no está activa")
    secret = mfa.decrypt_secret(user.mfa_secret_enc)
    if not mfa.verify_code(secret, payload.code):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Código inválido")

    user.mfa_enabled = False
    user.mfa_secret_enc = ""
    await db.commit()
    await mail.send_mfa_notice(user.email, "desactivada")
    return {"mfa_enabled": False}


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    try:
        data = decode_token(payload.refresh_token)
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido") from None
    if data.get("type") != "refresh":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido")

    user = await db.get(User, data["sub"])
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Usuario inválido")

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.get("/me", response_model=MeResponse)
async def me(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> MeResponse:
    result = await db.execute(
        select(Org, Membership.role)
        .join(Membership, Membership.org_id == Org.id)
        .where(Membership.user_id == user.id)
    )
    orgs = [
        OrgRoleOut(id=org.id, slug=org.slug, nombre=org.nombre, role=role)
        for org, role in result.all()
    ]
    return MeResponse(
        id=user.id,
        email=user.email,
        nombre=user.nombre,
        is_superadmin=user.is_superadmin,
        mfa_enabled=user.mfa_enabled,
        orgs=orgs,
    )
