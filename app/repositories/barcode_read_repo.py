# app/repositories/barcode_read_repo.py
from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import column, select, table
from sqlalchemy.orm import Session

from app.contracts.pms_read import (
    BarcodeProbeError,
    BarcodeProbeOut,
    BarcodeProbeStatus,
    BarcodeQueryOut,
    ItemBasic,
    PmsExportBarcode,
    PmsProjectionBarcodeFeedRow,
)


def _clean_ids(values: Iterable[int]) -> list[int]:
    return sorted({int(value) for value in values if int(value) > 0})


def _strip_or_none(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _uom_name(uom: object, display_name: object) -> str:
    display = _strip_or_none(display_name)
    if display:
        return display
    return str(uom).strip()


items_table = table(
    "items",
    column("id"),
    column("sku"),
    column("name"),
    column("spec"),
    column("enabled"),
    column("supplier_id"),
    column("brand_id"),
    column("category_id"),
)

brands_table = table(
    "pms_brands",
    column("id"),
    column("name_cn"),
)

categories_table = table(
    "pms_business_categories",
    column("id"),
    column("category_name"),
)

item_uoms_table = table(
    "item_uoms",
    column("id"),
    column("item_id"),
    column("uom"),
    column("display_name"),
    column("ratio_to_base"),
)

barcodes_table = table(
    "item_barcodes",
    column("id"),
    column("item_id"),
    column("item_uom_id"),
    column("barcode"),
    column("symbology"),
    column("active"),
    column("is_primary"),
    column("updated_at"),
)


class BarcodeReadRepository:
    def __init__(self, db: Session) -> None:
        self.db = db


    def list_projection_feed(
        self,
        *,
        limit: int,
        offset: int,
    ) -> list[PmsProjectionBarcodeFeedRow]:
        safe_limit = max(1, min(int(limit), 501))
        safe_offset = max(0, int(offset))

        stmt = (
            self._projection_feed_stmt()
            .order_by(barcodes_table.c.id.asc())
            .offset(safe_offset)
            .limit(safe_limit)
        )
        rows = self.db.execute(stmt).mappings().all()
        return [self._projection_feed_from_row(row) for row in rows]

    def get_barcode(self, *, barcode_id: int) -> PmsExportBarcode | None:
        stmt = (
            self._base_barcode_stmt()
            .where(barcodes_table.c.id == int(barcode_id))
            .limit(1)
        )
        row = self.db.execute(stmt).mappings().first()
        return self._barcode_contract(row) if row is not None else None

    def query_barcodes(
        self,
        *,
        item_ids: Iterable[int],
        item_uom_ids: Iterable[int],
        barcode: str | None,
        active: bool | None,
        primary_only: bool,
    ) -> BarcodeQueryOut:
        clean_item_ids = _clean_ids(item_ids)
        clean_uom_ids = _clean_ids(item_uom_ids)
        code = str(barcode or "").strip()

        if not clean_item_ids and not clean_uom_ids and not code:
            return BarcodeQueryOut()

        stmt = self._base_barcode_stmt()

        if clean_item_ids:
            stmt = stmt.where(barcodes_table.c.item_id.in_(clean_item_ids))
        if clean_uom_ids:
            stmt = stmt.where(barcodes_table.c.item_uom_id.in_(clean_uom_ids))
        if code:
            stmt = stmt.where(barcodes_table.c.barcode == code)
        if active is not None:
            stmt = stmt.where(barcodes_table.c.active.is_(bool(active)))
        if primary_only:
            stmt = stmt.where(barcodes_table.c.is_primary.is_(True))

        stmt = stmt.order_by(
            barcodes_table.c.item_id.asc(),
            barcodes_table.c.is_primary.desc(),
            barcodes_table.c.active.desc(),
            barcodes_table.c.id.asc(),
        )

        rows = self.db.execute(stmt).mappings().all()

        return BarcodeQueryOut(
            barcodes=[self._barcode_contract(row) for row in rows],
            errors=[],
        )

    def probe_barcode(self, *, barcode: str) -> BarcodeProbeOut:
        code = str(barcode or "").strip()
        if not code:
            return BarcodeProbeOut(
                ok=False,
                status=BarcodeProbeStatus.ERROR,
                barcode="",
                errors=[BarcodeProbeError(stage="probe", error="barcode is required")],
            )

        stmt = (
            self._base_barcode_stmt()
            .where(barcodes_table.c.barcode == code)
            .order_by(
                barcodes_table.c.active.desc(),
                barcodes_table.c.id.asc(),
            )
            .limit(1)
        )

        row = self.db.execute(stmt).mappings().first()
        if row is None:
            return BarcodeProbeOut(
                ok=True,
                status=BarcodeProbeStatus.UNBOUND,
                barcode=code,
            )

        item_basic = ItemBasic(
            id=int(row["item_id"]),
            sku=str(row["item_sku"]),
            name=str(row["item_name"]),
            spec=_strip_or_none(row["item_spec"]),
            enabled=bool(row["item_enabled"]),
            supplier_id=(
                int(row["supplier_id"]) if row["supplier_id"] is not None else None
            ),
            brand=_strip_or_none(row["brand"]),
            category=_strip_or_none(row["category"]),
        )

        return BarcodeProbeOut(
            ok=True,
            status=BarcodeProbeStatus.BOUND,
            barcode=code,
            item_id=int(row["item_id"]),
            item_uom_id=int(row["item_uom_id"]),
            ratio_to_base=int(row["ratio_to_base"]),
            symbology=str(row["symbology"]),
            active=bool(row["active"]),
            item_basic=item_basic,
            errors=[],
        )

    @staticmethod
    def _projection_feed_stmt():
        return select(
            barcodes_table.c.id.label("barcode_id"),
            barcodes_table.c.item_id.label("item_id"),
            barcodes_table.c.item_uom_id.label("item_uom_id"),
            barcodes_table.c.barcode.label("barcode"),
            barcodes_table.c.symbology.label("symbology"),
            barcodes_table.c.active.label("active"),
            barcodes_table.c.is_primary.label("is_primary"),
            barcodes_table.c.updated_at.label("pms_updated_at"),
        )

    @staticmethod
    def _base_barcode_stmt():
        return (
            select(
                barcodes_table.c.id.label("id"),
                barcodes_table.c.item_id.label("item_id"),
                barcodes_table.c.item_uom_id.label("item_uom_id"),
                barcodes_table.c.barcode.label("barcode"),
                barcodes_table.c.symbology.label("symbology"),
                barcodes_table.c.active.label("active"),
                barcodes_table.c.is_primary.label("is_primary"),
                item_uoms_table.c.uom.label("uom"),
                item_uoms_table.c.display_name.label("display_name"),
                item_uoms_table.c.ratio_to_base.label("ratio_to_base"),
                items_table.c.sku.label("item_sku"),
                items_table.c.name.label("item_name"),
                items_table.c.spec.label("item_spec"),
                items_table.c.enabled.label("item_enabled"),
                items_table.c.supplier_id.label("supplier_id"),
                brands_table.c.name_cn.label("brand"),
                categories_table.c.category_name.label("category"),
            )
            .select_from(
                barcodes_table.join(
                    item_uoms_table,
                    (item_uoms_table.c.id == barcodes_table.c.item_uom_id)
                    & (item_uoms_table.c.item_id == barcodes_table.c.item_id),
                )
                .join(items_table, items_table.c.id == barcodes_table.c.item_id)
                .outerjoin(brands_table, brands_table.c.id == items_table.c.brand_id)
                .outerjoin(
                    categories_table,
                    categories_table.c.id == items_table.c.category_id,
                )
            )
        )

    @staticmethod
    def _projection_feed_from_row(row) -> PmsProjectionBarcodeFeedRow:
        return PmsProjectionBarcodeFeedRow(
            barcode_id=int(row["barcode_id"]),
            item_id=int(row["item_id"]),
            item_uom_id=int(row["item_uom_id"]),
            barcode=str(row["barcode"]),
            symbology=str(row["symbology"]),
            active=bool(row["active"]),
            is_primary=bool(row["is_primary"]),
            pms_updated_at=row["pms_updated_at"],
        )

    @staticmethod
    def _barcode_contract(row) -> PmsExportBarcode:
        return PmsExportBarcode(
            id=int(row["id"]),
            item_id=int(row["item_id"]),
            item_uom_id=int(row["item_uom_id"]),
            barcode=str(row["barcode"]),
            symbology=str(row["symbology"]),
            active=bool(row["active"]),
            is_primary=bool(row["is_primary"]),
            uom=str(row["uom"]),
            display_name=_strip_or_none(row["display_name"]),
            uom_name=_uom_name(row["uom"], row["display_name"]),
            ratio_to_base=int(row["ratio_to_base"]),
        )


__all__ = ["BarcodeReadRepository"]
