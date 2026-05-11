# tests/api/test_pms_suppliers_owner_contract.py
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


def test_supplier_tables_are_owned_by_pms_metadata() -> None:
    tables = set(metadata.tables)

    assert "suppliers" in tables
    assert "supplier_contacts" in tables


def test_pms_supplier_owner_and_read_routes_are_registered() -> None:
    pairs = _method_paths()

    assert ("GET", "/pms/suppliers") in pairs
    assert ("POST", "/pms/suppliers") in pairs
    assert ("PATCH", "/pms/suppliers/{supplier_id}") in pairs
    assert ("POST", "/pms/suppliers/{supplier_id}/contacts") in pairs
    assert ("PATCH", "/pms/supplier-contacts/{contact_id}") in pairs
    assert ("DELETE", "/pms/supplier-contacts/{contact_id}") in pairs
    assert ("GET", "/pms/read/v1/suppliers") in pairs
    assert ("GET", "/pms/read/v1/suppliers/{supplier_id}") in pairs


def test_no_legacy_partners_supplier_routes_are_mounted_in_pms_api() -> None:
    paths = {path for _, path in _method_paths()}

    assert "/partners/suppliers" not in paths
    assert "/partners/export/suppliers" not in paths
    assert "/partners/supplier-contacts/{contact_id}" not in paths
