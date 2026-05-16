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
    ItemBasic,
    ItemBasicBatchOut,
    ItemIdsBatchIn,
    ItemPolicy,
    ItemPolicyBatchOut,
    ItemReportMetaBatchOut,
    PmsExportBarcode,
    PmsExportSkuCode,
    PmsExportSkuCodeResolution,
    PmsExportUom,
    PmsProjectionBarcodeFeedOut,
    PmsProjectionBarcodeFeedRow,
    PmsProjectionItemFeedOut,
    PmsProjectionItemFeedRow,
    PmsProjectionSkuCodeFeedOut,
    PmsProjectionSkuCodeFeedRow,
    PmsProjectionUomFeedOut,
    PmsProjectionUomFeedRow,
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
from app.repositories.barcode_read_repo import BarcodeReadRepository
from app.repositories.item_basic_read_repo import ItemBasicReadRepository
from app.repositories.item_policy_read_repo import ItemPolicyReadRepository
from app.repositories.item_report_meta_read_repo import ItemReportMetaReadRepository
from app.repositories.sku_code_read_repo import (
    SkuCodeReadRepository,
    SkuCodeResolveError,
)
from app.repositories.uom_read_repo import UomReadRepository
from app.service_auth.deps import require_pms_service_capability

router = APIRouter(prefix="/pms/read/v1", tags=["pms-read-v1"])


class ItemBasicReader(Protocol):
    def list_item_basics(
        self,
        *,
        supplier_id: int | None = None,
        keyword: str | None = None,
        enabled: bool | None = None,
        limit: int = 50,
    ) -> list[ItemBasic]:
        ...

    def get_item_basic(self, *, item_id: int) -> ItemBasic | None:
        ...

    def list_projection_feed(
        self,
        *,
        limit: int,
        offset: int,
    ) -> list[PmsProjectionItemFeedRow]:
        ...

    def get_item_basic_batch(
        self,
        *,
        item_ids: list[int],
        enabled_only: bool,
    ) -> ItemBasicBatchOut:
        ...


class ItemPolicyReader(Protocol):
    def get_item_policy(self, *, item_id: int) -> ItemPolicy | None:
        ...

    def get_item_policy_by_sku(self, *, sku: str) -> ItemPolicy | None:
        ...

    def get_item_policy_batch(
        self,
        *,
        item_ids: list[int],
        enabled_only: bool,
    ) -> ItemPolicyBatchOut:
        ...


class ItemReportMetaReader(Protocol):
    def search_report_item_ids_by_keyword(
        self,
        *,
        keyword: str,
        limit: int,
    ) -> list[int]:
        ...

    def get_item_report_meta_batch(
        self,
        *,
        item_ids: list[int],
    ) -> ItemReportMetaBatchOut:
        ...


class UomReader(Protocol):
    def get_uom(self, *, item_uom_id: int) -> PmsExportUom | None:
        ...

    def query_uoms(
        self,
        *,
        item_ids: list[int],
        item_uom_ids: list[int],
    ) -> UomQueryOut:
        ...

    def list_projection_feed(
        self,
        *,
        limit: int,
        offset: int,
    ) -> list[PmsProjectionUomFeedRow]:
        ...

    def get_default_or_base_batch(
        self,
        *,
        item_ids: list[int],
        usage: str,
    ) -> UomDefaultsBatchOut:
        ...


class BarcodeReader(Protocol):
    def get_barcode(self, *, barcode_id: int) -> PmsExportBarcode | None:
        ...

    def list_projection_feed(
        self,
        *,
        limit: int,
        offset: int,
    ) -> list[PmsProjectionBarcodeFeedRow]:
        ...

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


class SkuCodeReader(Protocol):
    def get_sku_code(self, *, sku_code_id: int) -> PmsExportSkuCode | None:
        ...

    def list_projection_feed(
        self,
        *,
        limit: int,
        offset: int,
    ) -> list[PmsProjectionSkuCodeFeedRow]:
        ...

    def query_sku_codes(
        self,
        *,
        item_ids: list[int],
        sku_code_ids: list[int],
        code: str | None,
        active: bool | None,
        primary_only: bool,
    ) -> SkuCodeQueryOut:
        ...

    def resolve_outbound_default_sku_code(
        self,
        *,
        code: str,
        enabled_only: bool,
    ) -> PmsExportSkuCodeResolution:
        ...


