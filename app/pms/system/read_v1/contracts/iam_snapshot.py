# app/pms/system/read_v1/contracts/iam_snapshot.py
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PmsSystemIamSnapshotUserOut(_Base):
    user_id: int = Field(..., ge=1)
    username: str = Field(..., min_length=1, max_length=64)
    is_active: bool
    full_name: str | None = Field(default=None, max_length=128)
    phone: str | None = Field(default=None, max_length=32)
    email: str | None = Field(default=None, max_length=255)


class PmsSystemIamSnapshotPermissionOut(_Base):
    permission_id: int = Field(..., ge=1)
    permission_code: str = Field(..., min_length=1, max_length=128)


class PmsSystemIamSnapshotUserPermissionOut(_Base):
    user_id: int = Field(..., ge=1)
    permission_id: int = Field(..., ge=1)
    permission_code: str = Field(..., min_length=1, max_length=128)
    granted_at: datetime | None = None


class PmsSystemIamSnapshotPageOut(_Base):
    page_code: str = Field(..., min_length=1, max_length=64)
    page_name: str = Field(..., min_length=1, max_length=64)
    parent_page_code: str | None = Field(default=None, max_length=64)
    level: int = Field(..., ge=1, le=3)
    domain_code: str = Field(..., min_length=1, max_length=32)
    show_in_topbar: bool
    show_in_sidebar: bool
    inherit_permissions: bool
    read_permission_code: str | None = Field(default=None, max_length=128)
    write_permission_code: str | None = Field(default=None, max_length=128)
    sort_order: int | None = None
    is_active: bool | None = None


class PmsSystemIamSnapshotRoutePrefixOut(_Base):
    id: int = Field(..., ge=1)
    page_code: str = Field(..., min_length=1, max_length=64)
    route_prefix: str = Field(..., min_length=1, max_length=255)
    sort_order: int | None = None
    is_active: bool | None = None


class PmsSystemIamSnapshotOut(_Base):
    app_code: Literal["pms"]
    app_name: str = Field(..., min_length=1)
    snapshot_at: datetime
    users: list[PmsSystemIamSnapshotUserOut] = Field(default_factory=list)
    permissions: list[PmsSystemIamSnapshotPermissionOut] = Field(default_factory=list)
    user_permissions: list[PmsSystemIamSnapshotUserPermissionOut] = Field(default_factory=list)
    page_registry: list[PmsSystemIamSnapshotPageOut] = Field(default_factory=list)
    page_route_prefixes: list[PmsSystemIamSnapshotRoutePrefixOut] = Field(default_factory=list)


__all__ = [
    "PmsSystemIamSnapshotOut",
    "PmsSystemIamSnapshotPageOut",
    "PmsSystemIamSnapshotPermissionOut",
    "PmsSystemIamSnapshotRoutePrefixOut",
    "PmsSystemIamSnapshotUserOut",
    "PmsSystemIamSnapshotUserPermissionOut",
]
