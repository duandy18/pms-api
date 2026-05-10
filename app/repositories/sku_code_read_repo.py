# app/repositories/sku_code_read_repo.py
from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import column, or_, select, table
from sqlalchemy.orm import Session

from app.contracts.pms_read import (
    PmsExportSkuCode,
    PmsExportSkuCodeResolution,
    SkuCodeQueryOut,
)


class SkuCodeResolveError(RuntimeError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


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


item_sku_codes_table = table(
    "item_sku_codes",
    column("id"),
    column("item_id"),
    column("code"),
    column("code_type"),
    column("is_primary"),
    column("is_active"),
    column("effective_from"),
    column("effective_to"),
    column("remark"),
)

items_table = table(
    "items",
    column("id"),
    column("sku"),
    column("name"),
    column("enabled"),
)

item_uoms_table = table(
    "item_uoms",
    column("id"),
    column("item_id"),
    column("uom"),
    column("display_name"),
    column("ratio_to_base"),
    column("is_base"),
    column("is_outbound_default"),
)


class SkuCodeReadRepository:
    def __init__(self, db: Session) -> None:
        self.db = db


    def get_sku_code(self, *, sku_code_id: int) -> PmsExportSkuCode | None:
        result = self.query_sku_codes(
            item_ids=[],
            sku_code_ids=[int(sku_code_id)],
            code=None,
            active=None,
            primary_only=False,
        )
        return result.sku_codes[0] if result.sku_codes else None

    def query_sku_codes(
        self,
        *,
        item_ids: Iterable[int],
        sku_code_ids: Iterable[int],
        code: str | None,
        active: bool | None,
        primary_only: bool,
    ) -> SkuCodeQueryOut:
        clean_item_ids = _clean_ids(item_ids)
        clean_sku_code_ids = _clean_ids(sku_code_ids)
        clean_code = str(code or "").strip()

        if not clean_item_ids and not clean_sku_code_ids and not clean_code:
            return SkuCodeQueryOut()

        stmt = self._base_sku_code_stmt()

        if clean_item_ids:
            stmt = stmt.where(item_sku_codes_table.c.item_id.in_(clean_item_ids))
        if clean_sku_code_ids:
            stmt = stmt.where(item_sku_codes_table.c.id.in_(clean_sku_code_ids))
        if clean_code:
            stmt = stmt.where(item_sku_codes_table.c.code == clean_code)
        if active is not None:
            stmt = stmt.where(item_sku_codes_table.c.is_active.is_(bool(active)))
        if primary_only:
            stmt = stmt.where(item_sku_codes_table.c.is_primary.is_(True))

        stmt = stmt.order_by(
            item_sku_codes_table.c.item_id.asc(),
            item_sku_codes_table.c.is_primary.desc(),
            item_sku_codes_table.c.id.asc(),
        )

        rows = self.db.execute(stmt).mappings().all()

        return SkuCodeQueryOut(
            sku_codes=[self._sku_code_contract(row) for row in rows],
            errors=[],
        )

    def resolve_outbound_default_sku_code(
        self,
        *,
        code: str,
        enabled_only: bool,
    ) -> PmsExportSkuCodeResolution:
        clean_code = str(code or "").strip()
        if not clean_code:
            raise SkuCodeResolveError("pms_invalid_sku_code")

        sku_stmt = self._base_sku_code_stmt().where(
            item_sku_codes_table.c.code == clean_code
        )

        row = self.db.execute(sku_stmt).mappings().first()
        if row is None:
            raise SkuCodeResolveError("pms_sku_code_not_found")

        if not bool(row["is_active"]):
            raise SkuCodeResolveError("pms_sku_code_inactive")

        if enabled_only and not bool(row["item_enabled"]):
            raise SkuCodeResolveError("pms_item_inactive")

        uom_stmt = (
            select(
                item_uoms_table.c.id.label("item_uom_id"),
                item_uoms_table.c.uom.label("uom"),
                item_uoms_table.c.display_name.label("display_name"),
                item_uoms_table.c.ratio_to_base.label("ratio_to_base"),
                item_uoms_table.c.is_base.label("is_base"),
                item_uoms_table.c.is_outbound_default.label("is_outbound_default"),
            )
            .where(item_uoms_table.c.item_id == int(row["item_id"]))
            .where(
                or_(
                    item_uoms_table.c.is_outbound_default.is_(True),
                    item_uoms_table.c.is_base.is_(True),
                )
            )
            .order_by(
                item_uoms_table.c.is_outbound_default.desc(),
                item_uoms_table.c.is_base.desc(),
                item_uoms_table.c.ratio_to_base.asc(),
                item_uoms_table.c.id.asc(),
            )
            .limit(1)
        )

        uom_row = self.db.execute(uom_stmt).mappings().first()
        if uom_row is None:
            raise SkuCodeResolveError("pms_outbound_uom_missing")

        return PmsExportSkuCodeResolution(
            sku_code_id=int(row["id"]),
            item_id=int(row["item_id"]),
            sku_code=str(row["code"]),
            code_type=str(row["code_type"]),
            is_primary=bool(row["is_primary"]),
            item_sku=str(row["item_sku"]),
            item_name=str(row["item_name"]),
            item_uom_id=int(uom_row["item_uom_id"]),
            uom=str(uom_row["uom"]),
            display_name=_strip_or_none(uom_row["display_name"]),
            uom_name=_uom_name(uom_row["uom"], uom_row["display_name"]),
            ratio_to_base=int(uom_row["ratio_to_base"]),
        )

    @staticmethod
    def _base_sku_code_stmt():
        return (
            select(
                item_sku_codes_table.c.id.label("id"),
                item_sku_codes_table.c.item_id.label("item_id"),
                item_sku_codes_table.c.code.label("code"),
                item_sku_codes_table.c.code_type.label("code_type"),
                item_sku_codes_table.c.is_primary.label("is_primary"),
                item_sku_codes_table.c.is_active.label("is_active"),
                item_sku_codes_table.c.effective_from.label("effective_from"),
                item_sku_codes_table.c.effective_to.label("effective_to"),
                item_sku_codes_table.c.remark.label("remark"),
                items_table.c.sku.label("item_sku"),
                items_table.c.name.label("item_name"),
                items_table.c.enabled.label("item_enabled"),
            )
            .select_from(
                item_sku_codes_table.join(
                    items_table,
                    items_table.c.id == item_sku_codes_table.c.item_id,
                )
            )
        )

    @staticmethod
    def _sku_code_contract(row) -> PmsExportSkuCode:
        return PmsExportSkuCode(
            id=int(row["id"]),
            item_id=int(row["item_id"]),
            code=str(row["code"]),
            code_type=str(row["code_type"]),
            is_primary=bool(row["is_primary"]),
            is_active=bool(row["is_active"]),
            effective_from=row["effective_from"],
            effective_to=row["effective_to"],
            remark=_strip_or_none(row["remark"]),
            item_sku=str(row["item_sku"]),
            item_name=str(row["item_name"]),
            item_enabled=bool(row["item_enabled"]),
        )


__all__ = ["SkuCodeReadRepository", "SkuCodeResolveError"]
