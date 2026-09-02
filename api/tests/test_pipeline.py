"""Tests for the 7-stage analysis pipeline (HLD §5), run through the real
`app.worker.analyze` job with a scripted LLM provider and seeded `articulos`
(real embeddings, via the actual `sentence-transformers` model) in the
throwaway Postgres started for this test run. No arq/redis involved: the
job function is invoked directly, exactly as arq would call it.
"""

import uuid

from app import worker
from app.db import async_session_maker
from app.embeddings import embed_passages
from app.models import (
    Analysis,
    AnalysisStatus,
    Articulo,
    CuerpoLegal,
    Document,
    OcrStatus,
    Org,
)
from app.schemas.dictamen import Dictamen

CONTRATO_TEXTO = (
    "PRIMERA. Objeto: el acreedor anticresista recibe en garantía el inmueble.\n"
    "SEGUNDA. Interés: el deudor pagará un interés del 5% mensual sobre el capital."
)


class ScriptedProvider:
    """Duck-types `LLMProviderBase.chat_json` (HLD §5) with a fixed script,
    one response per call in order — like `app.llm.fake.FakeProvider` but
    supporting a sequence of distinct per-stage responses instead of a
    single static one, which a full-pipeline test needs.
    """

    code = "fake"
    model = "fake-model"

    def __init__(self, responses: list[dict]):
        self._responses = list(responses)
        self.calls = 0

    async def chat_json(self, system, user, schema, max_tokens=2048):
        resp = self._responses[self.calls]
        self.calls += 1
        return resp


async def _seed_articulos(db) -> dict[str, Articulo]:
    cuerpo = CuerpoLegal(
        code="CC", nombre="Código Civil", tipo="codigo", fuente_url="https://example.org/cc"
    )
    db.add(cuerpo)
    await db.flush()

    rows = [
        (
            "491",
            "3",
            "El acreedor anticresista debe restituir el inmueble al concluir el contrato.",
        ),
        ("1430", None, "Es nulo el pacto que dispensa al deudor de restituir el capital recibido."),
        ("518", None, "Los contratos deben ejecutarse de buena fe."),
        ("535", None, "El precio o interés pactado no puede exceder los límites legales."),
        ("628", "2", "Toda estipulación que imponga una tasa de interés usuraria es nula."),
    ]
    vectors = embed_passages([texto for _, _, texto in rows])

    articulos: dict[str, Articulo] = {}
    for (numero, inciso, texto), vec in zip(rows, vectors, strict=True):
        art = Articulo(
            cuerpo_id=cuerpo.id,
            numero=numero,
            inciso=inciso,
            texto=texto,
            fuente_url=f"https://example.org/cc/{numero}",
            vigente=True,
            verificado=True,
            version=1,
            embedding=vec,
        )
        db.add(art)
        articulos[f"{numero}-{inciso}"] = art
    await db.flush()
    await db.commit()
    for art in articulos.values():
        await db.refresh(art)
    return articulos


async def _create_org_document(
    db, texto: str | None = CONTRATO_TEXTO, paperless_id: int | None = None
) -> tuple[Org, Document, Analysis]:
    org = Org(slug=f"org-{uuid.uuid4().hex[:8]}", nombre="Test Org", plan_code="free")
    db.add(org)
    await db.flush()

    document = Document(
        org_id=org.id,
        titulo="Contrato de prueba",
        texto=texto,
        ocr_status=OcrStatus.ready if texto else OcrStatus.pending,
        paperless_id=paperless_id,
    )
    db.add(document)
    await db.flush()

    analysis = Analysis(
        org_id=org.id, document_id=document.id, status=AnalysisStatus.queued, etapa=0
    )
    db.add(analysis)
    await db.commit()
    await db.refresh(document)
    await db.refresh(analysis)
    return org, document, analysis


