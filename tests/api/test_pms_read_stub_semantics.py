# tests/api/test_pms_read_stub_semantics.py
from __future__ import annotations

from fastapi.testclient import TestClient

from app.contracts.pms_read import (
    BarcodeProbeOut,
    BarcodeProbeStatus,
    BarcodeQueryOut,
    ItemBasic,
    ItemBasicBatchOut,
    ItemPolicy,
    ItemPolicyBatchOut,
    ItemReportMetaBatchOut,
    PmsExportBarcode,
    PmsExportSkuCode,
    PmsExportSkuCodeResolution,
    PmsExportUom,
    ReportSearchOut,
    SkuCodeQueryOut,
    UomDefaultsBatchOut,
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
from app.pms.system.service_auth.deps import (
    PMS_SERVICE_CLIENT_HEADER,
    get_pms_service_permission_service,
)


class FakePermissionService:
    def is_allowed(self, *, client_code: str | None, capability_code: str | None) -> bool:
        _ = client_code
        _ = capability_code
        return True


def _service_headers() -> dict[str, str]:
    return {PMS_SERVICE_CLIENT_HEADER: "wms-service"}


def _install_permission_override() -> None:
    app.dependency_overrides[get_pms_service_permission_service] = lambda: FakePermissionService()


class FakeItemBasicReader:
    def list_item_basics(self, *, supplier_id=None, keyword=None, enabled=None, limit=50):
        _ = supplier_id
        _ = keyword
        _ = enabled
        _ = limit
        return [ItemBasic(id=1, sku="SKU001", name="商品A")]

    def get_item_basic(self, *, item_id: int):
        return ItemBasic(id=item_id, sku="SKU001", name="商品A") if item_id == 1 else None

    def get_item_basic_batch(self, *, item_ids: list[int], enabled_only: bool):
        _ = enabled_only
        return ItemBasicBatchOut(missing_item_ids=item_ids)


class FakeItemPolicyReader:
    def get_item_policy(self, *, item_id: int):
        if item_id != 1:
            return None
        return ItemPolicy(
            item_id=1,
            expiry_policy="NONE",
            shelf_life_value=None,
            shelf_life_unit=None,
            lot_source_policy="INTERNAL_ONLY",
            derivation_allowed=True,
            uom_governance_enabled=False,
        )

    def get_item_policy_by_sku(self, *, sku: str):
        return self.get_item_policy(item_id=1) if sku == "SKU001" else None

    def get_item_policy_batch(self, *, item_ids: list[int], enabled_only: bool):
        _ = enabled_only
        return ItemPolicyBatchOut(missing_item_ids=item_ids)


class FakeItemReportMetaReader:
    def search_report_item_ids_by_keyword(self, *, keyword: str, limit: int):
        _ = keyword
        _ = limit
        return [1, 2]

    def get_item_report_meta_batch(self, *, item_ids: list[int]):
        return ItemReportMetaBatchOut(missing_item_ids=item_ids)


class FakeUomReader:
    def get_uom(self, *, item_uom_id: int):
        if item_uom_id != 7:
            return None
        return PmsExportUom(
            id=7,
            item_id=1,
            uom="PCS",
            display_name="件",
            uom_name="件",
            ratio_to_base=1,
            net_weight_kg=None,
            is_base=True,
            is_purchase_default=True,
            is_inbound_default=True,
            is_outbound_default=True,
        )

    def query_uoms(self, *, item_ids: list[int], item_uom_ids: list[int]):
        _ = item_ids
        return UomQueryOut(missing_item_uom_ids=item_uom_ids)

    def get_default_or_base_batch(self, *, item_ids: list[int], usage: str):
        _ = usage
        return UomDefaultsBatchOut(missing_item_ids=item_ids)


class FakeBarcodeReader:
    def get_barcode(self, *, barcode_id: int):
        if barcode_id != 2:
            return None
        return PmsExportBarcode(
            id=2,
            item_id=1,
            item_uom_id=7,
            barcode="BC1",
            symbology="CUSTOM",
            active=True,
            is_primary=True,
            uom="PCS",
            display_name="件",
            uom_name="件",
            ratio_to_base=1,
        )

    def query_barcodes(
        self,
        *,
        item_ids: list[int],
        item_uom_ids: list[int],
        barcode: str | None,
        active: bool | None,
        primary_only: bool,
    ):
        _ = item_ids
        _ = item_uom_ids
        _ = barcode
        _ = active
        _ = primary_only
        return BarcodeQueryOut()

    def probe_barcode(self, *, barcode: str):
        return BarcodeProbeOut(
            ok=True,
            status=BarcodeProbeStatus.UNBOUND,
            barcode=barcode.strip(),
        )


class FakeSkuCodeReader:
    def get_sku_code(self, *, sku_code_id: int):
        if sku_code_id != 10:
            return None
        return PmsExportSkuCode(
            id=10,
            item_id=1,
            code="SKU001",
            code_type="PRIMARY",
            is_primary=True,
            is_active=True,
            item_sku="SKU001",
            item_name="商品A",
            item_enabled=True,
        )

    def query_sku_codes(
        self,
        *,
        item_ids: list[int],
        sku_code_ids: list[int],
        code: str | None,
        active: bool | None,
        primary_only: bool,
    ):
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
    ):
        _ = enabled_only
        if code == "MISSING":
            raise SkuCodeResolveError("pms_sku_code_not_found")
        return PmsExportSkuCodeResolution(
            sku_code_id=10,
            item_id=1,
            sku_code=code,
            code_type="PRIMARY",
            is_primary=True,
            item_sku="SKU001",
            item_name="商品A",
            item_uom_id=7,
            uom="PCS",
            display_name="件",
            uom_name="件",
            ratio_to_base=1,
        )


