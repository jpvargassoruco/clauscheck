"""7-stage analysis pipeline (HLD §5).

`app.worker.analyze` resolves the LLM provider, sets
`analyses.provider_code/model`, then calls `run_pipeline`, which drives all
7 stages, updates `analyses.etapa` after each one, and leaves `analysis`
with `status=done` and a validated `dictamen` (or raises, so the caller can
set `status=failed` with a human-readable `error`).

Stage map (HLD §5):
  1 normalizar        -> `normalizar.normalizar`             (no LLM)
  2 separar clausulas  -> LLM (`prompts.clausulas_prompt`)
  3 identificar partes -> LLM (`prompts.partes_prompt`)
  4 detectar riesgos    -> LLM (`prompts.candidatos_prompt`)
  5 contrastar norma    -> pgvector (`retrieval.retrieve_articulos`) + LLM
                            (`prompts.contraste_prompt`)
  6 ponderar            -> `scoring.ponderar`                  (no LLM, deterministic)
  7 redactar dictamen   -> LLM (`prompts.dictamen_prompt`) + `verify.verify_citations`

Token/cost accounting is an estimate: the shared `chat_json(system, user,
schema) -> dict` provider interface (HLD §5) does not expose provider usage
counters, so `tokens_in`/`tokens_out` are approximated from prompt/response
character length (~4 chars/token) via `_estimate_tokens` below, then priced
with `pricing.cost_usd`.
"""

import json
import logging
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.base import LLMProviderBase
from app.models import Analysis, AnalysisStatus, Document, Rubro
from app.schemas.dictamen import DICTAMEN_VERSION, Dictamen, dictamen_json_schema

from .normalizar import normalizar
from .pricing import cost_usd
from .prompts import (
    SYSTEM,
    candidatos_prompt,
    clausulas_prompt,
    contraste_prompt,
    dictamen_prompt,
    partes_prompt,
)
from .retrieval import articulo_to_dict, retrieve_articulos
from .schemas import CANDIDATOS_SCHEMA, CLAUSULAS_SCHEMA, CONTRASTE_SCHEMA, PARTES_SCHEMA
from .scoring import NIVEL_WEIGHT, ponderar
from .verify import verify_citations

logger = logging.getLogger("clauscheck.pipeline")

_RUBRO_VALUES = {r.value for r in Rubro}


