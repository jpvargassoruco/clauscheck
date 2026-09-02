# Manual de Operaciones — ClausCheck

**Estado: 2026-09-02 — Fase A local operativa**

---

## 1. Estado Actual

| Concepto | Estado |
|---|---|
| **Fase** | A (local, Kali Linux) |
| **Stack completo** | Docker Compose en infra/docker-compose.yml |
| **Smoke test E2E** | ✓ Aprobado (registro → documento por texto → análisis DeepSeek 7 etapas → dictamen con citas verificadas, ~2 min) |
| **Dominio** | Pendiente Fase B |
| **Producción** | Fase B (VM COTAS accesible por VPN) |

---

## 2. Arranque y Parada

### Inicio del stack completo

```bash
cd /home/kali/personal_dev/clauscheck
docker compose -f infra/docker-compose.yml --env-file .env --profile app up -d
```

**Nota importante:** `make` no está instalado en Kali. Los comandos anteriores reemplazan los equivalentes del Makefile. Siempre usar `--env-file .env` desde la raíz del repo o las variables quedarán vacías y paperless reiniciará continuamente.

### Inicialización de BD y seed de datos

Dentro del contenedor api:
```bash
docker compose -f infra/docker-compose.yml --env-file .env --profile app exec api alembic upgrade head
docker compose -f infra/docker-compose.yml --env-file .env --profile app run --rm api python -m app.seed
```

### Detención

```bash
docker compose -f infra/docker-compose.yml --env-file .env down
```

---

## 3. Puertos y Servicios

| Servicio | Puerto | URL | Notas |
|---|---|---|---|
| **Caddy** (reverse proxy) | 8080 | http://localhost:8080 | Sirve web, API y docs-ui (Paperless) |
| **API** | 8001 | http://localhost:8001 | FastAPI, prefijo `/api/v1` |
| **Postgres** | 5433 | postgres://localhost:5433 | BDs: `clauscheck`, `paperless` |
| **Redis** | (interno) | — | arq + Paperless |
| **Paperless** | 8010 | http://localhost:8010 (vía /docs-ui) | OCR (OCR_LANGUAGE=spa, Tika+Gotenberg) |

---

## 4. Credenciales por Defecto

**Cambiar antes de uso comercial:**

| Usuario | Email/Usuario | Contraseña |
|---|---|---|
| **Superadmin API** | admin@clauscheck.local | changeme |
| **Paperless admin** | admin | (en .env) |

Acceder al admin de paperless desde http://localhost:8080/docs-ui/.

---

## 5. Proveedores LLM

### Configuración

Los proveedores se configuran en dos lugares (por orden de precedencia):

1. **Tabla `llm_providers`** en la BD (vía /admin/providers en web o API)
2. **Variables de entorno** (fallback): `DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`, `DEEPSEEK_MODEL`

### Probar un proveedor

```bash
POST /admin/providers/{id}/test
```

### Modelos y endpoints conocidos

| Proveedor | Base URL | Modelo | Tipo |
|---|---|---|---|
| **DeepSeek** | https://api.deepseek.com | deepseek-chat | OpenAI compat |
| **Moonshot** | https://api.moonshot.ai/v1 | moonshot-v1-8k | OpenAI compat |
| **OpenRouter** | https://openrouter.ai/api/v1 | (selectable) | OpenAI compat |
| **Anthropic** | https://api.anthropic.com/v1/messages | claude-opus-4-1 | Anthropic Messages API |

### Advertencia: clave DeepSeek

La clave `DEEPSEEK_API_KEY` en `.env` es **temporal** y debe rotarse antes de clientes reales. **Nunca commitear claves al repo.**

---

## 6. Normativa y Corpus

### Formato de seed

Véase docs/HLD.md §7 y docs/corpus-review.md para el esquema JSON completo.

- **`seed/normativa.json`**: cuerpos legales y artículos. Importar vía `POST /admin/normativa/import`.
- **`seed/corpus/*.json`**: documentos demo y dictámenes ya completados. Auto-importados por `python -m app.seed`.

### Revisión Legal

**IMPORTANTE:** `docs/corpus-review.md` documenta el estado de verificación de cada artículo. El catálogo completo requiere revisión de un abogado habilitado antes de uso comercial.

### Reembed

Si se actualiza la normativa, regenerar embeddings:
```bash
POST /admin/normativa/reembed
```

### Validación

Script de validación en `seed/validate_corpus.py`.

