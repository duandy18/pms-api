# tests/repositories/test_item_basic_read_repo.py
from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.repositories.item_basic_read_repo import ItemBasicReadRepository


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
                  category_id INTEGER,
                  expiry_policy VARCHAR(32) NOT NULL,
                  shelf_life_value INTEGER,
                  shelf_life_unit VARCHAR(16),
                  lot_source_policy VARCHAR(32) NOT NULL,
                  derivation_allowed BOOLEAN NOT NULL,
                  uom_governance_enabled BOOLEAN NOT NULL,
                  updated_at TIMESTAMP NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO pms_brands (id, name_cn)
                VALUES (10, '品牌A')
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO pms_business_categories (id, category_name)
                VALUES (20, '分类A')
                """
            )
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
                  category_id,
                  expiry_policy,
                  shelf_life_value,
                  shelf_life_unit,
                  lot_source_policy,
                  derivation_allowed,
                  uom_governance_enabled,
                  updated_at
                )
                VALUES
                  (
                    1,
                    'SKU001',
                    '商品A',
                    '规格A',
                    1,
                    100,
                    10,
                    20,
                    'NONE',
                    NULL,
                    NULL,
                    'INTERNAL_ONLY',
                    1,
                    0,
                    '2026-01-01 00:00:00'
                  ),
                  (
                    2,
                    'SKU002',
                    '商品B',
                    NULL,
                    0,
                    NULL,
                    NULL,
                    NULL,
                    'REQUIRED',
                    12,
                    'MONTH',
                    'SUPPLIER_ONLY',
                    0,
                    1,
                    '2026-01-02 00:00:00'
                  )
                """
            )
        )

    return Session(engine)


def test_item_basic_repository_reads_brand_and_category_names() -> None:
    session = _make_session()
    try:
        repo = ItemBasicReadRepository(session)

        result = repo.get_item_basic_batch(
            item_ids=[999, 2, 1, 1],
            enabled_only=False,
        )

        assert sorted(result.items_by_id) == [1, 2]
        assert result.missing_item_ids == [999]
        assert result.inactive_item_ids == []

        item = result.items_by_id[1]
        assert item.id == 1
        assert item.sku == "SKU001"
        assert item.name == "商品A"
        assert item.spec == "规格A"
        assert item.enabled is True
        assert item.supplier_id == 100
        assert item.brand == "品牌A"
        assert item.category == "分类A"

        disabled = result.items_by_id[2]
        assert disabled.enabled is False
        assert disabled.brand is None
        assert disabled.category is None
    finally:
        session.close()


def test_item_basic_repository_projection_feed_is_paginated() -> None:
    session = _make_session()
    try:
        repo = ItemBasicReadRepository(session)

        first = repo.list_projection_feed(limit=1, offset=0)
        second = repo.list_projection_feed(limit=1, offset=1)

        assert [row.item_id for row in first] == [1]
        assert [row.item_id for row in second] == [2]

        row = first[0]
        assert row.sku == "SKU001"
        assert row.brand == "品牌A"
        assert row.category == "分类A"
        assert row.expiry_policy == "NONE"
        assert row.lot_source_policy == "INTERNAL_ONLY"
        assert row.derivation_allowed is True
        assert row.uom_governance_enabled is False
        assert row.pms_updated_at is not None
    finally:
        session.close()


def test_item_basic_repository_reports_inactive_when_enabled_only() -> None:
    session = _make_session()
    try:
        repo = ItemBasicReadRepository(session)

        result = repo.get_item_basic_batch(
            item_ids=[1, 2, 3],
            enabled_only=True,
        )

        assert sorted(result.items_by_id) == [1]
        assert result.missing_item_ids == [3]
        assert result.inactive_item_ids == [2]
    finally:
        session.close()
