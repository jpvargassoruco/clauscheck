import { useAuthStore } from "@/store/auth";
import type {
  AdminOrg,
  Analysis,
  AnalysisStatus,
  AnalysisSummary,
  Articulo,
  AuthTokens,
  CorpusItem,
  CuerpoLegal,
  DocumentSummary,
  Invitation,
  LlmProvider,
  Member,
  NormativaImportResult,
  Org,
  Plan,
  Role,
  Usage,
  User
} from "@/types/domain";
import type { Dictamen, DocumentoContrato } from "@/types/dictamen";

const API_BASE = "/api/v1";

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  isForm?: boolean;
  withOrg?: boolean;
  skipAuth?: boolean;
  /** Evita el reintento con refresh (usado por el propio /auth/refresh). */
  noRetry?: boolean;
}

let refreshPromise: Promise<string | null> | null = null;

/**
 * `POST /auth/refresh` no usa cookie httpOnly: exige `refresh_token` en el
 * body y devuelve un par de tokens nuevo (rotado) — no un `user`.
 */
async function doRefresh(): Promise<string | null> {
  const { refreshToken } = useAuthStore.getState();
  if (!refreshToken) {
    useAuthStore.getState().logout();
    return null;
  }
  try {
    const res = await fetch(`${API_BASE}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken })
    });
    if (!res.ok) {
      useAuthStore.getState().logout();
      return null;
    }
    const data = (await res.json()) as AuthTokens;
    useAuthStore
      .getState()
      .setTokens({ accessToken: data.access_token, refreshToken: data.refresh_token });
    return data.access_token;
  } catch {
    useAuthStore.getState().logout();
    return null;
  }
}

async function request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, isForm, withOrg, skipAuth, noRetry } = opts;

  const headers: Record<string, string> = {};
  if (!isForm && body !== undefined) {
    headers["Content-Type"] = "application/json";
  }

  const { accessToken, currentOrgId } = useAuthStore.getState();
  if (!skipAuth && accessToken) {
    headers.Authorization = `Bearer ${accessToken}`;
  }
  if (withOrg && currentOrgId) {
    headers["X-Org-Id"] = currentOrgId;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body:
      body === undefined ? undefined : isForm ? (body as FormData) : JSON.stringify(body)
  });

  if (res.status === 401 && !skipAuth && !noRetry) {
    if (!refreshPromise) {
      refreshPromise = doRefresh().finally(() => {
        refreshPromise = null;
      });
    }
    const newToken = await refreshPromise;
    if (newToken) {
      return request<T>(path, { ...opts, noRetry: true });
    }
  }

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = (await res.json()) as { detail?: string };
      if (data.detail) detail = data.detail;
    } catch {
      // cuerpo no-JSON, se usa statusText
    }
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

// ---- auth -------------------------------------------------------------
// POST /auth/register|login|refresh sólo devuelven tokens (schemas.TokenResponse);
// no incluyen `user`. Para tener la sesión completa hay que encadenar GET /auth/me.

export const authApi = {
  register: (input: {
    email: string;
    password: string;
    nombre: string;
    org_nombre: string;
  }) =>
    request<AuthTokens>("/auth/register", {
      method: "POST",
      body: input,
      skipAuth: true
    }),
  login: (input: { email: string; password: string }) =>
    request<AuthTokens>("/auth/login", {
      method: "POST",
      body: input,
      skipAuth: true
    }),
  refresh: () => doRefresh(),
  me: () => request<User>("/auth/me")
};

// ---- orgs ---------------------------------------------------------------

function slugify(text: string): string {
  return (
    text
      .toLowerCase()
      .normalize("NFD")
      .replace(/[̀-ͯ]/g, "")
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "") || "org"
  );
}

export const orgsApi = {
  list: () => request<Org[]>("/orgs"),
  create: (nombre: string, slug?: string) =>
    request<Org>("/orgs", {
      method: "POST",
      body: { nombre, slug: slug || slugify(nombre) }
    }),
  members: (orgId: string) => request<Member[]>(`/orgs/${orgId}/members`),
  updateMember: (orgId: string, userId: string, role: Role) =>
    request<Member>(`/orgs/${orgId}/members/${userId}`, {
      method: "PATCH",
      body: { role }
    }),
  invite: (orgId: string, email: string, role: Role) =>
    request<Invitation>(`/orgs/${orgId}/invitations`, {
      method: "POST",
      body: { email, role }
    }),
  acceptInvitation: (token: string) =>
    request<Member>(`/invitations/${token}/accept`, { method: "POST" })
};

// ---- documents ------------------------------------------------------------
// GET /documents no está paginado con {items,total,...}: devuelve un arreglo
// plano (limit/offset por query, 20/0 por defecto).

export const documentsApi = {
  list: (params: { limit?: number; offset?: number } = {}) => {
    const qs = new URLSearchParams(
      Object.entries(params)
        .filter(([, v]) => v !== undefined)
        .map(([k, v]) => [k, String(v)])
    ).toString();
    return request<DocumentSummary[]>(`/documents${qs ? `?${qs}` : ""}`, {
      withOrg: true
    });
  },
  get: (id: string) =>
    request<DocumentoContrato>(`/documents/${id}`, { withOrg: true }),
  status: (id: string) =>
    request<{ id: string; ocr_status: DocumentSummary["ocr_status"] }>(
      `/documents/${id}/status`,
      { withOrg: true }
    ),
  createFromFile: (file: File, titulo: string) => {
    const form = new FormData();
    form.append("file", file);
    form.append("titulo", titulo);
    return request<DocumentSummary>("/documents", {
      method: "POST",
      body: form,
      isForm: true,
      withOrg: true
    });
  },
  // La API acepta JSON {titulo, texto} en /documents cuando no se manda archivo.
  createFromText: (titulo: string, texto: string) =>
    request<DocumentSummary>("/documents", {
      method: "POST",
      body: { titulo, texto },
      withOrg: true
    }),
  remove: (id: string) =>
    request(`/documents/${id}`, { method: "DELETE", withOrg: true })
};

// ---- analyses ---------------------------------------------------------------
// GET /analyses (lista) NO incluye `dictamen` (schemas.AnalysisOut); sólo
// GET /analyses/{id} lo incluye (schemas.AnalysisDetailOut).

export const analysesApi = {
  list: () => request<AnalysisSummary[]>("/analyses", { withOrg: true }),
  create: (documentId: string) =>
    request<{ id: string; status: AnalysisStatus }>("/analyses", {
      method: "POST",
      body: { document_id: documentId },
      withOrg: true
    }),
  get: (id: string) => request<Analysis>(`/analyses/${id}`, { withOrg: true }),
  remove: (id: string) =>
    request(`/analyses/${id}`, { method: "DELETE", withOrg: true })
};

// ---- usage ------------------------------------------------------------------

export const usageApi = {
  get: () => request<Usage>("/usage", { withOrg: true })
};

// ---- public (sin auth) -------------------------------------------------------

export const publicApi = {
  corpus: () =>
    request<CorpusItem[]>("/public/corpus", { skipAuth: true }),
  corpusItem: (id: string) =>
    request<{ document: DocumentoContrato; dictamen: Dictamen | null }>(
      `/public/corpus/${id}`,
      { skipAuth: true }
    ),
  articulo: (id: string) =>
    request<Articulo>(`/public/normativa/articulos/${id}`, { skipAuth: true })
};

// ---- admin --------------------------------------------------------------------

export interface ProviderCreateInput {
  code: LlmProvider["code"];
  kind: LlmProvider["kind"];
  base_url?: string;
  model?: string;
  api_key: string;
  enabled?: boolean;
  is_default?: boolean;
  params?: Record<string, unknown>;
}

export const adminApi = {
  providers: {
    list: () => request<LlmProvider[]>("/admin/providers"),
    create: (input: ProviderCreateInput) =>
      request<LlmProvider>("/admin/providers", { method: "POST", body: input }),
    update: (id: string, input: Partial<LlmProvider> & { api_key?: string }) =>
      request<LlmProvider>(`/admin/providers/${id}`, {
        method: "PATCH",
        body: input
      }),
    remove: (id: string) =>
      request(`/admin/providers/${id}`, { method: "DELETE" }),
    test: (id: string) =>
      request<{ ok: boolean; detail?: string }>(
        `/admin/providers/${id}/test`,
        { method: "POST" }
      )
  },
  normativa: {
    cuerpos: () => request<CuerpoLegal[]>("/admin/normativa/cuerpos"),
    createCuerpo: (input: Omit<CuerpoLegal, "id">) =>
      request<CuerpoLegal>("/admin/normativa/cuerpos", {
        method: "POST",
        body: input
      }),
    // PATCH /admin/normativa/cuerpos/{id} valida el cuerpo completo (no parcial).
    updateCuerpo: (id: string, input: Omit<CuerpoLegal, "id">) =>
      request<CuerpoLegal>(`/admin/normativa/cuerpos/${id}`, {
        method: "PATCH",
        body: input
      }),
    articulos: (params: { cuerpo?: string; numero?: string; q?: string } = {}) => {
      const qs = new URLSearchParams(
        Object.entries(params).filter(([, v]) => v) as [string, string][]
      ).toString();
      return request<Articulo[]>(
        `/admin/normativa/articulos${qs ? `?${qs}` : ""}`
      );
    },
    // schemas.ArticuloIn: no incluye `version` (lo asigna el servidor).
    createArticulo: (input: Omit<Articulo, "id" | "version">) =>
      request<Articulo>("/admin/normativa/articulos", {
        method: "POST",
        body: input
      }),
    // PATCH /admin/normativa/articulos/{id} valida el artículo completo (no parcial).
    updateArticulo: (id: string, input: Omit<Articulo, "id" | "version">) =>
      request<Articulo>(`/admin/normativa/articulos/${id}`, {
        method: "PATCH",
        body: input
      }),
    removeArticulo: (id: string) =>
      request(`/admin/normativa/articulos/${id}`, { method: "DELETE" }),
    // POST /admin/normativa/import espera JSON (formato seed), no multipart.
    importJson: async (file: File) => {
      const text = await file.text();
      let payload: unknown;
      try {
        payload = JSON.parse(text);
      } catch {
        throw new ApiError(400, "El archivo no es JSON válido.");
      }
      return request<NormativaImportResult>("/admin/normativa/import", {
        method: "POST",
        body: payload
      });
    },
    reembed: () =>
      request<{ reembedded: number }>("/admin/normativa/reembed", {
        method: "POST"
      })
  },
  orgs: {
    list: () => request<AdminOrg[]>("/admin/orgs"),
    updatePlan: (id: string, planCode: string) =>
      request<AdminOrg>(`/admin/orgs/${id}`, {
        method: "PATCH",
        body: { plan_code: planCode }
      })
  },
  plans: {
    list: () => request<Plan[]>("/admin/plans"),
    update: (code: string, input: Partial<Plan>) =>
      request<Plan>(`/admin/plans/${code}`, { method: "PATCH", body: input })
  }
};

// ---- health ---------------------------------------------------------------------

export const healthApi = {
  get: () =>
    request<{ status: "ok" | "degraded"; checks: Record<string, string> }>("/health", {
      skipAuth: true
    })
};
