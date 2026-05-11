# app/user/contracts/user.py
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, constr


class UserLogin(BaseModel):
    username: constr(strip_whitespace=True, min_length=3, max_length=64)
    password: constr(min_length=1)


class UserOut(BaseModel):
    id: int
    username: str
    is_active: bool = True
    full_name: str | None = None
    phone: str | None = None
    email: str | None = None
    permissions: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
