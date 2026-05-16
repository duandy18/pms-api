# tests/api/test_pms_owner_baseline_schema_contract.py
from __future__ import annotations

from pathlib import Path

from app.db.base import Base
from app.db.metadata import metadata

ROOT = Path(__file__).resolve().parents[2]

PMS_OWNER_BASELINE_TABLES = {
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

EXPECTED_CURRENT_PMS_TABLES = PMS_OWNER_BASELINE_TABLES | {
    "users",
    "permissions",
    "user_permissions",
    "page_registry",
    "page_route_prefixes",
    "suppliers",
    "supplier_contacts",
    "pms_service_capabilities",
    "pms_service_capability_routes",
    "pms_service_clients",
    "pms_service_permissions",
}


def test_pms_owner_metadata_contains_current_pms_owned_tables() -> None:
    tables = set(metadata.tables)

    assert EXPECTED_CURRENT_PMS_TABLES <= tables
    assert set(Base.metadata.tables) == tables


def test_pms_owner_baseline_migration_remains_pre_supplier_split() -> None:
    migration = ROOT / "alembic/versions/0001_pms_owner_baseline_schema.py"
    text = migration.read_text(encoding="utf-8")

    for table_name in PMS_OWNER_BASELINE_TABLES:
        assert f'"{table_name}"' in text

    assert '"suppliers"' not in text
    assert "fk_items_supplier" not in text
    assert 'sa.Column("supplier_id", sa.Integer(), nullable=True)' in text


def test_pms_suppliers_owner_migration_adds_supplier_tables_and_page_registry() -> None:
    migration = ROOT / "alembic/versions/0003_pms_suppliers_owner.py"
    text = migration.read_text(encoding="utf-8")

    assert '"suppliers"' in text
    assert '"supplier_contacts"' in text
    assert "pms.suppliers" in text
    assert "/pms/suppliers" in text


def test_item_supplier_id_is_scalar_not_foreign_key_during_stability_window() -> None:
    from app.pms.items.models.item import Item

    col = Item.__table__.c.supplier_id

    assert col.foreign_keys == set()
    assert col.nullable is True
