# tests/api/test_pms_read_stub_semantics.py
from __future__ import annotations

from fastapi.testclient import TestClient

from app.contracts.pms_read import (
    BarcodeProbeOut,
    BarcodeProbeStatus,
    BarcodeQueryOut,
    ItemBasicBatchOut,
    ItemPolicyBatchOut,
    ItemReportMetaBatchOut,
    PmsExportSkuCodeResolution,
    SkuCodeQueryOut,
    UomQueryOut,
)
from app.main import app
from app.repositories.sku_code_read_repo import SkuCodeResolveError
from app.routers.pms_read_v1 import (
    get_barcode_reader,
    get_item_basic_reader,
    get_item_policy_reader,
    get_item_report_meta_reader,
    get_sku_code_reader,
    get_uom_reader,
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


class FakeUomReader:
    def query_uoms(
        self,
        *,
        item_ids: list[int],
        item_uom_ids: list[int],
    ) -> UomQueryOut:
        _ = item_ids
        return UomQueryOut(missing_item_uom_ids=item_uom_ids)


class FakeBarcodeReader:
    def query_barcodes(
        self,
        *,
        item_ids: list[int],
        item_uom_ids: list[int],
        barcode: str | None,
        active: bool | None,
        primary_only: bool,
    ) -> BarcodeQueryOut:
        _ = item_ids
        _ = item_uom_ids
        _ = barcode
        _ = active
        _ = primary_only
        return BarcodeQueryOut()

    def probe_barcode(self, *, barcode: str) -> BarcodeProbeOut:
        return BarcodeProbeOut(
            ok=True,
            status=BarcodeProbeStatus.UNBOUND,
            barcode=barcode.strip(),
        )


class FakeSkuCodeReader:
    def query_sku_codes(
        self,
        *,
        item_ids: list[int],
        sku_code_ids: list[int],
        code: str | None,
        active: bool | None,
        primary_only: bool,
    ) -> SkuCodeQueryOut:
        _ = item_ids
        _ = sku_code_ids
        _ = code
        _ = active
        _ = primary_only
        return SkuCodeQueryOut()

    def resolve_outbound_default_sku_code(
        self,
        *,
        code: str,
        enabled_only: bool,
    ) -> PmsExportSkuCodeResolution:
        _ = code
        _ = enabled_only
        raise SkuCodeResolveError("pms_sku_code_not_found")


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
    assert response.json()["missing_item_ids"] == [2, 3]


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
    assert response.json()["missing_item_ids"] == [4, 5]


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
    assert response.json()["missing_item_ids"] == [8, 9]


def test_report_search_stub_returns_empty_item_ids() -> None:
    client = TestClient(app)

    response = client.get(
        "/pms/read/v1/items/report-search",
        params={"keyword": "SKU001", "limit": 50},
    )

    assert response.status_code == 200
    assert response.json() == {"item_ids": []}


def test_uom_query_cleans_ids_before_reader_dependency() -> None:
    app.dependency_overrides[get_uom_reader] = lambda: FakeUomReader()
    client = TestClient(app)

    try:
        response = client.post(
            "/pms/read/v1/uoms/query",
            json={"item_ids": [2, 1, 1, 0], "item_uom_ids": [11, 10, 10, -1]},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "uoms": [],
        "missing_item_uom_ids": [10, 11],
        "errors": [],
    }


def test_uom_defaults_batch_stub_cleans_ids_and_returns_missing_items() -> None:
    client = TestClient(app)

    response = client.post(
        "/pms/read/v1/items/uom-defaults/batch",
        json={"item_ids": [7, 6, 6, 0], "usage": "OUTBOUND"},
    )

    assert response.status_code == 200
    assert response.json()["missing_item_ids"] == [6, 7]


def test_barcode_query_uses_reader_dependency() -> None:
    app.dependency_overrides[get_barcode_reader] = lambda: FakeBarcodeReader()
    client = TestClient(app)

    try:
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
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "barcodes": [],
        "errors": [],
    }


def test_barcode_probe_uses_reader_dependency() -> None:
    app.dependency_overrides[get_barcode_reader] = lambda: FakeBarcodeReader()
    client = TestClient(app)

    try:
        response = client.post(
            "/pms/read/v1/barcodes/probe",
            json={"barcode": "  6900000000001  "},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "UNBOUND"
    assert response.json()["barcode"] == "6900000000001"


def test_sku_code_query_uses_reader_dependency() -> None:
    app.dependency_overrides[get_sku_code_reader] = lambda: FakeSkuCodeReader()
    client = TestClient(app)

    try:
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
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "sku_codes": [],
        "errors": [],
    }


def test_sku_code_resolve_maps_reader_error() -> None:
    app.dependency_overrides[get_sku_code_reader] = lambda: FakeSkuCodeReader()
    client = TestClient(app)

    try:
        response = client.get(
            "/pms/read/v1/sku-codes/resolve-outbound-default",
            params={"code": "SKU001", "enabled_only": True},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {
        "detail": "pms_sku_code_not_found",
    }
