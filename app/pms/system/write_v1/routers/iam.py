# app/pms/system/write_v1/routers/iam.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.pms.system.write_v1.contracts import (
    PmsSystemIamApplyIn,
    PmsSystemIamApplyOut,
    PmsSystemIamVerifyOut,
)
from app.pms.system.write_v1.repos import PmsIamWriteSaveError
from app.pms.system.write_v1.routers.service_permissions import require_erp_service_client
from app.pms.system.write_v1.services import (
    PmsIamPayloadError,
    PmsIamPermissionNotFoundError,
    PmsIamWriteService,
)

router = APIRouter(prefix="/system/write/v1", tags=["system-write-v1"])


@router.post(
    "/iam/apply",
    response_model=PmsSystemIamApplyOut,
    summary="Apply PMS IAM desired state",
)
async def apply_pms_iam(
    payload: PmsSystemIamApplyIn,
    _erp_service_client: None = Depends(require_erp_service_client),
    db: Session = Depends(get_db),
) -> PmsSystemIamApplyOut:
    """
    Apply PMS local user IAM runtime projection from ERP.

    Boundary:
    - Only X-Service-Client: erp-service may call this endpoint.
    - Writes only users / user_permissions.
    - Reads permissions only to validate PMS-owned permission codes.
    - Does not create unknown permissions.
    - Does not write page_registry / page_route_prefixes.
    """

    try:
        return PmsIamWriteService(db).apply(payload)
    except PmsIamPermissionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PmsIamPayloadError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except PmsIamWriteSaveError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.post(
    "/iam/verify",
    response_model=PmsSystemIamVerifyOut,
    summary="Verify PMS IAM desired state",
)
async def verify_pms_iam(
    payload: PmsSystemIamApplyIn,
    _erp_service_client: None = Depends(require_erp_service_client),
    db: Session = Depends(get_db),
) -> PmsSystemIamVerifyOut:
    """
    Verify PMS local user IAM runtime projection against ERP desired state.
    """

    try:
        return PmsIamWriteService(db).verify(payload)
    except PmsIamPayloadError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


__all__ = ["router"]