def _sku_code_error_status(code: str) -> int:
    if code == "pms_invalid_sku_code":
        return status.HTTP_422_UNPROCESSABLE_ENTITY
    if code == "pms_sku_code_not_found":
        return status.HTTP_404_NOT_FOUND
    if code in {
        "pms_sku_code_inactive",
        "pms_item_inactive",
        "pms_outbound_uom_missing",
    }:
        return status.HTTP_409_CONFLICT
    return status.HTTP_500_INTERNAL_SERVER_ERROR


def _clean_ids(values: list[int]) -> list[int]:
    return sorted({int(value) for value in values if int(value) > 0})


def _next_offset(*, offset: int, limit: int, fetched: int) -> int | None:
    return int(offset) + int(limit) if int(fetched) > int(limit) else None


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


def get_sku_code_reader(db: Session = Depends(get_db)) -> SkuCodeReader:
    return SkuCodeReadRepository(db)


require_pms_read_items = require_pms_service_capability("pms.read.items")
require_pms_read_uoms = require_pms_service_capability("pms.read.uoms")
require_pms_read_sku_codes = require_pms_service_capability("pms.read.sku_codes")
require_pms_read_barcodes = require_pms_service_capability("pms.read.barcodes")


@router.get("/health", response_model=PmsReadHealthOut)
async def read_v1_health() -> PmsReadHealthOut:
    return PmsReadHealthOut(status="ok", surface="pms-read-v1")


