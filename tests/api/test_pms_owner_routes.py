# tests/api/test_pms_owner_routes.py
from __future__ import annotations

from app.main import app


def test_pms_owner_routes_are_mounted() -> None:
    paths = {
        route.path
        for route in app.routes
        if getattr(route, "path", "").startswith(("/pms", "/items", "/item-uoms", "/item-barcodes"))
    }

    expected = {
        "/pms/brands",
        "/pms/brands/{brand_id}",
        "/pms/categories",
        "/pms/categories/{category_id}",
        "/pms/item-attribute-defs",
        "/items",
        "/items/{id}",
        "/items/list-rows",
        "/items/{item_id}/list-detail",
        "/items/{item_id}/aggregate",
        "/items/aggregate",
        "/item-uoms",
        "/item-uoms/item/{item_id}",
        "/item-uoms/item/{item_id}/rows",
        "/item-barcodes",
        "/item-barcodes/item/{item_id}",
        "/item-barcodes/item/{item_id}/rows",
        "/items/{item_id}/sku-codes",
        "/pms/sku-coding/generate",
        "/pms/sku-coding/items/{item_id}/generate",
    }

    missing = sorted(expected - paths)
    assert missing == []
