"""Tests for pseudonymization (`app.pipeline.anonymize`) and its wiring
into the pipeline (`app.pipeline.run_pipeline`, via `app.worker.analyze`):
the LLM provider must never see real Bolivian PII, and everything
persisted (documents.clausulas/partes, analyses.dictamen) must show real
values again.
"""

import uuid

from app import worker
from app.config import settings
from app.db import async_session_maker
from app.models import Analysis, AnalysisStatus, Document, OcrStatus, Org
from app.pipeline.anonymize import anonymize, restore
from app.schemas.dictamen import Dictamen

CONTRATO_TEXTO = (
    "Comparecen JUAN CARLOS PEREZ MAMANI, con C.I. 4567123 SC, con NIT 1029384756, "
    "en su calidad de CONTRATANTE, y la señora Maria Elena Gomez Vaca, con C.I. 7891234 LP, "
    "en su calidad de CONTRATISTA.\n"
    "PRIMERA. Objeto: la contratista prestará servicios de consultoría al contratante.\n"
    "SEGUNDA. La contratista atenderá al teléfono 70123456 para coordinar pagos a la "
    "cuenta bancaria Nº 4012345678 del banco, en la ciudad de Santa Cruz."
)

REAL_VALUES = [
    "JUAN CARLOS PEREZ MAMANI",
    "Maria Elena Gomez Vaca",
    "4567123",
    "7891234",
    "1029384756",
    "70123456",
    "4012345678",
]


# --- pure `anonymize`/`restore` unit tests --------------------------------


def test_anonymize_redacts_all_categories_and_keeps_legal_facts():
    pseudo, mapping = anonymize(CONTRATO_TEXTO)

    for value in REAL_VALUES:
        assert value not in pseudo

    assert "PARTE_1" in pseudo
    assert "PARTE_2" in pseudo
    assert "CI_1" in pseudo
    assert "CI_2" in pseudo
    assert "NIT_1" in pseudo
    assert "TEL_1" in pseudo
    assert "CUENTA_1" in pseudo

    # legally significant facts and jurisdiction are left untouched
    assert "PRIMERA" in pseudo
    assert "SEGUNDA" in pseudo
    assert "Santa Cruz" in pseudo

    tokens = {t for t in mapping if t.split("_")[0] in {"PARTE", "CI", "NIT", "TEL", "CUENTA"}}
    assert len(tokens) == 7  # 2 PARTE + 2 CI + 1 NIT + 1 TEL + 1 CUENTA


def test_anonymize_is_idempotent():
    pseudo1, mapping1 = anonymize(CONTRATO_TEXTO)
    pseudo2, mapping2 = anonymize(CONTRATO_TEXTO)
    assert pseudo1 == pseudo2
    assert mapping1 == mapping2

    # feeding a prior mapping back in reuses the same tokens, doesn't grow it
    pseudo3, mapping3 = anonymize(CONTRATO_TEXTO, mapping1)
    assert pseudo3 == pseudo1
    assert mapping3 == mapping1


def test_restore_roundtrips_and_is_case_insensitive():
    pseudo, mapping = anonymize(CONTRATO_TEXTO)
    restored = restore(pseudo, mapping)
    assert restored == CONTRATO_TEXTO

    # tokens surviving in lowercase (as an LLM might reproduce them) still
    # restore correctly, and nested JSON structures are walked recursively
    juan_token = next(t for t, v in mapping.items() if v == "JUAN CARLOS PEREZ MAMANI")
    obj = {
        "hallazgos": [
            {"cita_textual": f"El interés de {juan_token.lower()} es alto.", "nivel": "alto"}
        ],
        "numero": 42,
        "ok": True,
    }
    restored_obj = restore(obj, mapping)
    assert restored_obj["hallazgos"][0]["cita_textual"] == "El interés de JUAN CARLOS PEREZ MAMANI es alto."
    assert restored_obj["numero"] == 42
    assert restored_obj["ok"] is True


def test_restore_noop_without_mapping():
    assert restore("PARTE_1 dijo algo", {}) == "PARTE_1 dijo algo"


# --- pipeline wiring (through app.worker.analyze) -------------------------


class CapturingProvider:
    """Like `ScriptedProvider` in test_pipeline.py, but also records every
    `user` prompt sent, so tests can assert on what the LLM actually saw.
    """

    code = "fake"
    model = "fake-model"

    def __init__(self, responses: list[dict]):
        self._responses = list(responses)
        self.calls = 0
        self.prompts: list[str] = []

    async def chat_json(self, system, user, schema, max_tokens=2048):
        self.prompts.append(user)
        resp = self._responses[self.calls]
        self.calls += 1
        return resp


