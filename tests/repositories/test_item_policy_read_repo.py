# tests/repositories/test_item_policy_read_repo.py
from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.repositories.item_policy_read_repo import ItemPolicyReadRepository


def _make_session() -> Session:
    engine = create_engine("sqlite:///:memory:")

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE items (
                  id INTEGER PRIMARY KEY,
                  enabled BOOLEAN NOT NULL,
                  expiry_policy VARCHAR(16) NOT NULL,
                  shelf_life_value INTEGER,
                  shelf_life_unit VARCHAR(16),
                  lot_source_policy VARCHAR(32) NOT NULL,
                  derivation_allowed BOOLEAN NOT NULL,
                  uom_governance_enabled BOOLEAN NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO items (
                  id,
                  enabled,
                  expiry_policy,
                  shelf_life_value,
                  shelf_life_unit,
                  lot_source_policy,
                  derivation_allowed,
                  uom_governance_enabled
                )
                VALUES
                  (1, 1, 'REQUIRED', 12, 'MONTH', 'SUPPLIER_ONLY', 1, 1),
                  (2, 0, 'NONE', NULL, NULL, 'INTERNAL_ONLY', 0, 1)
                """
            )
        )

    return Session(engine)


def test_item_policy_repository_reads_policy_fields() -> None:
    session = _make_session()
    try:
        repo = ItemPolicyReadRepository(session)

        result = repo.get_item_policy_batch(
            item_ids=[999, 2, 1, 1],
            enabled_only=False,
        )

        assert sorted(result.policies_by_item_id) == [1, 2]
        assert result.missing_item_ids == [999]
        assert result.inactive_item_ids == []

        policy = result.policies_by_item_id[1]
        assert policy.item_id == 1
        assert policy.expiry_policy == "REQUIRED"
        assert policy.shelf_life_value == 12
        assert policy.shelf_life_unit == "MONTH"
        assert policy.lot_source_policy == "SUPPLIER_ONLY"
        assert policy.derivation_allowed is True
        assert policy.uom_governance_enabled is True

        disabled_policy = result.policies_by_item_id[2]
        assert disabled_policy.item_id == 2
        assert disabled_policy.expiry_policy == "NONE"
        assert disabled_policy.shelf_life_value is None
        assert disabled_policy.shelf_life_unit is None
        assert disabled_policy.lot_source_policy == "INTERNAL_ONLY"
        assert disabled_policy.derivation_allowed is False
        assert disabled_policy.uom_governance_enabled is True
    finally:
        session.close()


def test_item_policy_repository_reports_inactive_when_enabled_only() -> None:
    session = _make_session()
    try:
        repo = ItemPolicyReadRepository(session)

        result = repo.get_item_policy_batch(
            item_ids=[1, 2, 3],
            enabled_only=True,
        )

        assert sorted(result.policies_by_item_id) == [1]
        assert result.missing_item_ids == [3]
        assert result.inactive_item_ids == [2]
    finally:
        session.close()
