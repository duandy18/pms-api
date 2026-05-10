# app/routers/pms_read_v1.py
from __future__ import annotations

from typing import Protocol

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.contracts.pms_read import (
    BarcodeProbeIn,
    BarcodeProbeOut,
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
from app.repositories.uom_read_repo import UomReadRepository
from app.repositories.barcode_read_repo import BarcodeReadRepository

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


class UomReader(Protocol):
    def query_uoms(
        self,
        *,
        item_ids: list[int],
        item_uom_ids: list[int],
    ) -> UomQueryOut:
        ...


class BarcodeReader(Protocol):
    def query_barcodes(
        self,
        *,
        item_ids: list[int],
        item_uom_ids: list[int],
        barcode: str | None,
        active: bool | None,
        primary_only: bool,
    ) -> BarcodeQueryOut:
        ...

    def probe_barcode(self, *, barcode: str) -> BarcodeProbeOut:
        ...


def _clean_ids(values: list[int]) -> list[int]:
    return sorted({int(value) for value in values if int(value) > 0})


def get_item_basic_reader(db: Session = Depends(get_db)) -> ItemBasicReader:
    return ItemBasicReadRepository(db)


def get_item_policy_reader(db: Session = Depends(get_db)) -> ItemPolicyReader:
    return ItemPolicyReadRepository(db)


def get_item_report_meta_reader(db: Session = Depends(get_db)) -> ItemReportMetaReader:
    return ItemReportMetaReadRepository(db)


def get_uom_reader(db: Session = Depends(get_db)) -> UomReader:
    return UomReadRepository(db)


def get_barcode_reader(db: Session = Depends(get_db)) -> BarcodeReader:
    return BarcodeReadRepository(db)


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
async def query_uoms(
    payload: UomQueryIn,
    reader: UomReader = Depends(get_uom_reader),
) -> UomQueryOut:
    return reader.query_uoms(
        item_ids=_clean_ids(payload.item_ids),
        item_uom_ids=_clean_ids(payload.item_uom_ids),
    )


@router.post("/items/uom-defaults/batch", response_model=UomDefaultsBatchOut)
async def batch_uom_defaults(payload: UomDefaultsBatchIn) -> UomDefaultsBatchOut:
    item_ids = _clean_ids(payload.item_ids)
    return UomDefaultsBatchOut(missing_item_ids=item_ids)


@router.post("/barcodes/query", response_model=BarcodeQueryOut)
async def query_barcodes(
    payload: BarcodeQueryIn,
    reader: BarcodeReader = Depends(get_barcode_reader),
) -> BarcodeQueryOut:
    return reader.query_barcodes(
        item_ids=_clean_ids(payload.item_ids),
        item_uom_ids=_clean_ids(payload.item_uom_ids),
        barcode=payload.barcode,
        active=payload.active,
        primary_only=payload.primary_only,
    )


@router.post("/barcodes/probe", response_model=BarcodeProbeOut)
async def probe_barcode(
    payload: BarcodeProbeIn,
    reader: BarcodeReader = Depends(get_barcode_reader),
) -> BarcodeProbeOut:
    return reader.probe_barcode(barcode=payload.barcode)


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
    "get_barcode_reader",
    "get_item_basic_reader",
    "get_item_policy_reader",
    "get_item_report_meta_reader",
    "get_uom_reader",
    "router",
]
