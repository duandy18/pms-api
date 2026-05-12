# app/user/contracts/user.py
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, constr


class UserLogin(BaseModel):
    username: constr(strip_whitespace=True, min_length=3, max_length=64)
    password: constr(min_length=1)


class UserCreate(BaseModel):
    username: constr(strip_whitespace=True, min_length=3, max_length=64)
    password: constr(min_length=6, max_length=128)
    permission_ids: list[int] = Field(default_factory=list)
    full_name: str | None = None
    phone: str | None = None
    email: str | None = None


class UserOut(BaseModel):
    id: int
    username: str
    is_active: bool = True
    full_name: str | None = None
    phone: str | None = None
    email: str | None = None
    permissions: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


__all__ = ["UserLogin", "UserCreate", "UserOut"]
