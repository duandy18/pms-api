# app/pms/suppliers/routers/suppliers_projection_feed.py
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.pms.suppliers.contracts.suppliers import PmsProjectionSupplierFeedOut
from app.pms.suppliers.services.supplier_read_service import SupplierReadService

router = APIRouter(
    prefix="/pms/read/v1/projection-feed",
    tags=["pms-read-v1-projection-feed-suppliers"],
)


def get_supplier_read_service(db: Session = Depends(get_db)) -> SupplierReadService:
    return SupplierReadService(db)


@router.get("/suppliers", response_model=PmsProjectionSupplierFeedOut)
def projection_feed_suppliers(
    limit: int = Query(default=500, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    service: SupplierReadService = Depends(get_supplier_read_service),
) -> PmsProjectionSupplierFeedOut:
    rows = service.list_projection_feed(limit=int(limit) + 1, offset=int(offset))
    return PmsProjectionSupplierFeedOut(
        rows=rows[:limit],
        limit=int(limit),
        offset=int(offset),
        next_offset=(int(offset) + int(limit)) if len(rows) > int(limit) else None,
        has_more=len(rows) > int(limit),
    )
