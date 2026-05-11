# app/user/services/user_service.py
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.user.models.user import User
from app.user.repositories.user_repository import UserRepository
from app.user.services.user_auth import (
    authenticate_user as _authenticate_user,
    create_token_for_user as _create_token_for_user,
    get_user_from_token as _get_user_from_token,
)
from app.user.services.user_permissions import get_user_permissions as _get_user_permissions


class UserService:
    def __init__(self, db_session: Session):
        self.db: Session = db_session
        self.repo = UserRepository(db_session)

    def get_user_by_id(self, user_id: int) -> User | None:
        return self.repo.get_user_by_id(user_id)

    def get_user_by_username(self, username: str) -> User | None:
        return self.repo.get_user_by_username(username)

    def authenticate_user(self, username: str, password: str) -> User | None:
        return _authenticate_user(self.db, username, password)

    def create_token_for_user(self, user: User, *, expires_in: int | None = None) -> str:
        return _create_token_for_user(user, expires_in=expires_in)

    def get_user_from_token(self, token: str) -> User | None:
        return _get_user_from_token(self.db, token)

    def get_user_permissions(self, user: Any) -> list[str]:
        return _get_user_permissions(self.db, user)
