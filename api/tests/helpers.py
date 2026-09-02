async def register_org(client, email: str, org_nombre: str) -> dict:
    """Register a new user + org, return {access_token, org_id, user_email}."""
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "supersecret123",
            "nombre": email.split("@")[0],
            "org_nombre": org_nombre,
        },
    )
    assert resp.status_code == 201, resp.text
    tokens = resp.json()

    me_resp = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert me_resp.status_code == 200
    org_id = me_resp.json()["orgs"][0]["id"]

    return {
        "access_token": tokens["access_token"],
        "org_id": org_id,
        "email": email,
    }


def auth_headers(ctx: dict) -> dict:
    return {
        "Authorization": f"Bearer {ctx['access_token']}",
        "X-Org-Id": ctx["org_id"],
    }
