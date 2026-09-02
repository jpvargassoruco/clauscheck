import base64
import hashlib

from cryptography.fernet import Fernet

from app.config import settings


def _fernet() -> Fernet:
    key = settings.FERNET_KEY
    if not key:
        # Derive a stable dev key so the app still runs without one configured
        # (tests, first boot before infra sets FERNET_KEY). Not for production use.
        digest = hashlib.sha256(b"clauscheck-dev-fernet").digest()
        key = base64.urlsafe_b64encode(digest).decode()
    return Fernet(key if isinstance(key, bytes) else key.encode())


def encrypt(plaintext: str) -> str:
    if not plaintext:
        return ""
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    if not ciphertext:
        return ""
    return _fernet().decrypt(ciphertext.encode()).decode()
