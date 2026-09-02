import uuid

import jwt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import Membership, Org, User
from app.security import decode_token

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    try:
        payload = decode_token(credentials.credentials)
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Token inválido") from None
    if payload.get("type") != "access":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    try:
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Token inválido") from None

    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Usuario inválido")
    return user


async def get_current_org(
    x_org_id: str | None = Header(default=None, alias="X-Org-Id"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Org:
    if not x_org_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="X-Org-Id requerido")
    try:
        org_id = uuid.UUID(x_org_id)
    except ValueError:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="X-Org-Id inválido") from None

    membership = await db.get(Membership, {"user_id": user.id, "org_id": org_id})
    if membership is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Sin membresía en la organización")

    org = await db.get(Org, org_id)
    if org is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Organización no encontrada")
    return org


async def get_current_membership(
    x_org_id: str | None = Header(default=None, alias="X-Org-Id"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Membership:
    if not x_org_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="X-Org-Id requerido")
    try:
        org_id = uuid.UUID(x_org_id)
    except ValueError:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="X-Org-Id inválido") from None
    membership = await db.get(Membership, {"user_id": user.id, "org_id": org_id})
    if membership is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Sin membresía en la organización")
    return membership


async def require_superadmin(user: User = Depends(get_current_user)) -> User:
    if not user.is_superadmin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Requiere superadmin")
    return user


async def user_orgs(user: User, db: AsyncSession) -> list[Org]:
    result = await db.execute(
        select(Org).join(Membership, Membership.org_id == Org.id).where(Membership.user_id == user.id)
    )
    return list(result.scalars().all())
