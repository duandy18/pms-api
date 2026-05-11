# app/user/helpers/auth.py
from __future__ import annotations

import os


def token_expires_in_seconds() -> int:
    try:
        mins = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    except Exception:
        mins = 60
    if mins <= 0:
        mins = 60
    return mins * 60
