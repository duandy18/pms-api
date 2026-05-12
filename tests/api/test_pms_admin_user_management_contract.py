# tests/api/test_pms_admin_user_management_contract.py
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


def test_admin_user_management_routes_are_mounted() -> None:
    pairs = _method_paths()

    assert ("GET", "/admin/users/permission-matrix") in pairs
    assert ("GET", "/admin/users") in pairs
    assert ("POST", "/admin/users") in pairs
    assert ("PATCH", "/admin/users/{user_id}") in pairs
    assert ("PUT", "/admin/users/{user_id}/permission-matrix") in pairs
    assert ("POST", "/admin/users/{user_id}/delete") in pairs
    assert ("POST", "/admin/users/{user_id}/reset-password") in pairs


def test_admin_domain_is_allowed_in_page_registry_metadata() -> None:
    table = metadata.tables["page_registry"]
    constraint_texts = {str(constraint.sqltext) for constraint in table.constraints if hasattr(constraint, "sqltext")}

    assert any("admin" in text and "pms" in text for text in constraint_texts)


def test_admin_migration_registers_permissions_pages_and_route_prefix() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    migration = (root / "alembic/versions/0004_pms_admin_user_management.py").read_text()

    assert "page.admin.read" in migration
    assert "page.admin.write" in migration
    assert "'admin'" in migration
    assert "'admin.users'" in migration
    assert "/admin/users" in migration


def test_legacy_admin_permissions_page_is_not_mounted() -> None:
    paths = {path for _, path in _method_paths()}

    assert "/admin/permissions" not in paths
