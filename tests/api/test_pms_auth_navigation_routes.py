# tests/api/test_pms_auth_navigation_routes.py
from __future__ import annotations

from app.db.metadata import metadata
from app.main import app


def _method_paths() -> set[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    for route in app.routes:
        path = getattr(route, "path", "")
        methods = getattr(route, "methods", None) or []
        for method in methods:
            if method in {"GET", "POST", "PATCH", "PUT", "DELETE"}:
                pairs.add((method, path))
    return pairs


def test_user_auth_navigation_routes_are_mounted() -> None:
    pairs = _method_paths()

    assert ("POST", "/users/login") in pairs
    assert ("GET", "/users/me") in pairs
    assert ("GET", "/users/me/navigation") in pairs


def test_auth_navigation_tables_are_registered_in_metadata() -> None:
    assert {
        "users",
        "permissions",
        "user_permissions",
        "page_registry",
        "page_route_prefixes",
    }.issubset(set(metadata.tables))


def test_pms_owner_routes_still_mounted() -> None:
    pairs = _method_paths()

    assert ("GET", "/items") in pairs
    assert ("GET", "/items/list-rows") in pairs
    assert ("GET", "/pms/brands") in pairs
    assert ("POST", "/pms/sku-coding/generate") in pairs