@router.get("/projection-feed/items", response_model=PmsProjectionItemFeedOut)
async def projection_feed_items(
    limit: int = Query(default=500, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    reader: ItemBasicReader = Depends(get_item_basic_reader),
    _service_permission: None = Depends(require_pms_read_items),
) -> PmsProjectionItemFeedOut:
    rows = reader.list_projection_feed(limit=int(limit) + 1, offset=int(offset))
    return PmsProjectionItemFeedOut(
        rows=rows[:limit],
        limit=int(limit),
        offset=int(offset),
        next_offset=_next_offset(offset=int(offset), limit=int(limit), fetched=len(rows)),
        has_more=len(rows) > int(limit),
    )


@router.get("/projection-feed/uoms", response_model=PmsProjectionUomFeedOut)
async def projection_feed_uoms(
    limit: int = Query(default=500, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    reader: UomReader = Depends(get_uom_reader),
    _service_permission: None = Depends(require_pms_read_uoms),
) -> PmsProjectionUomFeedOut:
    rows = reader.list_projection_feed(limit=int(limit) + 1, offset=int(offset))
    return PmsProjectionUomFeedOut(
        rows=rows[:limit],
        limit=int(limit),
        offset=int(offset),
        next_offset=_next_offset(offset=int(offset), limit=int(limit), fetched=len(rows)),
        has_more=len(rows) > int(limit),
    )


@router.get("/projection-feed/sku-codes", response_model=PmsProjectionSkuCodeFeedOut)
async def projection_feed_sku_codes(
    limit: int = Query(default=500, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    reader: SkuCodeReader = Depends(get_sku_code_reader),
    _service_permission: None = Depends(require_pms_read_sku_codes),
) -> PmsProjectionSkuCodeFeedOut:
    rows = reader.list_projection_feed(limit=int(limit) + 1, offset=int(offset))
    return PmsProjectionSkuCodeFeedOut(
        rows=rows[:limit],
        limit=int(limit),
        offset=int(offset),
        next_offset=_next_offset(offset=int(offset), limit=int(limit), fetched=len(rows)),
        has_more=len(rows) > int(limit),
    )


@router.get("/projection-feed/barcodes", response_model=PmsProjectionBarcodeFeedOut)
async def projection_feed_barcodes(
    limit: int = Query(default=500, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    reader: BarcodeReader = Depends(get_barcode_reader),
    _service_permission: None = Depends(require_pms_read_barcodes),
) -> PmsProjectionBarcodeFeedOut:
    rows = reader.list_projection_feed(limit=int(limit) + 1, offset=int(offset))
    return PmsProjectionBarcodeFeedOut(
        rows=rows[:limit],
        limit=int(limit),
        offset=int(offset),
        next_offset=_next_offset(offset=int(offset), limit=int(limit), fetched=len(rows)),
        has_more=len(rows) > int(limit),
    )


@router.get("/items/basic", response_model=list[ItemBasic])
async def list_item_basics(
    supplier_id: int | None = Query(None, ge=1),
    keyword: str | None = Query(default=None, max_length=128),
    enabled: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    reader: ItemBasicReader = Depends(get_item_basic_reader),
) -> list[ItemBasic]:
    return reader.list_item_basics(
        supplier_id=supplier_id,
        keyword=keyword,
        enabled=enabled,
        limit=limit,
    )


@router.get("/items/basic/{item_id}", response_model=ItemBasic)
async def get_item_basic(
    item_id: int,
    reader: ItemBasicReader = Depends(get_item_basic_reader),
) -> ItemBasic:
    row = reader.get_item_basic(item_id=int(item_id))
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="pms_item_not_found")
    return row


@router.post("/items/basic/batch", response_model=ItemBasicBatchOut)
async def batch_item_basics(
    payload: ItemIdsBatchIn,
    reader: ItemBasicReader = Depends(get_item_basic_reader),
) -> ItemBasicBatchOut:
    item_ids = _clean_ids(payload.item_ids)
    if not item_ids:
        return ItemBasicBatchOut()
    return reader.get_item_basic_batch(item_ids=item_ids, enabled_only=payload.enabled_only)


@router.get("/items/policy-by-sku", response_model=ItemPolicy)
async def get_item_policy_by_sku(
    sku: str = Query(..., min_length=1, max_length=128),
    reader: ItemPolicyReader = Depends(get_item_policy_reader),
) -> ItemPolicy:
    row = reader.get_item_policy_by_sku(sku=sku)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="pms_item_policy_not_found")
    return row


@router.get("/items/{item_id}/policy", response_model=ItemPolicy)
async def get_item_policy(
    item_id: int,
    reader: ItemPolicyReader = Depends(get_item_policy_reader),
) -> ItemPolicy:
    row = reader.get_item_policy(item_id=int(item_id))
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="pms_item_policy_not_found")
    return row


@router.post("/items/policies/batch", response_model=ItemPolicyBatchOut)
async def batch_item_policies(
    payload: ItemIdsBatchIn,
    reader: ItemPolicyReader = Depends(get_item_policy_reader),
) -> ItemPolicyBatchOut:
    item_ids = _clean_ids(payload.item_ids)
    if not item_ids:
        return ItemPolicyBatchOut()
    return reader.get_item_policy_batch(item_ids=item_ids, enabled_only=payload.enabled_only)


@router.get("/items/report-search", response_model=ReportSearchOut)
async def search_report_items(
    keyword: str = Query(..., min_length=1, max_length=128),
    limit: int = Query(default=50, ge=1, le=500),
    reader: ItemReportMetaReader = Depends(get_item_report_meta_reader),
) -> ReportSearchOut:
    return ReportSearchOut(
        item_ids=reader.search_report_item_ids_by_keyword(keyword=keyword, limit=limit)
    )


@router.post("/items/report-meta/batch", response_model=ItemReportMetaBatchOut)
async def batch_item_report_meta(
    payload: ItemIdsBatchIn,
    reader: ItemReportMetaReader = Depends(get_item_report_meta_reader),
) -> ItemReportMetaBatchOut:
    item_ids = _clean_ids(payload.item_ids)
    if not item_ids:
        return ItemReportMetaBatchOut()
    return reader.get_item_report_meta_batch(item_ids=item_ids)


@router.get("/items/{item_id}/uoms", response_model=list[PmsExportUom])
async def list_item_uoms(
    item_id: int,
    reader: UomReader = Depends(get_uom_reader),
) -> list[PmsExportUom]:
    return reader.query_uoms(item_ids=[int(item_id)], item_uom_ids=[]).uoms


@router.get("/uoms/{item_uom_id}", response_model=PmsExportUom)
async def get_uom(
    item_uom_id: int,
    reader: UomReader = Depends(get_uom_reader),
) -> PmsExportUom:
    row = reader.get_uom(item_uom_id=int(item_uom_id))
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="pms_uom_not_found")
    return row


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
async def batch_uom_defaults(
    payload: UomDefaultsBatchIn,
    reader: UomReader = Depends(get_uom_reader),
) -> UomDefaultsBatchOut:
    item_ids = _clean_ids(payload.item_ids)
    if not item_ids:
        return UomDefaultsBatchOut()
    return reader.get_default_or_base_batch(item_ids=item_ids, usage=payload.usage)


