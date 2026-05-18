# app/pms/system/read_v1/routers/iam_snapshot.py
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.pms.system.read_v1.contracts import PmsSystemIamSnapshotOut
from app.pms.system.read_v1.repos import PmsIamSnapshotRepo
from app.pms.system.read_v1.services import PmsIamSnapshotService
from app.pms.system.service_auth.deps import require_pms_service_capability

router = APIRouter(prefix="/system/read/v1", tags=["system-read-v1"])

require_pms_read_iam_snapshot = require_pms_service_capability(
    "pms.read.iam_snapshot",
)


@router.get(
    "/iam-snapshot",
    response_model=PmsSystemIamSnapshotOut,
    summary="Get PMS IAM snapshot",
)
async def get_pms_iam_snapshot(
    _service_permission: None = Depends(require_pms_read_iam_snapshot),
    db: Session = Depends(get_db),
) -> PmsSystemIamSnapshotOut:
    """
    Return PMS users, user permissions, and page permission catalog for ERP projection sync.

    Boundary:
    - Only ERP service client should be granted this capability.
    - This endpoint is read-only.
    - This endpoint never exposes password_hash, tokens, or secrets.
    - This endpoint does not write PMS permissions.
    - This endpoint does not migrate permission execution to ERP.
    """

    return PmsIamSnapshotService(PmsIamSnapshotRepo(db)).get_iam_snapshot()


__all__ = ["router"]
