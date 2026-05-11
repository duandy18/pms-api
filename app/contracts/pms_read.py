# app/contracts/pms_read.py
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ReadContractBase(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


ShelfLifeUnit = Literal["DAY", "WEEK", "MONTH", "YEAR"]
ExpiryPolicy = Literal["NONE", "REQUIRED"]
LotSourcePolicy = Literal["INTERNAL_ONLY", "SUPPLIER_ONLY"]
PmsExportSkuCodeType = Literal["PRIMARY", "ALIAS", "LEGACY", "MANUAL"]
PmsUomDefaultUsage = Literal["PURCHASE", "INBOUND", "OUTBOUND"]


class PmsReadHealthOut(ReadContractBase):
    status: str
    surface: str


class PmsReadError(ReadContractBase):
    key: str | None = None
    code: str
    message: str


class ItemBasic(ReadContractBase):
    id: int = Field(gt=0)
    sku: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=128)
    spec: str | None = Field(default=None, max_length=128)

    enabled: bool = True
    supplier_id: int | None = None

    brand: str | None = Field(default=None, max_length=64)
    category: str | None = Field(default=None, max_length=64)


class ItemPolicy(ReadContractBase):
    item_id: int = Field(gt=0)

    expiry_policy: ExpiryPolicy
    shelf_life_value: int | None = Field(default=None, gt=0)
    shelf_life_unit: ShelfLifeUnit | None = None

    lot_source_policy: LotSourcePolicy
    derivation_allowed: bool
    uom_governance_enabled: bool


class ItemReportMeta(ReadContractBase):
    item_id: int = Field(gt=0)
    sku: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=128)
    brand: str | None = Field(default=None, max_length=64)
    category: str | None = Field(default=None, max_length=64)
    barcode: str | None = Field(default=None, max_length=128)


class PmsExportUom(ReadContractBase):
    id: int = Field(gt=0)
    item_id: int = Field(gt=0)

    uom: str = Field(min_length=1, max_length=16)
    display_name: str | None = Field(default=None, max_length=32)
    uom_name: str = Field(min_length=1, max_length=32)

    ratio_to_base: int = Field(ge=1)
    net_weight_kg: float | None = Field(default=None, ge=0)

    is_base: bool
    is_purchase_default: bool
    is_inbound_default: bool
    is_outbound_default: bool


class PmsExportBarcode(ReadContractBase):
    id: int = Field(gt=0)
    item_id: int = Field(gt=0)
    item_uom_id: int = Field(gt=0)

    barcode: str = Field(min_length=1, max_length=128)
    symbology: str = Field(min_length=1, max_length=32)

    active: bool
    is_primary: bool

    uom: str = Field(min_length=1, max_length=16)
    display_name: str | None = Field(default=None, max_length=32)
    uom_name: str = Field(min_length=1, max_length=32)
    ratio_to_base: int = Field(ge=1)


class BarcodeProbeStatus(str, Enum):
    BOUND = "BOUND"
    UNBOUND = "UNBOUND"
    ERROR = "ERROR"


class BarcodeProbeIn(ReadContractBase):
    barcode: str = Field(min_length=1, max_length=128)


class BarcodeProbeError(ReadContractBase):
    stage: str
    error: str


class BarcodeProbeOut(ReadContractBase):
    ok: bool
    status: BarcodeProbeStatus
    barcode: str

    item_id: int | None = None
    item_uom_id: int | None = None
    ratio_to_base: int | None = None

    symbology: str | None = None
    active: bool | None = None

    item_basic: ItemBasic | None = None

    errors: list[BarcodeProbeError] = Field(default_factory=list)


class PmsExportSkuCode(ReadContractBase):
    id: int = Field(gt=0)
    item_id: int = Field(gt=0)

    code: str = Field(min_length=1, max_length=128)
    code_type: PmsExportSkuCodeType
    is_primary: bool
    is_active: bool

    effective_from: datetime | None = None
    effective_to: datetime | None = None
    remark: str | None = Field(default=None, max_length=255)

    item_sku: str = Field(min_length=1, max_length=128)
    item_name: str = Field(min_length=1, max_length=128)
    item_enabled: bool


