# app/pms/system/write_v1/contracts/iam.py
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PmsSystemIamUserIn(_Base):
    username: str = Field(..., min_length=1, max_length=64)
    full_name: str | None = Field(default=None, max_length=128)
    phone: str | None = Field(default=None, max_length=32)
    email: str | None = Field(default=None, max_length=255)
    is_active: bool = True


class PmsSystemIamUserPermissionIn(_Base):
    username: str = Field(..., min_length=1, max_length=64)
    permission_code: str = Field(..., min_length=1, max_length=128)
    is_active: bool = True


class PmsSystemIamApplyIn(_Base):
    users: list[PmsSystemIamUserIn] = Field(default_factory=list)
    user_permissions: list[PmsSystemIamUserPermissionIn] = Field(default_factory=list)


class PmsSystemIamPermissionDiffOut(_Base):
    username: str
    permission_code: str


class PmsSystemIamUserDiffOut(_Base):
    username: str
    field_name: str
    expected: str | bool | None
    actual: str | bool | None


class PmsSystemIamVerifyOut(_Base):
    app_code: Literal["pms"]
    verified: bool
    user_count: int
    desired_permission_count: int
    missing_users: list[str] = Field(default_factory=list)
    missing_permission_codes: list[str] = Field(default_factory=list)
    mismatched_users: list[PmsSystemIamUserDiffOut] = Field(default_factory=list)
    missing_user_permissions: list[PmsSystemIamPermissionDiffOut] = Field(default_factory=list)
    extra_user_permissions: list[PmsSystemIamPermissionDiffOut] = Field(default_factory=list)


class PmsSystemIamApplyOut(PmsSystemIamVerifyOut):
    applied: bool


__all__ = [
    "PmsSystemIamApplyIn",
    "PmsSystemIamApplyOut",
    "PmsSystemIamPermissionDiffOut",
    "PmsSystemIamUserDiffOut",
    "PmsSystemIamUserIn",
    "PmsSystemIamUserPermissionIn",
    "PmsSystemIamVerifyOut",
]
