# app/user/models/page_registry.py
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import relationship

from app.db.base import Base


class PageRegistry(Base):
    __tablename__ = "page_registry"

    __table_args__ = (
        sa.CheckConstraint(
            "domain_code IN ('pms', 'admin')",
            name="ck_page_registry_domain_code",
        ),
        sa.CheckConstraint("level IN (1, 2, 3)", name="ck_page_registry_level"),
        sa.CheckConstraint(
            "((level = 1 AND parent_code IS NULL) OR (level IN (2, 3) AND parent_code IS NOT NULL))",
            name="ck_page_registry_parent_level_consistency",
        ),
        sa.CheckConstraint(
            "("
            "(inherit_permissions = TRUE AND read_permission_id IS NULL AND write_permission_id IS NULL) "
            "OR "
            "(inherit_permissions = FALSE AND read_permission_id IS NOT NULL AND write_permission_id IS NOT NULL)"
            ")",
            name="ck_page_registry_permission_inherit_consistency",
        ),
        sa.Index("ix_page_registry_parent_code", "parent_code"),
    )

    code = sa.Column(sa.String(64), primary_key=True)
    name = sa.Column(sa.String(64), nullable=False)

    parent_code = sa.Column(
        sa.String(64),
        sa.ForeignKey(
            "page_registry.code",
            name="fk_page_registry_parent_code_page_registry",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )

    level = sa.Column(sa.Integer, nullable=False)
    domain_code = sa.Column(sa.String(32), nullable=False)

    show_in_topbar = sa.Column(sa.Boolean, nullable=False)
    show_in_sidebar = sa.Column(sa.Boolean, nullable=False)
    inherit_permissions = sa.Column(sa.Boolean, nullable=False)

    read_permission_id = sa.Column(
        sa.Integer,
        sa.ForeignKey(
            "permissions.id",
            name="fk_page_registry_read_permission_id_permissions",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )
    write_permission_id = sa.Column(
        sa.Integer,
        sa.ForeignKey(
            "permissions.id",
            name="fk_page_registry_write_permission_id_permissions",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )

    sort_order = sa.Column(sa.Integer, nullable=False, server_default=sa.text("0"))
    is_active = sa.Column(sa.Boolean, nullable=False, server_default=sa.text("true"))

    parent = relationship(
        "PageRegistry",
        remote_side=[code],
        back_populates="children",
        foreign_keys=[parent_code],
        lazy="joined",
    )
    children = relationship(
        "PageRegistry",
        back_populates="parent",
        foreign_keys="PageRegistry.parent_code",
        lazy="selectin",
    )
    route_prefixes = relationship(
        "PageRoutePrefix",
        back_populates="page",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )
    read_permission = relationship("Permission", foreign_keys=[read_permission_id], lazy="joined")
    write_permission = relationship("Permission", foreign_keys=[write_permission_id], lazy="joined")