def _happy_responses(art_628_id: str, art_1430_id: str) -> list[dict]:
    return [
        {
            "clausulas": [
                {
                    "id": "c1",
                    "numero": "PRIMERA",
                    "titulo": "Objeto",
                    "texto": "El acreedor anticresista recibe en garantía el inmueble.",
                },
                {
                    "id": "c2",
                    "numero": "SEGUNDA",
                    "titulo": "Interés",
                    "texto": "El deudor pagará un interés del 5% mensual sobre el capital.",
                },
            ]
        },
        {
            "partes": [
                {
                    "id": "p1",
                    "nombre": "Juan Pérez",
                    "rol": "acreedor anticresista",
                    "redacto": True,
                },
                {
                    "id": "p2",
                    "nombre": "María López",
                    "rol": "deudor anticresista",
                    "redacto": False,
                },
            ],
            "ficha": {
                "plaza": "Santa Cruz",
                "fecha": "2024-01-01",
                "cuantia": "USD 10.000",
                "forma_instrumental": "documento privado",
                "tipo_contrato": "anticrético",
                "rubro": "civil",
            },
        },
        {
            "candidatos": [
                {
                    "id": "h1",
                    "tipo": "hallazgo",
                    "clausula_id": "c2",
                    "titulo": "Interés usurario",
                    "problema": "La cláusula segunda impone un interés mensual que podría exceder el límite legal.",
                    "nivel_tentativo": "alto",
                    "palabras_clave": ["interés", "usura"],
                    "cita_textual": "El deudor pagará un interés del 5% mensual sobre el capital.",
                },
                {
                    "id": "o1",
                    "tipo": "omision",
                    "clausula_id": None,
                    "titulo": "Falta restitución del capital",
                    "problema": "El contrato no establece la obligación de restituir el capital anticrético al finalizar.",
                    "nivel_tentativo": "critico",
                    "palabras_clave": ["restitución", "capital"],
                    "cita_textual": None,
                },
            ]
        },
        {
            "resultados": [
                {
                    "id": "h1",
                    "applicable": True,
                    "nivel": "alto",
                    "beneficia": "p1",
                    "perjudica": "p2",
                    "articulo_ids": [art_628_id],
                    "fundamento": "La tasa pactada excede el límite permitido por ley.",
                    "redaccion_sustitutiva": "El interés no podrá exceder la tasa máxima legal.",
                    "recomendacion": None,
                },
                {
                    "id": "o1",
                    "applicable": True,
                    "nivel": "critico",
                    "beneficia": None,
                    "perjudica": "p2",
                    "articulo_ids": [art_1430_id],
                    "fundamento": "El contrato omite la restitución del capital, exigida por la norma.",
                    "redaccion_sustitutiva": None,
                    "recomendacion": "Incluir cláusula expresa de restitución del capital.",
                },
            ]
        },
        {
            "sintesis": "El contrato anticrético presenta un interés potencialmente usurario y omite la restitución del capital.",
            "confianza": 0.8,
            "partes": [
                {"id": "p1", "lectura": "Parte beneficiada por la omisión y el interés elevado."},
                {
                    "id": "p2",
                    "lectura": "Parte perjudicada por el interés elevado y la omisión del capital.",
                },
            ],
            "hallazgos": [
                {
                    "id": "h1",
                    "titulo": "Interés usurario",
                    "fundamento": "La tasa del 5% mensual excede el límite legal permitido.",
                    "cita_textual": "El deudor pagará un interés del 5% mensual sobre el capital.",
                    "redaccion_sustitutiva": "El interés no podrá exceder la tasa máxima legal.",
                    "articulos": [
                        {
                            "articulo_id": art_628_id,
                            "cuerpo": "CC",
                            "numero": "628",
                            "inciso": "2",
                            "texto": "placeholder",
                            "fuente_url": "placeholder",
                        }
                    ],
                }
            ],
            "omisiones": [
                {
                    "id": "o1",
                    "titulo": "Falta restitución del capital",
                    "descripcion": "El contrato no obliga expresamente a restituir el capital al concluir.",
                    "recomendacion": "Incluir cláusula expresa de restitución del capital.",
                    "articulos": [
                        {
                            "articulo_id": art_1430_id,
                            "cuerpo": "CC",
                            "numero": "1430",
                            "inciso": None,
                            "texto": "placeholder",
                            "fuente_url": "placeholder",
                        }
                    ],
                }
            ],
            "recomendaciones": [
                {
                    "prioridad": 1,
                    "tipo": "correccion",
                    "accion": "Incluir cláusula de restitución del capital.",
                }
            ],
        },
    ]


