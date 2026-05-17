# app/pms/system/read_v1/routers/service_capabilities.py
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.pms.system.read_v1.contracts import PmsSystemServiceCapabilitiesOut
from app.pms.system.read_v1.repos import PmsServiceCapabilityReadRepo
from app.pms.system.read_v1.services import PmsServiceCapabilityReadService

router = APIRouter(prefix="/system/read/v1", tags=["system-read-v1"])


@router.get(
    "/service-capabilities",
    response_model=PmsSystemServiceCapabilitiesOut,
    summary="Get PMS service capabilities",
)
async def get_pms_service_capabilities(
    db: Session = Depends(get_db),
) -> PmsSystemServiceCapabilitiesOut:
    return PmsServiceCapabilityReadService(
        PmsServiceCapabilityReadRepo(db),
    ).get_service_capabilities()


__all__ = ["router"]
