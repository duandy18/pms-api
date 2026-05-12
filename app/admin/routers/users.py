# app/admin/routers/users.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.admin.contracts.user_permission_matrix import UserPermissionMatrixOut
from app.admin.contracts.user_permission_matrix_update import UserPermissionMatrixUpdateIn
from app.admin.services.user_permission_matrix_service import UserPermissionMatrixService
from app.admin.services.user_permission_matrix_write_service import UserPermissionMatrixWriteService
from app.db.deps import get_db
from app.user.contracts.user import UserOut
from app.user.contracts.user_admin import UserCreateMulti, UserUpdateMulti
from app.user.deps.auth import get_current_user
from app.user.services.user_errors import AuthorizationError, DuplicateUserError, NotFoundError
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
        raise HTTPException(status_code=403, detail=str(exc))


def _check_admin_write(svc: UserService, current_user) -> None:
    try:
        svc.check_permission(current_user, ["page.admin.write"])
    except AuthorizationError as exc:
        raise HTTPException(status_code=403, detail=str(exc))


@router.get("/permission-matrix", response_model=UserPermissionMatrixOut)
def get_permission_matrix(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> UserPermissionMatrixOut:
    svc = UserService(db)
    _check_admin_read(svc, current_user)
    return UserPermissionMatrixService(db).get_matrix()


@router.get("", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> list[UserOut]:
    svc = UserService(db)
    _check_admin_read(svc, current_user)
    return [_to_user_out(svc, user) for user in svc.list_users()]


@router.post("", response_model=UserOut, status_code=201)
def create_user(
    body: UserCreateMulti,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> UserOut:
    svc = UserService(db)
    _check_admin_write(svc, current_user)

    try:
        user = svc.create_user(
            username=body.username,
            password=body.password,
            permission_ids=body.permission_ids,
            full_name=body.full_name,
            phone=body.phone,
            email=body.email,
        )
    except DuplicateUserError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return _to_user_out(svc, user)


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    body: UserUpdateMulti,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> UserOut:
    svc = UserService(db)
    _check_admin_write(svc, current_user)

    try:
        user = svc.update_user(
            user_id=int(user_id),
            full_name=body.full_name,
            phone=body.phone,
            email=body.email,
            is_active=body.is_active,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return _to_user_out(svc, user)


@router.put("/{user_id}/permission-matrix", response_model=UserOut)
def save_user_permission_matrix(
    user_id: int,
    body: UserPermissionMatrixUpdateIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> UserOut:
    svc = UserService(db)
    _check_admin_write(svc, current_user)

    try:
        user = UserPermissionMatrixWriteService(db).save_matrix_for_user(
            user_id=int(user_id),
            body=body,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return _to_user_out(svc, user)


@router.post("/{user_id}/delete")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> dict[str, bool | str]:
    svc = UserService(db)
    _check_admin_write(svc, current_user)

    if int(getattr(current_user, "id", 0)) == int(user_id):
        raise HTTPException(status_code=400, detail="不能删除当前登录用户")

    try:
        svc.delete_user(int(user_id))
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {"ok": True, "message": "用户已删除"}


@router.post("/{user_id}/reset-password")
def reset_password(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> dict[str, bool | str]:
    svc = UserService(db)
    _check_admin_write(svc, current_user)

    try:
        svc.reset_user_password(int(user_id), new_password="000000")
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return {"ok": True, "message": "密码重置为 000000"}
