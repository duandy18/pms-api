# app/repositories/uom_read_repo.py
from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import column, or_, select, table
from sqlalchemy.orm import Session

from app.contracts.pms_read import (
    PmsExportUom,
    PmsProjectionUomFeedRow,
    UomDefaultsBatchOut,
    UomQueryOut,
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
)

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
    column("updated_at"),
)


_USAGE_FLAG_BY_NAME = {
    "PURCHASE": item_uoms_table.c.is_purchase_default,
    "INBOUND": item_uoms_table.c.is_inbound_default,
    "OUTBOUND": item_uoms_table.c.is_outbound_default,
}


class UomReadRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_uom(self, *, item_uom_id: int) -> PmsExportUom | None:
        result = self.query_uoms(item_ids=[], item_uom_ids=[int(item_uom_id)])
        return result.uoms[0] if result.uoms else None

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

        stmt = self._base_stmt()

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
            uoms.append(self._uom_from_row(row))

        return UomQueryOut(
            uoms=uoms,
            missing_item_uom_ids=sorted(set(clean_uom_ids) - found_uom_ids),
            errors=[],
        )

    def list_projection_feed(
        self,
        *,
        limit: int,
        offset: int,
    ) -> list[PmsProjectionUomFeedRow]:
        safe_limit = max(1, min(int(limit), 501))
        safe_offset = max(0, int(offset))

        stmt = (
            self._projection_feed_stmt()
            .order_by(item_uoms_table.c.id.asc())
            .offset(safe_offset)
            .limit(safe_limit)
        )
        rows = self.db.execute(stmt).mappings().all()
        return [self._projection_feed_from_row(row) for row in rows]

    def get_default_or_base_batch(
        self,
        *,
        item_ids: Iterable[int],
        usage: str,
    ) -> UomDefaultsBatchOut:
        ids = _clean_ids(item_ids)
        if not ids:
            return UomDefaultsBatchOut()

        usage_key = str(usage).strip().upper()
        flag = _USAGE_FLAG_BY_NAME[usage_key]

        found_item_rows = self.db.execute(
            select(items_table.c.id.label("item_id")).where(items_table.c.id.in_(ids))
        ).mappings().all()
        found_item_ids = {int(row["item_id"]) for row in found_item_rows}

        stmt = (
            self._base_stmt()
            .where(item_uoms_table.c.item_id.in_(ids))
            .where(or_(flag.is_(True), item_uoms_table.c.is_base.is_(True)))
            .order_by(
                item_uoms_table.c.item_id.asc(),
                flag.desc(),
                item_uoms_table.c.is_base.desc(),
                item_uoms_table.c.ratio_to_base.asc(),
                item_uoms_table.c.id.asc(),
            )
        )

        rows = self.db.execute(stmt).mappings().all()

        uoms_by_item_id: dict[int, PmsExportUom] = {}
        for row in rows:
            item_id = int(row["item_id"])
            if item_id in uoms_by_item_id:
                continue
            uoms_by_item_id[item_id] = self._uom_from_row(row)

        return UomDefaultsBatchOut(
            uoms_by_item_id=uoms_by_item_id,
            missing_item_ids=sorted(set(ids) - found_item_ids),
            missing_default_uom_item_ids=sorted(found_item_ids - set(uoms_by_item_id)),
            errors=[],
        )

    @staticmethod
    def _projection_feed_stmt():
        return select(
            item_uoms_table.c.id.label("item_uom_id"),
            item_uoms_table.c.item_id.label("item_id"),
            item_uoms_table.c.uom.label("uom"),
            item_uoms_table.c.display_name.label("display_name"),
            item_uoms_table.c.ratio_to_base.label("ratio_to_base"),
            item_uoms_table.c.net_weight_kg.label("net_weight_kg"),
            item_uoms_table.c.is_base.label("is_base"),
            item_uoms_table.c.is_purchase_default.label("is_purchase_default"),
            item_uoms_table.c.is_inbound_default.label("is_inbound_default"),
            item_uoms_table.c.is_outbound_default.label("is_outbound_default"),
            item_uoms_table.c.updated_at.label("pms_updated_at"),
        )

    @staticmethod
    def _base_stmt():
        return select(
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

    @staticmethod
    def _projection_feed_from_row(row) -> PmsProjectionUomFeedRow:
        net_weight_kg = row["net_weight_kg"]

        return PmsProjectionUomFeedRow(
            item_uom_id=int(row["item_uom_id"]),
            item_id=int(row["item_id"]),
            uom=str(row["uom"]),
            display_name=_strip_or_none(row["display_name"]),
            uom_name=_uom_name(row["uom"], row["display_name"]),
            ratio_to_base=int(row["ratio_to_base"]),
            net_weight_kg=float(net_weight_kg) if net_weight_kg is not None else None,
            is_base=bool(row["is_base"]),
            is_purchase_default=bool(row["is_purchase_default"]),
            is_inbound_default=bool(row["is_inbound_default"]),
            is_outbound_default=bool(row["is_outbound_default"]),
            pms_updated_at=row["pms_updated_at"],
        )

    @staticmethod
    def _uom_from_row(row) -> PmsExportUom:
        net_weight_kg = row["net_weight_kg"]

        return PmsExportUom(
            id=int(row["id"]),
            item_id=int(row["item_id"]),
            uom=str(row["uom"]),
            display_name=_strip_or_none(row["display_name"]),
            uom_name=_uom_name(row["uom"], row["display_name"]),
            ratio_to_base=int(row["ratio_to_base"]),
            net_weight_kg=float(net_weight_kg) if net_weight_kg is not None else None,
            is_base=bool(row["is_base"]),
            is_purchase_default=bool(row["is_purchase_default"]),
            is_inbound_default=bool(row["is_inbound_default"]),
            is_outbound_default=bool(row["is_outbound_default"]),
        )


__all__ = ["UomReadRepository"]