async def test_full_pipeline_happy_path(monkeypatch):
    async with async_session_maker() as db:
        articulos = await _seed_articulos(db)
        art_628_id = str(articulos["628-2"].id)
        art_1430_id = str(articulos["1430-None"].id)
        org, document, analysis = await _create_org_document(db)
        analysis_id = str(analysis.id)

    provider = ScriptedProvider(_happy_responses(art_628_id, art_1430_id))

    async def _fake_get_default_provider(_db):
        return provider

    monkeypatch.setattr(worker, "get_default_provider", _fake_get_default_provider)

    await worker.analyze({}, analysis_id)

    async with async_session_maker() as db:
        analysis2 = await db.get(Analysis, analysis_id)
        document2 = await db.get(Document, document.id)

        assert analysis2.status == AnalysisStatus.done, analysis2.error
        assert analysis2.etapa == 7
        assert analysis2.provider_code == "fake"
        assert analysis2.model == "fake-model"
        assert analysis2.tokens_in and analysis2.tokens_in > 0
        assert analysis2.tokens_out and analysis2.tokens_out > 0
        assert float(analysis2.costo_usd) == 0.0  # unknown (provider,model) -> priced at 0

        dictamen = Dictamen.model_validate(analysis2.dictamen)
        assert dictamen.version == "1.0"
        # one hallazgo nivel=alto (weight 25) -> indice = round(25*2.5) = 62 -> nivel alto
        assert dictamen.indice_riesgo == 62
        assert dictamen.nivel == "alto"
        assert dictamen.resumen.hallazgos == 1
        assert dictamen.resumen.omisiones == 1
        assert dictamen.resumen.por_nivel.alto == 1

        partes_by_id = {p.id: p for p in dictamen.partes}
        assert partes_by_id["p1"].balance == 25
        assert partes_by_id["p1"].a_favor == 1
        assert partes_by_id["p2"].balance == -25
        assert partes_by_id["p2"].en_contra == 1

        assert len(dictamen.hallazgos) == 1
        h = dictamen.hallazgos[0]
        assert len(h.articulos) == 1
        assert h.articulos[0].articulo_id == art_628_id
        assert h.articulos[0].texto == articulos["628-2"].texto  # DB text, not the LLM placeholder
        assert h.articulos[0].fuente_url == articulos["628-2"].fuente_url

        assert len(dictamen.omisiones) == 1
        o = dictamen.omisiones[0]
        assert o.articulos[0].articulo_id == art_1430_id
        assert o.articulos[0].texto == articulos["1430-None"].texto

        assert document2.clausulas and len(document2.clausulas) == 2
        assert document2.partes and len(document2.partes) == 2
        assert document2.ficha.get("tipo_contrato") == "anticrético"
        assert document2.rubro is not None and document2.rubro.value == "civil"


async def test_pipeline_drops_hallucinated_articulo_and_lowers_confianza(monkeypatch):
    async with async_session_maker() as db:
        articulos = await _seed_articulos(db)
        art_628_id = str(articulos["628-2"].id)
        art_1430_id = str(articulos["1430-None"].id)
        org, document, analysis = await _create_org_document(db)
        analysis_id = str(analysis.id)

    responses = _happy_responses(art_628_id, art_1430_id)
    hallucinated_id = str(uuid.uuid4())
    responses[-1]["hallazgos"][0]["articulos"].append(
        {
            "articulo_id": hallucinated_id,
            "cuerpo": "CC",
            "numero": "9999",
            "inciso": None,
            "texto": "artículo inventado por el modelo",
            "fuente_url": "https://example.org/inventado",
        }
    )
    responses[-1]["confianza"] = 0.8

    provider = ScriptedProvider(responses)

    async def _fake_get_default_provider(_db):
        return provider

    monkeypatch.setattr(worker, "get_default_provider", _fake_get_default_provider)

    await worker.analyze({}, analysis_id)

    async with async_session_maker() as db:
        analysis2 = await db.get(Analysis, analysis_id)
        assert analysis2.status == AnalysisStatus.done, analysis2.error

        dictamen = Dictamen.model_validate(analysis2.dictamen)
        h = dictamen.hallazgos[0]
        cited_ids = {a.articulo_id for a in h.articulos}
        assert hallucinated_id not in cited_ids
        assert cited_ids == {art_628_id}
        assert dictamen.confianza == 0.7  # 0.8 - 0.1 per dropped citation


async def test_pipeline_paperless_timeout_fails(monkeypatch):
    import sys

    # `app.pipeline` (the package __init__) re-exports the `normalizar`
    # function under the same name as this submodule, shadowing
    # `app.pipeline.normalizar` as an attribute — go through `sys.modules`
    # to reach the actual submodule and patch its module-level constants.
    normalizar_module = sys.modules["app.pipeline.normalizar"]

    monkeypatch.setattr(normalizar_module, "POLL_TIMEOUT", 0.05)
    monkeypatch.setattr(normalizar_module, "POLL_INTERVAL", 0.01)

    async def _always_empty(_paperless_id):
        return ""

    monkeypatch.setattr(normalizar_module, "get_content", _always_empty)

    async with async_session_maker() as db:
        org, document, analysis = await _create_org_document(db, texto=None, paperless_id=999)
        analysis_id = str(analysis.id)
        document_id = document.id

    provider = ScriptedProvider([])

    async def _fake_get_default_provider(_db):
        return provider

    monkeypatch.setattr(worker, "get_default_provider", _fake_get_default_provider)

    await worker.analyze({}, analysis_id)

    async with async_session_maker() as db:
        analysis2 = await db.get(Analysis, analysis_id)
        document2 = await db.get(Document, document_id)

        assert analysis2.status == AnalysisStatus.failed
        assert analysis2.etapa == 1
        assert analysis2.error and "paperless" in analysis2.error.lower()
        assert document2.ocr_status == OcrStatus.failed
        assert provider.calls == 0  # never reached an LLM call
