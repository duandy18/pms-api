# app/pms/suppliers/models/supplier_contact.py
from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SupplierContact(Base):
    __tablename__ = "supplier_contacts"

    __table_args__ = (
        sa.Index("ix_supplier_contacts_supplier_id", "supplier_id"),
        sa.Index(
            "uq_supplier_contacts_primary_per_supplier",
            "supplier_id",
            unique=True,
            postgresql_where=sa.text("is_primary = true"),
        ),
    )

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    supplier_id: Mapped[int] = mapped_column(
        sa.Integer,
        sa.ForeignKey(
            "suppliers.id",
            name="supplier_contacts_supplier_id_fkey",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    phone: Mapped[str | None] = mapped_column(sa.String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    wechat: Mapped[str | None] = mapped_column(sa.String(64), nullable=True)

    role: Mapped[str] = mapped_column(
        sa.String(32),
        nullable=False,
        default="other",
        server_default=sa.text("'other'"),
    )
    is_primary: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        default=False,
        server_default=sa.text("false"),
    )
    active: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        default=True,
        server_default=sa.text("true"),
    )

    supplier = relationship("Supplier", back_populates="contacts")

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


__all__ = ["SupplierContact"]
