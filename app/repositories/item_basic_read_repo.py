# app/repositories/item_basic_read_repo.py
from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import column, or_, select, table
from sqlalchemy.orm import Session

from app.contracts.pms_read import (
    ItemBasic,
    ItemBasicBatchOut,
    PmsProjectionItemFeedRow,
)


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
    column("expiry_policy"),
    column("shelf_life_value"),
    column("shelf_life_unit"),
    column("lot_source_policy"),
    column("derivation_allowed"),
    column("uom_governance_enabled"),
    column("updated_at"),
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

    def list_item_basics(
        self,
        *,
        keyword: str | None = None,
        enabled: bool | None = None,
        limit: int = 50,
    ) -> list[ItemBasic]:
        stmt = self._base_stmt()

        kw = str(keyword or "").strip()
        if kw:
            pattern = f"%{kw}%"
            stmt = stmt.where(
                or_(
                    items_table.c.sku.ilike(pattern),
                    items_table.c.name.ilike(pattern),
                    brands_table.c.name_cn.ilike(pattern),
                    categories_table.c.category_name.ilike(pattern),
                )
            )

        if enabled is not None:
            stmt = stmt.where(items_table.c.enabled.is_(bool(enabled)))

        stmt = stmt.order_by(items_table.c.id.asc()).limit(max(1, min(int(limit), 500)))
        rows = self.db.execute(stmt).mappings().all()
        return [self._item_basic_from_row(row) for row in rows]

    def list_projection_feed(
        self,
        *,
        limit: int,
        offset: int,
    ) -> list[PmsProjectionItemFeedRow]:
        safe_limit = max(1, min(int(limit), 501))
        safe_offset = max(0, int(offset))

        stmt = (
            self._projection_feed_stmt()
            .order_by(items_table.c.id.asc())
            .offset(safe_offset)
            .limit(safe_limit)
        )
        rows = self.db.execute(stmt).mappings().all()
        return [self._projection_feed_from_row(row) for row in rows]

    def get_item_basic(self, *, item_id: int) -> ItemBasic | None:
        result = self.get_item_basic_batch(item_ids=[int(item_id)], enabled_only=False)
        return result.items_by_id.get(int(item_id))

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
            self._base_stmt()
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

            items_by_id[item_id] = self._item_basic_from_row(row)

        return ItemBasicBatchOut(
            items_by_id=items_by_id,
            missing_item_ids=sorted(set(ids) - found_ids),
            inactive_item_ids=sorted(inactive_item_ids),
            errors=[],
        )

    @staticmethod
    def _projection_feed_stmt():
        return select(
            items_table.c.id.label("item_id"),
            items_table.c.sku.label("sku"),
            items_table.c.name.label("name"),
            items_table.c.spec.label("spec"),
            items_table.c.enabled.label("enabled"),
            items_table.c.supplier_id.label("supplier_id"),
            brands_table.c.name_cn.label("brand"),
            categories_table.c.category_name.label("category"),
            items_table.c.expiry_policy.label("expiry_policy"),
            items_table.c.shelf_life_value.label("shelf_life_value"),
            items_table.c.shelf_life_unit.label("shelf_life_unit"),
            items_table.c.lot_source_policy.label("lot_source_policy"),
            items_table.c.derivation_allowed.label("derivation_allowed"),
            items_table.c.uom_governance_enabled.label("uom_governance_enabled"),
            items_table.c.updated_at.label("pms_updated_at"),
        ).select_from(
            items_table.outerjoin(
                brands_table,
                brands_table.c.id == items_table.c.brand_id,
            ).outerjoin(
                categories_table,
                categories_table.c.id == items_table.c.category_id,
            )
        )

    @staticmethod
    def _base_stmt():
        return select(
            items_table.c.id.label("id"),
            items_table.c.sku.label("sku"),
            items_table.c.name.label("name"),
            items_table.c.spec.label("spec"),
            items_table.c.enabled.label("enabled"),
            items_table.c.supplier_id.label("supplier_id"),
            brands_table.c.name_cn.label("brand"),
            categories_table.c.category_name.label("category"),
        ).select_from(
            items_table.outerjoin(
                brands_table,
                brands_table.c.id == items_table.c.brand_id,
            ).outerjoin(
                categories_table,
                categories_table.c.id == items_table.c.category_id,
            )
        )

    @staticmethod
    def _projection_feed_from_row(row) -> PmsProjectionItemFeedRow:
        return PmsProjectionItemFeedRow(
            item_id=int(row["item_id"]),
            sku=str(row["sku"]),
            name=str(row["name"]),
            spec=_strip_or_none(row["spec"]),
            enabled=bool(row["enabled"]),
            supplier_id=(
                int(row["supplier_id"]) if row["supplier_id"] is not None else None
            ),
            brand=_strip_or_none(row["brand"]),
            category=_strip_or_none(row["category"]),
            expiry_policy=str(row["expiry_policy"]),
            shelf_life_value=(
                int(row["shelf_life_value"])
                if row["shelf_life_value"] is not None
                else None
            ),
            shelf_life_unit=_strip_or_none(row["shelf_life_unit"]),
            lot_source_policy=str(row["lot_source_policy"]),
            derivation_allowed=bool(row["derivation_allowed"]),
            uom_governance_enabled=bool(row["uom_governance_enabled"]),
            pms_updated_at=row["pms_updated_at"],
        )

    @staticmethod
    def _item_basic_from_row(row) -> ItemBasic:
        return ItemBasic(
            id=int(row["id"]),
            sku=str(row["sku"]),
            name=str(row["name"]),
            spec=_strip_or_none(row["spec"]),
            enabled=bool(row["enabled"]),
            supplier_id=(
                int(row["supplier_id"]) if row["supplier_id"] is not None else None
            ),
            brand=_strip_or_none(row["brand"]),
            category=_strip_or_none(row["category"]),
        )


__all__ = ["ItemBasicReadRepository"]
