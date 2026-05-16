# app/service_auth/services/pms_service_permission_service.py
from __future__ import annotations

from sqlalchemy.orm import Session

from app.service_auth.models import PmsServiceClient, PmsServicePermission


class PmsServicePermissionService:
    """
    PMS 本地系统间调用权限校验服务。

    Boundary:
    - 只判断 service client 是否拥有某个 PMS capability。
    - 不读取 users / permissions / user_permissions。
    - 不负责 service client 身份认证；身份认证后续由网关、service token 或签名机制承接。
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def _normalize(value: str | None) -> str:
        return (value or "").strip()

    def is_allowed(self, *, client_code: str | None, capability_code: str | None) -> bool:
        normalized_client_code = self._normalize(client_code)
        normalized_capability_code = self._normalize(capability_code)

        if not normalized_client_code or not normalized_capability_code:
            return False

        row = (
            self.db.query(PmsServicePermission.id)
            .join(PmsServiceClient, PmsServiceClient.id == PmsServicePermission.client_id)
            .filter(PmsServiceClient.client_code == normalized_client_code)
            .filter(PmsServiceClient.is_active.is_(True))
            .filter(PmsServicePermission.capability_code == normalized_capability_code)
            .filter(PmsServicePermission.is_active.is_(True))
            .first()
        )
        return row is not None


__all__ = ["PmsServicePermissionService"]