class PmsExportSkuCodeResolution(ReadContractBase):
    sku_code_id: int = Field(gt=0)
    item_id: int = Field(gt=0)

    sku_code: str = Field(min_length=1, max_length=128)
    code_type: PmsExportSkuCodeType
    is_primary: bool

    item_sku: str = Field(min_length=1, max_length=128)
    item_name: str = Field(min_length=1, max_length=128)

    item_uom_id: int = Field(gt=0)
    uom: str = Field(min_length=1, max_length=16)
    display_name: str | None = Field(default=None, max_length=32)
    uom_name: str = Field(min_length=1, max_length=32)
    ratio_to_base: int = Field(ge=1)


class ItemIdsBatchIn(ReadContractBase):
    item_ids: list[int] = Field(min_length=1, max_length=500)
    enabled_only: bool = False


class UomQueryIn(ReadContractBase):
    item_ids: list[int] = Field(default_factory=list, max_length=500)
    item_uom_ids: list[int] = Field(default_factory=list, max_length=500)


class UomDefaultsBatchIn(ReadContractBase):
    item_ids: list[int] = Field(min_length=1, max_length=500)
    usage: PmsUomDefaultUsage


class BarcodeQueryIn(ReadContractBase):
    item_ids: list[int] = Field(default_factory=list, max_length=500)
    item_uom_ids: list[int] = Field(default_factory=list, max_length=500)
    barcode: str | None = Field(default=None, max_length=128)
    active: bool | None = True
    primary_only: bool = False


class SkuCodeQueryIn(ReadContractBase):
    item_ids: list[int] = Field(default_factory=list, max_length=500)
    sku_code_ids: list[int] = Field(default_factory=list, max_length=500)
    code: str | None = Field(default=None, max_length=128)
    active: bool | None = True
    primary_only: bool = False


class ItemBasicBatchOut(ReadContractBase):
    items_by_id: dict[int, ItemBasic] = Field(default_factory=dict)
    missing_item_ids: list[int] = Field(default_factory=list)
    inactive_item_ids: list[int] = Field(default_factory=list)
    errors: list[PmsReadError] = Field(default_factory=list)


class ItemPolicyBatchOut(ReadContractBase):
    policies_by_item_id: dict[int, ItemPolicy] = Field(default_factory=dict)
    missing_item_ids: list[int] = Field(default_factory=list)
    inactive_item_ids: list[int] = Field(default_factory=list)
    errors: list[PmsReadError] = Field(default_factory=list)


class ItemReportMetaBatchOut(ReadContractBase):
    meta_by_item_id: dict[int, ItemReportMeta] = Field(default_factory=dict)
    missing_item_ids: list[int] = Field(default_factory=list)
    errors: list[PmsReadError] = Field(default_factory=list)


class UomQueryOut(ReadContractBase):
    uoms: list[PmsExportUom] = Field(default_factory=list)
    missing_item_uom_ids: list[int] = Field(default_factory=list)
    errors: list[PmsReadError] = Field(default_factory=list)


class UomDefaultsBatchOut(ReadContractBase):
    uoms_by_item_id: dict[int, PmsExportUom] = Field(default_factory=dict)
    missing_item_ids: list[int] = Field(default_factory=list)
    missing_default_uom_item_ids: list[int] = Field(default_factory=list)
    errors: list[PmsReadError] = Field(default_factory=list)


class BarcodeQueryOut(ReadContractBase):
    barcodes: list[PmsExportBarcode] = Field(default_factory=list)
    errors: list[PmsReadError] = Field(default_factory=list)


class SkuCodeQueryOut(ReadContractBase):
    sku_codes: list[PmsExportSkuCode] = Field(default_factory=list)
    errors: list[PmsReadError] = Field(default_factory=list)


class ReportSearchOut(ReadContractBase):
    item_ids: list[int] = Field(default_factory=list)


class _ProjectionFeedPage(ReadContractBase):
    limit: int = Field(ge=1, le=500)
    offset: int = Field(ge=0)
    next_offset: int | None = Field(default=None, ge=0)
    has_more: bool


