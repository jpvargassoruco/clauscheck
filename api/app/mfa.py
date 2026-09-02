"""TOTP MFA (CLAUDE.md tarea 3): secretos con `pyotp`, QR como data URL.

El secreto se guarda cifrado con Fernet (`app.crypto`) en `users.mfa_secret_enc`.
El token de "segundo factor pendiente" (`type=mfa`) se firma con el mismo
`JWT_SECRET`/algoritmo que `app.security`, pero se codifica aquí directamente
(sin tocar `app/security.py`, que no es propiedad de este agente) porque su
`_create_token` sólo admite `Literal["access", "refresh"]`.
"""

import base64
import io
import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pyotp
import qrcode

from app.config import settings
from app.crypto import decrypt, encrypt

ISSUER = "ClausCheck"
MFA_TOKEN_EXPIRE_MINUTES = 5


def generate_secret() -> str:
    return pyotp.random_base32()


def provisioning_uri(secret: str, email: str) -> str:
    return pyotp.totp.TOTP(secret).provisioning_uri(name=email, issuer_name=ISSUER)


def qr_data_url(uri: str) -> str:
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{b64}"


def verify_code(secret: str, code: str) -> bool:
    if not secret or not code:
        return False
    return pyotp.TOTP(secret).verify(code, valid_window=1)


def encrypt_secret(secret: str) -> str:
    return encrypt(secret)


def decrypt_secret(ciphertext: str) -> str:
    return decrypt(ciphertext)


def create_mfa_token(user_id: uuid.UUID | str) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "type": "mfa",
        "iat": now,
        "exp": now + timedelta(minutes=MFA_TOKEN_EXPIRE_MINUTES),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
