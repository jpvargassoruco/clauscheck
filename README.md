# ClausCheck

**Análisis jurídico automatizado de contratos con DeepSeek + normativa boliviana verificada.**

ClausCheck es un sistema SaaS que analiza documentos contractuales contra un catálogo de normativa legal boliviana, identificando riesgos, omisiones y fundamentos legales en segundos. Utiliza LLMs (DeepSeek, Moonshot, OpenRouter, Anthropic) con embeddings locales y verificación de citas.

---

## Stack Técnico

| Capa | Tecnología | Notas |
|---|---|---|
| **Frontend** | Vite + React 18 + TypeScript | Estático (web/dist), servido por Caddy |
| **Backend** | FastAPI (Python 3.12) + SQLAlchemy 2 | Prefijo `/api/v1`, JWT auth |
| **Worker** | arq (async Redis queue) | Análisis de 7 etapas, embeddings locales |
| **Base de datos** | PostgreSQL 16 + pgvector | DBs: clauscheck, paperless |
| **Cache/Queue** | Redis 7 | arq + Paperless |
| **OCR/Docs** | Paperless-ngx + Tika + Gotenberg | OCR español, PDF/DOCX/imagen |
| **Reverse proxy** | Caddy 2 | Routing a web/api/docs-ui |
| **Deployment** | Docker Compose | Fase A: local; Fase B: VM + Cloudflare Tunnel |

---

## Estructura de Carpetas

```
clauscheck/
├── README.md                    # Este archivo
├── Makefile                     # Equivalentes en docker compose (solo referencia)
├── .env                         # Secretos (gitignored, ver infra/.env.example)
│
├── docs/
│   ├── HLD.md                   # Contrato detallado entre módulos (obligatorio leer)
│   ├── HANDOFF.md               # Manual de operaciones
│   ├── corpus-review.md         # Estado de verificación de la normativa
│
├── infra/
│   ├── docker-compose.yml       # Definición de servicios
│   ├── .env.example             # Plantilla de .env
│   ├── Caddyfile                # Configuración de reverse proxy
│   ├── postgres-init/           # Init scripts para Postgres
│   ├── backup.sh                # Backup de BDs y archivos de Paperless
│   ├── restore.sh               # Restore desde backup
│   ├── scripts/
│   │   ├── bootstrap-vm.sh      # Setup inicial VM Ubuntu 24.04 (Fase B)
│   │   └── deploy.sh            # Deploy remoto via SSH (Fase B)
│   └── data/                    # Volúmenes (postgres, redis, caddy, paperless)
│
├── api/
│   ├── Dockerfile               # Python 3.12 + FastAPI
│   ├── pyproject.toml           # Dependencias (ruff, pytest, SQLAlchemy, fastapi)
│   ├── alembic/                 # Migraciones de BD
│   └── app/
│       ├── main.py              # Punto de entrada FastAPI
│       ├── config.py            # Settings desde .env
│       ├── seed.py              # Bootstrap: planes, demo org, normativa, corpus
│       ├── models.py            # SQLAlchemy ORM (orgs, users, documents, analyses, etc.)
│       ├── schemas/             # Pydantic (dictamen.py, authschemas, etc.)
│       ├── db.py                # SessionMaker async
│       ├── security.py          # JWT, Argon2, Fernet
│       ├── llm/                 # Interfaces LLM (openai_compat, anthropic)
│       ├── routers/             # FastAPI routers (/auth, /documents, /analyses, /admin)
│       ├── worker.py            # arq WorkerSettings (job analyze)
│       └── normativa_import.py  # Importador JSON de normativa
│
├── web/
│   ├── Dockerfile               # Node 22 → Vite build → dist/
│   ├── package.json             # Dependencias (React, react-router, TanStack Query, etc.)
│   ├── vite.config.ts           # Proxy /api → :8080
│   ├── src/
│   │   ├── main.tsx             # Entry point React
│   │   ├── App.tsx              # Rutas principales
│   │   ├── types/               # TypeScript (dictamen.ts, etc.)
│   │   ├── pages/               # Landing, login, app, admin
│   │   ├── components/          # React (Dictamen, DocumentList, etc.)
│   │   └── api/                 # Cliente fetch wrapper
│   └── dist/                    # Build estático (montado por Caddy)
│
└── seed/
    ├── normativa.json           # Catálogo de leyes bolivianas
    ├── corpus/                  # Documentos demo + dictámenes
    └── validate_corpus.py       # Validador de esquema
```

---

## Arranque Rápido (5 Comandos)

**Prerequisitos:** Docker + Docker Compose en Kali Linux, 8GB RAM disponibles.

