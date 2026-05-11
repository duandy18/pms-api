# app/user/models/page_route_prefix.py
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import relationship

from app.db.base import Base


class PageRoutePrefix(Base):
    __tablename__ = "page_route_prefixes"

    __table_args__ = (
        sa.UniqueConstraint("route_prefix", name="uq_page_route_prefixes_route_prefix"),
        sa.Index("ix_page_route_prefixes_page_code", "page_code"),
    )

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    page_code = sa.Column(
        sa.String(64),
        sa.ForeignKey(
            "page_registry.code",
            name="fk_page_route_prefixes_page_code_page_registry",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    route_prefix = sa.Column(sa.String(255), nullable=False)
    sort_order = sa.Column(sa.Integer, nullable=False, server_default=sa.text("0"))
    is_active = sa.Column(sa.Boolean, nullable=False, server_default=sa.text("true"))

    page = relationship("PageRegistry", back_populates="route_prefixes", lazy="joined")
