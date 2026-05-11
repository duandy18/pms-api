# tests/repositories/test_barcode_read_repo.py
from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.repositories.barcode_read_repo import BarcodeReadRepository


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
                  spec VARCHAR(128),
                  enabled BOOLEAN NOT NULL,
                  supplier_id INTEGER,
                  brand_id INTEGER,
                  category_id INTEGER
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
                  uom VARCHAR(16) NOT NULL,
                  display_name VARCHAR(32),
                  ratio_to_base INTEGER NOT NULL
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
                  is_primary BOOLEAN NOT NULL,
                  updated_at TIMESTAMP NOT NULL
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
                INSERT INTO items (
                  id,
                  sku,
                  name,
                  spec,
                  enabled,
                  supplier_id,
                  brand_id,
                  category_id
                )
                VALUES
                  (1, 'SKU001', '商品A', '规格A', 1, 100, 10, 20),
                  (2, 'SKU002', '商品B', NULL, 0, NULL, NULL, NULL)
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO item_uoms (id, item_id, uom, display_name, ratio_to_base)
                VALUES
                  (10, 1, 'PCS', '件', 1),
                  (11, 1, 'BOX', NULL, 12),
                  (20, 2, 'BAG', '袋', 6)
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO item_barcodes (
                  id,
                  item_id,
                  item_uom_id,
                  barcode,
                  symbology,
                  active,
                  is_primary,
                  updated_at
                )
                VALUES
                  (100, 1, 10, 'BC-OLD', 'CUSTOM', 0, 0, '2026-01-01 00:00:00'),
                  (101, 1, 10, 'BC-PRIMARY', 'EAN13', 1, 1, '2026-01-02 00:00:00'),
                  (102, 1, 11, 'BC-SECONDARY', 'CUSTOM', 1, 0, '2026-01-03 00:00:00'),
                  (200, 2, 20, 'BC-DISABLED-ITEM', 'CUSTOM', 1, 1, '2026-01-04 00:00:00')
                """
            )
        )

    return Session(engine)


def test_barcode_repository_queries_active_primary_barcodes() -> None:
    session = _make_session()
    try:
        repo = BarcodeReadRepository(session)

        result = repo.query_barcodes(
            item_ids=[1],
            item_uom_ids=[],
            barcode=None,
            active=True,
            primary_only=True,
        )

        assert [row.id for row in result.barcodes] == [101]
        row = result.barcodes[0]
        assert row.item_id == 1
        assert row.item_uom_id == 10
        assert row.barcode == "BC-PRIMARY"
        assert row.symbology == "EAN13"
        assert row.active is True
        assert row.is_primary is True
        assert row.uom == "PCS"
        assert row.display_name == "件"
        assert row.uom_name == "件"
        assert row.ratio_to_base == 1
    finally:
        session.close()


def test_barcode_repository_projection_feed_is_paginated() -> None:
    session = _make_session()
    try:
        repo = BarcodeReadRepository(session)

        rows = repo.list_projection_feed(limit=2, offset=1)

        assert [row.barcode_id for row in rows] == [101, 102]
        assert rows[0].item_id == 1
        assert rows[0].item_uom_id == 10
        assert rows[0].barcode == "BC-PRIMARY"
        assert rows[0].symbology == "EAN13"
        assert rows[0].active is True
        assert rows[0].is_primary is True
        assert rows[0].pms_updated_at is not None
    finally:
        session.close()


def test_barcode_repository_probe_bound_includes_item_basic() -> None:
    session = _make_session()
    try:
        repo = BarcodeReadRepository(session)

        result = repo.probe_barcode(barcode=" BC-PRIMARY ")

        assert result.ok is True
        assert result.status == "BOUND"
        assert result.barcode == "BC-PRIMARY"
        assert result.item_id == 1
        assert result.item_uom_id == 10
        assert result.ratio_to_base == 1
        assert result.symbology == "EAN13"
        assert result.active is True
        assert result.item_basic is not None
        assert result.item_basic.sku == "SKU001"
        assert result.item_basic.name == "商品A"
        assert result.item_basic.brand == "品牌A"
        assert result.item_basic.category == "分类A"
    finally:
        session.close()


def test_barcode_repository_probe_unbound_and_blank() -> None:
    session = _make_session()
    try:
        repo = BarcodeReadRepository(session)

        unbound = repo.probe_barcode(barcode="NOPE")
        assert unbound.ok is True
        assert unbound.status == "UNBOUND"

        blank = repo.probe_barcode(barcode="   ")
        assert blank.ok is False
        assert blank.status == "ERROR"
        assert blank.errors[0].error == "barcode is required"
    finally:
        session.close()
