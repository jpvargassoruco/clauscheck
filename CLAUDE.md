# ClausCheck — reglas del proyecto

## Premisas de trabajo (definidas por el usuario, 2026-09-02)
1. **Fable 5.1** actúa como profesional de desarrollo de software e infraestructura IT: planifica, investiga,
   interpreta los prompts del usuario y diseña arquitectura. **Toda otra tarea se delega** a modelos más
   económicos (Sonnet para implementación, Haiku para tareas mecánicas/documentación).
2. **Verbosidad mínima** del agente principal y de los agentes delegados, salvo que el usuario pida
   explícitamente explicaciones puntuales.

## Qué es
SaaS LegalTech multitenant (Bolivia): detecta cláusulas abusivas/engañosas en contratos y emite un
dictamen con citas normativas verificadas contra la base de datos. PWA (Vite+React+TS) + API FastAPI +
worker (arq) + Postgres/pgvector + Redis + paperless-ngx (gestor documental) tras Caddy.

## Dónde
- Fase A (actual): todo corre local en Kali con Docker Compose → `http://localhost:8080` (postgres :5433, paperless :8010).
- Fase B: VM en nube COTAS tras Cloudflare Tunnel con dominio propio (perfil compose `edge`).
- Repo: https://github.com/jpvargassoruco/clauscheck (privado).
- Plan aprobado: `~/.claude/plans/en-el-directorio-de-radiant-key.md`. Operación: `docs/HANDOFF.md`.

## Reglas duras
- Claves de proveedores LLM solo en `.env` del servidor / `~/.config/clauscheck/llm.env`. Nunca en el repo.
- El LLM solo cita artículos devueltos por la recuperación (pgvector); el verificador descarta citas
  inexistentes. El texto normativo mostrado es SIEMPRE el de la BD (oficial, con URL fuente).
- Todo dato de tenant lleva `org_id`; paperless nunca se expone directo al usuario final.
- Contenido legal del corpus/normativa es sintético/recopilado: pendiente de revisión de abogado (`docs/corpus-review.md`).
