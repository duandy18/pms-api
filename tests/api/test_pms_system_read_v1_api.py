# tests/api/test_pms_system_read_v1_api.py
from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.deps import get_db
from app.main import app
from app.pms.system.service_auth.models import (
    PmsServiceCapability,
    PmsServiceCapabilityRoute,
)
from app.user.models.page_registry import PageRegistry
from app.user.models.page_route_prefix import PageRoutePrefix
from app.user.models.permission import Permission


def _by_code(rows: list[dict], key: str) -> dict[str, dict]:
    return {str(row[key]): row for row in rows}


def _make_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _register_sqlite_functions(dbapi_connection, _connection_record) -> None:
        dbapi_connection.create_function(
            "btrim",
            1,
            lambda value: "" if value is None else str(value).strip(),
        )

    Permission.__table__.create(bind=engine, checkfirst=True)
    PageRegistry.__table__.create(bind=engine, checkfirst=True)
    PageRoutePrefix.__table__.create(bind=engine, checkfirst=True)
    PmsServiceCapability.__table__.create(bind=engine, checkfirst=True)
    PmsServiceCapabilityRoute.__table__.create(bind=engine, checkfirst=True)

    return engine


def _seed_pages(db: Session) -> None:
    read_permission = Permission(name="page.pms.read")
    write_permission = Permission(name="page.pms.write")
    db.add_all([read_permission, write_permission])
    db.flush()

    db.add_all(
        [
            PageRegistry(
                code="pms",
                name="商品管理",
                parent_code=None,
                level=1,
                domain_code="pms",
                show_in_topbar=True,
                show_in_sidebar=True,
                sort_order=10,
                is_active=True,
                inherit_permissions=False,
                read_permission_id=read_permission.id,
                write_permission_id=write_permission.id,
            ),
            PageRegistry(
                code="pms.items",
                name="商品资料",
                parent_code="pms",
                level=2,
                domain_code="pms",
                show_in_topbar=False,
                show_in_sidebar=True,
                sort_order=10,
                is_active=True,
                inherit_permissions=True,
                read_permission_id=None,
                write_permission_id=None,
            ),
            PageRegistry(
                code="pms.items.list",
                name="商品列表",
                parent_code="pms.items",
                level=3,
                domain_code="pms",
                show_in_topbar=False,
                show_in_sidebar=True,
                sort_order=10,
                is_active=True,
                inherit_permissions=True,
                read_permission_id=None,
                write_permission_id=None,
            ),
        ]
    )
    db.flush()

    db.add(
        PageRoutePrefix(
            page_code="pms.items.list",
            route_prefix="/items",
            sort_order=10,
            is_active=True,
        )
    )


