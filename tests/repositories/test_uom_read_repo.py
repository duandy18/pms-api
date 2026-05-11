# tests/repositories/test_uom_read_repo.py
from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.repositories.uom_read_repo import UomReadRepository


def _make_session() -> Session:
    engine = create_engine("sqlite:///:memory:")

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE item_uoms (
                  id INTEGER PRIMARY KEY,
                  item_id INTEGER NOT NULL,
                  uom VARCHAR(16) NOT NULL,
                  display_name VARCHAR(32),
                  ratio_to_base INTEGER NOT NULL,
                  net_weight_kg NUMERIC,
                  is_base BOOLEAN NOT NULL,
                  is_purchase_default BOOLEAN NOT NULL,
                  is_inbound_default BOOLEAN NOT NULL,
                  is_outbound_default BOOLEAN NOT NULL,
                  updated_at TIMESTAMP NOT NULL
                )
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
                  net_weight_kg,
                  is_base,
                  is_purchase_default,
                  is_inbound_default,
                  is_outbound_default,
                  updated_at
                )
                VALUES
                  (10, 1, 'PCS', '件', 1, 0.500, 1, 0, 1, 1, '2026-01-01 00:00:00'),
                  (11, 1, 'BOX', NULL, 12, NULL, 0, 1, 0, 0, '2026-01-02 00:00:00'),
                  (20, 2, 'BAG', '袋', 6, 1.250, 0, 0, 0, 1, '2026-01-03 00:00:00')
                """
            )
        )

    return Session(engine)


def test_uom_repository_queries_by_item_ids() -> None:
    session = _make_session()
    try:
        repo = UomReadRepository(session)

        result = repo.query_uoms(item_ids=[1], item_uom_ids=[])

        assert [row.id for row in result.uoms] == [10, 11]
        assert result.missing_item_uom_ids == []

        base = result.uoms[0]
        assert base.item_id == 1
        assert base.uom == "PCS"
        assert base.display_name == "件"
        assert base.uom_name == "件"
        assert base.ratio_to_base == 1
        assert base.net_weight_kg == 0.5
        assert base.is_base is True
        assert base.is_inbound_default is True
        assert base.is_outbound_default is True

        box = result.uoms[1]
        assert box.uom_name == "BOX"
        assert box.net_weight_kg is None
    finally:
        session.close()


def test_uom_repository_projection_feed_is_paginated() -> None:
    session = _make_session()
    try:
        repo = UomReadRepository(session)

        rows = repo.list_projection_feed(limit=2, offset=1)

        assert [row.item_uom_id for row in rows] == [11, 20]
        assert rows[0].item_id == 1
        assert rows[0].uom == "BOX"
        assert rows[0].uom_name == "BOX"
        assert rows[0].ratio_to_base == 12
        assert rows[0].pms_updated_at is not None
    finally:
        session.close()


def test_uom_repository_queries_by_uom_ids_and_reports_missing() -> None:
    session = _make_session()
    try:
        repo = UomReadRepository(session)

        result = repo.query_uoms(item_ids=[], item_uom_ids=[999, 20, 20])

        assert [row.id for row in result.uoms] == [20]
        assert result.missing_item_uom_ids == [999]
    finally:
        session.close()
