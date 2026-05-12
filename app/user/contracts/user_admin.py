# app/user/contracts/user_admin.py
from __future__ import annotations

from pydantic import BaseModel, Field, constr


class UserCreateMulti(BaseModel):
    username: constr(strip_whitespace=True, min_length=3, max_length=64)
    password: constr(min_length=6, max_length=128)
    permission_ids: list[int] = Field(default_factory=list)
    full_name: str | None = None
    phone: str | None = None
    email: str | None = None


class UserUpdateMulti(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    email: str | None = None
    is_active: bool | None = None
    permission_ids: list[int] = Field(default_factory=list)


class UserSetPermissionsIn(BaseModel):
    permission_ids: list[int] = Field(default_factory=list)


__all__ = ["UserCreateMulti", "UserUpdateMulti", "UserSetPermissionsIn"]
