# app/core/security.py
"""
PMS API security helpers.

Rules:
- JWT is HS256 only.
- Non-dev environments must provide a real JWT_SECRET.
- The fallback implementation is intentionally dependency-light for local/dev CI.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any


_ENV = os.environ.get("PMS_ENV") or os.environ.get("ENV") or "dev"
_JWT_SECRET = os.environ.get("JWT_SECRET", "dev-temp-secret")
_JWT_EXP_MIN = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
_JWT_ALG = "HS256"

_DEV_SECRETS = {
    "",
    "dev-temp-secret",
    "dev-secret-change-me",
}

if _ENV != "dev":
    if not _JWT_SECRET or _JWT_SECRET in _DEV_SECRETS:
        raise RuntimeError(
            "SECURITY ERROR: JWT_SECRET is not properly configured for non-dev PMS API."
        )


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def _b64url_decode(s: str) -> bytes:
    pad = "=" * ((4 - (len(s) % 4)) % 4)
    return base64.urlsafe_b64decode((s + pad).encode("utf-8"))


def _hs256_sign(message: bytes, secret: str) -> str:
    sig = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).digest()
    return _b64url_encode(sig)


def get_password_hash(password: str) -> str:
    salt = _b64url_encode(os.urandom(12))
    digest = hashlib.sha256((salt + ":" + password).encode("utf-8")).hexdigest()
    return f"sha256${salt}${digest}"


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        algo, salt, digest = password_hash.split("$", 2)
        if algo != "sha256":
            return False
        expected = hashlib.sha256((salt + ":" + plain_password).encode("utf-8")).hexdigest()
        return hmac.compare_digest(expected, digest)
    except Exception:
        return False


def create_access_token(
    data: dict[str, Any],
    expires_minutes: int | None = None,
) -> str:
    payload = dict(data)
    payload["exp"] = int(time.time()) + 60 * int(expires_minutes or _JWT_EXP_MIN)

    header = {"alg": _JWT_ALG, "typ": "JWT"}
    header_b64 = _b64url_encode(
        json.dumps(header, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    )
    payload_b64 = _b64url_encode(
        json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    )
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    sig_b64 = _hs256_sign(signing_input, _JWT_SECRET)
    return f"{header_b64}.{payload_b64}.{sig_b64}"


def decode_access_token(token: str) -> dict[str, Any] | None:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        header_b64, payload_b64, sig_b64 = parts
        header = json.loads(_b64url_decode(header_b64).decode("utf-8"))
        if not isinstance(header, dict):
            return None
        if header.get("alg") != _JWT_ALG:
            return None

        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
        expected_sig = _hs256_sign(signing_input, _JWT_SECRET)
        if not hmac.compare_digest(expected_sig, sig_b64):
            return None

        payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
        if not isinstance(payload, dict):
            return None

        exp = payload.get("exp")
        if exp is not None:
            if int(time.time()) >= int(exp):
                return None

        return payload
    except Exception:
        return None


hash_password = get_password_hash
