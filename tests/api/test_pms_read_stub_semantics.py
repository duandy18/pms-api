# tests/api/test_pms_read_stub_semantics.py
from __future__ import annotations

from fastapi.testclient import TestClient

from app.contracts.pms_read import (
    ItemBasicBatchOut,
    ItemPolicyBatchOut,
    ItemReportMetaBatchOut,
)
from app.main import app
from app.routers.pms_read_v1 import (
    get_item_basic_reader,
    get_item_policy_reader,
    get_item_report_meta_reader,
)


class FakeItemBasicReader:
    def get_item_basic_batch(
        self,
        *,
        item_ids: list[int],
        enabled_only: bool,
    ) -> ItemBasicBatchOut:
        _ = enabled_only
        return ItemBasicBatchOut(missing_item_ids=item_ids)


class FakeItemPolicyReader:
    def get_item_policy_batch(
        self,
        *,
        item_ids: list[int],
        enabled_only: bool,
    ) -> ItemPolicyBatchOut:
        _ = enabled_only
        return ItemPolicyBatchOut(missing_item_ids=item_ids)


class FakeItemReportMetaReader:
    def get_item_report_meta_batch(
        self,
        *,
        item_ids: list[int],
    ) -> ItemReportMetaBatchOut:
        return ItemReportMetaBatchOut(missing_item_ids=item_ids)


def test_item_basic_batch_cleans_ids_before_reader_dependency() -> None:
    app.dependency_overrides[get_item_basic_reader] = lambda: FakeItemBasicReader()
    client = TestClient(app)

    try:
        response = client.post(
            "/pms/read/v1/items/basic/batch",
            json={"item_ids": [3, 2, 2, 0, -1], "enabled_only": True},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "items_by_id": {},
        "missing_item_ids": [2, 3],
        "inactive_item_ids": [],
        "errors": [],
    }


def test_item_policy_batch_cleans_ids_before_reader_dependency() -> None:
    app.dependency_overrides[get_item_policy_reader] = lambda: FakeItemPolicyReader()
    client = TestClient(app)

    try:
        response = client.post(
            "/pms/read/v1/items/policies/batch",
            json={"item_ids": [5, 4, 5, 0], "enabled_only": False},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "policies_by_item_id": {},
        "missing_item_ids": [4, 5],
        "inactive_item_ids": [],
        "errors": [],
    }


def test_item_report_meta_batch_cleans_ids_before_reader_dependency() -> None:
    app.dependency_overrides[get_item_report_meta_reader] = lambda: FakeItemReportMetaReader()
    client = TestClient(app)

    try:
        response = client.post(
            "/pms/read/v1/items/report-meta/batch",
            json={"item_ids": [9, 8, 8, -2], "enabled_only": False},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "meta_by_item_id": {},
        "missing_item_ids": [8, 9],
        "errors": [],
    }


def test_report_search_stub_returns_empty_item_ids() -> None:
    client = TestClient(app)

    response = client.get(
        "/pms/read/v1/items/report-search",
        params={"keyword": "SKU001", "limit": 50},
    )

    assert response.status_code == 200
    assert response.json() == {"item_ids": []}


def test_uom_query_stub_returns_empty_list() -> None:
    client = TestClient(app)

    response = client.post(
        "/pms/read/v1/uoms/query",
        json={"item_ids": [1, 2], "item_uom_ids": [10, 11]},
    )

    assert response.status_code == 200
    assert response.json() == {
        "uoms": [],
        "missing_item_uom_ids": [],
        "errors": [],
    }


def test_uom_defaults_batch_stub_cleans_ids_and_returns_missing_items() -> None:
    client = TestClient(app)

    response = client.post(
        "/pms/read/v1/items/uom-defaults/batch",
        json={"item_ids": [7, 6, 6, 0], "usage": "OUTBOUND"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "uoms_by_item_id": {},
        "missing_item_ids": [6, 7],
        "missing_default_uom_item_ids": [],
        "errors": [],
    }


def test_barcode_query_stub_returns_empty_list() -> None:
    client = TestClient(app)

    response = client.post(
        "/pms/read/v1/barcodes/query",
        json={
            "item_ids": [1],
            "item_uom_ids": [10],
            "barcode": "6900000000001",
            "active": True,
            "primary_only": False,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "barcodes": [],
        "errors": [],
    }


def test_barcode_probe_stub_trims_and_returns_unbound() -> None:
    client = TestClient(app)

    response = client.post(
        "/pms/read/v1/barcodes/probe",
        json={"barcode": "  6900000000001  "},
    )

    assert response.status_code == 200
    assert response.json() == {
        "ok": True,
        "status": "UNBOUND",
        "barcode": "6900000000001",
        "item_id": None,
        "item_uom_id": None,
        "ratio_to_base": None,
        "symbology": None,
        "active": None,
        "item_basic": None,
        "errors": [],
    }


def test_sku_code_query_stub_returns_empty_list() -> None:
    client = TestClient(app)

    response = client.post(
        "/pms/read/v1/sku-codes/query",
        json={
            "item_ids": [1],
            "sku_code_ids": [10],
            "code": "SKU001",
            "active": True,
            "primary_only": False,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "sku_codes": [],
        "errors": [],
    }


def test_sku_code_resolve_stub_returns_501_until_database_is_connected() -> None:
    client = TestClient(app)

    response = client.get(
        "/pms/read/v1/sku-codes/resolve-outbound-default",
        params={"code": "SKU001", "enabled_only": True},
    )

    assert response.status_code == 501
    assert response.json() == {
        "detail": "pms_read_sku_code_resolution_not_implemented",
    }
