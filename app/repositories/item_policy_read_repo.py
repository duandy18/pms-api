# app/repositories/item_policy_read_repo.py
from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import column, select, table
from sqlalchemy.orm import Session

from app.contracts.pms_read import ItemPolicy, ItemPolicyBatchOut


def _clean_ids(values: Iterable[int]) -> list[int]:
    return sorted({int(value) for value in values if int(value) > 0})


def _enum_value(value: object) -> str:
    raw = getattr(value, "value", value)
    return str(raw)


items_table = table(
    "items",
    column("id"),
    column("sku"),
    column("enabled"),
    column("expiry_policy"),
    column("shelf_life_value"),
    column("shelf_life_unit"),
    column("lot_source_policy"),
    column("derivation_allowed"),
    column("uom_governance_enabled"),
)


class ItemPolicyReadRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_item_policy(self, *, item_id: int) -> ItemPolicy | None:
        result = self.get_item_policy_batch(item_ids=[int(item_id)], enabled_only=False)
        return result.policies_by_item_id.get(int(item_id))

    def get_item_policy_by_sku(self, *, sku: str) -> ItemPolicy | None:
        clean_sku = str(sku or "").strip()
        if not clean_sku:
            return None

        stmt = self._base_stmt().where(items_table.c.sku == clean_sku).limit(1)
        row = self.db.execute(stmt).mappings().first()
        return self._policy_from_row(row) if row is not None else None

    def get_item_policy_batch(
        self,
        *,
        item_ids: Iterable[int],
        enabled_only: bool,
    ) -> ItemPolicyBatchOut:
        ids = _clean_ids(item_ids)
        if not ids:
            return ItemPolicyBatchOut()

        stmt = (
            self._base_stmt()
            .where(items_table.c.id.in_(ids))
            .order_by(items_table.c.id.asc())
        )

        rows = self.db.execute(stmt).mappings().all()

        found_ids: set[int] = set()
        inactive_item_ids: list[int] = []
        policies_by_item_id: dict[int, ItemPolicy] = {}

        for row in rows:
            item_id = int(row["item_id"])
            found_ids.add(item_id)

            enabled = bool(row["enabled"])
            if enabled_only and not enabled:
                inactive_item_ids.append(item_id)
                continue

            policies_by_item_id[item_id] = self._policy_from_row(row)

        return ItemPolicyBatchOut(
            policies_by_item_id=policies_by_item_id,
            missing_item_ids=sorted(set(ids) - found_ids),
            inactive_item_ids=sorted(inactive_item_ids),
            errors=[],
        )

    @staticmethod
    def _base_stmt():
        return select(
            items_table.c.id.label("item_id"),
            items_table.c.enabled.label("enabled"),
            items_table.c.expiry_policy.label("expiry_policy"),
            items_table.c.shelf_life_value.label("shelf_life_value"),
            items_table.c.shelf_life_unit.label("shelf_life_unit"),
            items_table.c.lot_source_policy.label("lot_source_policy"),
            items_table.c.derivation_allowed.label("derivation_allowed"),
            items_table.c.uom_governance_enabled.label("uom_governance_enabled"),
        )

    @staticmethod
    def _policy_from_row(row) -> ItemPolicy:
        shelf_life_value = row["shelf_life_value"]
        shelf_life_unit = row["shelf_life_unit"]

        return ItemPolicy(
            item_id=int(row["item_id"]),
            expiry_policy=_enum_value(row["expiry_policy"]),
            shelf_life_value=(
                int(shelf_life_value) if shelf_life_value is not None else None
            ),
            shelf_life_unit=(
                _enum_value(shelf_life_unit) if shelf_life_unit is not None else None
            ),
            lot_source_policy=_enum_value(row["lot_source_policy"]),
            derivation_allowed=bool(row["derivation_allowed"]),
            uom_governance_enabled=bool(row["uom_governance_enabled"]),
        )


__all__ = ["ItemPolicyReadRepository"]
