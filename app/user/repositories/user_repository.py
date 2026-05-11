# app/user/repositories/user_repository.py
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.user.models.permission import Permission
from app.user.models.user import User, user_permissions


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_user_by_id(self, user_id: int) -> User | None:
        return self.db.query(User).filter(User.id == int(user_id)).first()

    def get_user_by_username(self, username: str) -> User | None:
        return self.db.query(User).filter(User.username == username).first()

    def list_users(self) -> list[User]:
        return self.db.query(User).order_by(User.id.asc()).all()

    def _replace_user_permissions(self, user_id: int, permission_ids: list[int]) -> None:
        self.db.execute(user_permissions.delete().where(user_permissions.c.user_id == user_id))
        for permission_id in permission_ids:
            self.db.execute(
                user_permissions.insert().values(
                    user_id=user_id,
                    permission_id=int(permission_id),
                )
            )

    def create_user(
        self,
        *,
        username: str,
        password: str,
        permission_ids: list[int] | None = None,
        full_name: str | None = None,
        phone: str | None = None,
        email: str | None = None,
    ) -> User:
        existed = self.get_user_by_username(username)
        if existed:
            raise ValueError("用户名已存在")

        ids = []
        if permission_ids:
            perms = self.db.query(Permission).filter(Permission.id.in_(permission_ids)).all()
            existing_ids = {int(permission.id) for permission in perms}
            missing = [int(permission_id) for permission_id in permission_ids if int(permission_id) not in existing_ids]
            if missing:
                raise ValueError(f"权限不存在: {missing}")
            ids = sorted(existing_ids)

        user = User(
            username=username.strip(),
            password_hash=get_password_hash(password),
            full_name=(full_name or "").strip() or None,
            phone=(phone or "").strip() or None,
            email=(email or "").strip() or None,
        )
        self.db.add(user)
        self.db.flush()

        self._replace_user_permissions(int(user.id), ids)

        self.db.commit()
        self.db.refresh(user)
        self.db.expire(user, ["permissions"])
        return user
