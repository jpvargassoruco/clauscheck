from tests.helpers import auth_headers, register_org


async def test_org_isolation_documents_and_analyses(client, fake_arq_pool):
    org_a = await register_org(client, "a-owner@example.com", "Org A")
    org_b = await register_org(client, "b-owner@example.com", "Org B")

    resp = await client.post(
        "/api/v1/documents",
        data={"titulo": "Contrato A", "texto": "texto del contrato de la organización A"},
        headers=auth_headers(org_a),
    )
    assert resp.status_code == 201, resp.text
    doc_a_id = resp.json()["id"]

    resp = await client.post(
        "/api/v1/analyses", json={"document_id": doc_a_id}, headers=auth_headers(org_a)
    )
    assert resp.status_code == 201, resp.text
    analysis_a_id = resp.json()["id"]

    # Org B (valid membership, different org) must get 404 for Org A's resources.
    resp = await client.get(f"/api/v1/documents/{doc_a_id}", headers=auth_headers(org_b))
    assert resp.status_code == 404

    resp = await client.get(f"/api/v1/analyses/{analysis_a_id}", headers=auth_headers(org_b))
    assert resp.status_code == 404

    # Org B's own (empty) lists must not include Org A's data.
    resp = await client.get("/api/v1/documents", headers=auth_headers(org_b))
    assert resp.status_code == 200
    assert resp.json() == []

    resp = await client.get("/api/v1/analyses", headers=auth_headers(org_b))
    assert resp.status_code == 200
    assert resp.json() == []

    # Org A can see its own resources fine.
    resp = await client.get(f"/api/v1/documents/{doc_a_id}", headers=auth_headers(org_a))
    assert resp.status_code == 200

    # A user with no membership at all in an org must not pass X-Org-Id.
    resp = await client.get(
        f"/api/v1/documents/{doc_a_id}",
        headers={"Authorization": auth_headers(org_b)["Authorization"]},
    )
    assert resp.status_code == 403
