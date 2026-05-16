# app/pms/system/service_auth/repos/pms_service_permission_repo.py
from __future__ import annotations

from sqlalchemy.orm import Session

from app.pms.system.service_auth.models import (
    PmsServiceCapability,
    PmsServiceClient,
    PmsServicePermission,
)


class PmsServicePermissionRepo:
    """
    PMS 系统间调用权限仓储。

    Boundary:
    - 只读取 pms_service_* 表。
    - 不读取 users / permissions / user_permissions。
    - 不做 HTTP header 解析；header 解析由 deps 层负责。
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def exists_active_permission(
        self,
        *,
        client_code: str,
        capability_code: str,
    ) -> bool:
        row = (
            self.db.query(PmsServicePermission.id)
            .join(PmsServiceClient, PmsServiceClient.id == PmsServicePermission.client_id)
            .join(
                PmsServiceCapability,
                PmsServiceCapability.capability_code == PmsServicePermission.capability_code,
            )
            .filter(PmsServiceClient.client_code == client_code)
            .filter(PmsServiceClient.is_active.is_(True))
            .filter(PmsServiceCapability.is_active.is_(True))
            .filter(PmsServicePermission.capability_code == capability_code)
            .filter(PmsServicePermission.is_active.is_(True))
            .first()
        )
        return row is not None


__all__ = ["PmsServicePermissionRepo"]
