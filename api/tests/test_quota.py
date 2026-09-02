from datetime import UTC, datetime

from tests.helpers import auth_headers, register_org


async def test_analysis_quota_returns_402_when_exhausted(client):
    from app.db import async_session_maker
    from app.models import Usage

    org = await register_org(client, "quota-owner@example.com", "Quota Org")

    resp = await client.post(
        "/api/v1/documents",
        data={"titulo": "Contrato", "texto": "texto del contrato"},
        headers=auth_headers(org),
    )
    assert resp.status_code == 201
    document_id = resp.json()["id"]

    # free plan allows 5 analyses/month (seeded in conftest); exhaust the quota directly.
    periodo = datetime.now(UTC).strftime("%Y-%m")
    async with async_session_maker() as db:
        db.add(Usage(org_id=org["org_id"], periodo=periodo, analisis_count=5))
        await db.commit()

    resp = await client.post(
        "/api/v1/analyses", json={"document_id": document_id}, headers=auth_headers(org)
    )
    assert resp.status_code == 402, resp.text

    resp = await client.get("/api/v1/usage", headers=auth_headers(org))
    assert resp.status_code == 200
    usage = resp.json()
    assert usage["analisis_count"] == 5
    assert usage["analisis_mes"] == 5
