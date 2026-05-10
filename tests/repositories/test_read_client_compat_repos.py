# tests/repositories/test_read_client_compat_repos.py
from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.repositories.barcode_read_repo import BarcodeReadRepository
from app.repositories.item_basic_read_repo import ItemBasicReadRepository
from app.repositories.item_policy_read_repo import ItemPolicyReadRepository
from app.repositories.item_report_meta_read_repo import ItemReportMetaReadRepository
from app.repositories.sku_code_read_repo import SkuCodeReadRepository
from app.repositories.uom_read_repo import UomReadRepository


def _make_session() -> Session:
    engine = create_engine("sqlite:///:memory:")

    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE pms_brands (id INTEGER PRIMARY KEY, name_cn TEXT NOT NULL)"))
        conn.execute(
            text("CREATE TABLE pms_business_categories (id INTEGER PRIMARY KEY, category_name TEXT NOT NULL)")
        )
        conn.execute(
            text(
                """
                CREATE TABLE items (
                  id INTEGER PRIMARY KEY,
                  sku TEXT NOT NULL,
                  name TEXT NOT NULL,
                  spec TEXT,
                  enabled BOOLEAN NOT NULL,
                  supplier_id INTEGER,
                  brand_id INTEGER,
                  category_id INTEGER,
                  expiry_policy TEXT NOT NULL,
                  shelf_life_value INTEGER,
                  shelf_life_unit TEXT,
                  lot_source_policy TEXT NOT NULL,
                  derivation_allowed BOOLEAN NOT NULL,
                  uom_governance_enabled BOOLEAN NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE item_uoms (
                  id INTEGER PRIMARY KEY,
                  item_id INTEGER NOT NULL,
                  uom TEXT NOT NULL,
                  display_name TEXT,
                  ratio_to_base INTEGER NOT NULL,
                  net_weight_kg NUMERIC,
                  is_base BOOLEAN NOT NULL,
                  is_purchase_default BOOLEAN NOT NULL,
                  is_inbound_default BOOLEAN NOT NULL,
                  is_outbound_default BOOLEAN NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE item_barcodes (
                  id INTEGER PRIMARY KEY,
                  item_id INTEGER NOT NULL,
                  item_uom_id INTEGER NOT NULL,
                  barcode TEXT NOT NULL,
                  symbology TEXT NOT NULL,
                  active BOOLEAN NOT NULL,
                  is_primary BOOLEAN NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE item_sku_codes (
                  id INTEGER PRIMARY KEY,
                  item_id INTEGER NOT NULL,
                  code TEXT NOT NULL,
                  code_type TEXT NOT NULL,
                  is_primary BOOLEAN NOT NULL,
                  is_active BOOLEAN NOT NULL,
                  effective_from TIMESTAMP,
                  effective_to TIMESTAMP,
                  remark TEXT
                )
                """
            )
        )

        conn.execute(text("INSERT INTO pms_brands VALUES (10, '品牌A')"))
        conn.execute(text("INSERT INTO pms_business_categories VALUES (20, '分类A')"))
        conn.execute(
            text(
                """
                INSERT INTO items (
                  id, sku, name, spec, enabled, supplier_id, brand_id, category_id,
                  expiry_policy, shelf_life_value, shelf_life_unit,
                  lot_source_policy, derivation_allowed, uom_governance_enabled
                )
                VALUES
                  (1, 'SKU001', '商品A', '规格A', 1, 100, 10, 20,
                   'NONE', NULL, NULL, 'INTERNAL_ONLY', 1, 0),
                  (2, 'SKU002', '商品B', NULL, 1, NULL, NULL, NULL,
                   'REQUIRED', 12, 'MONTH', 'SUPPLIER_ONLY', 1, 1)
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO item_uoms (
                  id, item_id, uom, display_name, ratio_to_base, net_weight_kg,
                  is_base, is_purchase_default, is_inbound_default, is_outbound_default
                )
                VALUES
                  (7, 1, 'PCS', '件', 1, 0.2, 1, 0, 1, 1),
                  (8, 1, 'BOX', NULL, 12, NULL, 0, 1, 0, 0)
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO item_barcodes (
                  id, item_id, item_uom_id, barcode, symbology, active, is_primary
                )
                VALUES
                  (2, 1, 7, 'BC1', 'CUSTOM', 1, 1)
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO item_sku_codes (
                  id, item_id, code, code_type, is_primary, is_active,
                  effective_from, effective_to, remark
                )
                VALUES
                  (10, 1, 'SKU001', 'PRIMARY', 1, 1, NULL, NULL, NULL)
                """
            )
        )

    return Session(engine)


def test_item_basic_and_policy_compat_methods() -> None:
    session = _make_session()
    try:
        item_repo = ItemBasicReadRepository(session)
        policy_repo = ItemPolicyReadRepository(session)

        assert item_repo.get_item_basic(item_id=1).sku == "SKU001"  # type: ignore[union-attr]
        assert item_repo.get_item_basic(item_id=999) is None
        assert [row.id for row in item_repo.list_item_basics(keyword="商品", limit=10)] == [1, 2]

        assert policy_repo.get_item_policy(item_id=1).item_id == 1  # type: ignore[union-attr]
        assert policy_repo.get_item_policy_by_sku(sku="SKU001").item_id == 1  # type: ignore[union-attr]
        assert policy_repo.get_item_policy_by_sku(sku="NOPE") is None
    finally:
        session.close()


def test_report_search_uom_barcode_and_sku_compat_methods() -> None:
    session = _make_session()
    try:
        report_repo = ItemReportMetaReadRepository(session)
        uom_repo = UomReadRepository(session)
        barcode_repo = BarcodeReadRepository(session)
        sku_repo = SkuCodeReadRepository(session)

        assert report_repo.search_report_item_ids_by_keyword(keyword="BC1", limit=10) == [1]

        defaults = uom_repo.get_default_or_base_batch(item_ids=[1, 999], usage="OUTBOUND")
        assert defaults.uoms_by_item_id[1].id == 7
        assert defaults.missing_item_ids == [999]

        assert uom_repo.get_uom(item_uom_id=7).uom == "PCS"  # type: ignore[union-attr]
        assert barcode_repo.get_barcode(barcode_id=2).barcode == "BC1"  # type: ignore[union-attr]
        assert sku_repo.get_sku_code(sku_code_id=10).code == "SKU001"  # type: ignore[union-attr]
    finally:
        session.close()