async def _create_org_document(db, texto: str) -> tuple[Org, Document, Analysis]:
    org = Org(slug=f"org-{uuid.uuid4().hex[:8]}", nombre="Test Org", plan_code="free")
    db.add(org)
    await db.flush()

    document = Document(org_id=org.id, titulo="Contrato de prueba", texto=texto, ocr_status=OcrStatus.ready)
    db.add(document)
    await db.flush()

    analysis = Analysis(org_id=org.id, document_id=document.id, status=AnalysisStatus.queued, etapa=0)
    db.add(analysis)
    await db.commit()
    await db.refresh(document)
    await db.refresh(analysis)
    return org, document, analysis


def _happy_responses(mapping: dict[str, str]) -> list[dict]:
    tok_juan = next(t for t, v in mapping.items() if v == "JUAN CARLOS PEREZ MAMANI")
    tok_maria = next(t for t, v in mapping.items() if v == "Maria Elena Gomez Vaca")
    tok_tel = next(t for t, v in mapping.items() if v == "70123456")

    return [
        {
            "clausulas": [
                {
                    "id": "c1",
                    "numero": "PRIMERA",
                    "titulo": "Objeto",
                    "texto": f"la contratista prestará servicios de consultoría al {tok_juan}.",
                },
                {
                    "id": "c2",
                    "numero": "SEGUNDA",
                    "titulo": "Contacto",
                    "texto": f"La contratista atenderá al {tok_tel} para coordinar pagos.",
                },
            ]
        },
        {
            "partes": [
                {"id": "p1", "nombre": tok_juan, "rol": "contratante", "redacto": True},
                {"id": "p2", "nombre": tok_maria, "rol": "contratista", "redacto": False},
            ],
            "ficha": {
                "plaza": "Santa Cruz",
                "fecha": "2024-01-01",
                "cuantia": None,
                "forma_instrumental": "documento privado",
                "tipo_contrato": "servicios",
                "rubro": "comercial",
            },
        },
        {
            "candidatos": [
                {
                    "id": "h1",
                    "tipo": "hallazgo",
                    "clausula_id": "c2",
                    "titulo": "Contacto exclusivo",
                    "problema": "La cláusula segunda concentra el contacto en un solo teléfono.",
                    "nivel_tentativo": "bajo",
                    "palabras_clave": ["contacto"],
                    "cita_textual": f"La contratista atenderá al {tok_tel} para coordinar pagos.",
                }
            ]
        },
        {
            "resultados": [
                {
                    "id": "h1",
                    "applicable": True,
                    "nivel": "bajo",
                    "beneficia": "p1",
                    "perjudica": "p2",
                    "articulo_ids": [],
                    "fundamento": f"Solo {tok_maria} puede ser contactada por ese medio.",
                    "redaccion_sustitutiva": None,
                    "recomendacion": None,
                }
            ]
        },
        {
            "sintesis": f"El contrato entre {tok_juan} y {tok_maria} concentra el contacto.",
            "confianza": 0.7,
            "partes": [
                {"id": "p1", "lectura": f"{tok_juan} no tiene riesgo relevante."},
                {"id": "p2", "lectura": f"{tok_maria} depende de un único canal de contacto."},
            ],
            "hallazgos": [
                {
                    "id": "h1",
                    "titulo": "Contacto exclusivo",
                    "fundamento": f"Solo {tok_maria} puede ser contactada por ese medio.",
                    "cita_textual": f"La contratista atenderá al {tok_tel} para coordinar pagos.",
                    "redaccion_sustitutiva": None,
                    "articulos": [],
                }
            ],
            "omisiones": [],
            "recomendaciones": [],
        },
    ]


