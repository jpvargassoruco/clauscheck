# ClausCheck — HLD / contratos compartidos (v0.1, 2026-09-02)

Este documento es el contrato entre los módulos. Los agentes implementan CONTRA este documento; si algo falta, se decide aquí primero.

## 1. Servicios (docker compose, raíz `infra/`)

| servicio | imagen / build | puerto host | notas |
|---|---|---|---|
| caddy | caddy:2 | 8080 | `/` → web (estático `web/dist`), `/api/*` → api:8000, `/docs-ui/*` → paperless:8000 (strip prefix; PAPERLESS_FORCE_SCRIPT_NAME=/docs-ui) |
| web | build web/ (node 22 → nginx-less: Caddy sirve `web/dist` por volumen) | — | dev: `npm run dev` en :5173 con proxy `/api` → :8080 |
| api | build api/ (python 3.12, uvicorn) | 8001 (dev) | FastAPI, prefijo `/api/v1` |
| worker | build api/ (mismo código, `arq app.worker.WorkerSettings`) | — | jobs de análisis + embeddings |
| postgres | pgvector/pgvector:pg16 | 5433 | DBs `clauscheck`, `paperless`; extensión vector en `clauscheck` |
| redis | redis:7 | — | arq + paperless |
| paperless | ghcr.io/paperless-ngx/paperless-ngx:latest | 8010 | OCR_LANGUAGE=spa, tika+gotenberg habilitados |
| tika, gotenberg | apache/tika, gotenberg/gotenberg | — | |
| cloudflared | cloudflare/cloudflared | — | **profile `edge`** (solo Fase B) |

`.env` (raíz repo, gitignored; `infra/.env.example` documenta): `POSTGRES_PASSWORD`, `PAPERLESS_SECRET_KEY`, `PAPERLESS_ADMIN_USER`, `PAPERLESS_ADMIN_PASSWORD`, `PAPERLESS_API_TOKEN`, `JWT_SECRET`, `FERNET_KEY`, `DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`, `DEEPSEEK_MODEL`, `MOONSHOT_API_KEY`, `OPENROUTER_API_KEY`, `ANTHROPIC_API_KEY`, `EMBEDDING_MODEL=intfloat/multilingual-e5-small`, `CF_TUNNEL_TOKEN`.

## 2. Modelo de datos (Postgres, SQLAlchemy 2 + Alembic). Todo id = uuid.

- `orgs(id, slug uq, nombre, plan_code, paperless_user_id, paperless_tag_id, paperless_storage_path_id, is_demo bool, created_at)`
- `users(id, email uq, password_hash argon2, nombre, is_superadmin, is_active, created_at)`
- `memberships(user_id, org_id, role enum owner|admin|member, pk(user_id,org_id))`
- `invitations(id, org_id, email, role, token uq, expires_at, accepted_at)`
- `plans(code pk free|personal|pro|despacho, nombre, analisis_mes int, docs_max int, precio_bob numeric, palabras_mes int, palabras_max_doc int)` — `palabras_mes` = presupuesto mensual de palabras; `palabras_max_doc` = máximo por documento. Seed: free 5/15.000/5.000 · personal 20/60.000/6.000 · pro ("Despacho") 100/400.000/15.000 · despacho ("Empresa") 300/1.500.000/30.000.
- `usage(org_id, periodo 'YYYY-MM', analisis_count, palabras_count, pk(org_id,periodo))`
- `llm_providers(id, code uq deepseek|moonshot|openrouter|anthropic, kind enum openai_compat|anthropic, base_url, model, api_key_enc (Fernet), enabled, is_default, params jsonb, updated_at)`
- `cuerpos_legales(id, code uq p.ej. CC|CPE|LGT|DS110|LEY065, nombre, tipo, numero, fecha, fuente_url)`
- `articulos(id, cuerpo_id, numero text, inciso text null, titulo null, texto, vigente bool, verificado bool, fuente_url, version int, valid_from date, valid_to date null, embedding vector(384), uq(cuerpo_id,numero,inciso,version))`
- `documents(id, org_id, paperless_id int null, titulo, tipo_contrato, rubro enum laboral|comercial|financiero|civil, ficha jsonb, partes jsonb, clausulas jsonb, texto text, palabras int, ocr_status enum pending|ready|failed, is_public bool, created_by, created_at)` — `palabras` se computa al crear (JSON `texto`) y al sincronizar el OCR (`GET /documents/{id}/status` y pipeline etapa 1).
- `analyses(id, org_id, document_id, status enum queued|running|done|failed, etapa int 0..7, provider_code, model, dictamen jsonb null, error text null, tokens_in, tokens_out, costo_usd numeric, costo_estimado bool, created_by, created_at, started_at, finished_at)` — `costo_estimado=true` salvo que el proveedor haya devuelto `usage` real en TODAS las llamadas del run.

