# app/pms/suppliers/services/supplier_read_service.py
from __future__ import annotations

from sqlalchemy.orm import Session

from app.pms.suppliers.contracts.suppliers import SupplierBasic
from app.pms.suppliers.models.supplier import Supplier
from app.pms.suppliers.repos.supplier_repo import list_suppliers_basic as repo_list_suppliers_basic


class SupplierReadService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_basic(
        self,
        *,
        active: bool | None = True,
        q: str | None = None,
    ) -> list[SupplierBasic]:
        rows = repo_list_suppliers_basic(self.db, active=active, q=q)
        return [self._to_basic(row) for row in rows]

    def get_basic_by_id(self, *, supplier_id: int) -> SupplierBasic | None:
        obj = self.db.get(Supplier, int(supplier_id))
        if obj is None:
            return None
        return self._to_basic(obj)

    @staticmethod
    def _to_basic(supplier: Supplier) -> SupplierBasic:
        return SupplierBasic(
            id=int(supplier.id),
            name=str(supplier.name),
            code=supplier.code,
            active=bool(supplier.active),
        )
