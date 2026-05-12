# app/admin/contracts/user_permission_matrix.py
from __future__ import annotations

from pydantic import BaseModel, Field


class PermissionMatrixPageOut(BaseModel):
    page_code: str
    page_name: str
    read_permission: str | None = None
    write_permission: str | None = None


class PermissionMatrixPageGrantOut(BaseModel):
    page_code: str
    can_read: bool = False
    can_write: bool = False


class PermissionMatrixRowOut(BaseModel):
    user_id: int
    username: str
    full_name: str | None = None
    is_active: bool
    pages: list[PermissionMatrixPageGrantOut] = Field(default_factory=list)


class UserPermissionMatrixOut(BaseModel):
    pages: list[PermissionMatrixPageOut] = Field(default_factory=list)
    users: list[PermissionMatrixRowOut] = Field(default_factory=list)


__all__ = [
    "PermissionMatrixPageOut",
    "PermissionMatrixPageGrantOut",
    "PermissionMatrixRowOut",
    "UserPermissionMatrixOut",
]