def _seed_capabilities(db: Session) -> None:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)

    capabilities = [
        PmsServiceCapability(
            capability_code="pms.read.health",
            capability_name="Read PMS health",
            resource_code="health",
            description="PMS read-v1 health check",
            is_active=True,
            created_at=now,
            updated_at=now,
        ),
        PmsServiceCapability(
            capability_code="pms.read.items",
            capability_name="Read PMS items",
            resource_code="items",
            description="读取 PMS 商品能力",
            is_active=True,
            created_at=now,
            updated_at=now,
        ),
        PmsServiceCapability(
            capability_code="pms.read.uoms",
            capability_name="Read PMS UOMs",
            resource_code="uoms",
            description="读取 PMS 包装单位能力",
            is_active=True,
            created_at=now,
            updated_at=now,
        ),
        PmsServiceCapability(
            capability_code="pms.read.sku_codes",
            capability_name="Read PMS SKU codes",
            resource_code="sku_codes",
            description="读取 PMS SKU 编码能力",
            is_active=True,
            created_at=now,
            updated_at=now,
        ),
        PmsServiceCapability(
            capability_code="pms.read.barcodes",
            capability_name="Read PMS barcodes",
            resource_code="barcodes",
            description="读取 PMS 条码能力",
            is_active=True,
            created_at=now,
            updated_at=now,
        ),
        PmsServiceCapability(
            capability_code="pms.read.suppliers",
            capability_name="Read PMS suppliers",
            resource_code="suppliers",
            description="读取 PMS 供应商能力",
            is_active=True,
            created_at=now,
            updated_at=now,
        ),
    ]
    db.add_all(capabilities)
    db.flush()

    db.add_all(
        [
            PmsServiceCapabilityRoute(
                capability_code="pms.read.health",
                http_method="GET",
                route_path="/pms/read/v1/health",
                route_name="read_v1_health",
                auth_required=False,
                is_active=True,
                created_at=now,
            ),
            PmsServiceCapabilityRoute(
                capability_code="pms.read.items",
                http_method="GET",
                route_path="/pms/read/v1/projection-feed/items",
                route_name="projection_feed_items",
                auth_required=True,
                is_active=True,
                created_at=now,
            ),
            PmsServiceCapabilityRoute(
                capability_code="pms.read.items",
                http_method="GET",
                route_path="/pms/read/v1/items/basic",
                route_name="list_item_basics",
                auth_required=True,
                is_active=True,
                created_at=now,
            ),
            PmsServiceCapabilityRoute(
                capability_code="pms.read.items",
                http_method="POST",
                route_path="/pms/read/v1/items/basic/batch",
                route_name="batch_item_basics",
                auth_required=True,
                is_active=True,
                created_at=now,
            ),
            PmsServiceCapabilityRoute(
                capability_code="pms.read.uoms",
                http_method="POST",
                route_path="/pms/read/v1/uoms/query",
                route_name="query_uoms",
                auth_required=True,
                is_active=True,
                created_at=now,
            ),
            PmsServiceCapabilityRoute(
                capability_code="pms.read.sku_codes",
                http_method="POST",
                route_path="/pms/read/v1/sku-codes/query",
                route_name="query_sku_codes",
                auth_required=True,
                is_active=True,
                created_at=now,
            ),
            PmsServiceCapabilityRoute(
                capability_code="pms.read.barcodes",
                http_method="POST",
                route_path="/pms/read/v1/barcodes/query",
                route_name="query_barcodes",
                auth_required=True,
                is_active=True,
                created_at=now,
            ),
            PmsServiceCapabilityRoute(
                capability_code="pms.read.suppliers",
                http_method="GET",
                route_path="/pms/read/v1/suppliers",
                route_name="list_read_suppliers",
                auth_required=True,
                is_active=True,
                created_at=now,
            ),
        ]
    )


def _seed_db(db: Session) -> None:
    _seed_pages(db)
    _seed_capabilities(db)
    db.commit()


@pytest.fixture()
def client_with_system_db() -> Generator[TestClient, None, None]:
    engine = _make_engine()
    session_factory = sessionmaker(bind=engine)

    with session_factory() as seed_session:
        _seed_db(seed_session)

    def override_get_db() -> Generator[Session, None, None]:
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_db, None)
        engine.dispose()


def test_pms_api_service_name_is_pms_api() -> None:
    client = TestClient(app)

    root_response = client.get("/")
    assert root_response.status_code == 200, root_response.text
    assert root_response.json()["name"] == "pms-api"
    assert root_response.json()["version"] == "0.1.0"

    openapi_response = client.get("/openapi.json")
    assert openapi_response.status_code == 200, openapi_response.text
    assert openapi_response.json()["info"]["title"] == "pms-api"
    assert openapi_response.json()["info"]["version"] == "0.1.0"


def test_pms_system_app_manifest_returns_self_description_defaults() -> None:
    client = TestClient(app)

    response = client.get("/system/read/v1/app-manifest")

    assert response.status_code == 200, response.text
    body = response.json()

    assert body["app_code"] == "pms"
    assert body["app_name"] == "商品管理"
    assert body["app_type"] == "business_system"
    assert body["status"] == "available"
    assert body["default_web_path"] == "/pms/"
    assert body["default_api_path"] == "/api/pms"
    assert body["local_web_url"] == "http://127.0.0.1:5174"
    assert body["local_api_url"] == "http://127.0.0.1:8005"
    assert body["health_url"] == "/healthz"
    assert body["db_health_url"] == "/health/db"
    assert body["openapi_url"] == "/openapi.json"
    assert body["page_catalog_url"] == "/system/read/v1/page-catalog"
    assert body["service_capabilities_url"] == "/system/read/v1/service-capabilities"
    assert body["service_dependencies_url"] == "/system/read/v1/service-dependencies"
    assert body["version"] == "0.1.0"

    assert "is_active" not in body
    assert "is_visible" not in body
    assert "is_published" not in body


