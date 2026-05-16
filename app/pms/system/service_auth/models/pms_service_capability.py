# app/pms/system/service_auth/models/pms_service_capability.py
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import relationship

from app.db.base import Base


class PmsServiceCapability(Base):
    """
    PMS 本地系统间调用能力目录。

    Boundary:
    - PMS 自己声明自己暴露哪些 capability。
    - ERP 后续只能读取 PMS 声明的 capability，不猜测 PMS 能力。
    - capability 是系统间调用授权的能力粒度，不是用户页面权限。
    """

    __tablename__ = "pms_service_capabilities"

    __table_args__ = (
        sa.PrimaryKeyConstraint("id", name="pk_pms_service_capabilities"),
        sa.UniqueConstraint(
            "capability_code",
            name="uq_pms_service_capabilities_capability_code",
        ),
        sa.CheckConstraint(
            "btrim(capability_code) <> ''",
            name="ck_pms_service_capabilities_capability_code_not_blank",
        ),
        sa.CheckConstraint(
            "btrim(capability_name) <> ''",
            name="ck_pms_service_capabilities_capability_name_not_blank",
        ),
        sa.CheckConstraint(
            "btrim(resource_code) <> ''",
            name="ck_pms_service_capabilities_resource_code_not_blank",
        ),
        sa.Index("ix_pms_service_capabilities_resource_code", "resource_code"),
    )

    id = sa.Column(sa.Integer, autoincrement=True)
    capability_code = sa.Column(sa.String(128), nullable=False)
    capability_name = sa.Column(sa.String(128), nullable=False)
    resource_code = sa.Column(sa.String(64), nullable=False)
    description = sa.Column(sa.String(255), nullable=True)
    is_active = sa.Column(sa.Boolean, nullable=False, server_default=sa.text("true"))
    created_at = sa.Column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("CURRENT_TIMESTAMP"),
    )
    updated_at = sa.Column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("CURRENT_TIMESTAMP"),
    )

    permissions = relationship(
        "PmsServicePermission",
        back_populates="capability",
        lazy="selectin",
    )
    routes = relationship(
        "PmsServiceCapabilityRoute",
        back_populates="capability",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )


__all__ = ["PmsServiceCapability"]
