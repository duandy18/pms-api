# app/pms/system/write_v1/repos/service_permission_write_repo.py
from __future__ import annotations

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.pms.system.service_auth.models import (
    PmsServiceCapability,
    PmsServiceClient,
    PmsServicePermission,
)


class PmsServicePermissionWriteSaveError(RuntimeError):
    pass


class PmsServicePermissionWriteRepo:
    """
    PMS service permission write repository.

    Boundary:
    - Only reads/writes pms_service_clients and pms_service_permissions.
    - Reads pms_service_capabilities only to validate target capability existence.
    - Never reads users / permissions / user_permissions.
    - Never writes ERP tables or other systems.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_client_by_code(self, client_code: str) -> PmsServiceClient | None:
        return (
            self.db.query(PmsServiceClient)
            .filter(PmsServiceClient.client_code == client_code)
            .one_or_none()
        )

    def get_capability_by_code(self, capability_code: str) -> PmsServiceCapability | None:
        return (
            self.db.query(PmsServiceCapability)
            .filter(PmsServiceCapability.capability_code == capability_code)
            .one_or_none()
        )

    def get_permission(
        self,
        *,
        client_id: int,
        capability_code: str,
    ) -> PmsServicePermission | None:
        return (
            self.db.query(PmsServicePermission)
            .filter(PmsServicePermission.client_id == client_id)
            .filter(PmsServicePermission.capability_code == capability_code)
            .one_or_none()
        )

    def add(self, row: object) -> None:
        self.db.add(row)

    def flush(self) -> None:
        try:
            self.db.flush()
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise PmsServicePermissionWriteSaveError(
                "pms_service_permission_write_flush_failed"
            ) from exc

    def commit(self) -> None:
        try:
            self.db.commit()
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise PmsServicePermissionWriteSaveError(
                "pms_service_permission_write_commit_failed"
            ) from exc

    def refresh(self, row: object) -> None:
        self.db.refresh(row)


__all__ = [
    "PmsServicePermissionWriteRepo",
    "PmsServicePermissionWriteSaveError",
]
