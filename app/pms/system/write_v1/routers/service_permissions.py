# app/pms/system/write_v1/routers/service_permissions.py
from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.pms.system.service_auth.deps import PMS_SERVICE_CLIENT_HEADER
from app.pms.system.write_v1.contracts import (
    PmsSystemServicePermissionApplyIn,
    PmsSystemServicePermissionApplyOut,
    PmsSystemServicePermissionVerifyOut,
)
from app.pms.system.write_v1.repos import PmsServicePermissionWriteSaveError
from app.pms.system.write_v1.services import (
    PmsServicePermissionCapabilityNotFoundError,
    PmsServicePermissionClientCodeReservedError,
    PmsServicePermissionWriteService,
)

router = APIRouter(prefix="/system/write/v1", tags=["system-write-v1"])

ERP_SERVICE_CLIENT_CODE = "erp-service"


def require_erp_service_client(
    x_service_client: str | None = Header(default=None, alias=PMS_SERVICE_CLIENT_HEADER),
) -> None:
    client_code = (x_service_client or "").strip()

    if not client_code:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="pms_service_client_required",
        )

    if client_code != ERP_SERVICE_CLIENT_CODE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="pms_service_permission_write_denied",
        )


@router.post(
    "/service-permissions/apply",
    response_model=PmsSystemServicePermissionApplyOut,
    summary="Apply PMS service permission",
)
async def apply_pms_service_permission(
    payload: PmsSystemServicePermissionApplyIn,
    _erp_service_client: None = Depends(require_erp_service_client),
    db: Session = Depends(get_db),
) -> PmsSystemServicePermissionApplyOut:
    """
    Apply one PMS local service permission from ERP.

    Boundary:
    - Only X-Service-Client: erp-service may call this endpoint.
    - Writes only pms_service_clients and pms_service_permissions.
    - Does not write ERP tables.
    - Does not write other systems.
    - Does not read users / permissions / user_permissions.
    """

    try:
        return PmsServicePermissionWriteService(db).apply_permission(payload)
    except PmsServicePermissionCapabilityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PmsServicePermissionClientCodeReservedError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except PmsServicePermissionWriteSaveError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.get(
    "/service-permissions/verify",
    response_model=PmsSystemServicePermissionVerifyOut,
    summary="Verify PMS service permission",
)
async def verify_pms_service_permission(
    client_code: str = Query(..., min_length=1, max_length=64),
    capability_code: str = Query(..., min_length=1, max_length=128),
    _erp_service_client: None = Depends(require_erp_service_client),
    db: Session = Depends(get_db),
) -> PmsSystemServicePermissionVerifyOut:
    """
    Verify one PMS local service permission for ERP.

    Boundary:
    - Only X-Service-Client: erp-service may call this endpoint.
    - Reads only pms_service_clients, pms_service_capabilities, and pms_service_permissions.
    - Does not write anything.
    - Does not read users / permissions / user_permissions.
    """

    return PmsServicePermissionWriteService(db).verify_permission(
        client_code=client_code,
        capability_code=capability_code,
    )


__all__ = ["router"]
