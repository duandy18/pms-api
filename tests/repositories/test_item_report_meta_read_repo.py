# tests/repositories/test_item_report_meta_read_repo.py
from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.repositories.item_report_meta_read_repo import ItemReportMetaReadRepository


def _make_session() -> Session:
    engine = create_engine("sqlite:///:memory:")

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE pms_brands (
                  id INTEGER PRIMARY KEY,
                  name_cn VARCHAR(128) NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE pms_business_categories (
                  id INTEGER PRIMARY KEY,
                  category_name VARCHAR(128) NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE items (
                  id INTEGER PRIMARY KEY,
                  sku VARCHAR(128) NOT NULL,
                  name VARCHAR(128) NOT NULL,
                  brand_id INTEGER,
                  category_id INTEGER
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
                  barcode TEXT NOT NULL,
                  active BOOLEAN NOT NULL,
                  is_primary BOOLEAN NOT NULL
                )
                """
            )
        )

        conn.execute(text("INSERT INTO pms_brands (id, name_cn) VALUES (10, '品牌A')"))
        conn.execute(
            text("INSERT INTO pms_business_categories (id, category_name) VALUES (20, '分类A')")
        )
        conn.execute(
            text(
                """
                INSERT INTO items (id, sku, name, brand_id, category_id)
                VALUES
                  (1, 'SKU001', '商品A', 10, 20),
                  (2, 'SKU002', '商品B', NULL, NULL),
                  (3, 'SKU003', '商品C', NULL, NULL)
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO item_barcodes (id, item_id, barcode, active, is_primary)
                VALUES
                  (10, 1, 'INACTIVE', 0, 0),
                  (11, 1, 'SECONDARY', 1, 0),
                  (12, 1, 'PRIMARY', 1, 1),
                  (13, 2, 'LOW-ID', 1, 0),
                  (14, 2, 'HIGH-ID', 1, 0)
                """
            )
        )

    return Session(engine)


def test_item_report_meta_repository_reads_meta_and_primary_barcode() -> None:
    session = _make_session()
    try:
        repo = ItemReportMetaReadRepository(session)

        result = repo.get_item_report_meta_batch(item_ids=[999, 3, 2, 1, 1])

        assert sorted(result.meta_by_item_id) == [1, 2, 3]
        assert result.missing_item_ids == [999]

        item = result.meta_by_item_id[1]
        assert item.item_id == 1
        assert item.sku == "SKU001"
        assert item.name == "商品A"
        assert item.brand == "品牌A"
        assert item.category == "分类A"
        assert item.barcode == "PRIMARY"

        fallback = result.meta_by_item_id[2]
        assert fallback.barcode == "LOW-ID"

        no_barcode = result.meta_by_item_id[3]
        assert no_barcode.barcode is None
    finally:
        session.close()
