# app/pms/system/read_v1/services/service_dependencies_service.py
from __future__ import annotations

from app.pms.system.read_v1.contracts import PmsSystemServiceDependenciesOut
from app.pms.system.read_v1.services.app_manifest_service import PMS_APP_CODE, PMS_APP_NAME

PMS_SERVICE_CLIENT_CODE = "pms-service"


def build_pms_service_dependencies() -> PmsSystemServiceDependenciesOut:
    """
    Return PMS declared outbound service dependencies.

    Current boundary:
    - PMS has no declared outbound service dependencies in the current codebase.
    - Empty list does not mean ERP has no work; it means PMS is not currently a source system.
    - ERP still reads PMS service-capabilities because PMS is a target system for WMS/OMS/Procurement.
    """

    return PmsSystemServiceDependenciesOut(
        app_code=PMS_APP_CODE,
        app_name=PMS_APP_NAME,
        source_service_client_code=PMS_SERVICE_CLIENT_CODE,
        dependencies=[],
    )


__all__ = [
    "PMS_SERVICE_CLIENT_CODE",
    "build_pms_service_dependencies",
]
