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
  orgs: OrgRole[];
}

/** POST /auth/register|login|refresh — schemas.TokenResponse. */
export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
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
  created_at: string;
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
  code: "free" | "pro" | "despacho";
  nombre: string;
  analisis_mes: number;
  docs_max: number;
  precio_bob: number;
}

/** GET /usage — schemas.UsageOut (plano, sin org_id ni Plan anidado). */
export interface Usage {
  periodo: string;
  analisis_count: number;
  analisis_mes: number;
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

export interface ApiError {
  detail: string;
}

export type { DocumentoContrato };
