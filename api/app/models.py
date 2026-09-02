import enum
import uuid
from datetime import date, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config import settings
from app.db import Base


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


class MembershipRole(str, enum.Enum):
    owner = "owner"
    admin = "admin"
    member = "member"


class LLMProviderKind(str, enum.Enum):
    openai_compat = "openai_compat"
    anthropic = "anthropic"


class Rubro(str, enum.Enum):
    laboral = "laboral"
    comercial = "comercial"
    financiero = "financiero"
    civil = "civil"


class OcrStatus(str, enum.Enum):
    pending = "pending"
    ready = "ready"
    failed = "failed"


class AnalysisStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    done = "done"
    failed = "failed"


class Org(Base):
    __tablename__ = "orgs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    plan_code: Mapped[str] = mapped_column(
        String(20), ForeignKey("plans.code"), nullable=False, default="free"
    )
    paperless_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    paperless_tag_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    paperless_storage_path_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    memberships: Mapped[list["Membership"]] = relationship(back_populates="org")


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    is_superadmin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    memberships: Mapped[list["Membership"]] = relationship(back_populates="user")


class Membership(Base):
    __tablename__ = "memberships"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orgs.id", ondelete="CASCADE"), primary_key=True
    )
    role: Mapped[MembershipRole] = mapped_column(
        Enum(MembershipRole, name="membership_role"), nullable=False, default=MembershipRole.member
    )

    user: Mapped["User"] = relationship(back_populates="memberships")
    org: Mapped["Org"] = relationship(back_populates="memberships")


class Invitation(Base):
    __tablename__ = "invitations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[MembershipRole] = mapped_column(
        Enum(MembershipRole, name="membership_role"), nullable=False, default=MembershipRole.member
    )
    token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Plan(Base):
    __tablename__ = "plans"

    code: Mapped[str] = mapped_column(String(20), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    analisis_mes: Mapped[int] = mapped_column(Integer, nullable=False)
    docs_max: Mapped[int] = mapped_column(Integer, nullable=False)
    precio_bob: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)


class Usage(Base):
    __tablename__ = "usage"

    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orgs.id", ondelete="CASCADE"), primary_key=True
    )
    periodo: Mapped[str] = mapped_column(String(7), primary_key=True)  # 'YYYY-MM'
    analisis_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class LLMProvider(Base):
    __tablename__ = "llm_providers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    kind: Mapped[LLMProviderKind] = mapped_column(
        Enum(LLMProviderKind, name="llm_provider_kind"), nullable=False
    )
    base_url: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    model: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    api_key_enc: Mapped[str] = mapped_column(Text, nullable=False, default="")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    params: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class CuerpoLegal(Base):
    __tablename__ = "cuerpos_legales"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    numero: Mapped[str | None] = mapped_column(String(50), nullable=True)
    fecha: Mapped[date | None] = mapped_column(Date, nullable=True)
    fuente_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")

    articulos: Mapped[list["Articulo"]] = relationship(back_populates="cuerpo")


class Articulo(Base):
    __tablename__ = "articulos"
    __table_args__ = (
        UniqueConstraint("cuerpo_id", "numero", "inciso", "version", name="uq_articulo_version"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    cuerpo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cuerpos_legales.id", ondelete="CASCADE"), nullable=False
    )
    numero: Mapped[str] = mapped_column(String(50), nullable=False)
    inciso: Mapped[str | None] = mapped_column(String(50), nullable=True)
    titulo: Mapped[str | None] = mapped_column(String(500), nullable=True)
    texto: Mapped[str] = mapped_column(Text, nullable=False)
    vigente: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    verificado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    fuente_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    valid_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(settings.EMBEDDING_DIM), nullable=True
    )

    cuerpo: Mapped["CuerpoLegal"] = relationship(back_populates="articulos")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    paperless_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    titulo: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    tipo_contrato: Mapped[str | None] = mapped_column(String(100), nullable=True)
    rubro: Mapped[Rubro | None] = mapped_column(Enum(Rubro, name="rubro"), nullable=True)
    ficha: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    partes: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    clausulas: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    texto: Mapped[str | None] = mapped_column(Text, nullable=True)
    ocr_status: Mapped[OcrStatus] = mapped_column(
        Enum(OcrStatus, name="ocr_status"), nullable=False, default=OcrStatus.pending
    )
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[AnalysisStatus] = mapped_column(
        Enum(AnalysisStatus, name="analysis_status"),
        nullable=False,
        default=AnalysisStatus.queued,
    )
    etapa: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    provider_code: Mapped[str | None] = mapped_column(String(30), nullable=True)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    dictamen: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    tokens_in: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_out: Mapped[int | None] = mapped_column(Integer, nullable=True)
    costo_usd: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
