# app/pms/system/service_auth/deps/pms_service_permission_deps.py
from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.pms.system.service_auth.services import PmsServicePermissionService

PMS_SERVICE_CLIENT_HEADER = "X-Service-Client"

GET_DB_DEP = Depends(get_db)
PMS_SERVICE_CLIENT_HEADER_DEP = Header(default=None, alias=PMS_SERVICE_CLIENT_HEADER)


def get_pms_service_permission_service(
    db: Session = GET_DB_DEP,
) -> PmsServicePermissionService:
    return PmsServicePermissionService(db)


PMS_SERVICE_PERMISSION_SERVICE_DEP = Depends(get_pms_service_permission_service)


def require_pms_service_capability(
    capability_code: str,
) -> Callable[[str | None, PmsServicePermissionService], None]:
    """
    Build a FastAPI dependency for PMS service-to-service capability checks.

    Usage example:
        Depends(require_pms_service_capability("pms.read.items"))

    Boundary:
    - capability_code 由 PMS 路由自己声明，不能由调用方传入。
    - 调用方只通过 X-Service-Client 声明自己是谁。
    - 这不是用户权限校验。
    """

    normalized_capability_code = (capability_code or "").strip()

    def dependency(
        x_service_client: str | None = PMS_SERVICE_CLIENT_HEADER_DEP,
        service: PmsServicePermissionService = PMS_SERVICE_PERMISSION_SERVICE_DEP,
    ) -> None:
        client_code = (x_service_client or "").strip()
        if not client_code:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="pms_service_client_required",
            )

        if not service.is_allowed(
            client_code=client_code,
            capability_code=normalized_capability_code,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="pms_service_permission_denied",
            )

    return dependency


__all__ = [
    "PMS_SERVICE_CLIENT_HEADER",
    "get_pms_service_permission_service",
    "require_pms_service_capability",
]
