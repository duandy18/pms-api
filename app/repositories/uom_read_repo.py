# app/repositories/uom_read_repo.py
from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import column, select, table
from sqlalchemy.orm import Session

from app.contracts.pms_read import PmsExportUom, UomQueryOut


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


item_uoms_table = table(
    "item_uoms",
    column("id"),
    column("item_id"),
    column("uom"),
    column("display_name"),
    column("ratio_to_base"),
    column("net_weight_kg"),
    column("is_base"),
    column("is_purchase_default"),
    column("is_inbound_default"),
    column("is_outbound_default"),
)


class UomReadRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def query_uoms(
        self,
        *,
        item_ids: Iterable[int],
        item_uom_ids: Iterable[int],
    ) -> UomQueryOut:
        clean_item_ids = _clean_ids(item_ids)
        clean_uom_ids = _clean_ids(item_uom_ids)

        if not clean_item_ids and not clean_uom_ids:
            return UomQueryOut()

        stmt = select(
            item_uoms_table.c.id.label("id"),
            item_uoms_table.c.item_id.label("item_id"),
            item_uoms_table.c.uom.label("uom"),
            item_uoms_table.c.display_name.label("display_name"),
            item_uoms_table.c.ratio_to_base.label("ratio_to_base"),
            item_uoms_table.c.net_weight_kg.label("net_weight_kg"),
            item_uoms_table.c.is_base.label("is_base"),
            item_uoms_table.c.is_purchase_default.label("is_purchase_default"),
            item_uoms_table.c.is_inbound_default.label("is_inbound_default"),
            item_uoms_table.c.is_outbound_default.label("is_outbound_default"),
        )

        if clean_item_ids:
            stmt = stmt.where(item_uoms_table.c.item_id.in_(clean_item_ids))
        if clean_uom_ids:
            stmt = stmt.where(item_uoms_table.c.id.in_(clean_uom_ids))

        stmt = stmt.order_by(
            item_uoms_table.c.item_id.asc(),
            item_uoms_table.c.ratio_to_base.asc(),
            item_uoms_table.c.id.asc(),
        )

        rows = self.db.execute(stmt).mappings().all()
        found_uom_ids: set[int] = set()
        uoms: list[PmsExportUom] = []

        for row in rows:
            uom_id = int(row["id"])
            found_uom_ids.add(uom_id)

            net_weight_kg = row["net_weight_kg"]

            uoms.append(
                PmsExportUom(
                    id=uom_id,
                    item_id=int(row["item_id"]),
                    uom=str(row["uom"]),
                    display_name=_strip_or_none(row["display_name"]),
                    uom_name=_uom_name(row["uom"], row["display_name"]),
                    ratio_to_base=int(row["ratio_to_base"]),
                    net_weight_kg=(
                        float(net_weight_kg) if net_weight_kg is not None else None
                    ),
                    is_base=bool(row["is_base"]),
                    is_purchase_default=bool(row["is_purchase_default"]),
                    is_inbound_default=bool(row["is_inbound_default"]),
                    is_outbound_default=bool(row["is_outbound_default"]),
                )
            )

        return UomQueryOut(
            uoms=uoms,
            missing_item_uom_ids=sorted(set(clean_uom_ids) - found_uom_ids),
            errors=[],
        )


__all__ = ["UomReadRepository"]
