# app/user/services/user_service.py
from __future__ import annotations

from typing import Any

from app.core.security import get_password_hash, verify_password
from sqlalchemy.orm import Session

from app.user.models.user import User
from app.user.repositories.user_repository import UserRepository
from app.user.services.user_auth import (
    authenticate_user as _authenticate_user,
    create_token_for_user as _create_token_for_user,
    get_user_from_token as _get_user_from_token,
)
from app.user.services.user_errors import AuthorizationError, DuplicateUserError, NotFoundError
from app.user.services.user_permissions import (
    check_permission as _check_permission,
    get_user_permissions as _get_user_permissions,
)

ADMIN_WRITE_PERMISSION = "page.admin.write"


class UserService:
    def __init__(self, db_session: Session):
        self.db: Session = db_session
        self.repo = UserRepository(db_session)

    def get_user_by_id(self, user_id: int) -> User | None:
        return self.repo.get_user_by_id(user_id)

    def get_user_by_username(self, username: str) -> User | None:
        return self.repo.get_user_by_username(username)

    def list_users(self) -> list[User]:
        return self.repo.list_users()

    def authenticate_user(self, username: str, password: str) -> User | None:
        return _authenticate_user(self.db, username, password)

    def create_token_for_user(self, user: User, *, expires_in: int | None = None) -> str:
        return _create_token_for_user(user, expires_in=expires_in)

    def get_user_from_token(self, token: str) -> User | None:
        return _get_user_from_token(self.db, token)

    def create_user(
        self,
        username: str,
        password: str,
        *,
        permission_ids: list[int] | None = None,
        full_name: str | None = None,
        phone: str | None = None,
        email: str | None = None,
    ) -> User:
        return self.repo.create_user(
            username=username,
            password=password,
            permission_ids=permission_ids,
            full_name=full_name,
            phone=phone,
            email=email,
        )

    def update_user(
        self,
        user_id: int,
        *,
        full_name: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        is_active: bool | None = None,
    ) -> User:
        user = self.repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("用户不存在")

        if is_active is False and self._is_active_admin_write_user(user):
            self._ensure_not_last_active_admin_writer(action="停用")

        return self.repo.update_user_profile(
            user_id=user_id,
            full_name=full_name,
            phone=phone,
            email=email,
            is_active=is_active,
        )

    def delete_user(self, user_id: int) -> None:
        user = self.repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("用户不存在")

        if self._is_active_admin_write_user(user):
            self._ensure_not_last_active_admin_writer(action="删除")

        self.repo.delete_user(user_id=user_id)

    def set_user_permissions(
        self,
        user_id: int,
        *,
        permission_ids: list[int] | None = None,
    ) -> User:
        user = self.repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("用户不存在")

        before_admin_write = self._is_active_admin_write_user(user)
        target_permission_ids = [int(pid) for pid in (permission_ids or [])]

        admin_write = (
            self.db.query(self.repo.list_permissions()[0].__class__)
            .filter_by(name=ADMIN_WRITE_PERMISSION)
            .one_or_none()
        )
        admin_write_id = int(admin_write.id) if admin_write is not None else None
        after_admin_write = admin_write_id is not None and admin_write_id in target_permission_ids

        if before_admin_write and not after_admin_write:
            self._ensure_not_last_active_admin_writer(action="移除权限")

        return self.repo.replace_user_permissions(
            user_id=user_id,
            permission_ids=target_permission_ids,
        )

    def reset_user_password(self, user_id: int, *, new_password: str = "000000") -> User:
        return self.repo.reset_user_password(user_id=user_id, new_password=new_password)

    def change_password(self, user_id: int, old_password: str, new_password: str) -> None:
        user = self.repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("用户不存在")
        if not getattr(user, "password_hash", None):
            raise AuthorizationError("旧密码不正确")
        if not verify_password(old_password, user.password_hash):
            raise AuthorizationError("旧密码不正确")
        user.password_hash = get_password_hash(new_password)
        self.db.commit()

    def get_user_permissions(self, user: Any) -> list[str]:
        return _get_user_permissions(self.db, user)

    def check_permission(self, user: Any, required: list[str], *, any_of: bool = True) -> bool:
        return _check_permission(self.db, user, required, any_of=any_of)

    def _is_active_admin_write_user(self, user: User) -> bool:
        if not bool(getattr(user, "is_active", True)):
            return False

        return ADMIN_WRITE_PERMISSION in set(self.get_user_permissions(user))

    def _ensure_not_last_active_admin_writer(self, *, action: str) -> None:
        count = self.repo.count_active_users_with_permission(ADMIN_WRITE_PERMISSION)
        if count <= 1:
            raise ValueError(f"不能{action}最后一个仍拥有 page.admin.write 的有效用户")


__all__ = [
    "ADMIN_WRITE_PERMISSION",
    "AuthorizationError",
    "DuplicateUserError",
    "NotFoundError",
    "UserService",
]
