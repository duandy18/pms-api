# tests/api/test_pms_read_contracts.py
from __future__ import annotations

from fastapi.testclient import TestClient

from app.contracts.pms_read import (
    BarcodeProbeOut,
    BarcodeProbeStatus,
    BarcodeQueryOut,
    ItemBasic,
    ItemBasicBatchOut,
    ItemPolicy,
    PmsExportSkuCodeResolution,
    PmsProjectionItemFeedOut,
    PmsProjectionItemFeedRow,
)
from app.main import app
from app.routers.pms_read_v1 import get_barcode_reader, get_item_basic_reader
from app.service_auth.deps import (
    PMS_SERVICE_CLIENT_HEADER,
    get_pms_service_permission_service,
)


class FakePermissionService:
    def is_allowed(self, *, client_code: str | None, capability_code: str | None) -> bool:
        _ = client_code
        _ = capability_code
        return True


class FakeItemBasicReader:
    def get_item_basic_batch(
        self,
        *,
        item_ids: list[int],
        enabled_only: bool,
    ) -> ItemBasicBatchOut:
        _ = enabled_only
        return ItemBasicBatchOut(missing_item_ids=item_ids)


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


def _service_headers() -> dict[str, str]:
    return {PMS_SERVICE_CLIENT_HEADER: "wms-service"}


def test_contract_models_validate_current_read_shapes() -> None:
    item = ItemBasic(
        id=1,
        sku="SKU001",
        name="商品A",
        spec=None,
        enabled=True,
        supplier_id=None,
        brand=None,
        category=None,
    )
    assert item.id == 1
    assert item.sku == "SKU001"

    policy = ItemPolicy(
        item_id=1,
        expiry_policy="REQUIRED",
        shelf_life_value=12,
        shelf_life_unit="MONTH",
        lot_source_policy="SUPPLIER_ONLY",
        derivation_allowed=True,
        uom_governance_enabled=True,
    )
    assert policy.item_id == 1
    assert policy.expiry_policy == "REQUIRED"

    resolution = PmsExportSkuCodeResolution(
        sku_code_id=10,
        item_id=1,
        sku_code="SKU001",
        code_type="PRIMARY",
        is_primary=True,
        item_sku="SKU001",
        item_name="商品A",
        item_uom_id=20,
        uom="PCS",
        display_name="件",
        uom_name="件",
        ratio_to_base=1,
    )
    assert resolution.item_uom_id == 20

    feed = PmsProjectionItemFeedOut(
        rows=[
            PmsProjectionItemFeedRow(
                item_id=1,
                sku="SKU001",
                name="商品A",
                spec=None,
                enabled=True,
                supplier_id=None,
                brand=None,
                category=None,
                expiry_policy="NONE",
                shelf_life_value=None,
                shelf_life_unit=None,
                lot_source_policy="INTERNAL_ONLY",
                derivation_allowed=True,
                uom_governance_enabled=False,
                pms_updated_at="2026-01-01T00:00:00Z",
            )
        ],
        limit=500,
        offset=0,
        next_offset=None,
        has_more=False,
    )
    assert feed.rows[0].item_id == 1


def test_read_v1_routes_are_mounted() -> None:
    paths = {
        str(getattr(route, "path", ""))
        for route in app.routes
        if isinstance(getattr(route, "path", ""), str)
    }

    assert "/pms/read/v1/health" in paths
    assert "/pms/read/v1/projection-feed/items" in paths
    assert "/pms/read/v1/projection-feed/uoms" in paths
    assert "/pms/read/v1/projection-feed/sku-codes" in paths
    assert "/pms/read/v1/projection-feed/barcodes" in paths
    assert "/pms/read/v1/items/basic/batch" in paths
    assert "/pms/read/v1/items/policies/batch" in paths
    assert "/pms/read/v1/items/report-search" in paths
    assert "/pms/read/v1/items/report-meta/batch" in paths
    assert "/pms/read/v1/uoms/query" in paths
    assert "/pms/read/v1/items/uom-defaults/batch" in paths
    assert "/pms/read/v1/barcodes/query" in paths
    assert "/pms/read/v1/barcodes/probe" in paths
    assert "/pms/read/v1/sku-codes/query" in paths
    assert "/pms/read/v1/sku-codes/resolve-outbound-default" in paths


def test_batch_item_basic_endpoint_uses_reader_dependency() -> None:
    app.dependency_overrides[get_item_basic_reader] = lambda: FakeItemBasicReader()
    app.dependency_overrides[get_pms_service_permission_service] = lambda: FakePermissionService()
    client = TestClient(app)

    try:
        response = client.post(
            "/pms/read/v1/items/basic/batch",
            json={"item_ids": [2, 1, 1], "enabled_only": True},
            headers=_service_headers(),
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "items_by_id": {},
        "missing_item_ids": [1, 2],
        "inactive_item_ids": [],
        "errors": [],
    }


def test_barcode_probe_stub_returns_unbound() -> None:
    app.dependency_overrides[get_barcode_reader] = lambda: FakeBarcodeReader()
    app.dependency_overrides[get_pms_service_permission_service] = lambda: FakePermissionService()
    client = TestClient(app)

    try:
        response = client.post(
            "/pms/read/v1/barcodes/probe",
            json={"barcode": "6900000000001"},
            headers=_service_headers(),
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "UNBOUND"
    assert response.json()["barcode"] == "6900000000001"
