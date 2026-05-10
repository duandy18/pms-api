# app/partners/suppliers/models/supplier.py
from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    code: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    website: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    active: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=True)
    created_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)


__all__ = ["Supplier"]
