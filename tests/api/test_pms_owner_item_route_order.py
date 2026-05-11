# tests/api/test_pms_owner_item_route_order.py
from __future__ import annotations

from app.main import app


def _route_index(*, method: str, path: str) -> int:
    wanted_method = method.upper()

    for index, route in enumerate(app.routes):
        route_path = getattr(route, "path", "")
        methods = getattr(route, "methods", None) or set()

        if route_path == path and wanted_method in methods:
            return index

    raise AssertionError(f"route not found: {wanted_method} {path}")


def test_static_item_owner_routes_are_before_generic_item_id_route() -> None:
    generic_get_item_index = _route_index(method="GET", path="/items/{id}")

    assert _route_index(method="GET", path="/items/list-rows") < generic_get_item_index
    assert _route_index(method="POST", path="/items/aggregate") < generic_get_item_index
    assert _route_index(method="GET", path="/items/sku/{sku}") < generic_get_item_index
