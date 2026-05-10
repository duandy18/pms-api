# app/routers/pms_read_v1.py
from __future__ import annotations

from typing import Protocol

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.contracts.pms_read import (
    BarcodeProbeIn,
    BarcodeProbeOut,
    BarcodeProbeStatus,
    BarcodeQueryIn,
    BarcodeQueryOut,
    ItemBasicBatchOut,
    ItemIdsBatchIn,
    ItemPolicyBatchOut,
    ItemReportMetaBatchOut,
    PmsExportSkuCodeResolution,
    PmsReadHealthOut,
    ReportSearchOut,
    SkuCodeQueryIn,
    SkuCodeQueryOut,
    UomDefaultsBatchIn,
    UomDefaultsBatchOut,
    UomQueryIn,
    UomQueryOut,
)
from app.db.session import get_db
from app.repositories.item_basic_read_repo import ItemBasicReadRepository
from app.repositories.item_policy_read_repo import ItemPolicyReadRepository
from app.repositories.item_report_meta_read_repo import ItemReportMetaReadRepository

router = APIRouter(prefix="/pms/read/v1", tags=["pms-read-v1"])


class ItemBasicReader(Protocol):
    def get_item_basic_batch(
        self,
        *,
        item_ids: list[int],
        enabled_only: bool,
    ) -> ItemBasicBatchOut:
        ...


class ItemPolicyReader(Protocol):
    def get_item_policy_batch(
        self,
        *,
        item_ids: list[int],
        enabled_only: bool,
    ) -> ItemPolicyBatchOut:
        ...


class ItemReportMetaReader(Protocol):
    def get_item_report_meta_batch(
        self,
        *,
        item_ids: list[int],
    ) -> ItemReportMetaBatchOut:
        ...


def _clean_ids(values: list[int]) -> list[int]:
    return sorted({int(value) for value in values if int(value) > 0})


def get_item_basic_reader(db: Session = Depends(get_db)) -> ItemBasicReader:
    return ItemBasicReadRepository(db)


def get_item_policy_reader(db: Session = Depends(get_db)) -> ItemPolicyReader:
    return ItemPolicyReadRepository(db)


def get_item_report_meta_reader(db: Session = Depends(get_db)) -> ItemReportMetaReader:
    return ItemReportMetaReadRepository(db)


@router.get("/health", response_model=PmsReadHealthOut)
async def read_v1_health() -> PmsReadHealthOut:
    return PmsReadHealthOut(status="ok", surface="pms-read-v1")


@router.post("/items/basic/batch", response_model=ItemBasicBatchOut)
async def batch_item_basics(
    payload: ItemIdsBatchIn,
    reader: ItemBasicReader = Depends(get_item_basic_reader),
) -> ItemBasicBatchOut:
    item_ids = _clean_ids(payload.item_ids)
    if not item_ids:
        return ItemBasicBatchOut()
    return reader.get_item_basic_batch(
        item_ids=item_ids,
        enabled_only=payload.enabled_only,
    )


@router.post("/items/policies/batch", response_model=ItemPolicyBatchOut)
async def batch_item_policies(
    payload: ItemIdsBatchIn,
    reader: ItemPolicyReader = Depends(get_item_policy_reader),
) -> ItemPolicyBatchOut:
    item_ids = _clean_ids(payload.item_ids)
    if not item_ids:
        return ItemPolicyBatchOut()
    return reader.get_item_policy_batch(
        item_ids=item_ids,
        enabled_only=payload.enabled_only,
    )


@router.get("/items/report-search", response_model=ReportSearchOut)
async def search_report_items(
    keyword: str = Query(..., min_length=1, max_length=128),
    limit: int = Query(default=50, ge=1, le=500),
) -> ReportSearchOut:
    _ = keyword
    _ = limit
    return ReportSearchOut(item_ids=[])


@router.post("/items/report-meta/batch", response_model=ItemReportMetaBatchOut)
async def batch_item_report_meta(
    payload: ItemIdsBatchIn,
    reader: ItemReportMetaReader = Depends(get_item_report_meta_reader),
) -> ItemReportMetaBatchOut:
    item_ids = _clean_ids(payload.item_ids)
    if not item_ids:
        return ItemReportMetaBatchOut()
    return reader.get_item_report_meta_batch(item_ids=item_ids)


@router.post("/uoms/query", response_model=UomQueryOut)
async def query_uoms(payload: UomQueryIn) -> UomQueryOut:
    _ = payload
    return UomQueryOut()


@router.post("/items/uom-defaults/batch", response_model=UomDefaultsBatchOut)
async def batch_uom_defaults(payload: UomDefaultsBatchIn) -> UomDefaultsBatchOut:
    item_ids = _clean_ids(payload.item_ids)
    return UomDefaultsBatchOut(missing_item_ids=item_ids)


@router.post("/barcodes/query", response_model=BarcodeQueryOut)
async def query_barcodes(payload: BarcodeQueryIn) -> BarcodeQueryOut:
    _ = payload
    return BarcodeQueryOut()


@router.post("/barcodes/probe", response_model=BarcodeProbeOut)
async def probe_barcode(payload: BarcodeProbeIn) -> BarcodeProbeOut:
    return BarcodeProbeOut(
        ok=True,
        status=BarcodeProbeStatus.UNBOUND,
        barcode=payload.barcode.strip(),
    )


@router.post("/sku-codes/query", response_model=SkuCodeQueryOut)
async def query_sku_codes(payload: SkuCodeQueryIn) -> SkuCodeQueryOut:
    _ = payload
    return SkuCodeQueryOut()


@router.get(
    "/sku-codes/resolve-outbound-default",
    response_model=PmsExportSkuCodeResolution,
)
async def resolve_outbound_default_sku_code(
    code: str = Query(..., min_length=1, max_length=128),
    enabled_only: bool = Query(default=True),
) -> PmsExportSkuCodeResolution:
    _ = code
    _ = enabled_only
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="pms_read_sku_code_resolution_not_implemented",
    )


__all__ = [
    "get_item_basic_reader",
    "get_item_policy_reader",
    "get_item_report_meta_reader",
    "router",
]