def test_batch_endpoints_clean_ids_before_reader_dependency() -> None:
    _install_permission_override()
    app.dependency_overrides[get_item_basic_reader] = lambda: FakeItemBasicReader()
    app.dependency_overrides[get_item_policy_reader] = lambda: FakeItemPolicyReader()
    app.dependency_overrides[get_item_report_meta_reader] = lambda: FakeItemReportMetaReader()
    client = TestClient(app)

    try:
        assert client.post(
            "/pms/read/v1/items/basic/batch",
            json={"item_ids": [3, 2, 2, 0]},
            headers=_service_headers(),
        ).json()["missing_item_ids"] == [2, 3]

        assert client.post(
            "/pms/read/v1/items/policies/batch",
            json={"item_ids": [5, 4, 4, 0]},
            headers=_service_headers(),
        ).json()["missing_item_ids"] == [4, 5]

        assert client.post(
            "/pms/read/v1/items/report-meta/batch",
            json={"item_ids": [9, 8, 8, 0]},
            headers=_service_headers(),
        ).json()["missing_item_ids"] == [8, 9]
    finally:
        app.dependency_overrides.clear()


def test_single_item_policy_and_search_endpoints_use_reader_dependency() -> None:
    _install_permission_override()
    app.dependency_overrides[get_item_basic_reader] = lambda: FakeItemBasicReader()
    app.dependency_overrides[get_item_policy_reader] = lambda: FakeItemPolicyReader()
    app.dependency_overrides[get_item_report_meta_reader] = lambda: FakeItemReportMetaReader()
    client = TestClient(app)

    try:
        assert client.get(
            "/pms/read/v1/items/basic",
            headers=_service_headers(),
        ).status_code == 200
        assert client.get(
            "/pms/read/v1/items/basic/1",
            headers=_service_headers(),
        ).json()["id"] == 1
        assert client.get(
            "/pms/read/v1/items/basic/999",
            headers=_service_headers(),
        ).status_code == 404
        assert client.get(
            "/pms/read/v1/items/1/policy",
            headers=_service_headers(),
        ).json()["item_id"] == 1
        assert client.get(
            "/pms/read/v1/items/999/policy",
            headers=_service_headers(),
        ).status_code == 404
        assert client.get(
            "/pms/read/v1/items/policy-by-sku",
            params={"sku": "SKU001"},
            headers=_service_headers(),
        ).json()["item_id"] == 1
        assert client.get(
            "/pms/read/v1/items/report-search",
            params={"keyword": "SKU", "limit": 50},
            headers=_service_headers(),
        ).json() == ReportSearchOut(item_ids=[1, 2]).model_dump()
    finally:
        app.dependency_overrides.clear()


def test_uom_barcode_and_sku_code_compat_endpoints_use_reader_dependency() -> None:
    _install_permission_override()
    app.dependency_overrides[get_uom_reader] = lambda: FakeUomReader()
    app.dependency_overrides[get_barcode_reader] = lambda: FakeBarcodeReader()
    app.dependency_overrides[get_sku_code_reader] = lambda: FakeSkuCodeReader()
    client = TestClient(app)

    try:
        assert client.get(
            "/pms/read/v1/uoms/7",
            headers=_service_headers(),
        ).json()["id"] == 7
        assert client.get(
            "/pms/read/v1/uoms/999",
            headers=_service_headers(),
        ).status_code == 404
        assert client.get(
            "/pms/read/v1/items/1/uoms",
            headers=_service_headers(),
        ).json() == []
        assert client.post(
            "/pms/read/v1/uoms/query",
            json={"item_ids": [1], "item_uom_ids": [10]},
            headers=_service_headers(),
        ).json()["missing_item_uom_ids"] == [10]
        assert client.post(
            "/pms/read/v1/items/uom-defaults/batch",
            json={"item_ids": [1, 0], "usage": "OUTBOUND"},
            headers=_service_headers(),
        ).json()["missing_item_ids"] == [1]

        assert client.get(
            "/pms/read/v1/barcodes/2",
            headers=_service_headers(),
        ).json()["id"] == 2
        assert client.get(
            "/pms/read/v1/barcodes/999",
            headers=_service_headers(),
        ).status_code == 404
        assert client.get(
            "/pms/read/v1/items/1/barcodes",
            headers=_service_headers(),
        ).json() == []
        assert client.post(
            "/pms/read/v1/barcodes/probe",
            json={"barcode": " BC1 "},
            headers=_service_headers(),
        ).json()["barcode"] == "BC1"

        assert client.get(
            "/pms/read/v1/sku-codes/10",
            headers=_service_headers(),
        ).json()["id"] == 10
        assert client.get(
            "/pms/read/v1/sku-codes/999",
            headers=_service_headers(),
        ).status_code == 404
        assert client.get(
            "/pms/read/v1/items/1/sku-codes",
            headers=_service_headers(),
        ).json() == []
        assert client.post(
            "/pms/read/v1/sku-codes/query",
            json={"item_ids": [1], "sku_code_ids": [10]},
            headers=_service_headers(),
        ).json()["sku_codes"] == []
        assert client.get(
            "/pms/read/v1/sku-codes/resolve-outbound-default",
            params={"code": "SKU001"},
            headers=_service_headers(),
        ).json()["sku_code"] == "SKU001"
        assert client.get(
            "/pms/read/v1/sku-codes/resolve-outbound-default",
            params={"code": "MISSING"},
            headers=_service_headers(),
        ).status_code == 404
    finally:
        app.dependency_overrides.clear()
