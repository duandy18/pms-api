# tests/api/test_pms_admin_users_read_only_api.py
from __future__ import annotations

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


def test_pms_admin_user_read_routes_still_mounted() -> None:
    pairs = _method_paths()

    assert ("GET", "/admin/users/permission-matrix") in pairs
    assert ("GET", "/admin/users") in pairs


def test_pms_admin_user_write_routes_are_removed() -> None:
    pairs = _method_paths()
    paths = {path for _, path in pairs}

    assert ("POST", "/admin/users") not in pairs
    assert "/admin/users/{user_id}" not in paths
    assert "/admin/users/{user_id}/delete" not in paths
    assert "/admin/users/{user_id}/reset-password" not in paths
    assert "/admin/users/{user_id}/permission-matrix" not in paths
