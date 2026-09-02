import secrets
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import get_current_user, user_orgs
from app.models import Invitation, Membership, MembershipRole, Org, User
from app.paperless import provision_org
from app.routers.auth import _slugify, _unique_slug
from app.schemas.api import (
    InvitationCreate,
    InvitationOut,
    MemberOut,
    MemberUpdate,
    OrgCreate,
    OrgOut,
)

router = APIRouter(tags=["orgs"])


async def _get_membership_or_403(db: AsyncSession, user: User, org_id: uuid.UUID) -> Membership:
    membership = await db.get(Membership, {"user_id": user.id, "org_id": org_id})
    if membership is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Sin membresía en la organización")
    return membership


def _require_admin_role(membership: Membership) -> None:
    if membership.role not in (MembershipRole.owner, MembershipRole.admin):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Requiere rol owner o admin")


@router.get("/orgs", response_model=list[OrgOut])
async def list_orgs(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[Org]:
    return await user_orgs(user, db)


@router.post("/orgs", response_model=OrgOut, status_code=status.HTTP_201_CREATED)
async def create_org(
    payload: OrgCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> Org:
    slug = payload.slug or _slugify(payload.nombre)
    slug = await _unique_slug(db, slug)

    org = Org(slug=slug, nombre=payload.nombre, plan_code="free")
    db.add(org)
    await db.flush()

    resources = await provision_org(slug, org.id)
    org.paperless_user_id = resources.user_id
    org.paperless_tag_id = resources.tag_id
    org.paperless_storage_path_id = resources.storage_path_id

    db.add(Membership(user_id=user.id, org_id=org.id, role=MembershipRole.owner))
    await db.commit()
    await db.refresh(org)
    return org


@router.get("/orgs/{org_id}/members", response_model=list[MemberOut])
async def list_members(
    org_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[MemberOut]:
    await _get_membership_or_403(db, user, org_id)
    result = await db.execute(
        select(Membership, User).join(User, User.id == Membership.user_id).where(
            Membership.org_id == org_id
        )
    )
    return [
        MemberOut(user_id=u.id, email=u.email, nombre=u.nombre, role=m.role) for m, u in result.all()
    ]


@router.patch("/orgs/{org_id}/members/{user_id}", response_model=MemberOut)
async def update_member(
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    payload: MemberUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MemberOut:
    membership = await _get_membership_or_403(db, user, org_id)
    _require_admin_role(membership)

    target = await db.get(Membership, {"user_id": user_id, "org_id": org_id})
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Miembro no encontrado")

    target.role = payload.role
    await db.commit()

    target_user = await db.get(User, user_id)
    return MemberOut(
        user_id=user_id, email=target_user.email, nombre=target_user.nombre, role=target.role
    )


@router.post(
    "/orgs/{org_id}/invitations", response_model=InvitationOut, status_code=status.HTTP_201_CREATED
)
async def create_invitation(
    org_id: uuid.UUID,
    payload: InvitationCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Invitation:
    membership = await _get_membership_or_403(db, user, org_id)
    _require_admin_role(membership)

    invitation = Invitation(
        org_id=org_id,
        email=payload.email,
        role=payload.role,
        token=secrets.token_urlsafe(32),
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    db.add(invitation)
    await db.commit()
    await db.refresh(invitation)
    return invitation


@router.post("/invitations/{token}/accept", response_model=MemberOut)
async def accept_invitation(
    token: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> MemberOut:
    result = await db.execute(select(Invitation).where(Invitation.token == token))
    invitation = result.scalars().first()
    if invitation is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Invitación no encontrada")
    if invitation.accepted_at is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invitación ya aceptada")
    if invitation.expires_at < datetime.now(UTC):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invitación expirada")
    if invitation.email.lower() != user.email.lower():
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Invitación destinada a otro email")

    existing = await db.get(Membership, {"user_id": user.id, "org_id": invitation.org_id})
    if existing is None:
        db.add(Membership(user_id=user.id, org_id=invitation.org_id, role=invitation.role))
    else:
        existing.role = invitation.role

    invitation.accepted_at = datetime.now(UTC)
    await db.commit()

    return MemberOut(user_id=user.id, email=user.email, nombre=user.nombre, role=invitation.role)
