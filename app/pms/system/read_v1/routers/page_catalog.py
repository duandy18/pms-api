# app/pms/system/read_v1/routers/page_catalog.py
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.pms.system.read_v1.contracts import PmsSystemPageCatalogOut
from app.pms.system.read_v1.repos import PmsPageCatalogRepo
from app.pms.system.read_v1.services import PmsPageCatalogService

router = APIRouter(prefix="/system/read/v1", tags=["system-read-v1"])


@router.get(
    "/page-catalog",
    response_model=PmsSystemPageCatalogOut,
    summary="Get PMS page catalog",
)
async def get_pms_page_catalog(
    db: Session = Depends(get_db),
) -> PmsSystemPageCatalogOut:
    return PmsPageCatalogService(PmsPageCatalogRepo(db)).get_page_catalog()


__all__ = ["router"]