def _estimate_tokens(text: str) -> int:
    """Rough ~4 chars/token estimate (see module docstring)."""
    return max(1, len(text) // 4)


def _articulo_citado(a: dict) -> dict:
    return {
        "articulo_id": a["id"],
        "cuerpo": a["cuerpo"],
        "numero": a["numero"],
        "inciso": a["inciso"],
        "texto": a["texto"],
        "fuente_url": a["fuente_url"],
    }


async def run_pipeline(
    db: AsyncSession, analysis: Analysis, document: Document, provider: LLMProviderBase
) -> None:
    tokens_in_total = 0
    tokens_out_total = 0

    async def call_llm(user: str, schema: dict, max_tokens: int = 2048) -> dict:
        nonlocal tokens_in_total, tokens_out_total
        tokens_in_total += _estimate_tokens(SYSTEM) + _estimate_tokens(user)
        result = await provider.chat_json(SYSTEM, user, schema, max_tokens=max_tokens)
        tokens_out_total += _estimate_tokens(json.dumps(result, ensure_ascii=False))
        return result

    async def set_etapa(n: int) -> None:
        analysis.etapa = n
        await db.commit()

    # --- 1. normalizar --------------------------------------------------
    await set_etapa(1)
    try:
        texto = await normalizar(document)
    except Exception:
        # Persist any partial state normalizar() left on `document` (e.g.
        # `ocr_status=failed`) before the caller rolls back on failure.
        await db.commit()
        raise
    await db.commit()

    # --- 2. separar clausulas --------------------------------------------
    await set_etapa(2)
    resp = await call_llm(clausulas_prompt(texto), CLAUSULAS_SCHEMA, max_tokens=4096)
    clausulas = resp.get("clausulas") or []
    document.clausulas = clausulas
    await db.commit()

    # --- 3. identificar partes + redacto ----------------------------------
    await set_etapa(3)
    resp = await call_llm(partes_prompt(texto, clausulas), PARTES_SCHEMA)
    partes = resp.get("partes") or []
    document.partes = partes

    ficha_nuevo = resp.get("ficha") or {}
    ficha = dict(document.ficha or {})
    for k, v in ficha_nuevo.items():
        if v:
            ficha[k] = v
    document.ficha = ficha
    if ficha.get("tipo_contrato"):
        document.tipo_contrato = ficha["tipo_contrato"]
    if ficha.get("rubro") in _RUBRO_VALUES:
        document.rubro = Rubro(ficha["rubro"])
    await db.commit()

    # --- 4. detectar patrones de riesgo (candidatos) ----------------------
    await set_etapa(4)
    resp = await call_llm(candidatos_prompt(clausulas, partes), CANDIDATOS_SCHEMA, max_tokens=8192)
    candidatos = resp.get("candidatos") or []

    # --- 5. contrastar norma: retrieval (pgvector) + LLM selection --------
    await set_etapa(5)
    clausula_by_id = {c["id"]: c for c in clausulas if "id" in c}
    retrieved_by_cand: dict[str, list[dict]] = {}
    articulos_by_id: dict[str, dict] = {}
    allowed_ids: set[str] = set()

    for cand in candidatos:
        clausula_texto = ""
        cid = cand.get("clausula_id")
        if cid and cid in clausula_by_id:
            clausula_texto = clausula_by_id[cid].get("texto", "")
        query_text = f"{clausula_texto} {cand.get('problema', '')}".strip()
        rows = await retrieve_articulos(db, query_text) if query_text else []
        arts = [articulo_to_dict(r) for r in rows]
        retrieved_by_cand[cand.get("id", "")] = arts
        for a in arts:
            articulos_by_id[a["id"]] = a
            allowed_ids.add(a["id"])

    resultado_by_id: dict[str, dict] = {}
    if candidatos:
        resp = await call_llm(
            contraste_prompt(candidatos, retrieved_by_cand, partes),
            CONTRASTE_SCHEMA,
            max_tokens=8192,
        )
        resultado_by_id = {r["id"]: r for r in (resp.get("resultados") or []) if "id" in r}

    hallazgos_ctx: list[dict] = []
    omisiones_ctx: list[dict] = []
    for cand in candidatos:
        cand_id = cand.get("id", "")
        res = resultado_by_id.get(cand_id)
        if not res or not res.get("applicable"):
            continue

        cand_allowed = {a["id"] for a in retrieved_by_cand.get(cand_id, [])}
        chosen_ids = [aid for aid in (res.get("articulo_ids") or []) if aid in cand_allowed]
        arts = [_articulo_citado(articulos_by_id[aid]) for aid in chosen_ids]

        base = {
            "id": cand_id,
            "nivel": res.get("nivel") or cand.get("nivel_tentativo", "informativo"),
            "titulo": cand.get("titulo", ""),
            "fundamento": res.get("fundamento") or cand.get("problema", ""),
            "articulos": arts,
        }
        if cand.get("tipo") == "hallazgo":
            hallazgos_ctx.append(
                {
                    **base,
                    "clausula_id": cand.get("clausula_id"),
                    "cita_textual": cand.get("cita_textual"),
                    "redaccion_sustitutiva": res.get("redaccion_sustitutiva"),
                    "beneficia": res.get("beneficia"),
                    "perjudica": res.get("perjudica"),
                }
            )
        else:
            fundamento = base.pop("fundamento")
            omisiones_ctx.append(
                {
                    **base,
                    "descripcion": fundamento,
                    "recomendacion": res.get("recomendacion"),
                }
            )

    # --- 6. ponderar (deterministic) --------------------------------------
    await set_etapa(6)
    parte_ids = [p["id"] for p in partes if "id" in p]
    partes_calc, indice_riesgo, nivel_global = ponderar(hallazgos_ctx, parte_ids)
    partes_for_prompt = [
        {**p, **partes_calc.get(p["id"], {"balance": 0, "a_favor": 0, "en_contra": 0})}
        for p in partes
    ]

    # --- 7. redactar dictamen (LLM) + verificador --------------------------
    await set_etapa(7)
    # hallazgos_ctx omisiones carry "descripcion" not "fundamento"; the
    # prompt only reads ["fundamento"] for hallazgos and omisiones alike, so
    # give it a matching view without mutating the stored omisiones_ctx.
    omisiones_for_prompt = [{**o, "fundamento": o.get("descripcion", "")} for o in omisiones_ctx]
    resp = await call_llm(
        dictamen_prompt(
            document.ficha,
            partes_for_prompt,
            hallazgos_ctx,
            omisiones_for_prompt,
            indice_riesgo,
            nivel_global,
        ),
        dictamen_json_schema(),
        max_tokens=8192,
    )

    resp["version"] = DICTAMEN_VERSION
    resp["indice_riesgo"] = indice_riesgo
    resp["nivel"] = nivel_global  # deterministic (HLD §5: "Set nivel from índice")

    # partes: balance/a_favor/en_contra are the deterministic stage-6 output;
    # only `lectura` is LLM prose.
    llm_partes_by_id = {p.get("id"): p for p in (resp.get("partes") or [])}
    resp["partes"] = [
        {
            "id": p["id"],
            "nombre": p.get("nombre", ""),
            "rol": p.get("rol", ""),
            "redacto": p.get("redacto", False),
            **partes_calc.get(p["id"], {"balance": 0, "a_favor": 0, "en_contra": 0}),
            "lectura": (llm_partes_by_id.get(p["id"]) or {}).get("lectura"),
        }
        for p in partes
    ]

    # hallazgos/omisiones: nivel/beneficia/perjudica/clausula_id are the
    # deterministic stage-5/6 facts (what `ponderar` scored); titulo,
    # fundamento/descripcion, redaccion_sustitutiva/recomendacion are LLM
    # prose (falling back to the stage-5 base text). `articulos` is kept as
    # authored by the LLM so `verify_citations` below has something to
    # check (and can drop a hallucinated id) — any ctx hallazgo/omision the
    # LLM dropped is re-added with its stage-5 articulos so no deterministic
    # finding is silently lost.
    llm_hallazgos_by_id = {h.get("id"): h for h in (resp.get("hallazgos") or [])}
    final_hallazgos = []
    for ctx in hallazgos_ctx:
        h = llm_hallazgos_by_id.get(ctx["id"], {})
        final_hallazgos.append(
            {
                "id": ctx["id"],
                "nivel": ctx["nivel"],
                "titulo": h.get("titulo") or ctx["titulo"],
                "clausula_id": ctx.get("clausula_id"),
                "cita_textual": h.get("cita_textual") or ctx.get("cita_textual"),
                "fundamento": h.get("fundamento") or ctx["fundamento"],
                "articulos": h.get("articulos") if h else ctx["articulos"],
                "redaccion_sustitutiva": h.get("redaccion_sustitutiva")
                or ctx.get("redaccion_sustitutiva"),
                "beneficia": ctx.get("beneficia"),
                "perjudica": ctx.get("perjudica"),
            }
        )
    resp["hallazgos"] = final_hallazgos

    llm_omisiones_by_id = {o.get("id"): o for o in (resp.get("omisiones") or [])}
    final_omisiones = []
    for ctx in omisiones_ctx:
        o = llm_omisiones_by_id.get(ctx["id"], {})
        final_omisiones.append(
            {
                "id": ctx["id"],
                "nivel": ctx["nivel"],
                "titulo": o.get("titulo") or ctx["titulo"],
                "descripcion": o.get("descripcion") or ctx["descripcion"],
                "articulos": o.get("articulos") if o else ctx["articulos"],
                "recomendacion": o.get("recomendacion") or ctx.get("recomendacion"),
            }
        )
    resp["omisiones"] = final_omisiones

    resp = verify_citations(resp, allowed_ids, articulos_by_id)

    por_nivel = {n: 0 for n in NIVEL_WEIGHT}
    for h in resp["hallazgos"]:
        por_nivel[h["nivel"]] = por_nivel.get(h["nivel"], 0) + 1
    resp["resumen"] = {
        "hallazgos": len(resp["hallazgos"]),
        "omisiones": len(resp["omisiones"]),
        "por_nivel": por_nivel,
    }
    resp.setdefault("recomendaciones", [])
    resp.setdefault("sintesis", "")
    resp.setdefault("confianza", 0.5)

    dictamen = Dictamen.model_validate(resp)

    analysis.dictamen = dictamen.model_dump(mode="json")
    analysis.tokens_in = tokens_in_total
    analysis.tokens_out = tokens_out_total
    analysis.costo_usd = cost_usd(provider.code, provider.model, tokens_in_total, tokens_out_total)
    analysis.status = AnalysisStatus.done
    analysis.finished_at = datetime.now(UTC)
    await db.commit()
