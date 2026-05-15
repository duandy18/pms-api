from __future__ import annotations

import inspect
from pathlib import Path

from app.repositories.item_basic_read_repo import ItemBasicReadRepository


def test_item_basic_read_repo_accepts_supplier_id_filter() -> None:
    signature = inspect.signature(ItemBasicReadRepository.list_item_basics)

    assert "supplier_id" in signature.parameters

    source = Path("app/repositories/item_basic_read_repo.py").read_text(encoding="utf-8")
    assert "items_table.c.supplier_id == int(supplier_id)" in source


def test_pms_read_v1_item_basic_route_exposes_supplier_id_query() -> None:
    source = Path("app/routers/pms_read_v1.py").read_text(encoding="utf-8")

    assert "supplier_id: int | None = Query(None, ge=1)" in source
    assert "supplier_id=supplier_id" in source