@router.get("/barcodes/{barcode_id}", response_model=PmsExportBarcode)
async def get_barcode(
    barcode_id: int,
    reader: BarcodeReader = Depends(get_barcode_reader),
) -> PmsExportBarcode:
    row = reader.get_barcode(barcode_id=int(barcode_id))
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="pms_barcode_not_found")
    return row


@router.get("/items/{item_id}/barcodes", response_model=list[PmsExportBarcode])
async def list_item_barcodes(
    item_id: int,
    active: bool | None = Query(default=True),
    primary_only: bool = Query(default=False),
    reader: BarcodeReader = Depends(get_barcode_reader),
) -> list[PmsExportBarcode]:
    return reader.query_barcodes(
        item_ids=[int(item_id)],
        item_uom_ids=[],
        barcode=None,
        active=active,
        primary_only=primary_only,
    ).barcodes


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


@router.get(
    "/sku-codes/resolve-outbound-default",
    response_model=PmsExportSkuCodeResolution,
)
async def resolve_outbound_default_sku_code(
    code: str = Query(..., min_length=1, max_length=128),
    enabled_only: bool = Query(default=True),
    reader: SkuCodeReader = Depends(get_sku_code_reader),
) -> PmsExportSkuCodeResolution:
    try:
        return reader.resolve_outbound_default_sku_code(
            code=code,
            enabled_only=enabled_only,
        )
    except SkuCodeResolveError as exc:
        raise HTTPException(
            status_code=_sku_code_error_status(exc.code),
            detail=exc.code,
        ) from exc


@router.get("/sku-codes/{sku_code_id}", response_model=PmsExportSkuCode)
async def get_sku_code(
    sku_code_id: int,
    reader: SkuCodeReader = Depends(get_sku_code_reader),
) -> PmsExportSkuCode:
    row = reader.get_sku_code(sku_code_id=int(sku_code_id))
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="pms_sku_code_not_found")
    return row


@router.get("/items/{item_id}/sku-codes", response_model=list[PmsExportSkuCode])
async def list_item_sku_codes(
    item_id: int,
    active: bool | None = Query(default=True),
    primary_only: bool = Query(default=False),
    reader: SkuCodeReader = Depends(get_sku_code_reader),
) -> list[PmsExportSkuCode]:
    return reader.query_sku_codes(
        item_ids=[int(item_id)],
        sku_code_ids=[],
        code=None,
        active=active,
        primary_only=primary_only,
    ).sku_codes


@router.post("/sku-codes/query", response_model=SkuCodeQueryOut)
async def query_sku_codes(
    payload: SkuCodeQueryIn,
    reader: SkuCodeReader = Depends(get_sku_code_reader),
) -> SkuCodeQueryOut:
    return reader.query_sku_codes(
        item_ids=_clean_ids(payload.item_ids),
        sku_code_ids=_clean_ids(payload.sku_code_ids),
        code=payload.code,
        active=payload.active,
        primary_only=payload.primary_only,
    )


__all__ = [
    "get_barcode_reader",
    "get_item_basic_reader",
    "get_item_policy_reader",
    "get_item_report_meta_reader",
    "get_sku_code_reader",
    "get_uom_reader",
    "require_pms_read_barcodes",
    "require_pms_read_items",
    "require_pms_read_sku_codes",
    "require_pms_read_uoms",
    "router",
]
