async def test_register_login_refresh_me(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "owner@example.com",
            "password": "supersecret123",
            "nombre": "Owner",
            "org_nombre": "Acme SRL",
        },
    )
    assert resp.status_code == 201, resp.text
    tokens = resp.json()
    assert tokens["access_token"] and tokens["refresh_token"]

    # duplicate registration is rejected
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "owner@example.com",
            "password": "supersecret123",
            "nombre": "Owner",
            "org_nombre": "Acme SRL",
        },
    )
    assert resp.status_code == 400

    resp = await client.post(
        "/api/v1/auth/login", json={"email": "owner@example.com", "password": "supersecret123"}
    )
    assert resp.status_code == 200, resp.text
    login_tokens = resp.json()

    resp = await client.post(
        "/api/v1/auth/login", json={"email": "owner@example.com", "password": "wrong"}
    )
    assert resp.status_code == 401

    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {login_tokens['access_token']}"},
    )
    assert resp.status_code == 200, resp.text
    me = resp.json()
    assert me["email"] == "owner@example.com"
    assert len(me["orgs"]) == 1
    assert me["orgs"][0]["role"] == "owner"
    assert me["orgs"][0]["nombre"] == "Acme SRL"

    resp = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": login_tokens["refresh_token"]}
    )
    assert resp.status_code == 200, resp.text
    refreshed = resp.json()
    assert refreshed["access_token"]

    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401
