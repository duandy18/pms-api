# app/user/models/user.py
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import relationship

from app.db.base import Base

user_permissions = sa.Table(
    "user_permissions",
    Base.metadata,
    sa.Column(
        "user_id",
        sa.Integer,
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    sa.Column(
        "permission_id",
        sa.Integer,
        sa.ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    sa.Column(
        "granted_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("CURRENT_TIMESTAMP"),
    ),
    sa.Index("ix_user_permissions_permission_id", "permission_id"),
)


class User(Base):
    __tablename__ = "users"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    username = sa.Column(sa.String(64), nullable=False, unique=True)
    password_hash = sa.Column(sa.String(255), nullable=False)
    is_active = sa.Column(sa.Boolean, nullable=False, server_default=sa.text("true"))

    full_name = sa.Column(sa.String(128), nullable=True)
    phone = sa.Column(sa.String(32), nullable=True)
    email = sa.Column(sa.String(255), nullable=True)

    permissions = relationship(
        "Permission",
        secondary=user_permissions,
        back_populates="users",
        lazy="selectin",
    )
