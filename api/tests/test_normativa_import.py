async def _create_superadmin_token(client) -> str:
    from app.db import async_session_maker
    from app.models import User
    from app.security import hash_password

    async with async_session_maker() as db:
        db.add(
            User(
                email="normativa-admin@example.com",
                password_hash=hash_password("supersecret123"),
                nombre="Admin",
                is_superadmin=True,
            )
        )
        await db.commit()

    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "normativa-admin@example.com", "password": "supersecret123"},
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


async def test_import_normativa_then_public_articulo(client):
    token = await _create_superadmin_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "cuerpos": [
            {
                "code": "CC",
                "nombre": "Código Civil",
                "tipo": "codigo",
                "numero": None,
                "fecha": None,
                "fuente_url": "https://example.org/cc",
            }
        ],
        "articulos": [
            {
                "cuerpo": "CC",
                "numero": "491",
                "inciso": "3",
                "titulo": "Anticresis",
                "texto": "Texto oficial del artículo 491 inciso 3.",
                "fuente_url": "https://example.org/cc/491",
                "verificado": True,
            }
        ],
    }

    resp = await client.post("/api/v1/admin/normativa/import", json=payload, headers=headers)
    assert resp.status_code == 200, resp.text
    result = resp.json()
    assert result["cuerpos_creados"] == 1
    assert result["articulos_creados"] == 1

    resp = await client.get("/api/v1/admin/normativa/articulos", headers=headers)
    assert resp.status_code == 200
    articulos = resp.json()
    assert len(articulos) == 1
    articulo_id = articulos[0]["id"]

    # Re-importing the same payload updates rather than duplicates.
    resp = await client.post("/api/v1/admin/normativa/import", json=payload, headers=headers)
    assert resp.status_code == 200
    result2 = resp.json()
    assert result2["cuerpos_actualizados"] == 1
    assert result2["articulos_actualizados"] == 1

    resp = await client.get("/api/v1/admin/normativa/articulos", headers=headers)
    assert len(resp.json()) == 1

    # public endpoint requires no auth and returns the DB's official text.
    resp = await client.get(f"/api/v1/public/normativa/articulos/{articulo_id}")
    assert resp.status_code == 200, resp.text
    articulo = resp.json()
    assert articulo["cuerpo"] == "CC"
    assert articulo["numero"] == "491"
    assert articulo["inciso"] == "3"
    assert articulo["texto"] == "Texto oficial del artículo 491 inciso 3."
    assert articulo["fuente_url"] == "https://example.org/cc/491"