```bash
# 1. Clonar y navegar
cd /home/kali/personal_dev/clauscheck

# 2. Crear .env (copiar plantilla y llenar POSTGRES_PASSWORD, etc.)
cp infra/.env.example .env
# Editar .env: POSTGRES_PASSWORD, PAPERLESS_SECRET_KEY, JWT_SECRET, FERNET_KEY, DEEPSEEK_API_KEY

# 3. Crear volúmenes e iniciar stack
docker compose -f infra/docker-compose.yml --env-file .env --profile app up -d

# 4. Migrar BD y cargar datos iniciales
docker compose -f infra/docker-compose.yml --env-file .env --profile app exec api alembic upgrade head
docker compose -f infra/docker-compose.yml --env-file .env --profile app run --rm api python -m app.seed

# 5. Acceder
echo "Web: http://localhost:8080"
echo "API: http://localhost:8080/api/v1/health"
echo "Admin: http://localhost:8080/admin (login: admin@clauscheck.local / changeme)"
```

**Verificar setup:**
```bash
docker compose -f infra/docker-compose.yml --env-file .env ps
docker compose -f infra/docker-compose.yml --env-file .env logs -f --tail=50
```

---

## Prueba E2E (Smoke Test)

1. Acceder a http://localhost:8080/registro
2. Crear usuario: nombre@example.com / password / Org test
3. Login y subir un documento (texto o PDF)
4. Crear análisis (click en "Analizar")
5. Esperar ~2 min, verificar dictamen con 7 etapas + hallazgos + citas verificadas

Cada análisis genera un HTTP POST a `/api/v1/analyses/{id}` con etapa, status y dictamen JSON v1.0.

---

## Administración

### Superadmin (web)

**URL:** http://localhost:8080/admin
**Credenciales por defecto:** admin@clauscheck.local / changeme

**Secciones:**
- **Proveedores LLM**: crear/editar/probar endpoints (DeepSeek, Moonshot, OpenRouter, Anthropic)
- **Normativa**: importar `normativa.json`, reembed, CRUD artículos
- **Organizaciones**: gestionar planes, uso, miembros
- **Planes**: editar cuotas (free=5, pro=50, despacho=500 análisis/mes)

### Backup/Restore

```bash
# Backup
./infra/backup.sh              # → backups/20260902-150000/

# Restore
./infra/restore.sh 20260902-150000
```

### Base de datos (psql)

```bash
docker compose -f infra/docker-compose.yml --env-file .env exec postgres psql -U postgres -d clauscheck
```

---

## Documentación Principal

- **[docs/HLD.md](docs/HLD.md)** — Arquitectura detallada: servicios, esquema BD, API, worker, seed
- **[docs/HANDOFF.md](docs/HANDOFF.md)** — Manual de operaciones: arranque, proveedores LLM, backup, trampas conocidas, Fase B
- **[docs/corpus-review.md](docs/corpus-review.md)** — Estado de verificación de la normativa legal boliviana

---

## Notas de Desarrollo

### Premisas de trabajo

1. **Idioma:** El usuario puede escribir en español o inglés; siempre responder en inglés (salvo que pida otro idioma explícitamente).
2. **Atribución:** Commits y PRs con firma `Claude Fable 5.1 <noreply@anthropic.com>` y enlace a sesión.

### Estado actual (2026-09-02)

- **Fase A (local):** Stack completo en Docker, smoke test E2E aprobado (~2 min análisis).
- **Fase B (pendiente):** VM Ubuntu 24.04 en COTAS con Cloudflare Tunnel, acceso por VPN OpenVPN.
- **Revisión legal:** Catálogo normativo requiere validación de abogado antes de clientes reales.

### Variables de entorno críticas

```env
POSTGRES_PASSWORD=          # Postgres
JWT_SECRET=                 # JWT sign
FERNET_KEY=                 # Encrypt LLM keys (32 bytes base64)
DEEPSEEK_API_KEY=          # LLM (fallback si no en BD)
PAPERLESS_SECRET_KEY=      # Paperless
PAPERLESS_ADMIN_PASSWORD=  # Paperless admin
```

Nunca commitear `.env` ni claves al repo.

---

## Próximos Pasos

1. Revisión legal de corpus (véase docs/corpus-review.md)
2. OCR real con Paperless (PDF escaneado)
3. Rotar clave DeepSeek
4. Implementar pagos y planes reales
5. Fase B: deployment en VM COTAS con Cloudflare Tunnel

---

**Contacto / Problemas:** Email del usuario en `.claude/CLAUDE.md` (jpvargas.soruco@gmail.com).
