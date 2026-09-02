"""Request/response Pydantic models for the REST API (non-dictamen)."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field

from app.models import AccessRequestStatus, AnalysisStatus, MembershipRole, OcrStatus, Rubro

# --- auth ---------------------------------------------------------------


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    nombre: str = ""
    org_nombre: str


class LoginRequest(BaseModel):
    # Plain str (not EmailStr): login must accept whatever email is on file
    # (e.g. the seeded superadmin admin@clauscheck.local), and email-validator
    # rejects reserved/special-use TLDs like .local even without deliverability
    # checks. Format validation belongs at registration time, not login.
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class OrgRoleOut(BaseModel):
    id: uuid.UUID
    slug: str
    nombre: str
    role: MembershipRole


class MeResponse(BaseModel):
    id: uuid.UUID
    email: str
    nombre: str
    is_superadmin: bool
    mfa_enabled: bool = False
    orgs: list[OrgRoleOut]


class MfaRequiredOut(BaseModel):
    mfa_required: bool = True
    mfa_token: str


class MfaVerifyRequest(BaseModel):
    mfa_token: str
    code: str


class MfaSetupOut(BaseModel):
    secret: str
    otpauth_url: str
    qr: str


class MfaCodeRequest(BaseModel):
    code: str


# --- orgs -----------------------------------------------------------------


class OrgCreate(BaseModel):
    nombre: str
    slug: str


class OrgOut(BaseModel):
    id: uuid.UUID
    slug: str
    nombre: str
    plan_code: str
    is_demo: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class MemberOut(BaseModel):
    user_id: uuid.UUID
    email: str
    nombre: str
    role: MembershipRole


class MemberUpdate(BaseModel):
    role: MembershipRole


class InvitationCreate(BaseModel):
    email: EmailStr
    role: MembershipRole = MembershipRole.member


class InvitationOut(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    email: str
    role: MembershipRole
    token: str
    expires_at: datetime
    accepted_at: datetime | None

    model_config = {"from_attributes": True}


# --- documents --------------------------------------------------------------


class DocumentCreateJSON(BaseModel):
    titulo: str
    texto: str
    tipo_contrato: str | None = None
    rubro: Rubro | None = None


class DocumentOut(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    titulo: str
    tipo_contrato: str | None
    rubro: Rubro | None
    ocr_status: OcrStatus
    is_public: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentDetailOut(DocumentOut):
    ficha: dict
    partes: list
    clausulas: list
    texto: str | None


class DocumentStatusOut(BaseModel):
    id: uuid.UUID
    ocr_status: OcrStatus


# --- analyses -----------------------------------------------------------------


class AnalysisCreate(BaseModel):
    document_id: uuid.UUID


class AnalysisOut(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    document_id: uuid.UUID
    status: AnalysisStatus
    etapa: int
    provider_code: str | None
    model: str | None
    error: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None

    model_config = {"from_attributes": True}


class AnalysisDetailOut(AnalysisOut):
    dictamen: dict | None


class AnalysisQueuedOut(BaseModel):
    id: uuid.UUID
    status: AnalysisStatus


# --- usage --------------------------------------------------------------


class UsageOut(BaseModel):
    periodo: str
    analisis_count: int
    analisis_mes: int
    plan_code: str


# --- public ---------------------------------------------------------------


class PublicCorpusItem(BaseModel):
    id: uuid.UUID
    titulo: str
    tipo_contrato: str | None
    rubro: Rubro | None
    indice_riesgo: int | None = None
    nivel: str | None = None
    hallazgos: int | None = None


class ArticuloPublicOut(BaseModel):
    id: uuid.UUID
    cuerpo: str
    numero: str
    inciso: str | None
    titulo: str | None
    texto: str
    fuente_url: str | None
    vigente: bool

    model_config = {"from_attributes": True}


# --- admin ------------------------------------------------------------------


class ProviderCreate(BaseModel):
    code: str
    kind: str
    base_url: str = ""
    model: str = ""
    api_key: str | None = None
    enabled: bool = True
    is_default: bool = False
    params: dict = Field(default_factory=dict)


class ProviderUpdate(BaseModel):
    base_url: str | None = None
    model: str | None = None
    api_key: str | None = None
    enabled: bool | None = None
    is_default: bool | None = None
    params: dict | None = None


class ProviderOut(BaseModel):
    id: uuid.UUID
    code: str
    kind: str
    base_url: str
    model: str
    enabled: bool
    is_default: bool
    params: dict

    model_config = {"from_attributes": True}


class ProviderTestResult(BaseModel):
    ok: bool
    detail: str | None = None


class CuerpoLegalIn(BaseModel):
    code: str
    nombre: str
    tipo: str = ""
    numero: str | None = None
    # `date`, no `str`: la columna es Date y Pydantic la serializa a ISO
    # (YYYY-MM-DD) sola; declararlo `str` rompía GET (ResponseValidationError).
    fecha: date | None = None
    fuente_url: str = ""


class CuerpoLegalOut(CuerpoLegalIn):
    id: uuid.UUID

    model_config = {"from_attributes": True}


class ArticuloIn(BaseModel):
    cuerpo_id: uuid.UUID
    numero: str
    inciso: str | None = None
    titulo: str | None = None
    texto: str
    vigente: bool = True
    verificado: bool = False
    fuente_url: str = ""


class ArticuloOut(BaseModel):
    id: uuid.UUID
    cuerpo_id: uuid.UUID
    numero: str
    inciso: str | None
    titulo: str | None
    texto: str
    vigente: bool
    verificado: bool
    fuente_url: str
    version: int

    model_config = {"from_attributes": True}


class NormativaImportResult(BaseModel):
    cuerpos_creados: int
    cuerpos_actualizados: int
    articulos_creados: int
    articulos_actualizados: int


class PlanOut(BaseModel):
    code: str
    nombre: str
    analisis_mes: int
    docs_max: int
    precio_bob: float

    model_config = {"from_attributes": True}


class PlanUpdate(BaseModel):
    nombre: str | None = None
    analisis_mes: int | None = None
    docs_max: int | None = None
    precio_bob: float | None = None


class OrgAdminUpdate(BaseModel):
    plan_code: str | None = None


# --- access requests / invitaciones públicas --------------------------------


class AccessRequestCreate(BaseModel):
    nombre: str
    email: EmailStr
    organizacion: str
    telefono: str = ""
    motivo: str = ""
    # Honeypot anti-spam: debe llegar vacío; si viene con contenido se
    # descarta la solicitud silenciosamente (sin revelar el filtro al bot).
    website: str = ""


class AccessRequestOut(BaseModel):
    id: uuid.UUID
    nombre: str
    email: str
    organizacion: str
    telefono: str
    motivo: str
    status: AccessRequestStatus
    created_at: datetime
    decided_at: datetime | None
    org_id: uuid.UUID | None

    model_config = {"from_attributes": True}


class AccessRequestApprove(BaseModel):
    plan_code: str
    role: MembershipRole = MembershipRole.owner


class AccessRequestReject(BaseModel):
    motivo: str = ""


class InvitationPreviewOut(BaseModel):
    org_nombre: str
    email: str
    role: MembershipRole
    expired: bool
    accepted: bool


class InvitationAcceptRequest(BaseModel):
    nombre: str
    password: str = Field(min_length=8)


class PublicConfigOut(BaseModel):
    registration_mode: str
