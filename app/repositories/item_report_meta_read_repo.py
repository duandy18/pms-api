# app/repositories/item_report_meta_read_repo.py
from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import column, select, table
from sqlalchemy.orm import Session

from app.contracts.pms_read import ItemReportMeta, ItemReportMetaBatchOut


def _clean_ids(values: Iterable[int]) -> list[int]:
    return sorted({int(value) for value in values if int(value) > 0})


def _strip_or_none(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


items_table = table(
    "items",
    column("id"),
    column("sku"),
    column("name"),
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

barcodes_table = table(
    "item_barcodes",
    column("id"),
    column("item_id"),
    column("barcode"),
    column("active"),
    column("is_primary"),
)


class ItemReportMetaReadRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_item_report_meta_batch(
        self,
        *,
        item_ids: Iterable[int],
    ) -> ItemReportMetaBatchOut:
        ids = _clean_ids(item_ids)
        if not ids:
            return ItemReportMetaBatchOut()

        items_stmt = (
            select(
                items_table.c.id.label("item_id"),
                items_table.c.sku.label("sku"),
                items_table.c.name.label("name"),
                brands_table.c.name_cn.label("brand"),
                categories_table.c.category_name.label("category"),
            )
            .select_from(
                items_table.outerjoin(
                    brands_table,
                    brands_table.c.id == items_table.c.brand_id,
                ).outerjoin(
                    categories_table,
                    categories_table.c.id == items_table.c.category_id,
                )
            )
            .where(items_table.c.id.in_(ids))
            .order_by(items_table.c.id.asc())
        )

        item_rows = self.db.execute(items_stmt).mappings().all()
        found_ids = {int(row["item_id"]) for row in item_rows}

        barcode_stmt = (
            select(
                barcodes_table.c.item_id.label("item_id"),
                barcodes_table.c.barcode.label("barcode"),
            )
            .where(barcodes_table.c.item_id.in_(ids))
            .where(barcodes_table.c.active.is_(True))
            .order_by(
                barcodes_table.c.item_id.asc(),
                barcodes_table.c.is_primary.desc(),
                barcodes_table.c.id.asc(),
            )
        )

        barcode_rows = self.db.execute(barcode_stmt).mappings().all()
        barcode_by_item_id: dict[int, str] = {}

        for row in barcode_rows:
            item_id = int(row["item_id"])
            if item_id in barcode_by_item_id:
                continue

            barcode = _strip_or_none(row["barcode"])
            if barcode is not None:
                barcode_by_item_id[item_id] = barcode

        meta_by_item_id: dict[int, ItemReportMeta] = {}

        for row in item_rows:
            item_id = int(row["item_id"])
            meta_by_item_id[item_id] = ItemReportMeta(
                item_id=item_id,
                sku=str(row["sku"]),
                name=str(row["name"]),
                brand=_strip_or_none(row["brand"]),
                category=_strip_or_none(row["category"]),
                barcode=barcode_by_item_id.get(item_id),
            )

        return ItemReportMetaBatchOut(
            meta_by_item_id=meta_by_item_id,
            missing_item_ids=sorted(set(ids) - found_ids),
            errors=[],
        )


__all__ = ["ItemReportMetaReadRepository"]
