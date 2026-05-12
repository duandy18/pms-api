# app/admin/contracts/user_permission_matrix_update.py
from __future__ import annotations

from pydantic import BaseModel, Field


class PermissionMatrixPageUpdateIn(BaseModel):
    page_code: str
    can_read: bool = False
    can_write: bool = False


class UserPermissionMatrixUpdateIn(BaseModel):
    pages: list[PermissionMatrixPageUpdateIn] = Field(default_factory=list)


__all__ = ["PermissionMatrixPageUpdateIn", "UserPermissionMatrixUpdateIn"]
