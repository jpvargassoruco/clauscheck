import pyotp

from tests.helpers import register_org


async def test_mfa_setup_enable_login_verify_disable(client):
    ctx = await register_org(client, "mfa-user@example.com", "MFA Org")
    headers = {"Authorization": f"Bearer {ctx['access_token']}"}

    # setup: generates a secret + otpauth URL + QR data URL
    resp = await client.post("/api/v1/auth/mfa/setup", headers=headers)
    assert resp.status_code == 200, resp.text
    setup = resp.json()
    assert setup["secret"]
    assert setup["otpauth_url"].startswith("otpauth://totp/")
    assert setup["qr"].startswith("data:image/png;base64,")

    secret = setup["secret"]
    totp = pyotp.TOTP(secret)

    # enabling with a wrong code fails
    resp = await client.post("/api/v1/auth/mfa/enable", json={"code": "000000"}, headers=headers)
    assert resp.status_code == 400

    resp = await client.post("/api/v1/auth/mfa/enable", json={"code": totp.now()}, headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["mfa_enabled"] is True

    resp = await client.get("/api/v1/auth/me", headers=headers)
    assert resp.json()["mfa_enabled"] is True

    # login now returns an mfa challenge instead of tokens directly
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "mfa-user@example.com", "password": "supersecret123"},
    )
    assert resp.status_code == 200, resp.text
    challenge = resp.json()
    assert challenge["mfa_required"] is True
    mfa_token = challenge["mfa_token"]
    assert "access_token" not in challenge

    # wrong code at verify time is rejected
    resp = await client.post(
        "/api/v1/auth/mfa/verify", json={"mfa_token": mfa_token, "code": "000000"}
    )
    assert resp.status_code == 401

    resp = await client.post(
        "/api/v1/auth/mfa/verify", json={"mfa_token": mfa_token, "code": totp.now()}
    )
    assert resp.status_code == 200, resp.text
    tokens = resp.json()
    assert tokens["access_token"]

    resp = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == "mfa-user@example.com"

    # a normal access token cannot be replayed as an mfa_token
    resp = await client.post(
        "/api/v1/auth/mfa/verify", json={"mfa_token": tokens["access_token"], "code": totp.now()}
    )
    assert resp.status_code == 401

    # disable requires a valid code too
    resp = await client.post("/api/v1/auth/mfa/disable", json={"code": "000000"}, headers=headers)
    assert resp.status_code == 400

    resp = await client.post("/api/v1/auth/mfa/disable", json={"code": totp.now()}, headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["mfa_enabled"] is False

    # login goes back to returning tokens directly
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "mfa-user@example.com", "password": "supersecret123"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


async def test_mfa_enable_requires_setup_first(client):
    ctx = await register_org(client, "mfa-nosetup@example.com", "MFA Org 2")
    headers = {"Authorization": f"Bearer {ctx['access_token']}"}

    resp = await client.post("/api/v1/auth/mfa/enable", json={"code": "123456"}, headers=headers)
    assert resp.status_code == 400
