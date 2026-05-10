# tests/repositories/test_sku_code_read_repo.py
from __future__ import annotations

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.repositories.sku_code_read_repo import SkuCodeReadRepository, SkuCodeResolveError


def _make_session() -> Session:
    engine = create_engine("sqlite:///:memory:")

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE items (
                  id INTEGER PRIMARY KEY,
                  sku VARCHAR(128) NOT NULL,
                  name VARCHAR(128) NOT NULL,
                  enabled BOOLEAN NOT NULL
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
                  code VARCHAR(128) NOT NULL,
                  code_type VARCHAR(16) NOT NULL,
                  is_primary BOOLEAN NOT NULL,
                  is_active BOOLEAN NOT NULL,
                  effective_from TIMESTAMP,
                  effective_to TIMESTAMP,
                  remark VARCHAR(255)
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
                  ratio_to_base INTEGER NOT NULL,
                  is_base BOOLEAN NOT NULL,
                  is_outbound_default BOOLEAN NOT NULL
                )
                """
            )
        )

        conn.execute(
            text(
                """
                INSERT INTO items (id, sku, name, enabled)
                VALUES
                  (1, 'SKU001', '商品A', 1),
                  (2, 'SKU002', '商品B', 0),
                  (3, 'SKU003', '商品C', 1)
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO item_sku_codes (
                  id,
                  item_id,
                  code,
                  code_type,
                  is_primary,
                  is_active,
                  effective_from,
                  effective_to,
                  remark
                )
                VALUES
                  (10, 1, 'SKU001', 'PRIMARY', 1, 1, NULL, NULL, 'primary'),
                  (11, 1, 'SKU001-ALIAS', 'ALIAS', 0, 1, NULL, NULL, NULL),
                  (12, 1, 'SKU001-INACTIVE', 'ALIAS', 0, 0, NULL, NULL, NULL),
                  (20, 2, 'SKU002', 'PRIMARY', 1, 1, NULL, NULL, NULL),
                  (30, 3, 'SKU003', 'PRIMARY', 1, 1, NULL, NULL, NULL)
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO item_uoms (
                  id,
                  item_id,
                  uom,
                  display_name,
                  ratio_to_base,
                  is_base,
                  is_outbound_default
                )
                VALUES
                  (100, 1, 'PCS', '件', 1, 1, 0),
                  (101, 1, 'BOX', NULL, 12, 0, 1),
                  (200, 2, 'PCS', '件', 1, 1, 1)
                """
            )
        )

    return Session(engine)


def test_sku_code_repository_queries_codes() -> None:
    session = _make_session()
    try:
        repo = SkuCodeReadRepository(session)

        result = repo.query_sku_codes(
            item_ids=[1],
            sku_code_ids=[],
            code=None,
            active=True,
            primary_only=False,
        )

        assert [row.id for row in result.sku_codes] == [10, 11]
        primary = result.sku_codes[0]
        assert primary.item_id == 1
        assert primary.code == "SKU001"
        assert primary.code_type == "PRIMARY"
        assert primary.is_primary is True
        assert primary.is_active is True
        assert primary.item_sku == "SKU001"
        assert primary.item_name == "商品A"
        assert primary.item_enabled is True
        assert primary.remark == "primary"
    finally:
        session.close()


def test_sku_code_repository_filters_by_code_and_primary_only() -> None:
    session = _make_session()
    try:
        repo = SkuCodeReadRepository(session)

        by_code = repo.query_sku_codes(
            item_ids=[],
            sku_code_ids=[],
            code=" SKU001-ALIAS ",
            active=True,
            primary_only=False,
        )
        assert [row.code for row in by_code.sku_codes] == ["SKU001-ALIAS"]

        primary_only = repo.query_sku_codes(
            item_ids=[1],
            sku_code_ids=[],
            code=None,
            active=True,
            primary_only=True,
        )
        assert [row.code for row in primary_only.sku_codes] == ["SKU001"]
    finally:
        session.close()


def test_sku_code_repository_resolves_outbound_default_uom() -> None:
    session = _make_session()
    try:
        repo = SkuCodeReadRepository(session)

        result = repo.resolve_outbound_default_sku_code(
            code=" SKU001 ",
            enabled_only=True,
        )

        assert result.sku_code_id == 10
        assert result.item_id == 1
        assert result.sku_code == "SKU001"
        assert result.code_type == "PRIMARY"
        assert result.is_primary is True
        assert result.item_sku == "SKU001"
        assert result.item_name == "商品A"
        assert result.item_uom_id == 101
        assert result.uom == "BOX"
        assert result.display_name is None
        assert result.uom_name == "BOX"
        assert result.ratio_to_base == 12
    finally:
        session.close()


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("", "pms_invalid_sku_code"),
        ("NOPE", "pms_sku_code_not_found"),
        ("SKU001-INACTIVE", "pms_sku_code_inactive"),
        ("SKU002", "pms_item_inactive"),
        ("SKU003", "pms_outbound_uom_missing"),
    ],
)
def test_sku_code_repository_resolve_errors(code: str, expected: str) -> None:
    session = _make_session()
    try:
        repo = SkuCodeReadRepository(session)

        with pytest.raises(SkuCodeResolveError) as exc_info:
            repo.resolve_outbound_default_sku_code(
                code=code,
                enabled_only=True,
            )

        assert exc_info.value.code == expected
    finally:
        session.close()
