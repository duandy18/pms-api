# app/user/services/user_errors.py
from __future__ import annotations


class AuthorizationError(Exception):
    pass


class DuplicateUserError(Exception):
    pass


class NotFoundError(Exception):
    pass


__all__ = ["AuthorizationError", "DuplicateUserError", "NotFoundError"]
