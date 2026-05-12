# app/user/services/user_permissions.py
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.user.models.permission import Permission
from app.user.models.user import user_permissions
from app.user.services.user_errors import AuthorizationError


def get_user_permissions(db: Session, user: Any) -> list[str]:
    if not user:
        return []

    perms_attr = getattr(user, "permissions", None)
    if perms_attr is not None:
        out: list[str] = []
        seen: set[str] = set()
        for item in perms_attr:
            name = item if isinstance(item, str) else getattr(item, "name", None)
            if name and str(name) not in seen:
                seen.add(str(name))
                out.append(str(name))
        if out:
            return out

    user_id = getattr(user, "id", None)
    if user_id is None:
        return []

    rows = (
        db.query(Permission.name)
        .join(user_permissions, Permission.id == user_permissions.c.permission_id)
        .filter(user_permissions.c.user_id == int(user_id))
        .order_by(Permission.id.asc())
        .all()
    )

    out: list[str] = []
    seen: set[str] = set()
    for (name,) in rows:
        if name and name not in seen:
            seen.add(name)
            out.append(name)
    return out


def check_permission(
    db: Session,
    user: Any,
    required: list[str],
    *,
    any_of: bool = True,
) -> bool:
    perms = set(get_user_permissions(db, user))
    req = set(required)

    ok = bool(perms & req) if any_of else req.issubset(perms)
    if not ok:
        raise AuthorizationError("你没有访问该资源的权限")

    return True


__all__ = ["get_user_permissions", "check_permission"]
