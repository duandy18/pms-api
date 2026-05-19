# app/admin/routers/users.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.admin.contracts.user_permission_matrix import UserPermissionMatrixOut
from app.admin.services.user_permission_matrix_service import UserPermissionMatrixService
from app.db.deps import get_db
from app.user.contracts.user import UserOut
from app.user.deps.auth import get_current_user
from app.user.services.user_errors import AuthorizationError
from app.user.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["admin-users"])


def _to_user_out(svc: UserService, user) -> UserOut:
    return UserOut(
        id=int(user.id),
        username=str(user.username),
        is_active=bool(getattr(user, "is_active", True)),
        full_name=getattr(user, "full_name", None),
        phone=getattr(user, "phone", None),
        email=getattr(user, "email", None),
        permissions=svc.get_user_permissions(user),
    )


def _check_admin_read(svc: UserService, current_user) -> None:
    try:
        svc.check_permission(current_user, ["page.admin.read"])
    except AuthorizationError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/permission-matrix", response_model=UserPermissionMatrixOut)
def get_permission_matrix(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> UserPermissionMatrixOut:
    """
    Read-only PMS local IAM runtime projection.

    ERP is the IAM owner. PMS keeps local users / user_permissions only for
    runtime permission execution and diagnostic visibility.
    """

    svc = UserService(db)
    _check_admin_read(svc, current_user)
    return UserPermissionMatrixService(db).get_matrix()


@router.get("", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> list[UserOut]:
    """
    Read-only PMS local users runtime projection.

    User creation, status changes, password reset, deletion, and permission
    assignment are managed by ERP and applied through /system/write/v1/iam.
    """

    svc = UserService(db)
    _check_admin_read(svc, current_user)
    return [_to_user_out(svc, user) for user in svc.list_users()]


__all__ = ["router"]