def test_pms_system_page_catalog_returns_standard_catalog(
    client_with_system_db: TestClient,
) -> None:
    response = client_with_system_db.get("/system/read/v1/page-catalog")

    assert response.status_code == 200, response.text
    body = response.json()

    assert body["app_code"] == "pms"
    assert body["app_name"] == "商品管理"

    pages = body["pages"]
    assert isinstance(pages, list)
    assert pages

    by_code = _by_code(pages, "page_code")
    assert "pms" in by_code
    assert "pms.items.list" in by_code

    root = by_code["pms"]
    assert root["parent_page_code"] is None
    assert root["level"] == 1
    assert root["read_permission_code"] == "page.pms.read"
    assert root["write_permission_code"] == "page.pms.write"
    assert root["source_updated_at"] is None

    item_list = by_code["pms.items.list"]
    assert item_list["parent_page_code"] == "pms.items"
    assert item_list["level"] == 3
    assert item_list["route_path"] == "/items"
    assert item_list["read_permission_code"] == "page.pms.read"
    assert item_list["write_permission_code"] == "page.pms.write"

    required_keys = {
        "page_code",
        "page_name",
        "route_path",
        "parent_page_code",
        "level",
        "read_permission_code",
        "write_permission_code",
        "is_active",
        "sort_order",
        "source_updated_at",
    }
    for page in pages:
        assert required_keys <= set(page.keys())


def test_pms_system_service_capabilities_returns_declared_capabilities(
    client_with_system_db: TestClient,
) -> None:
    response = client_with_system_db.get("/system/read/v1/service-capabilities")

    assert response.status_code == 200, response.text
    body = response.json()

    assert body["app_code"] == "pms"
    assert body["app_name"] == "商品管理"

    capabilities = body["capabilities"]
    assert isinstance(capabilities, list)
    assert capabilities

    by_code = _by_code(capabilities, "capability_code")

    assert "pms.read.items" in by_code
    assert "pms.read.uoms" in by_code
    assert "pms.read.sku_codes" in by_code
    assert "pms.read.barcodes" in by_code
    assert "pms.read.suppliers" in by_code
    assert "pms.read.health" in by_code

    items = by_code["pms.read.items"]
    assert items["permission_code"] == "pms.read.items"
    assert items["resource_code"] == "items"
    assert items["is_active"] is True
    assert items["source_updated_at"] is not None

    route_pairs = {(route["http_method"], route["path"]) for route in items["routes"]}
    assert ("GET", "/pms/read/v1/projection-feed/items") in route_pairs
    assert ("GET", "/pms/read/v1/items/basic") in route_pairs
    assert ("POST", "/pms/read/v1/items/basic/batch") in route_pairs

    required_capability_keys = {
        "capability_code",
        "capability_name",
        "resource_code",
        "permission_code",
        "description",
        "is_active",
        "source_updated_at",
        "routes",
    }
    for capability in capabilities:
        assert required_capability_keys <= set(capability)
        assert capability["permission_code"] == capability["capability_code"]
        assert "approved" not in capability
        assert "written" not in capability
        assert "verified" not in capability


def test_pms_system_service_dependencies_are_empty_until_pms_has_outbound_integrations() -> None:
    client = TestClient(app)

    response = client.get("/system/read/v1/service-dependencies")

    assert response.status_code == 200, response.text
    body = response.json()

    assert body["app_code"] == "pms"
    assert body["app_name"] == "商品管理"
    assert body["source_service_client_code"] == "pms-service"
    assert body["dependencies"] == []


def test_pms_system_read_v1_endpoints_are_registered_in_openapi() -> None:
    client = TestClient(app)

    response = client.get("/openapi.json")

    assert response.status_code == 200, response.text
    paths = response.json()["paths"]

    assert "/system/read/v1/app-manifest" in paths
    assert "/system/read/v1/page-catalog" in paths
    assert "/system/read/v1/service-capabilities" in paths
    assert "/system/read/v1/service-dependencies" in paths
