# app/pms/system/read_v1/routers/service_dependencies.py
from __future__ import annotations

from fastapi import APIRouter

from app.pms.system.read_v1.contracts import PmsSystemServiceDependenciesOut
from app.pms.system.read_v1.services import build_pms_service_dependencies

router = APIRouter(prefix="/system/read/v1", tags=["system-read-v1"])


@router.get(
    "/service-dependencies",
    response_model=PmsSystemServiceDependenciesOut,
    summary="Get PMS service dependencies",
)
async def get_pms_service_dependencies() -> PmsSystemServiceDependenciesOut:
    return build_pms_service_dependencies()


__all__ = ["router"]