class PmsProjectionItemFeedRow(ReadContractBase):
    item_id: int = Field(gt=0)

    sku: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=128)
    spec: str | None = Field(default=None, max_length=128)
    enabled: bool

    supplier_id: int | None = None
    brand: str | None = Field(default=None, max_length=64)
    category: str | None = Field(default=None, max_length=64)

    expiry_policy: ExpiryPolicy
    shelf_life_value: int | None = Field(default=None, gt=0)
    shelf_life_unit: ShelfLifeUnit | None = None
    lot_source_policy: LotSourcePolicy
    derivation_allowed: bool
    uom_governance_enabled: bool

    pms_updated_at: datetime


class PmsProjectionUomFeedRow(ReadContractBase):
    item_uom_id: int = Field(gt=0)
    item_id: int = Field(gt=0)

    uom: str = Field(min_length=1, max_length=16)
    display_name: str | None = Field(default=None, max_length=32)
    uom_name: str = Field(min_length=1, max_length=32)

    ratio_to_base: int = Field(ge=1)
    net_weight_kg: float | None = Field(default=None, ge=0)

    is_base: bool
    is_purchase_default: bool
    is_inbound_default: bool
    is_outbound_default: bool

    pms_updated_at: datetime


class PmsProjectionSkuCodeFeedRow(ReadContractBase):
    sku_code_id: int = Field(gt=0)
    item_id: int = Field(gt=0)

    sku_code: str = Field(min_length=1, max_length=128)
    code_type: PmsExportSkuCodeType
    is_primary: bool
    is_active: bool

    effective_from: datetime | None = None
    effective_to: datetime | None = None

    pms_updated_at: datetime


class PmsProjectionBarcodeFeedRow(ReadContractBase):
    barcode_id: int = Field(gt=0)
    item_id: int = Field(gt=0)
    item_uom_id: int = Field(gt=0)

    barcode: str = Field(min_length=1, max_length=128)
    symbology: str = Field(min_length=1, max_length=32)
    active: bool
    is_primary: bool

    pms_updated_at: datetime


class PmsProjectionItemFeedOut(_ProjectionFeedPage):
    rows: list[PmsProjectionItemFeedRow] = Field(default_factory=list)


class PmsProjectionUomFeedOut(_ProjectionFeedPage):
    rows: list[PmsProjectionUomFeedRow] = Field(default_factory=list)


class PmsProjectionSkuCodeFeedOut(_ProjectionFeedPage):
    rows: list[PmsProjectionSkuCodeFeedRow] = Field(default_factory=list)


class PmsProjectionBarcodeFeedOut(_ProjectionFeedPage):
    rows: list[PmsProjectionBarcodeFeedRow] = Field(default_factory=list)


__all__ = [
    "BarcodeProbeError",
    "BarcodeProbeIn",
    "BarcodeProbeOut",
    "BarcodeProbeStatus",
    "BarcodeQueryIn",
    "BarcodeQueryOut",
    "ExpiryPolicy",
    "ItemBasic",
    "ItemBasicBatchOut",
    "ItemIdsBatchIn",
    "ItemPolicy",
    "ItemPolicyBatchOut",
    "ItemReportMeta",
    "ItemReportMetaBatchOut",
    "LotSourcePolicy",
    "PmsExportBarcode",
    "PmsExportSkuCode",
    "PmsExportSkuCodeResolution",
    "PmsExportSkuCodeType",
    "PmsExportUom",
    "PmsProjectionBarcodeFeedOut",
    "PmsProjectionBarcodeFeedRow",
    "PmsProjectionItemFeedOut",
    "PmsProjectionItemFeedRow",
    "PmsProjectionSkuCodeFeedOut",
    "PmsProjectionSkuCodeFeedRow",
    "PmsProjectionUomFeedOut",
    "PmsProjectionUomFeedRow",
    "PmsReadError",
    "PmsReadHealthOut",
    "PmsUomDefaultUsage",
    "ReportSearchOut",
    "ShelfLifeUnit",
    "SkuCodeQueryIn",
    "SkuCodeQueryOut",
    "UomDefaultsBatchIn",
    "UomDefaultsBatchOut",
    "UomQueryIn",
    "UomQueryOut",
]