Org demo: slug `clauscheck-demo`, `is_demo=true`, sus documents tienen `is_public=true` y un analysis `done` → corpus de ejemplos.

Aislamiento: toda consulta a documents/analyses/usage pasa por `get_current_org()` (header `X-Org-Id`, validado contra memberships) y filtra `org_id`. Tests de aislamiento obligatorios.

## 3. Esquema JSON del documento y del dictamen (Pydantic en `api/app/schemas/dictamen.py`, TS en `web/src/types/dictamen.ts` — deben coincidir)

```jsonc
// documents.ficha / partes / clausulas
"ficha": {"plaza":"Santa Cruz","fecha":"2024-03-01","cuantia":"USD 15.000","forma_instrumental":"documento privado","tipo_contrato":"anticrético","rubro":"civil"}
"partes": [{"id":"p1","nombre":"J. P. R.","rol":"acreedor anticresista","redacto":true}]
"clausulas": [{"id":"c1","numero":"PRIMERA","titulo":"Objeto","texto":"..."}]

// analyses.dictamen  (version 1.0)
{
  "version":"1.0",
  "indice_riesgo": 87,                 // 0..100, NO es promedio: un crítico eleva el índice
  "nivel": "critico",                  // critico|alto|medio|bajo|informativo
  "confianza": 0.82,
  "resumen": {"hallazgos":5,"omisiones":2,"por_nivel":{"critico":1,"alto":2,"medio":1,"bajo":1,"informativo":0}},
  "sintesis": "párrafo ejecutivo",
  "partes": [{"id":"p1","nombre":"...","rol":"...","redacto":true,"balance":-40,"a_favor":2,"en_contra":5,"lectura":"..."}],
  "hallazgos": [{
    "id":"h1","nivel":"critico","titulo":"...","clausula_id":"c3",
    "cita_textual":"fragmento literal del contrato",
    "fundamento":"explicación jurídica",
    "articulos":[{"articulo_id":"uuid","cuerpo":"CC","numero":"491","inciso":"3","texto":"texto oficial desde BD","fuente_url":"..."}],
    "redaccion_sustitutiva":"...", "beneficia":"p1", "perjudica":"p2"
  }],
  "omisiones": [{"id":"o1","nivel":"critico","titulo":"...","descripcion":"...","articulos":[...],"recomendacion":"..."}],
  "recomendaciones": [{"prioridad":1,"tipo":"correccion|tramite|asesoria","accion":"..."}]
}
```
Escala: crítico = nulidad/inoponibilidad/renuncia irrenunciable; alto = desequilibrio grave/leonino; medio = ambigüedad explotable o carga subsanable; bajo = defecto técnico menor; informativo = conforme a derecho (se documenta).

## 4. API (`/api/v1`, JWT Bearer; refresh token en cookie httpOnly o body)

- `POST /auth/register {email,password,nombre,org_nombre}` → crea user + org (owner). `POST /auth/login`, `POST /auth/refresh`, `GET /auth/me` (incluye orgs+roles).
- `GET /orgs` · `POST /orgs` · `GET /orgs/{id}/members` · `PATCH /orgs/{id}/members/{user_id}` · `POST /orgs/{id}/invitations` · `POST /invitations/{token}/accept`
- Header `X-Org-Id` obligatorio en documents/analyses/usage.
- `POST /documents` multipart `file` (pdf/png/jpg/docx/txt) **o** JSON `{titulo, texto}` → sube a paperless (si file) y crea document `ocr_status=pending`; caps duros anti-abuso (independientes del plan): texto pegado ≤ `MAX_TEXTO_CHARS` (200.000) y archivo ≤ `MAX_UPLOAD_BYTES` (20 MB), ambos 413. `GET /documents` (paginado) · `GET /documents/{id}` · `DELETE /documents/{id}` · `GET /documents/{id}/status` (sincroniza OCR + `palabras`) · `GET /documents/{id}/estimate` → `{palabras, tokens_estimados, costo_estimado_usd, dentro_del_plan, motivo}` (pricing.py, sin llamar al proveedor)
- `POST /analyses {document_id}` → 413 si `document.palabras > plan.palabras_max_doc`; 402 si la cuota mensual de análisis o de palabras del plan está agotada; si ok, **reserva** 1 análisis + las palabras del documento en `usage` (misma transacción) y encola el job, devuelve `{id,status:"queued"}`. Si el job falla, el worker reembolsa esa reserva. `GET /analyses` · `GET /analyses/{id}` (status, etapa, dictamen) · `DELETE`
- `GET /usage` (periodo actual: análisis y palabras, usados vs plan)
- Público sin auth: `GET /public/corpus` (lista documentos demo + índice/nivel/hallazgos) · `GET /public/corpus/{id}` (document + dictamen) · `GET /public/normativa/articulos/{id}`
- Superadmin: `GET/POST/PATCH/DELETE /admin/providers`, `POST /admin/providers/{id}/test` · `GET/POST/PATCH /admin/normativa/cuerpos` · `GET/POST/PATCH/DELETE /admin/normativa/articulos` (filtros cuerpo, numero, q) · `POST /admin/normativa/import` (JSON del formato seed) · `POST /admin/normativa/reembed` · `GET /admin/orgs`, `PATCH /admin/orgs/{id}` (plan) · `GET/PATCH /admin/plans` (incluye `palabras_mes`/`palabras_max_doc`) · `GET /admin/consumo?desde=&hasta=&org_id=` → totales + filas por org (análisis, palabras, tokens_in/out, costo_usd, costo_bs a `USD_BOB`) + serie diaria · `GET /admin/consumo/export.csv` (mismo filtro, CSV)
- `GET /health` (db, redis, paperless).

