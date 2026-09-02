import logging

from tests.helpers import auth_headers, register_org


async def _create_superadmin(email: str, password: str) -> None:
    from app.db import async_session_maker
    from app.models import User
    from app.security import hash_password

    async with async_session_maker() as db:
        db.add(
            User(email=email, password_hash=hash_password(password), nombre="Admin", is_superadmin=True)
        )
        await db.commit()


async def _login(client, email: str, password: str) -> str:
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


async def test_registration_blocked_in_approval_mode(client, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "REGISTRATION_MODE", "approval")
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "blocked@example.com",
            "password": "supersecret123",
            "nombre": "Blocked",
            "org_nombre": "Blocked Org",
        },
    )
    assert resp.status_code == 403
    assert resp.json()["detail"] == "El registro es por solicitud"

    monkeypatch.setattr(settings, "REGISTRATION_MODE", "closed")
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "blocked2@example.com",
            "password": "supersecret123",
            "nombre": "Blocked",
            "org_nombre": "Blocked Org 2",
        },
    )
    assert resp.status_code == 403


async def test_access_request_approve_invite_accept_login(client, monkeypatch, caplog):
    from app.config import settings

    monkeypatch.setattr(settings, "ADMIN_NOTIFY_EMAIL", "admin-notify@example.com")

    # alembic's `command.upgrade` (run once per session in the `_migrate_db`
    # fixture) calls `logging.config.fileConfig(alembic.ini)`, which disables
    # every pre-existing logger not listed in its `[loggers]` section —
    # including `clauscheck.mail`. Re-enable it so caplog can capture it.
    logging.getLogger("clauscheck.mail").disabled = False

    with caplog.at_level(logging.INFO, logger="clauscheck.mail"):
        resp = await client.post(
            "/api/v1/public/access-requests",
            json={
                "nombre": "Ana Pérez",
                "email": "ana@example.com",
                "organizacion": "Estudio Ana",
                "telefono": "70000000",
                "motivo": "Quiero probar ClausCheck",
            },
        )
    assert resp.status_code == 201, resp.text

    # both the "solicitud recibida" (requester) and "nueva solicitud" (admin)
    # emails must have gone through the console backend / captured log.
    log_text = "\n".join(r.message for r in caplog.records)
    assert "ana@example.com" in log_text
    assert "admin-notify@example.com" in log_text

    await _create_superadmin("root-ar@example.com", "supersecret123")
    admin_token = await _login(client, "root-ar@example.com", "supersecret123")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    resp = await client.get("/api/v1/admin/access-requests?status=pending", headers=admin_headers)
    assert resp.status_code == 200, resp.text
    pending = resp.json()
    assert len(pending) == 1
    request_id = pending[0]["id"]

    resp = await client.post(
        f"/api/v1/admin/access-requests/{request_id}/approve",
        json={"plan_code": "pro", "role": "owner"},
        headers=admin_headers,
    )
    assert resp.status_code == 200, resp.text
    approved = resp.json()
    assert approved["status"] == "approved"
    org_id = approved["org_id"]
    assert org_id

    # re-approving is rejected (already decided)
    resp = await client.post(
        f"/api/v1/admin/access-requests/{request_id}/approve",
        json={"plan_code": "pro"},
        headers=admin_headers,
    )
    assert resp.status_code == 400

    from sqlalchemy import select

    from app.db import async_session_maker
    from app.models import Invitation

    async with async_session_maker() as db:
        result = await db.execute(select(Invitation).where(Invitation.org_id == org_id))
        invitation = result.scalars().first()
    assert invitation is not None
    assert invitation.email == "ana@example.com"

    resp = await client.get(f"/api/v1/public/invitations/{invitation.token}")
    assert resp.status_code == 200, resp.text
    preview = resp.json()
    assert preview["email"] == "ana@example.com"
    assert preview["expired"] is False
    assert preview["accepted"] is False

    resp = await client.post(
        f"/api/v1/public/invitations/{invitation.token}/accept",
        json={"nombre": "Ana Pérez", "password": "supersecret123"},
    )
    assert resp.status_code == 200, resp.text
    tokens = resp.json()
    assert tokens["access_token"]

    resp = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert resp.status_code == 200, resp.text
    me = resp.json()
    assert me["email"] == "ana@example.com"
    assert len(me["orgs"]) == 1
    assert me["orgs"][0]["id"] == org_id
    assert me["orgs"][0]["role"] == "owner"

    # accepting a second time fails
    resp = await client.post(
        f"/api/v1/public/invitations/{invitation.token}/accept",
        json={"nombre": "Ana Pérez", "password": "supersecret123"},
    )
    assert resp.status_code == 400


async def test_access_request_reject_flow(client):
    resp = await client.post(
        "/api/v1/public/access-requests",
        json={
            "nombre": "Beto Gómez",
            "email": "beto@example.com",
            "organizacion": "Beto SRL",
        },
    )
    assert resp.status_code == 201

    await _create_superadmin("root-rej@example.com", "supersecret123")
    admin_token = await _login(client, "root-rej@example.com", "supersecret123")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    resp = await client.get("/api/v1/admin/access-requests?status=pending", headers=admin_headers)
    request_id = resp.json()[0]["id"]

    resp = await client.post(
        f"/api/v1/admin/access-requests/{request_id}/reject",
        json={"motivo": "No cumple los requisitos"},
        headers=admin_headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "rejected"

    resp = await client.get("/api/v1/admin/access-requests?status=rejected", headers=admin_headers)
    assert len(resp.json()) == 1


async def test_access_request_honeypot_is_silently_dropped(client):
    resp = await client.post(
        "/api/v1/public/access-requests",
        json={
            "nombre": "Bot",
            "email": "bot@example.com",
            "organizacion": "Bot Org",
            "website": "http://spam.example.com",
        },
    )
    assert resp.status_code == 201

    await _create_superadmin("root-honeypot@example.com", "supersecret123")
    admin_token = await _login(client, "root-honeypot@example.com", "supersecret123")
    resp = await client.get(
        "/api/v1/admin/access-requests", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.json() == []


async def test_access_request_rate_limit(client):
    # Reset the in-memory rate-limit state: it's module-level (not DB-backed,
    # not cleared by the `_clean_db` fixture) so other tests hitting this
    # same endpoint earlier in the session would otherwise leak into the count.
    from app.routers import access_requests

    access_requests._rate_limit_state.clear()

    for i in range(5):
        resp = await client.post(
            "/api/v1/public/access-requests",
            json={"nombre": f"Rate {i}", "email": f"rate{i}@example.com", "organizacion": "Rate Org"},
        )
        assert resp.status_code == 201, resp.text

    resp = await client.post(
        "/api/v1/public/access-requests",
        json={"nombre": "Rate over", "email": "rate-over@example.com", "organizacion": "Rate Org"},
    )
    assert resp.status_code == 429


async def test_org_invitation_sends_mail(client, caplog):
    logging.getLogger("clauscheck.mail").disabled = False
    ctx = await register_org(client, "inviter@example.com", "Inviter Org")

    with caplog.at_level(logging.INFO, logger="clauscheck.mail"):
        resp = await client.post(
            f"/api/v1/orgs/{ctx['org_id']}/invitations",
            json={"email": "invited@example.com", "role": "member"},
            headers=auth_headers(ctx),
        )
    assert resp.status_code == 201, resp.text

    log_text = "\n".join(r.message for r in caplog.records)
    assert "invited@example.com" in log_text
