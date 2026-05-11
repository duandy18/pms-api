# app/pms/suppliers/models/supplier.py
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.db.base import Base

if TYPE_CHECKING:
    from app.pms.suppliers.models.supplier_contact import SupplierContact


class Supplier(Base):
    __tablename__ = "suppliers"

    __table_args__ = (
        sa.UniqueConstraint("name", name="uq_suppliers_name"),
        sa.UniqueConstraint("code", name="uq_suppliers_code"),
        sa.CheckConstraint("btrim(code) <> ''", name="ck_suppliers_code_nonblank"),
        sa.CheckConstraint("code = btrim(code)", name="ck_suppliers_code_trimmed"),
        sa.CheckConstraint("code = upper(code)", name="ck_suppliers_code_upper"),
        sa.CheckConstraint("btrim(name) <> ''", name="ck_suppliers_name_nonblank"),
        sa.CheckConstraint("name = btrim(name)", name="ck_suppliers_name_trimmed"),
        sa.Index("ix_suppliers_active", "active"),
        sa.Index("ix_suppliers_name", "name"),
    )

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    code: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    website: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    active: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        default=True,
        server_default=sa.text("true"),
    )

    contacts: Mapped[list["SupplierContact"]] = relationship(
        "SupplierContact",
        back_populates="supplier",
        cascade="save-update, merge",
        passive_deletes=True,
        lazy="selectin",
    )

    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
        onupdate=sa.func.now(),
    )

    @validates("code")
    def _validate_code(self, _key: str, value: str) -> str:
        if value is None:
            raise ValueError("supplier.code 不能为空")

        normalized = value.strip().upper()
        if normalized == "":
            raise ValueError("supplier.code 不能为空白")

        return normalized

    @validates("name")
    def _validate_name(self, _key: str, value: str) -> str:
        if value is None:
            raise ValueError("supplier.name 不能为空")

        normalized = value.strip()
        if normalized == "":
            raise ValueError("supplier.name 不能为空白")

        return normalized


__all__ = ["Supplier"]
