# app/admin/services/user_permission_matrix_service.py
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.admin.contracts.user_permission_matrix import (
    PermissionMatrixPageGrantOut,
    PermissionMatrixPageOut,
    PermissionMatrixRowOut,
    UserPermissionMatrixOut,
)
from app.user.repositories.navigation_repository import NavigationRepository
from app.user.repositories.user_repository import UserRepository
from app.user.services.user_permissions import get_user_permissions


class UserPermissionMatrixService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.navigation_repo = NavigationRepository(db)
        self.user_repo = UserRepository(db)

    @classmethod
    def _resolve_effective_permissions(
        cls,
        *,
        code: str,
        rows_by_code: dict[str, dict[str, Any]],
        cache: dict[str, tuple[str | None, str | None]],
    ) -> tuple[str | None, str | None]:
        cached = cache.get(code)
        if cached is not None:
            return cached

        row = rows_by_code.get(code)
        if row is None:
            cache[code] = (None, None)
            return cache[code]

        if not bool(row.get("inherit_permissions")):
            result = (
                row.get("self_read_permission"),
                row.get("self_write_permission"),
            )
            cache[code] = result
            return result

        parent_code = row.get("parent_code")
        if not parent_code:
            cache[code] = (None, None)
            return cache[code]

        result = cls._resolve_effective_permissions(
            code=str(parent_code),
            rows_by_code=rows_by_code,
            cache=cache,
        )
        cache[code] = result
        return result

    def get_matrix(self) -> UserPermissionMatrixOut:
        raw_pages = self.navigation_repo.list_pages()
        rows_by_code = {str(row["code"]): row for row in raw_pages}
        cache: dict[str, tuple[str | None, str | None]] = {}

        pages: list[PermissionMatrixPageOut] = []
        for page in raw_pages:
            code = str(page["code"])
            read_permission, write_permission = self._resolve_effective_permissions(
                code=code,
                rows_by_code=rows_by_code,
                cache=cache,
            )
            if not read_permission and not write_permission:
                continue

            pages.append(
                PermissionMatrixPageOut(
                    page_code=code,
                    page_name=str(page["name"]),
                    read_permission=read_permission,
                    write_permission=write_permission,
                )
            )

        matrix_users: list[PermissionMatrixRowOut] = []
        for user in self.user_repo.list_users():
            user_permission_names = set(get_user_permissions(self.db, user))
            grants = [
                PermissionMatrixPageGrantOut(
                    page_code=page.page_code,
                    can_read=bool(page.read_permission and page.read_permission in user_permission_names),
                    can_write=bool(page.write_permission and page.write_permission in user_permission_names),
                )
                for page in pages
            ]
            matrix_users.append(
                PermissionMatrixRowOut(
                    user_id=int(user.id),
                    username=str(user.username),
                    full_name=getattr(user, "full_name", None),
                    is_active=bool(getattr(user, "is_active", True)),
                    pages=grants,
                )
            )

        return UserPermissionMatrixOut(pages=pages, users=matrix_users)
