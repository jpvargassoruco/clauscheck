from tests.helpers import auth_headers, register_org


async def test_create_document_json_body(client):
    org = await register_org(client, "json-doc@example.com", "JSON Doc Org")

    resp = await client.post(
        "/api/v1/documents",
        json={"titulo": "Contrato JSON", "texto": "texto del contrato en JSON"},
        headers=auth_headers(org),
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["titulo"] == "Contrato JSON"
    assert body["ocr_status"] == "ready"

    resp = await client.get(f"/api/v1/documents/{body['id']}", headers=auth_headers(org))
    assert resp.status_code == 200, resp.text
    assert resp.json()["texto"] == "texto del contrato en JSON"


async def test_create_document_json_body_without_texto_is_rejected(client):
    org = await register_org(client, "json-doc-empty@example.com", "JSON Doc Empty Org")

    resp = await client.post(
        "/api/v1/documents",
        json={"titulo": "Sin texto"},
        headers=auth_headers(org),
    )
    assert resp.status_code == 400, resp.text
