# app/pms/system/service_auth/deps/__init__.py
from __future__ import annotations

from app.pms.system.service_auth.deps.pms_service_permission_deps import (
    PMS_SERVICE_CLIENT_HEADER,
    get_pms_service_permission_service,
    require_pms_service_capability,
)

__all__ = [
    "PMS_SERVICE_CLIENT_HEADER",
    "get_pms_service_permission_service",
    "require_pms_service_capability",
]
