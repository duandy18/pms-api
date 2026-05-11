# tests/api/test_pms_owner_runtime_read_surface_guard.py
from __future__ import annotations

import re
from pathlib import Path

from app.main import app

ROOT = Path(__file__).resolve().parents[2]

FORBIDDEN_CROSS_DOMAIN_IMPORT_RE = re.compile(
    r"^\s*(from|import)\s+app\.(wms|oms|procurement|finance|shipping_assist)\b"
)


def _mounted_method_paths() -> set[tuple[str, str]]:
    rows: set[tuple[str, str]] = set()

    for route in app.routes:
        path = getattr(route, "path", "")
        methods = getattr(route, "methods", set()) or set()
        for method in methods:
            rows.add((str(method).upper(), str(path)))

    return rows


def _mounted_paths() -> set[str]:
    return {getattr(route, "path", "") for route in app.routes}


def test_pms_owner_runtime_routes_are_mounted() -> None:
    mounted = _mounted_method_paths()

    expected = {
        ("GET", "/items"),
        ("POST", "/items"),
        ("GET", "/items/{id}"),
        ("PATCH", "/items/{id}"),
        ("POST", "/items/aggregate"),
        ("GET", "/items/{item_id}/aggregate"),
        ("PUT", "/items/{item_id}/aggregate"),
        ("GET", "/items/list-rows"),
        ("GET", "/items/{item_id}/list-detail"),
        ("GET", "/items/{item_id}/sku-codes"),
        ("POST", "/items/{item_id}/sku-codes"),
        ("POST", "/items/{item_id}/sku-codes/change-primary"),
        ("POST", "/item-uoms"),
        ("GET", "/item-uoms/by-items"),
        ("GET", "/item-uoms/item/{item_id}"),
        ("GET", "/item-uoms/item/{item_id}/rows"),
        ("PATCH", "/item-uoms/{id}"),
        ("DELETE", "/item-uoms/{id}"),
        ("POST", "/item-barcodes"),
        ("GET", "/item-barcodes/by-items"),
        ("GET", "/item-barcodes/item/{item_id}"),
        ("GET", "/item-barcodes/item/{item_id}/rows"),
        ("PATCH", "/item-barcodes/{id}"),
        ("DELETE", "/item-barcodes/{id}"),
        ("GET", "/pms/brands"),
        ("POST", "/pms/brands"),
        ("PATCH", "/pms/brands/{brand_id}"),
        ("GET", "/pms/categories"),
        ("POST", "/pms/categories"),
        ("PATCH", "/pms/categories/{category_id}"),
        ("GET", "/pms/item-attribute-defs"),
        ("POST", "/pms/item-attribute-defs"),
        ("PATCH", "/pms/item-attribute-defs/{attribute_def_id}"),
        ("POST", "/pms/sku-coding/generate"),
        ("POST", "/pms/sku-coding/items/{item_id}/generate"),
    }

    missing = sorted(expected - mounted)
    assert missing == []


def test_pms_read_v1_routes_are_mounted() -> None:
    mounted = _mounted_method_paths()

    expected = {
        ("GET", "/pms/read/v1/health"),
        ("GET", "/pms/read/v1/items/basic"),
        ("GET", "/pms/read/v1/items/basic/{item_id}"),
        ("POST", "/pms/read/v1/items/basic/batch"),
        ("POST", "/pms/read/v1/items/policies/batch"),
        ("GET", "/pms/read/v1/items/policy-by-sku"),
        ("GET", "/pms/read/v1/items/report-search"),
        ("POST", "/pms/read/v1/items/report-meta/batch"),
        ("POST", "/pms/read/v1/items/uom-defaults/batch"),
        ("GET", "/pms/read/v1/items/{item_id}/uoms"),
        ("GET", "/pms/read/v1/items/{item_id}/barcodes"),
        ("GET", "/pms/read/v1/items/{item_id}/sku-codes"),
        ("POST", "/pms/read/v1/uoms/query"),
        ("GET", "/pms/read/v1/uoms/{item_uom_id}"),
        ("POST", "/pms/read/v1/barcodes/query"),
        ("POST", "/pms/read/v1/barcodes/probe"),
        ("GET", "/pms/read/v1/barcodes/{barcode_id}"),
        ("POST", "/pms/read/v1/sku-codes/query"),
        ("GET", "/pms/read/v1/sku-codes/{sku_code_id}"),
        ("GET", "/pms/read/v1/sku-codes/resolve-outbound-default"),
    }

    missing = sorted(expected - mounted)
    assert missing == []


def test_pms_api_has_both_owner_and_read_surfaces() -> None:
    paths = _mounted_paths()

    assert any(path == "/items" or path.startswith("/items/") for path in paths)
    assert any(path == "/pms/brands" or path.startswith("/pms/brands/") for path in paths)
    assert any(path == "/pms/read/v1/health" or path.startswith("/pms/read/v1/") for path in paths)


def test_pms_owner_runtime_does_not_import_non_pms_business_domains() -> None:
    violations: list[str] = []

    for path in sorted((ROOT / "app" / "pms").rglob("*.py")):
        rel = path.relative_to(ROOT).as_posix()

        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if FORBIDDEN_CROSS_DOMAIN_IMPORT_RE.search(line):
                violations.append(f"{rel}:{line_no}: {line.strip()}")

    assert violations == []


def test_pms_api_owns_legacy_app_pms_package() -> None:
    assert (ROOT / "app" / "pms").is_dir()
