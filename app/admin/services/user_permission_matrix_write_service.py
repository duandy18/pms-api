# app/admin/services/user_permission_matrix_write_service.py
from __future__ import annotations

from sqlalchemy.orm import Session

from app.admin.contracts.user_permission_matrix_update import UserPermissionMatrixUpdateIn
from app.admin.services.user_permission_matrix_service import UserPermissionMatrixService
from app.user.models.permission import Permission
from app.user.repositories.user_repository import UserRepository


class UserPermissionMatrixWriteService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.matrix_service = UserPermissionMatrixService(db)
        self.user_repo = UserRepository(db)

    def _resolve_permission_ids_by_names(self, permission_names: set[str]) -> list[int]:
        if not permission_names:
            return []

        rows = (
            self.db.query(Permission)
            .filter(Permission.name.in_(sorted(permission_names)))
            .order_by(Permission.id.asc())
            .all()
        )
        return [int(row.id) for row in rows]

    def save_matrix_for_user(
        self,
        *,
        user_id: int,
        body: UserPermissionMatrixUpdateIn,
    ):
        matrix = self.matrix_service.get_matrix()
        pages_by_code = {page.page_code: page for page in matrix.pages}

        final_permission_names: set[str] = set()

        for item in body.pages:
            page = pages_by_code.get(item.page_code)
            if page is None:
                continue

            if item.can_read and page.read_permission:
                final_permission_names.add(page.read_permission)
            if item.can_write and page.write_permission:
                final_permission_names.add(page.write_permission)
                if page.read_permission:
                    final_permission_names.add(page.read_permission)

        final_permission_ids = self._resolve_permission_ids_by_names(final_permission_names)
        return self.user_repo.replace_user_permissions(
            user_id=int(user_id),
            permission_ids=final_permission_ids,
        )
