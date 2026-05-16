# app/pms/suppliers/routers/suppliers_read_v1.py
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.pms.suppliers.contracts.suppliers import SupplierBasic
from app.pms.suppliers.services.supplier_read_service import SupplierReadService
from app.service_auth.deps import require_pms_service_capability

router = APIRouter(prefix="/pms/read/v1/suppliers", tags=["pms-read-v1-suppliers"])

require_pms_read_suppliers = require_pms_service_capability("pms.read.suppliers")


def get_supplier_read_service(db: Session = Depends(get_db)) -> SupplierReadService:
    return SupplierReadService(db)


@router.get("", response_model=list[SupplierBasic], status_code=status.HTTP_200_OK)
def list_read_suppliers(
    active: Optional[bool] = Query(
        True,
        description="默认仅返回合作中供应商（用于 PMS/WMS/OMS 下拉）",
    ),
    q: Optional[str] = Query(None, description="名称/编码 模糊搜索"),
    service: SupplierReadService = Depends(get_supplier_read_service),
    _service_permission: None = Depends(require_pms_read_suppliers),
) -> list[SupplierBasic]:
    return service.list_basic(active=active, q=q)


@router.get("/{supplier_id}", response_model=SupplierBasic, status_code=status.HTTP_200_OK)
def get_read_supplier(
    supplier_id: int,
    service: SupplierReadService = Depends(get_supplier_read_service),
    _service_permission: None = Depends(require_pms_read_suppliers),
) -> SupplierBasic:
    supplier = service.get_basic_by_id(supplier_id=int(supplier_id))
    if supplier is None:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier


__all__ = [
    "get_read_supplier",
    "get_supplier_read_service",
    "list_read_suppliers",
    "require_pms_read_suppliers",
    "router",
]
