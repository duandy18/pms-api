# tests/api/test_pms_owner_baseline_schema_contract.py
from __future__ import annotations

from pathlib import Path

from app.db.base import Base
from app.db.metadata import metadata

ROOT = Path(__file__).resolve().parents[2]

EXPECTED_PMS_TABLES = {
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


def test_pms_owner_metadata_contains_owner_tables_only() -> None:
    tables = set(metadata.tables)

    assert EXPECTED_PMS_TABLES <= tables
    assert "suppliers" not in tables
    assert set(Base.metadata.tables) == tables


def test_pms_owner_baseline_migration_exists_and_excludes_suppliers() -> None:
    migration = ROOT / "alembic/versions/0001_pms_owner_baseline_schema.py"
    text = migration.read_text(encoding="utf-8")

    for table_name in EXPECTED_PMS_TABLES:
        assert f'"{table_name}"' in text

    assert '"suppliers"' not in text
    assert "fk_items_supplier" not in text
    assert 'sa.Column("supplier_id", sa.Integer(), nullable=True)' in text


def test_item_supplier_id_is_scalar_not_foreign_key() -> None:
    from app.pms.items.models.item import Item

    col = Item.__table__.c.supplier_id

    assert col.foreign_keys == set()
    assert col.nullable is True
