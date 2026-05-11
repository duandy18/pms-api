# tests/api/test_pms_split_migration_scripts.py
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

PMS_TABLES = {
    "items",
    "item_uoms",
    "item_barcodes",
    "item_sku_codes",
    "pms_brands",
    "pms_business_categories",
    "item_attribute_defs",
    "item_attribute_options",
    "item_attribute_values",
    "sku_code_templates",
    "sku_code_template_segments",
}


def test_pms_split_export_import_script_exists() -> None:
    script = ROOT / "scripts/migration/pms_split_export_import.sh"

    assert script.exists()
    assert script.read_text(encoding="utf-8").startswith("#!/usr/bin/env bash")


def test_pms_split_export_import_script_covers_all_initial_pms_tables() -> None:
    text = (ROOT / "scripts/migration/pms_split_export_import.sh").read_text(
        encoding="utf-8"
    )

    for table_name in PMS_TABLES:
        assert table_name in text


def test_pms_split_export_import_script_keeps_supplier_migration_separate() -> None:
    text = (ROOT / "scripts/migration/pms_split_export_import.sh").read_text(
        encoding="utf-8"
    )

    assert "suppliers.csv" not in text
    assert "\\copy suppliers" not in text
    assert "fk_items_supplier" not in text


def test_pms_supplier_export_import_script_exists() -> None:
    text = (ROOT / "scripts/migration/pms_suppliers_export_import.sh").read_text(
        encoding="utf-8"
    )

    assert "PMS_SUPPLIER_SOURCE_PSQL_DSN" in text
    assert "PMS_SUPPLIER_TARGET_PSQL_DSN" in text
    assert "suppliers.csv" in text
    assert "supplier_contacts.csv" in text
    assert "\\copy suppliers" in text
    assert "\\copy supplier_contacts" in text


def test_pms_split_export_import_script_has_safety_guards() -> None:
    text = (ROOT / "scripts/migration/pms_split_export_import.sh").read_text(
        encoding="utf-8"
    )

    assert "set -Eeuo pipefail" in text
    assert "PMS_SPLIT_RESET_TARGET" in text
    assert "PMS_SPLIT_ALLOW_NON_EMPTY_TARGET" in text
    assert "target_total_rows" in text
    assert "PMS FK to non-PMS tables should be empty" in text
    assert "alembic check" in text
