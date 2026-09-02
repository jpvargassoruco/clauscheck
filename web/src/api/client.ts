import { useAuthStore } from "@/store/auth";
import type {
  AdminOrg,
  Analysis,
  Articulo,
  CorpusItem,
  CuerpoLegal,
  DocumentSummary,
  LlmProvider,
  LoginResponse,
  Membership,
  Paginated,
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

async function doRefresh(): Promise<string | null> {
  try {
    const res = await fetch(`${API_BASE}/auth/refresh`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({})
    });
    if (!res.ok) {
      useAuthStore.getState().logout();
      return null;
    }
    const data = (await res.json()) as { access_token: string };
    useAuthStore.getState().setAccessToken(data.access_token);
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
    credentials: "include",
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

export const authApi = {
  register: (input: {
    email: string;
    password: string;
    nombre: string;
    org_nombre: string;
  }) =>
    request<LoginResponse>("/auth/register", {
      method: "POST",
      body: input,
      skipAuth: true
    }),
  login: (input: { email: string; password: string }) =>
    request<LoginResponse>("/auth/login", {
      method: "POST",
      body: input,
      skipAuth: true
    }),
  refresh: () => doRefresh(),
  me: () => request<User>("/auth/me")
};

// ---- orgs ---------------------------------------------------------------

export const orgsApi = {
  list: () => request<Membership[]>("/orgs"),
  create: (nombre: string) =>
    request<Membership>("/orgs", { method: "POST", body: { nombre } }),
  members: (orgId: string) =>
    request<{ user_id: string; email: string; nombre: string; role: Role }[]>(
      `/orgs/${orgId}/members`
    ),
  updateMember: (orgId: string, userId: string, role: Role) =>
    request(`/orgs/${orgId}/members/${userId}`, {
      method: "PATCH",
      body: { role }
    }),
  invite: (orgId: string, email: string, role: Role) =>
    request(`/orgs/${orgId}/invitations`, {
      method: "POST",
      body: { email, role }
    }),
  acceptInvitation: (token: string) =>
    request(`/invitations/${token}/accept`, { method: "POST" })
};

// ---- documents ------------------------------------------------------------

export const documentsApi = {
  list: (page = 1) =>
    request<Paginated<DocumentSummary>>(`/documents?page=${page}`, {
      withOrg: true
    }),
  get: (id: string) =>
    request<DocumentoContrato>(`/documents/${id}`, { withOrg: true }),
  status: (id: string) =>
    request<{ ocr_status: DocumentSummary["ocr_status"] }>(
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

export const analysesApi = {
  list: () => request<Analysis[]>("/analyses", { withOrg: true }),
  create: (documentId: string) =>
    request<{ id: string; status: string }>("/analyses", {
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
    request<{ document: DocumentoContrato; dictamen: Dictamen }>(
      `/public/corpus/${id}`,
      { skipAuth: true }
    ),
  articulo: (id: string) =>
    request<Articulo>(`/public/normativa/articulos/${id}`, { skipAuth: true })
};

// ---- admin --------------------------------------------------------------------

export const adminApi = {
  providers: {
    list: () => request<LlmProvider[]>("/admin/providers"),
    create: (input: Partial<LlmProvider> & { api_key: string }) =>
      request<LlmProvider>("/admin/providers", { method: "POST", body: input }),
    update: (id: string, input: Partial<LlmProvider>) =>
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
    updateCuerpo: (id: string, input: Partial<CuerpoLegal>) =>
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
    createArticulo: (input: Omit<Articulo, "id">) =>
      request<Articulo>("/admin/normativa/articulos", {
        method: "POST",
        body: input
      }),
    updateArticulo: (id: string, input: Partial<Articulo>) =>
      request<Articulo>(`/admin/normativa/articulos/${id}`, {
        method: "PATCH",
        body: input
      }),
    removeArticulo: (id: string) =>
      request(`/admin/normativa/articulos/${id}`, { method: "DELETE" }),
    importJson: (file: File) => {
      const form = new FormData();
      form.append("file", file);
      return request<{ cuerpos: number; articulos: number }>(
        "/admin/normativa/import",
        { method: "POST", body: form, isForm: true }
      );
    },
    reembed: () =>
      request<{ queued: number }>("/admin/normativa/reembed", {
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
    request<{ db: boolean; redis: boolean; paperless: boolean }>("/health", {
      skipAuth: true
    })
};
