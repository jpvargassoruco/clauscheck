/** Tipos de dominio adicionales (usuarios, orgs, análisis, admin) — HLD §2/§4. */

import type { Dictamen, DocumentoContrato, Rubro } from "./dictamen";

export type Role = "owner" | "admin" | "member";

export interface Org {
  id: string;
  slug: string;
  nombre: string;
  plan_code: string;
  is_demo: boolean;
  created_at: string;
}

export interface Membership {
  org: Org;
  role: Role;
}

export interface User {
  id: string;
  email: string;
  nombre: string;
  is_superadmin: boolean;
  is_active: boolean;
  orgs: Membership[];
}

export interface AuthTokens {
  access_token: string;
  refresh_token?: string;
  token_type: "bearer";
}

export interface LoginResponse extends AuthTokens {
  user: User;
}

export type OcrStatus = "pending" | "ready" | "failed";

export interface DocumentSummary {
  id: string;
  titulo: string;
  tipo_contrato: string;
  rubro: Rubro;
  ocr_status: OcrStatus;
  is_public: boolean;
  created_at: string;
}

export type AnalysisStatus = "queued" | "running" | "done" | "failed";

export interface Analysis {
  id: string;
  org_id: string;
  document_id: string;
  status: AnalysisStatus;
  etapa: number; // 0..7
  provider_code: string | null;
  model: string | null;
  dictamen: Dictamen | null;
  error: string | null;
  tokens_in: number | null;
  tokens_out: number | null;
  costo_usd: number | null;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
}

export interface CorpusItem {
  id: string;
  titulo: string;
  tipo_contrato: string;
  rubro: Rubro;
  indice_riesgo: number;
  nivel: string;
  hallazgos: number;
}

export interface Plan {
  code: "free" | "pro" | "despacho";
  nombre: string;
  analisis_mes: number;
  docs_max: number;
  precio_bob: number;
}

export interface Usage {
  org_id: string;
  periodo: string;
  analisis_count: number;
  plan: Plan;
}

export interface LlmProvider {
  id: string;
  code: "deepseek" | "moonshot" | "openrouter" | "anthropic";
  kind: "openai_compat" | "anthropic";
  base_url: string;
  model: string;
  enabled: boolean;
  is_default: boolean;
  params: Record<string, unknown>;
  updated_at: string;
}

export interface CuerpoLegal {
  id: string;
  code: string;
  nombre: string;
  tipo: string;
  numero: string;
  fecha: string;
  fuente_url: string;
}

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

export interface AdminOrg extends Org {
  paperless_user_id: number | null;
}

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface ApiError {
  detail: string;
}

export type { DocumentoContrato };
