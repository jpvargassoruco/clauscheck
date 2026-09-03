/**
 * Tipos de dominio adicionales (usuarios, orgs, análisis, admin) — HLD §2/§4.
 * Espejo de las respuestas reales de `api/app/schemas/api.py` (verificado
 * contra la API en ejecución), no de una forma "ideal".
 */

import type { Dictamen, DocumentoContrato, Rubro } from "./dictamen";

export type Role = "owner" | "admin" | "member";

/** GET /orgs, POST /orgs, GET/PATCH /admin/orgs — schemas.OrgOut */
export interface Org {
  id: string;
  slug: string;
  nombre: string;
  plan_code: string;
  is_demo: boolean;
  created_at: string;
}

/** Elemento de `MeResponse.orgs` (schemas.OrgRoleOut): org "aplanada" + role. */
export interface OrgRole {
  id: string;
  slug: string;
  nombre: string;
  role: Role;
}

/** GET /auth/me — schemas.MeResponse (no incluye is_active). */
export interface User {
  id: string;
  email: string;
  nombre: string;
  is_superadmin: boolean;
  mfa_enabled: boolean;
  orgs: OrgRole[];
}

/** POST /auth/register|login|refresh|mfa/verify — schemas.TokenResponse. */
export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
}

/** POST /auth/login cuando el usuario tiene MFA activo — schemas.MfaRequiredOut. */
export interface MfaRequired {
  mfa_required: true;
  mfa_token: string;
}

/** POST /auth/mfa/setup — schemas.MfaSetupOut. */
export interface MfaSetup {
  secret: string;
  otpauth_url: string;
  qr: string;
}

/** GET /public/config — schemas.PublicConfigOut. */
export interface PublicConfig {
  registration_mode: "open" | "approval" | "closed";
}

export type AccessRequestStatusValue = "pending" | "approved" | "rejected";

/** GET/POST /admin/access-requests — schemas.AccessRequestOut. */
export interface AccessRequest {
  id: string;
  nombre: string;
  email: string;
  organizacion: string;
  telefono: string;
  motivo: string;
  status: AccessRequestStatusValue;
  created_at: string;
  decided_at: string | null;
  org_id: string | null;
}

/** GET /public/invitations/{token} — schemas.InvitationPreviewOut. */
export interface InvitationPreview {
  org_nombre: string;
  email: string;
  role: Role;
  expired: boolean;
  accepted: boolean;
}

/** GET /orgs/{id}/members, PATCH .../members/{user_id}, POST /invitations/{token}/accept — schemas.MemberOut */
export interface Member {
  user_id: string;
  email: string;
  nombre: string;
  role: Role;
}

/** POST /orgs/{id}/invitations — schemas.InvitationOut */
export interface Invitation {
  id: string;
  org_id: string;
  email: string;
  role: Role;
  token: string;
  expires_at: string;
  accepted_at: string | null;
}

export type OcrStatus = "pending" | "ready" | "failed";

/** POST /documents, GET /documents (lista) — schemas.DocumentOut */
export interface DocumentSummary {
  id: string;
  org_id: string;
  titulo: string;
  tipo_contrato: string | null;
  rubro: Rubro | null;
  ocr_status: OcrStatus;
  is_public: boolean;
  palabras: number;
  created_at: string;
}

/** GET /documents/{id}/estimate — schemas.DocumentEstimateOut */
export interface DocumentEstimate {
  palabras: number;
  tokens_estimados: number;
  costo_estimado_usd: number;
  dentro_del_plan: boolean;
  motivo: string;
}

export type AnalysisStatus = "queued" | "running" | "done" | "failed";

/** GET /analyses (lista) — schemas.AnalysisOut (sin dictamen). */
export interface AnalysisSummary {
  id: string;
  org_id: string;
  document_id: string;
  status: AnalysisStatus;
  etapa: number; // 0..7
  provider_code: string | null;
  model: string | null;
  error: string | null;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
}

/** GET /analyses/{id} — schemas.AnalysisDetailOut (AnalysisOut + dictamen). */
export interface Analysis extends AnalysisSummary {
  dictamen: Dictamen | null;
}

/** GET /public/corpus (lista) — schemas.PublicCorpusItem */
export interface CorpusItem {
  id: string;
  titulo: string;
  tipo_contrato: string | null;
  rubro: Rubro | null;
  indice_riesgo: number | null;
  nivel: string | null;
  hallazgos: number | null;
}

/** GET/PATCH /admin/plans — schemas.PlanOut */
export interface Plan {
  code: "free" | "personal" | "pro" | "despacho";
  nombre: string;
  analisis_mes: number;
  docs_max: number;
  precio_bob: number;
  palabras_mes: number;
  palabras_max_doc: number;
}

/** GET /usage — schemas.UsageOut (plano, sin org_id ni Plan anidado). */
export interface Usage {
  periodo: string;
  analisis_count: number;
  analisis_mes: number;
  palabras_count: number;
  palabras_mes: number;
  plan_code: string;
}

/** GET/POST/PATCH /admin/providers — schemas.ProviderOut (api_key nunca se devuelve). */
export interface LlmProvider {
  id: string;
  code: "deepseek" | "moonshot" | "openrouter" | "anthropic";
  kind: "openai_compat" | "anthropic";
  base_url: string;
  model: string;
  enabled: boolean;
  is_default: boolean;
  params: Record<string, unknown>;
}

/** GET/POST/PATCH /admin/normativa/cuerpos — schemas.CuerpoLegalOut */
export interface CuerpoLegal {
  id: string;
  code: string;
  nombre: string;
  tipo: string;
  numero: string | null;
  fecha: string | null;
  fuente_url: string;
}

/** GET/POST/PATCH /admin/normativa/articulos — schemas.ArticuloOut */
export interface Articulo {
  id: string;
  cuerpo_id: string;
  numero: string;
  inciso: string | null;
  titulo: string | null;
  texto: string;
  vigente: boolean;
  verificado: boolean;
  fuente_url: string;
  version: number;
}

/** POST /admin/normativa/import — schemas.NormativaImportResult */
export interface NormativaImportResult {
  cuerpos_creados: number;
  cuerpos_actualizados: number;
  articulos_creados: number;
  articulos_actualizados: number;
}

/** GET/PATCH /admin/orgs — misma forma que OrgOut (paperless_* no se expone). */
export type AdminOrg = Org;

// ---- admin: consumo -----------------------------------------------------
// GET /admin/consumo — schemas.ConsumoOut

export interface ConsumoOrgRow {
  org_id: string;
  org_nombre: string;
  plan_code: string;
  analisis: number;
  palabras: number;
  tokens_in: number;
  tokens_out: number;
  costo_usd: number;
  costo_bs: number;
  analisis_mes_plan: number;
  palabras_mes_plan: number;
  analisis_mes_usado: number;
  palabras_mes_usado: number;
}

export interface ConsumoDiaRow {
  fecha: string;
  analisis: number;
  palabras: number;
  costo_usd: number;
}

export interface ConsumoTotales {
  analisis: number;
  palabras: number;
  tokens_in: number;
  tokens_out: number;
  costo_usd: number;
  costo_bs: number;
}

export interface Consumo {
  desde: string;
  hasta: string;
  usd_bob: number;
  totales: ConsumoTotales;
  rows: ConsumoOrgRow[];
  serie_diaria: ConsumoDiaRow[];
}

export interface ApiError {
  detail: string;
}

export type { DocumentoContrato };
