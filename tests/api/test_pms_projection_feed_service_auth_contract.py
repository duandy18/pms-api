# tests/api/test_pms_projection_feed_service_auth_contract.py
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.pms.suppliers.routers.suppliers_projection_feed import (
    get_supplier_read_service,
)
from app.routers.pms_read_v1 import (
    get_barcode_reader,
    get_item_basic_reader,
    get_sku_code_reader,
    get_uom_reader,
)
from app.pms.system.service_auth.deps import (
    PMS_SERVICE_CLIENT_HEADER,
    get_pms_service_permission_service,
)


class FakeProjectionReader:
    def list_projection_feed(self, *, limit: int, offset: int) -> list[object]:
        _ = limit
        _ = offset
        return []


class FakeSupplierProjectionService:
    def list_projection_feed(self, *, limit: int, offset: int) -> list[object]:
        _ = limit
        _ = offset
        return []


class FakePermissionService:
    def __init__(self, *, allowed: bool) -> None:
        self.allowed = allowed
        self.calls: list[tuple[str | None, str | None]] = []

    def is_allowed(self, *, client_code: str | None, capability_code: str | None) -> bool:
        self.calls.append((client_code, capability_code))
        return self.allowed


def _override_projection_readers() -> None:
    app.dependency_overrides[get_item_basic_reader] = lambda: FakeProjectionReader()
    app.dependency_overrides[get_uom_reader] = lambda: FakeProjectionReader()
    app.dependency_overrides[get_sku_code_reader] = lambda: FakeProjectionReader()
    app.dependency_overrides[get_barcode_reader] = lambda: FakeProjectionReader()
    app.dependency_overrides[get_supplier_read_service] = lambda: FakeSupplierProjectionService()


def test_projection_feed_routes_require_service_permissions_and_keep_capabilities_fixed() -> None:
    permission_service = FakePermissionService(allowed=True)
    _override_projection_readers()
    app.dependency_overrides[get_pms_service_permission_service] = lambda: permission_service
    client = TestClient(app)

    expected = [
        ("/pms/read/v1/projection-feed/items", "pms.read.items"),
        ("/pms/read/v1/projection-feed/uoms", "pms.read.uoms"),
        ("/pms/read/v1/projection-feed/sku-codes", "pms.read.sku_codes"),
        ("/pms/read/v1/projection-feed/barcodes", "pms.read.barcodes"),
        ("/pms/read/v1/projection-feed/suppliers", "pms.read.suppliers"),
    ]

    try:
        for path, _capability_code in expected:
            response = client.get(path, headers={PMS_SERVICE_CLIENT_HEADER: "wms-service"})
            assert response.status_code == 200
            assert response.json()["rows"] == []
    finally:
        app.dependency_overrides.clear()

    assert permission_service.calls == [
        ("wms-service", capability_code) for _path, capability_code in expected
    ]


def test_projection_feed_route_rejects_missing_service_client_header() -> None:
    permission_service = FakePermissionService(allowed=True)
    _override_projection_readers()
    app.dependency_overrides[get_pms_service_permission_service] = lambda: permission_service
    client = TestClient(app)

    try:
        response = client.get("/pms/read/v1/projection-feed/items")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 401
    assert response.json()["detail"] == "pms_service_client_required"
    assert permission_service.calls == []


def test_projection_feed_route_rejects_denied_service_permission() -> None:
    permission_service = FakePermissionService(allowed=False)
    _override_projection_readers()
    app.dependency_overrides[get_pms_service_permission_service] = lambda: permission_service
    client = TestClient(app)

    try:
        response = client.get(
            "/pms/read/v1/projection-feed/suppliers",
            headers={PMS_SERVICE_CLIENT_HEADER: "wms-service"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["detail"] == "pms_service_permission_denied"
    assert permission_service.calls == [("wms-service", "pms.read.suppliers")]


def test_non_projection_read_v1_routes_are_not_service_permission_gated_yet() -> None:
    paths = {
        str(getattr(route, "path", ""))
        for route in app.routes
        if isinstance(getattr(route, "path", ""), str)
    }

    assert "/pms/read/v1/items/basic" in paths
    assert "/pms/read/v1/items/basic/{item_id}" in paths
    assert "/pms/read/v1/items/basic/batch" in paths