Errores: JSON `{detail}`; 402 cuota agotada; 403 sin membresía; 404 recursos de otra org (nunca 403 para no filtrar existencia).

## 5. Worker (arq) — job `analyze(analysis_id)`

Etapas (actualizar `analyses.etapa` tras cada una): 1 normalizar (texto desde `documents.texto` o paperless `content` cuando OCR listo) · 2 separar cláusulas (LLM → `clausulas`) · 3 identificar partes + quién redactó (LLM) · 4 detectar patrones de riesgo por cláusula (LLM, candidatos) · 5 contrastar norma: embed(cláusula + candidato) → top-k `articulos` por pgvector (k=8) → LLM elige aplicables SOLO entre esos ids · 6 ponderar impacto por parte (cálculo determinista de balances/índice) · 7 redactar dictamen (LLM, JSON estricto v1.0) → **verificador**: toda `articulos[].articulo_id` debe existir en BD; se reemplaza `texto/fuente_url` por el de BD; citas inexistentes se eliminan y se anota en `confianza`. Guardar tokens/costo; `status=done|failed` con `error` legible.

Proveedores (`api/app/llm/`): interfaz `chat_json(system, user, schema) -> dict`; adaptadores `openai_compat` (DeepSeek `https://api.deepseek.com`, Moonshot `https://api.moonshot.ai/v1`, OpenRouter `https://openrouter.ai/api/v1`) y `anthropic` (Messages API). Selección: `llm_providers.is_default`; fallback env `DEEPSEEK_*`. Un reintento de reparación si el JSON no valida. Embeddings locales con `sentence-transformers` (`intfloat/multilingual-e5-small`, 384 dims, prefijos `query:`/`passage:`).

Paperless: token superusuario en env. Al crear org: user `org-<slug>`, tag `org:<uuid>`, storage path `orgs/<uuid>`. Upload: `POST /api/documents/post_document/` (title, tags) → task id → poll `/api/tasks/?task_id=` → `PATCH /api/documents/{id}/` owner + permissions (solo el user de la org) → `content` = texto OCR. Búsqueda: `/api/documents/?query=&tags__id__all=<tag>`. El usuario final nunca recibe el token ni URLs de paperless.

## 6. Web (Vite + React 18 + TS, react-router, TanStack Query, vite-plugin-pwa, es-BO)

Rutas: `/` landing (Inicio, Producto, Ejemplos=corpus público, Planes, Equipo, Manual, Contacto) · `/login` `/registro` · `/app` (Documentos, Análisis, Historial, Ajustes, selector de org) · `/app/analisis/:id` (progreso 7 etapas + Dictamen) · `/admin` (proveedores, normativa, orgs, planes; solo superadmin). Componente `Dictamen` único para demo y análisis reales, con "Copiar dictamen completo" (texto plano). Marca: azul `#1E3A8A`, dorado `#C9A227`, blanco; tipografías Spectral (títulos) + IBM Plex Sans; modo claro/oscuro.

## 7. Seed (`seed/`)

`normativa.json`: `{"cuerpos":[{code,nombre,tipo,numero,fecha,fuente_url}],"articulos":[{cuerpo,numero,inciso,titulo,texto,fuente_url,verificado}]}`.
`corpus/*.json`: `{document:{titulo,tipo_contrato,rubro,ficha,partes,clausulas,texto}, dictamen:{...v1.0 con articulos referenciados por (cuerpo,numero,inciso)}}` — el importador resuelve ids.