async def test_pipeline_hides_pii_from_llm_and_restores_on_persistence(monkeypatch):
    expected_pseudo, expected_mapping = anonymize(CONTRATO_TEXTO)

    async with async_session_maker() as db:
        org, document, analysis = await _create_org_document(db, CONTRATO_TEXTO)
        analysis_id = str(analysis.id)
        document_id = document.id

    provider = CapturingProvider(_happy_responses(expected_mapping))

    async def _fake_get_default_provider(_db):
        return provider

    monkeypatch.setattr(worker, "get_default_provider", _fake_get_default_provider)

    await worker.analyze({}, analysis_id)

    # --- the LLM never saw real PII ---------------------------------
    all_prompts = "\n".join(provider.prompts)
    for value in REAL_VALUES:
        assert value not in all_prompts, f"PII leaked to LLM: {value!r}"
    assert "PARTE_1" in all_prompts or "PARTE_2" in all_prompts
    assert "CI_1" in all_prompts or "CI_2" in all_prompts

    # --- persisted data has real values again -----------------------
    async with async_session_maker() as db:
        analysis2 = await db.get(Analysis, analysis_id)
        document2 = await db.get(Document, document_id)

        assert analysis2.status == AnalysisStatus.done, analysis2.error
        dictamen = Dictamen.model_validate(analysis2.dictamen)

        nombres = {p.nombre for p in dictamen.partes}
        assert nombres == {"JUAN CARLOS PEREZ MAMANI", "Maria Elena Gomez Vaca"}
        assert "70123456" in dictamen.hallazgos[0].cita_textual
        assert "TEL_1" not in dictamen.hallazgos[0].cita_textual

        assert {p["nombre"] for p in document2.partes} == {
            "JUAN CARLOS PEREZ MAMANI",
            "Maria Elena Gomez Vaca",
        }
        clausulas_texto = " ".join(c["texto"] for c in document2.clausulas)
        assert "JUAN CARLOS PEREZ MAMANI" in clausulas_texto
        assert "70123456" in clausulas_texto
        assert "PARTE_" not in clausulas_texto
        assert "TEL_" not in clausulas_texto

        # the mapping used matches a standalone `anonymize()` call and is
        # persisted for re-run stability
        assert document2.pseudonyms == expected_mapping


async def test_pipeline_persisted_mapping_is_stable_across_reruns(monkeypatch):
    """`run_pipeline` seeds `anonymize()` with `document.pseudonyms` on every
    run (see `app/pipeline/__init__.py`), so a re-run of the same document
    reuses the same tokens. Exercising that with a second full
    `worker.analyze` call would double this test's DB/LLM-pipeline cost for
    no extra coverage over `test_anonymize_is_idempotent` above, so instead
    this confirms the actual, JSONB-round-tripped mapping written to
    `documents.pseudonyms` by one real run is a stable fixed point: feeding
    it back into `anonymize()` (exactly what the next run would do) yields
    the identical mapping, unchanged.
    """
    async with async_session_maker() as db:
        org, document, analysis = await _create_org_document(db, CONTRATO_TEXTO)
        document_id = document.id
        analysis_id = str(analysis.id)

    _, mapping = anonymize(CONTRATO_TEXTO)
    provider = CapturingProvider(_happy_responses(mapping))

    async def _fake_get_default_provider(_db):
        return provider

    monkeypatch.setattr(worker, "get_default_provider", _fake_get_default_provider)
    await worker.analyze({}, analysis_id)

    async with async_session_maker() as db:
        document_after_run = await db.get(Document, document_id)
        persisted_mapping = dict(document_after_run.pseudonyms)

    assert persisted_mapping  # something was actually persisted
    rerun_text, rerun_mapping = anonymize(CONTRATO_TEXTO, persisted_mapping)
    assert rerun_mapping == persisted_mapping
    assert rerun_text == anonymize(CONTRATO_TEXTO)[0]


async def test_pseudonymize_disabled_lets_real_pii_reach_the_llm(monkeypatch):
    monkeypatch.setattr(settings, "PSEUDONYMIZE", False)
    try:
        async with async_session_maker() as db:
            org, document, analysis = await _create_org_document(db, CONTRATO_TEXTO)
            analysis_id = str(analysis.id)

        # with pseudonymization off, prompts are built from the real text,
        # so a plain fixed-response fake provider is enough.
        responses = _happy_responses(
            {
                "PARTE_1": "JUAN CARLOS PEREZ MAMANI",
                "PARTE_2": "Maria Elena Gomez Vaca",
                "TEL_1": "70123456",
            }
        )
        provider = CapturingProvider(responses)

        async def _fake_get_default_provider(_db):
            return provider

        monkeypatch.setattr(worker, "get_default_provider", _fake_get_default_provider)
        await worker.analyze({}, analysis_id)

        all_prompts = "\n".join(provider.prompts)
        assert "JUAN CARLOS PEREZ MAMANI" in all_prompts
        assert "70123456" in all_prompts

        async with async_session_maker() as db:
            document2 = await db.get(Document, document.id)
            assert document2.pseudonyms == {}
    finally:
        monkeypatch.setattr(settings, "PSEUDONYMIZE", True)
