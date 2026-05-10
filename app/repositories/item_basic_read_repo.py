# app/repositories/item_basic_read_repo.py
from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import column, select, table
from sqlalchemy.orm import Session

from app.contracts.pms_read import ItemBasic, ItemBasicBatchOut


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


class ItemBasicReadRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_item_basic_batch(
        self,
        *,
        item_ids: Iterable[int],
        enabled_only: bool,
    ) -> ItemBasicBatchOut:
        ids = _clean_ids(item_ids)
        if not ids:
            return ItemBasicBatchOut()

        stmt = (
            select(
                items_table.c.id.label("id"),
                items_table.c.sku.label("sku"),
                items_table.c.name.label("name"),
                items_table.c.spec.label("spec"),
                items_table.c.enabled.label("enabled"),
                items_table.c.supplier_id.label("supplier_id"),
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

        rows = self.db.execute(stmt).mappings().all()

        found_ids: set[int] = set()
        inactive_item_ids: list[int] = []
        items_by_id: dict[int, ItemBasic] = {}

        for row in rows:
            item_id = int(row["id"])
            found_ids.add(item_id)

            enabled = bool(row["enabled"])
            if enabled_only and not enabled:
                inactive_item_ids.append(item_id)
                continue

            items_by_id[item_id] = ItemBasic(
                id=item_id,
                sku=str(row["sku"]),
                name=str(row["name"]),
                spec=_strip_or_none(row["spec"]),
                enabled=enabled,
                supplier_id=(
                    int(row["supplier_id"])
                    if row["supplier_id"] is not None
                    else None
                ),
                brand=_strip_or_none(row["brand"]),
                category=_strip_or_none(row["category"]),
            )

        return ItemBasicBatchOut(
            items_by_id=items_by_id,
            missing_item_ids=sorted(set(ids) - found_ids),
            inactive_item_ids=sorted(inactive_item_ids),
            errors=[],
        )


__all__ = ["ItemBasicReadRepository"]