---

## 7. Cuotas y Planes

| Plan | Análisis/mes | Docs máximo | Precio (BOB) |
|---|---|---|---|
| **Free** | 5 | 10 | 0 |
| **Pro** | 50 | 200 | 150 |
| **Despacho** | 500 | 2.000 | 800 |

- Al agotar cuota: respuesta HTTP **402** (Payment Required).
- Uso trackeable vía `GET /usage` (periodo actual vs plan).
- Planes en tabla `plans`, usage en tabla `usage(org_id, periodo 'YYYY-MM', analisis_count)`.

---

## 8. Backup y Restore

### Backup

Desde la raíz del repo:
```bash
./infra/backup.sh
```

Genera en `backups/<timestamp>/`:
- `clauscheck.sql.gz` (BD de clauscheck)
- `paperless.sql.gz` (BD de paperless)
- `paperless-media.tar.gz` (datos y archivos de Paperless)

### Restore

```bash
./infra/restore.sh <timestamp>
```

Ejemplo:
```bash
./infra/restore.sh 20260902-150000
```

**Cuidado:** Esta operación destruye y recrea las BDs. Requiere confirmación interactiva.

---

## 9. Trampas Conocidas

| Trampa | Síntoma | Solución |
|---|---|---|
| Variables vacías en .env | Paperless reinicia, DB connection refused | Ejecutar compose SIEMPRE con `--env-file .env` desde la raíz |
| Puerto 5432 ocupado | postgres no inicia | Cambiar puerto en docker-compose.yml o matar proceso en host |
| seed/ no se monta | "no module named seed" | Volumen en docker-compose.yml monta en `/seed`, la ruta relativa debe ser `../seed` |
| Truncado de JSON en análisis | dictamen incompleto (etapas 4, 5, 7) | Incrementar `max_tokens` en etapas 4/5/7; DeepSeek tiende a truncar |
| Tokens/costo estimados | usage incoherente | Usar ~4 caracteres por token (aproximación) |

---

## 10. Fase B (Pendiente, Sesión Aparte)

### Requisitos

- **VM COTAS**: Ubuntu 24.04, 4vCPU, 8GB RAM, 100GB disco, accesible por VPN OpenVPN existente
- **Dominio**: ClausCheck en Cloudflare (CNAME o A record)
- **Tunnel token**: Cloudflare Tunnel (generar en dashboard)

### Pasos de deployment

1. `VPN_SUBNET=10.8.0.0/24 ./infra/scripts/bootstrap-vm.sh` (en la VM)
2. Clonar repo en `/opt/clauscheck` (o path configurado)
3. Copiar `.env` desde plantilla y llenar secretos
4. `docker compose -f infra/docker-compose.yml --env-file .env --profile app --profile edge up -d`
5. Configurar ruta del tunnel: `<dominio>` → caddy:80
6. Cloudflare Access sobre `/docs-ui` y `/admin`
7. Smoke test E2E
8. Cron de backup (véase `man crontab`)

Ver `infra/scripts/bootstrap-vm.sh` y `infra/scripts/deploy.sh` para detalles.

---

## 11. Pendientes Ordenados por Prioridad

1. **Revisión legal del catálogo y corpus** (docs/corpus-review.md)
   - Abogado debe confirmar Art. 685 CC, completar D.S. 110 art. 2, validar Ley 065 art. 91, etc.

2. **OCR y captura de cámara probados con PDF escaneado real** vía Paperless
   - Validar que Tika+Gotenberg procesan documentos físicos correctamente.

3. **Rotar clave DeepSeek**
   - Generar nueva clave, actualizar .env y BD.

4. **Pagos y planes reales**
   - Integración con procesador de pagos (no definido aún).

5. **Fase B (deployment en VM COTAS)**
   - Requiere VM preparada, dominio, tunnel token, revisión de seguridad.

---

## 12. Referencias

- **Arquitectura detallada**: docs/HLD.md
- **Revisión del corpus normativo**: docs/corpus-review.md
- **Instrucciones globales del proyecto**: /home/kali/.claude/CLAUDE.md

## 13. Inicio de una nueva sesión (leer primero)

