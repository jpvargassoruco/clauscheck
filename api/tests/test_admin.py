from tests.helpers import register_org


async def _create_superadmin(email: str, password: str) -> None:
    from app.db import async_session_maker
    from app.models import User
    from app.security import hash_password

    async with async_session_maker() as db:
        db.add(
            User(email=email, password_hash=hash_password(password), nombre="Admin", is_superadmin=True)
        )
        await db.commit()


async def test_admin_requires_superadmin(client):
    regular = await register_org(client, "regular@example.com", "Regular Org")

    resp = await client.get(
        "/api/v1/admin/providers",
        headers={"Authorization": f"Bearer {regular['access_token']}"},
    )
    assert resp.status_code == 403

    await _create_superadmin("root@example.com", "supersecret123")
    resp = await client.post(
        "/api/v1/auth/login", json={"email": "root@example.com", "password": "supersecret123"}
    )
    assert resp.status_code == 200
    admin_token = resp.json()["access_token"]

    resp = await client.get(
        "/api/v1/admin/providers", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 200
    assert resp.json() == []

    resp = await client.get(
        "/api/v1/admin/orgs", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 1
