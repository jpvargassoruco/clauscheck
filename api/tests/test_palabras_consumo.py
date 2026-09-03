"""Tests for word-based plan limits, enforcement, refunds, the per-document
estimate endpoint, and the admin consumo dashboard aggregates (see prompt
item 6): 413 over the per-document word limit, 402 over the monthly word
budget, refund on job failure, GET /documents/{id}/estimate, and
GET /admin/consumo.
"""

from datetime import UTC, datetime

from tests.helpers import auth_headers, register_org
from tests.test_admin import _create_superadmin


async def _make_text_document(client, org, palabras: int, titulo: str = "Contrato"):
    texto = " ".join(f"palabra{i}" for i in range(palabras))
    resp = await client.post(
        "/api/v1/documents",
        json={"titulo": titulo, "texto": texto},
        headers=auth_headers(org),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _login_superadmin(client, email: str, password: str) -> str:
    await _create_superadmin(email, password)
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


async def test_analysis_413_over_per_document_word_limit(client):
    # free plan: palabras_max_doc = 5000 (seeded in conftest)
    org = await register_org(client, "words-doc@example.com", "Words Doc Org")
    doc = await _make_text_document(client, org, 5001)

    resp = await client.post(
        "/api/v1/analyses", json={"document_id": doc["id"]}, headers=auth_headers(org)
    )
    assert resp.status_code == 413, resp.text
    assert "palabras" in resp.json()["detail"]


async def test_analysis_402_over_monthly_word_budget(client):
    from app.db import async_session_maker
    from app.models import Usage

    org = await register_org(client, "words-month@example.com", "Words Month Org")
    doc = await _make_text_document(client, org, 100)  # well within the per-doc limit

    periodo = datetime.now(UTC).strftime("%Y-%m")
    async with async_session_maker() as db:
        # free plan: palabras_mes = 15000; pre-fill usage so this doc's 100
        # words would push the org over its monthly budget.
        db.add(
            Usage(org_id=org["org_id"], periodo=periodo, analisis_count=0, palabras_count=14_950)
        )
        await db.commit()

    resp = await client.post(
        "/api/v1/analyses", json={"document_id": doc["id"]}, headers=auth_headers(org)
    )
    assert resp.status_code == 402, resp.text
    assert "palabras" in resp.json()["detail"]


async def test_analysis_refund_on_job_failure(client):
    from app import worker
    from app.db import async_session_maker
    from app.models import Usage

    org = await register_org(client, "refund@example.com", "Refund Org")
    doc = await _make_text_document(client, org, 200)

    resp = await client.post(
        "/api/v1/analyses", json={"document_id": doc["id"]}, headers=auth_headers(org)
    )
    assert resp.status_code == 201, resp.text
    analysis_id = resp.json()["id"]

    periodo = datetime.now(UTC).strftime("%Y-%m")
    async with async_session_maker() as db:
        usage = await db.get(Usage, {"org_id": org["org_id"], "periodo": periodo})
        assert usage.analisis_count == 1
        assert usage.palabras_count == 200

    # No LLM provider is configured in the test env (no llm_providers row,
    # no *_API_KEY): the job fails at get_default_provider(), before any
    # network call — a clean, deterministic failure to exercise the refund.
    await worker.analyze({}, analysis_id)

    resp = await client.get(f"/api/v1/analyses/{analysis_id}", headers=auth_headers(org))
    assert resp.status_code == 200
    assert resp.json()["status"] == "failed"

    async with async_session_maker() as db:
        usage = await db.get(Usage, {"org_id": org["org_id"], "periodo": periodo})
        assert usage.analisis_count == 0
        assert usage.palabras_count == 0


async def test_document_estimate_endpoint(client):
    org = await register_org(client, "estimate@example.com", "Estimate Org")

    doc = await _make_text_document(client, org, 500)
    resp = await client.get(
        f"/api/v1/documents/{doc['id']}/estimate", headers=auth_headers(org)
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["palabras"] == 500
    assert body["tokens_estimados"] > 0
    assert body["costo_estimado_usd"] >= 0
    assert body["dentro_del_plan"] is True
    assert body["motivo"] == ""

    doc_over = await _make_text_document(client, org, 6000)
    resp = await client.get(
        f"/api/v1/documents/{doc_over['id']}/estimate", headers=auth_headers(org)
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["dentro_del_plan"] is False
    assert "palabras" in body["motivo"]


async def test_admin_consumo_aggregates(client):
    from app.models import Analysis, AnalysisStatus, Document, Org

    org = await register_org(client, "consumo-org@example.com", "Consumo Org")

    from app.db import async_session_maker

    async with async_session_maker() as db:
        org_row = await db.get(Org, org["org_id"])
        document = Document(
            org_id=org_row.id,
            titulo="Doc consumo",
            texto="palabra " * 1000,
            palabras=1000,
            ocr_status="ready",
        )
        db.add(document)
        await db.flush()
        analysis = Analysis(
            org_id=org_row.id,
            document_id=document.id,
            status=AnalysisStatus.done,
            etapa=7,
            tokens_in=1000,
            tokens_out=500,
            costo_usd=0.05,
            costo_estimado=False,
        )
        db.add(analysis)
        await db.commit()

    admin_token = await _login_superadmin(client, "consumo-admin@example.com", "supersecret123")
    headers = {"Authorization": f"Bearer {admin_token}"}

    resp = await client.get("/api/v1/admin/consumo", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["totales"]["analisis"] == 1
    assert body["totales"]["palabras"] == 1000
    assert body["totales"]["tokens_in"] == 1000
    assert body["totales"]["tokens_out"] == 500
    assert abs(body["totales"]["costo_usd"] - 0.05) < 1e-6
    assert len(body["rows"]) == 1
    assert body["rows"][0]["org_id"] == org["org_id"]
    assert body["rows"][0]["org_nombre"] == "Consumo Org"

    resp = await client.get("/api/v1/admin/consumo/export.csv", headers=headers)
    assert resp.status_code == 200, resp.text
    assert "text/csv" in resp.headers["content-type"]
    assert "Consumo Org" in resp.text