1. Leer `CLAUDE.md` (premisas: Fable planifica, Sonnet/Haiku implementan; verbosidad mínima), este HANDOFF y `docs/HLD.md`.
2. Local: `docker compose -f infra/docker-compose.yml --env-file .env --profile app up -d` → `curl -s localhost:8080/api/v1/health` debe dar `ok` en db/redis/paperless. Web en http://localhost:8080.
3. VPS Fase B (COTAS, IP privada por VPN del proyecto cloud.cotas.com):
   `ssh -i /home/kali/it911/cloud.cotas.com/kit_de_bienvenida/jpvargassoruco/cliente/jpvargassoruco-admin_ed25519 ubuntu@10.40.2.235` (host `jpv-srv-01`, Ubuntu 24.04, 4 vCPU / 7 GB / 96 GB). Repo en `/opt/clauscheck`, `.env` propio. Deploy: `infra/scripts/deploy.sh` (ver cabecera del script). Falta: dominio en Cloudflare + token de Tunnel (perfil `edge`), Cloudflare Access sobre `/docs-ui` y `/admin`, cron de backup.
4. Verificado el 2026-09-02 en local: registro → documento (texto pegado y PNG escaneado vía paperless OCR) → análisis DeepSeek 7 etapas (115–140 s) → dictamen con citas verificadas contra la BD; aislamiento entre orgs; cuota free 5/mes.
5. Detalles de integración descubiertos hoy: paperless-ngx 2.x devuelve las tareas como `{results:[...]}` con `status` en minúsculas y el id del documento en `result_data.document_id` / `related_document_ids` (ya soportado); `GET /documents/{id}/status` sincroniza el texto OCR desde paperless y pasa a `ready`; `POST /documents` acepta JSON y multipart; `email-validator` rechaza dominios `.local` en registro (el superadmin `admin@clauscheck.local` entra por login porque `LoginRequest.email` es `str`).
6. Datos de prueba en la BD local (usuarios `smoke*@example.com`, `probe*@example.com`, cuerpo `TESTCUERPO`): se pueden borrar.

## 14. Cambios del 2026-09-02 (tarde) — Fase 0 en marcha

- **Registro por solicitud** (`REGISTRATION_MODE=approval` por defecto): `/solicitar-acceso` → correo al solicitante y a `ADMIN_NOTIFY_EMAIL` → `/admin/solicitudes` aprobar (crea org + invitación) o rechazar → `/invitacion/:token` fija contraseña. `POST /auth/register` responde 403 salvo `REGISTRATION_MODE=open`.
- **Correo SMTP real**: `contacto@clauscheck.info` en `mail.redesk.we.bs:465` (variables `SMTP_*`, `MAIL_BACKEND=smtp`, credenciales en `~/.config/clauscheck/smtp.env` y en los `.env`). Falta SPF/DKIM en la zona `clauscheck.info` (Cloudflare) para no caer en spam.
- **MFA TOTP** para cualquier usuario (Ajustes); el superadmin sigue sin MFA hasta que lo active — hacerlo antes de exponer el sitio.
- **Salida renombrada** a «Informe de revisión asistida» en toda la interfaz, con aviso de responsabilidad fijo y botón «Enviar a un abogado» (placeholder). Claves JSON/DB siguen llamándose `dictamen`.
- **Seudonimización** (`PSEUDONYMIZE=true`): nombres, CI, NIT, teléfonos, correos, cuentas, placas, direcciones y razones sociales se reemplazan por tokens antes de cada llamada al LLM y se restituyen al guardar; mapa en `documents.pseudonyms`. Página `/confidencialidad`.
- **Normativa**: 170 artículos / 18 cuerpos (Ley 453, D.S. 2130, D.S. 4732, Ley 393, Código de Comercio parcial, Ley 708 añadidos). Ver `docs/normativa-consumidor-financiero.md`. Reembed hecho local y en VPS.
- **VPS**: túnel Cloudflare activo (perfil `edge`, token en `.env` del VPS), `PUBLIC_URL=https://mvp.clauscheck.info` para paperless. Pendiente del usuario: crear el hostname público `mvp.clauscheck.info → http://caddy:80` en Zero Trust (crea el DNS) y añadir Cloudflare Access sobre `/docs-ui` y `/admin`. Puerto 8080 del VPS solo alcanzable si se abre en el security group del tenant (no necesario con el túnel).
- **Roadmap comercial**: `docs/dictamen-roadmap.html` (artefacto compartible) con verticales, panel de consumo y BYOK por organización como siguientes ítems de Fase 1.
- Sección «Equipo» y menciones a UAGRM eliminadas del portal a pedido del usuario.
