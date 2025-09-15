import base64
import binascii
import hashlib
import hmac
import os
from typing import Final

_SALT_SIZE: Final[int] = 16
_ITERATIONS: Final[int] = 120_000
_ALGORITHM: Final[str] = "sha256"


def hash_password(password: str, *, salt: bytes | None = None) -> tuple[str, str]:
    if not password:
        msg = "Password must not be empty"
        raise ValueError(msg)

    raw_salt = salt or os.urandom(_SALT_SIZE)
    derived = hashlib.pbkdf2_hmac(_ALGORITHM, password.encode("utf-8"), raw_salt, _ITERATIONS)

    salt_b64 = base64.b64encode(raw_salt).decode("utf-8")
    hash_b64 = base64.b64encode(derived).decode("utf-8")
    return salt_b64, hash_b64


def verify_password(password: str, *, salt_b64: str, hash_b64: str) -> bool:
    if not password:
        return False

    try:
        salt = base64.b64decode(salt_b64.encode("utf-8"))
        expected = base64.b64decode(hash_b64.encode("utf-8"))
    except (ValueError, binascii.Error):
        return False

    candidate = hashlib.pbkdf2_hmac(_ALGORITHM, password.encode("utf-8"), salt, _ITERATIONS)
    return hmac.compare_digest(candidate, expected)
