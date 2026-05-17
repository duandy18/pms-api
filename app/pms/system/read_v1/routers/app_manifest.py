# app/pms/system/read_v1/routers/app_manifest.py
from __future__ import annotations

from fastapi import APIRouter

from app.pms.system.read_v1.contracts import PmsSystemAppManifestOut
from app.pms.system.read_v1.services import build_pms_app_manifest

router = APIRouter(prefix="/system/read/v1", tags=["system-read-v1"])


@router.get(
    "/app-manifest",
    response_model=PmsSystemAppManifestOut,
    summary="Get PMS app manifest",
)
async def get_pms_app_manifest() -> PmsSystemAppManifestOut:
    return build_pms_app_manifest()


__all__ = ["router"]
