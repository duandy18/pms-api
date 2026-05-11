# app/pms/suppliers/routers/supplier_contacts.py
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.pms.suppliers.contracts.suppliers import (
    SupplierContactCreateIn,
    SupplierContactOut,
    SupplierContactUpdateIn,
)
from app.pms.suppliers.helpers.suppliers import check_perm
from app.pms.suppliers.repos.supplier_contact_repo import (
    clear_primary_contacts as repo_clear_primary_contacts,
    create_contact as repo_create_contact,
    delete_contact as repo_delete_contact,
    get_contact as repo_get_contact,
    get_supplier as repo_get_supplier,
    save_contact as repo_save_contact,
)
from app.user.deps.auth import get_current_user

router = APIRouter(tags=["pms-supplier-contacts"])


def _to_out(contact) -> SupplierContactOut:
    return SupplierContactOut(
        id=int(contact.id),
        supplier_id=int(contact.supplier_id),
        name=str(contact.name),
        phone=contact.phone,
        email=contact.email,
        wechat=contact.wechat,
        role=str(contact.role),
        is_primary=bool(contact.is_primary),
        active=bool(contact.active),
    )


def _trim_or_none(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed if trimmed else None


@router.post(
    "/pms/suppliers/{supplier_id}/contacts",
    response_model=SupplierContactOut,
    status_code=status.HTTP_201_CREATED,
    name="pms_supplier_create_contact",
)
def create_contact(
    supplier_id: int = Path(..., ge=1),
    payload: SupplierContactCreateIn = ...,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> SupplierContactOut:
    check_perm(db, user, ["page.pms.write"])

    supplier = repo_get_supplier(db, supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="name is required")

    if payload.is_primary:
        repo_clear_primary_contacts(db, supplier_id)

    contact = repo_create_contact(
        db,
        supplier_id=supplier_id,
        name=name,
        phone=_trim_or_none(payload.phone),
        email=str(payload.email).strip() if payload.email else None,
        wechat=_trim_or_none(payload.wechat),
        role=(payload.role or "other").strip() or "other",
        is_primary=payload.is_primary,
        active=payload.active,
    )
    return _to_out(contact)


@router.patch(
    "/pms/supplier-contacts/{contact_id}",
    response_model=SupplierContactOut,
    name="pms_supplier_update_contact",
)
def update_contact(
    contact_id: int = Path(..., ge=1),
    payload: SupplierContactUpdateIn = ...,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> SupplierContactOut:
    check_perm(db, user, ["page.pms.write"])

    contact = repo_get_contact(db, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    if payload.is_primary is True:
        repo_clear_primary_contacts(db, contact.supplier_id)

    data = payload.model_dump(exclude_unset=True)

    if "name" in data:
        name = (data["name"] or "").strip()
        if not name:
            raise HTTPException(status_code=422, detail="name is required")
        contact.name = name

    if "phone" in data:
        contact.phone = _trim_or_none(data["phone"])
    if "email" in data:
        contact.email = str(data["email"]).strip() if data["email"] else None
    if "wechat" in data:
        contact.wechat = _trim_or_none(data["wechat"])
    if "role" in data:
        contact.role = (data["role"] or "other").strip() or "other"
    if "is_primary" in data:
        contact.is_primary = bool(data["is_primary"])
    if "active" in data:
        contact.active = bool(data["active"])

    contact = repo_save_contact(db, contact)
    return _to_out(contact)


@router.delete(
    "/pms/supplier-contacts/{contact_id}",
    status_code=status.HTTP_200_OK,
    name="pms_supplier_delete_contact",
)
def delete_contact(
    contact_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> dict[str, bool]:
    check_perm(db, user, ["page.pms.write"])

    contact = repo_get_contact(db, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    repo_delete_contact(db, contact)
    return {"ok": True}
