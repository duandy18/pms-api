# app/routers/pms_owner.py
from __future__ import annotations

from fastapi import APIRouter

from app.pms.items.routers.item_aggregate import router as item_aggregate_router
from app.pms.items.routers.item_barcodes import router as item_barcodes_router
from app.pms.items.routers.item_list import router as item_list_router
from app.pms.items.routers.item_master import router as item_master_router
from app.pms.items.routers.item_sku_codes import router as item_sku_codes_router
from app.pms.items.routers.item_uoms import router as item_uoms_router
from app.pms.items.routers.items import router as items_router
from app.pms.sku_coding.routers.sku_coding import router as sku_coding_router

router = APIRouter()

# PMS owner UI/API routes.
router.include_router(item_master_router)
router.include_router(items_router)
router.include_router(item_list_router)
router.include_router(item_aggregate_router)
router.include_router(item_uoms_router)
router.include_router(item_barcodes_router)
router.include_router(item_sku_codes_router)
router.include_router(sku_coding_router)

__all__ = ["router"]
