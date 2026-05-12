# app/pms/suppliers/contracts/suppliers.py
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SupplierContactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    supplier_id: int
    name: str
    phone: str | None = None
    email: str | None = None
    wechat: str | None = None
    role: str
    is_primary: bool
    active: bool


class SupplierOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    website: str | None = None
    active: bool
    contacts: list[SupplierContactOut] = Field(default_factory=list)


class SupplierCreateIn(BaseModel):
    name: str = Field(..., min_length=1)
    code: str = Field(..., min_length=1)
    website: str | None = None
    active: bool = True


class SupplierUpdateIn(BaseModel):
    name: str | None = None
    code: str | None = None
    website: str | None = None
    active: bool | None = None


class SupplierContactCreateIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    phone: str | None = Field(None, max_length=50)
    email: str | None = Field(None, max_length=255)
    wechat: str | None = Field(None, max_length=64)
    role: str = Field(default="other", max_length=32)
    is_primary: bool = False
    active: bool = True


class SupplierContactUpdateIn(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    phone: str | None = Field(None, max_length=50)
    email: str | None = Field(None, max_length=255)
    wechat: str | None = Field(None, max_length=64)
    role: str | None = Field(None, max_length=32)
    is_primary: bool | None = None
    active: bool | None = None


class SupplierBasic(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore", populate_by_name=True)

    id: int
    name: str
    code: str | None = None
    active: bool


class PmsProjectionSupplierFeedRow(BaseModel):
    """
    PMS supplier projection feed row.

    This is the read model consumed by WMS projection sync.
    It intentionally carries only supplier master data needed for WMS read/options/display.
    Supplier contacts remain PMS-owner data and are not included in this first projection feed.
    """

    supplier_id: int
    supplier_code: str
    supplier_name: str
    active: bool
    website: str | None = None
    source_updated_at: datetime | None = None


class PmsProjectionSupplierFeedOut(BaseModel):
    rows: list[PmsProjectionSupplierFeedRow] = Field(default_factory=list)
    limit: int
    offset: int
    next_offset: int | None = None
    has_more: bool = False
