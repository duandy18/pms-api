# app/pms/suppliers/helpers/suppliers.py
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.pms.suppliers.contracts.suppliers import SupplierContactOut
from app.pms.suppliers.models.supplier_contact import SupplierContact
from app.user.services.user_service import UserService


def check_perm(db: Session, user, permissions: list[str]) -> None:
    svc = UserService(db)
    user_permissions = set(svc.get_user_permissions(user))

    if not user_permissions.intersection(set(permissions)):
        raise HTTPException(status_code=403, detail="Not authorized")


def contacts_out(contacts: list[SupplierContact]) -> list[SupplierContactOut]:
    ordered = sorted(contacts, key=lambda contact: (not bool(contact.is_primary), contact.id))
    return [
        SupplierContactOut(
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
        for contact in ordered
    ]
