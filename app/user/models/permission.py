# app/user/models/permission.py
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.user.models.user import user_permissions


class Permission(Base):
    __tablename__ = "permissions"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    name = sa.Column(sa.String(128), nullable=False, unique=True)

    users = relationship(
        "User",
        secondary=user_permissions,
        back_populates="permissions",
        lazy="selectin",
    )
