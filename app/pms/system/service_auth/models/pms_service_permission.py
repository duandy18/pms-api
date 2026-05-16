# app/pms/system/service_auth/models/pms_service_permission.py
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import relationship

from app.db.base import Base


class PmsServicePermission(Base):
    """
    PMS 本地系统间调用权限。

    Boundary:
    - capability_code 表示 PMS 暴露给其他系统的能力。
    - 不复用 users / permissions / user_permissions。
    - 运行时是否放行由 PMS 自己查这张表决定。
    """

    __tablename__ = "pms_service_permissions"

    __table_args__ = (
        sa.PrimaryKeyConstraint("id", name="pk_pms_service_permissions"),
        sa.UniqueConstraint(
            "client_id",
            "capability_code",
            name="uq_pms_service_permissions_client_capability",
        ),
        sa.CheckConstraint(
            "btrim(capability_code) <> ''",
            name="ck_pms_service_permissions_capability_code_not_blank",
        ),
        sa.Index("ix_pms_service_permissions_client_id", "client_id"),
        sa.Index("ix_pms_service_permissions_capability_code", "capability_code"),
    )

    id = sa.Column(sa.Integer, autoincrement=True)
    client_id = sa.Column(
        sa.Integer,
        sa.ForeignKey(
            "pms_service_clients.id",
            name="fk_pms_service_permissions_client_id_pms_service_clients",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    capability_code = sa.Column(
        sa.String(128),
        sa.ForeignKey(
            "pms_service_capabilities.capability_code",
            name="fk_pms_service_permissions_capability_code",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    description = sa.Column(sa.String(255), nullable=True)
    is_active = sa.Column(sa.Boolean, nullable=False, server_default=sa.text("true"))
    granted_at = sa.Column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("CURRENT_TIMESTAMP"),
    )

    client = relationship(
        "PmsServiceClient",
        back_populates="permissions",
        lazy="joined",
    )
    capability = relationship(
        "PmsServiceCapability",
        back_populates="permissions",
        lazy="joined",
    )


__all__ = ["PmsServicePermission"]
