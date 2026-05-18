# tests/api/test_pms_system_service_permission_write_api.py
from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.session import get_engine, get_session_factory
from app.main import app
from app.pms.system.service_auth.models import (
    PmsServiceCapability,
    PmsServiceClient,
)
from app.settings import get_settings

APPLY_PATH = "/system/write/v1/service-permissions/apply"
VERIFY_PATH = "/system/write/v1/service-permissions/verify"
ERP_HEADERS = {"X-Service-Client": "erp-service"}

TEST_CLIENT_CODES = {
    "zz-erp-write-test-service",
    "zz-erp-write-test-disable-service",
    "zz-erp-write-test-missing-service",
}


@pytest.fixture(autouse=True)
def _clear_cached_db_settings() -> Generator[None, None, None]:
    get_settings.cache_clear()
    get_engine.cache_clear()
    yield
    get_engine.cache_clear()
    get_settings.cache_clear()


def _cleanup_test_clients(db: Session) -> None:
    db.query(PmsServiceClient).filter(
        PmsServiceClient.client_code.in_(TEST_CLIENT_CODES),
    ).delete(synchronize_session=False)
    db.commit()


def _upsert_client(
    db: Session,
    *,
    client_code: str,
    client_name: str,
    description: str,
    is_active: bool = True,
) -> PmsServiceClient:
    client = (
        db.query(PmsServiceClient)
        .filter(PmsServiceClient.client_code == client_code)
        .one_or_none()
    )

    if client is None:
        client = PmsServiceClient(
            client_code=client_code,
            client_name=client_name,
            description=description,
            is_active=is_active,
        )
        db.add(client)
    else:
        client.client_name = client_name
        client.description = description
        client.is_active = is_active

    db.flush()
    return client


def _upsert_capability(
    db: Session,
    *,
    capability_code: str,
    capability_name: str,
    resource_code: str,
    description: str,
    is_active: bool = True,
) -> PmsServiceCapability:
    capability = (
        db.query(PmsServiceCapability)
        .filter(PmsServiceCapability.capability_code == capability_code)
        .one_or_none()
    )

    if capability is None:
        capability = PmsServiceCapability(
            capability_code=capability_code,
            capability_name=capability_name,
            resource_code=resource_code,
            description=description,
            is_active=is_active,
        )
        db.add(capability)
    else:
        capability.capability_name = capability_name
        capability.resource_code = resource_code
        capability.description = description
        capability.is_active = is_active

    db.flush()
    return capability


def _prepare_db(db: Session) -> None:
    _cleanup_test_clients(db)

    _upsert_client(
        db,
        client_code="erp-service",
        client_name="ERP Service",
        description="ERP 调用 PMS 配置/治理能力的调用方",
        is_active=True,
    )
    _upsert_capability(
        db,
        capability_code="pms.read.items",
        capability_name="Read PMS items",
        resource_code="items",
        description="读取 PMS 商品基础数据",
        is_active=True,
    )
    _upsert_capability(
        db,
        capability_code="pms.read.suppliers",
        capability_name="Read PMS suppliers",
        resource_code="suppliers",
        description="读取 PMS 供应商",
        is_active=True,
    )
    db.commit()


@pytest.fixture()
def client_with_pg_db() -> Generator[TestClient, None, None]:
    session_factory = get_session_factory()

    with session_factory() as db:
        _prepare_db(db)

    try:
        with TestClient(app) as client:
            yield client
    finally:
        with session_factory() as db:
            _cleanup_test_clients(db)


def _apply_payload(
    *,
    client_code: str = "zz-erp-write-test-service",
    capability_code: str = "pms.read.items",
    is_active: bool = True,
) -> dict:
    return {
        "client_code": client_code,
        "client_name": "ERP Write Test Service",
        "capability_code": capability_code,
        "description": "ERP 写入 PMS service permission 测试",
        "is_active": is_active,
    }


def test_pms_service_permission_apply_requires_erp_service_client_header(
    client_with_pg_db: TestClient,
) -> None:
    response = client_with_pg_db.post(APPLY_PATH, json=_apply_payload())

    assert response.status_code == 401
    assert "pms_service_client_required" in response.text


def test_pms_service_permission_apply_rejects_non_erp_service_client(
    client_with_pg_db: TestClient,
) -> None:
    response = client_with_pg_db.post(
        APPLY_PATH,
        headers={"X-Service-Client": "wms-service"},
        json=_apply_payload(),
    )

    assert response.status_code == 403
    assert "pms_service_permission_write_denied" in response.text


def test_pms_service_permission_apply_and_verify_round_trip(
    client_with_pg_db: TestClient,
) -> None:
    response = client_with_pg_db.post(
        APPLY_PATH,
        headers=ERP_HEADERS,
        json=_apply_payload(),
    )

    assert response.status_code == 200, response.text
    body = response.json()

    assert body["app_code"] == "pms"
    assert body["client_code"] == "zz-erp-write-test-service"
    assert body["client_name"] == "ERP Write Test Service"
    assert body["capability_code"] == "pms.read.items"
    assert body["description"] == "ERP 写入 PMS service permission 测试"
    assert body["is_active"] is True
    assert body["applied"] is True
    assert body["verified"] is True
    assert body["permission_id"] > 0
    assert body["granted_at"]

    verify_response = client_with_pg_db.get(
        VERIFY_PATH,
        headers=ERP_HEADERS,
        params={
            "client_code": "zz-erp-write-test-service",
            "capability_code": "pms.read.items",
        },
    )

    assert verify_response.status_code == 200, verify_response.text
    verify_body = verify_response.json()

    assert verify_body["app_code"] == "pms"
    assert verify_body["client_code"] == "zz-erp-write-test-service"
    assert verify_body["capability_code"] == "pms.read.items"
    assert verify_body["client_exists"] is True
    assert verify_body["capability_exists"] is True
    assert verify_body["permission_exists"] is True
    assert verify_body["client_is_active"] is True
    assert verify_body["capability_is_active"] is True
    assert verify_body["permission_is_active"] is True
    assert verify_body["verified"] is True


def test_pms_service_permission_apply_can_disable_permission_without_disabling_client(
    client_with_pg_db: TestClient,
) -> None:
    response = client_with_pg_db.post(
        APPLY_PATH,
        headers=ERP_HEADERS,
        json=_apply_payload(
            client_code="zz-erp-write-test-disable-service",
            capability_code="pms.read.items",
            is_active=False,
        ),
    )

    assert response.status_code == 200, response.text
    body = response.json()

    assert body["client_code"] == "zz-erp-write-test-disable-service"
    assert body["is_active"] is False
    assert body["verified"] is False

    verify_response = client_with_pg_db.get(
        VERIFY_PATH,
        headers=ERP_HEADERS,
        params={
            "client_code": "zz-erp-write-test-disable-service",
            "capability_code": "pms.read.items",
        },
    )

    assert verify_response.status_code == 200, verify_response.text
    verify_body = verify_response.json()

    assert verify_body["client_is_active"] is True
    assert verify_body["permission_is_active"] is False
    assert verify_body["verified"] is False


def test_pms_service_permission_apply_rejects_unknown_capability(
    client_with_pg_db: TestClient,
) -> None:
    response = client_with_pg_db.post(
        APPLY_PATH,
        headers=ERP_HEADERS,
        json=_apply_payload(capability_code="pms.read.unknown_for_write_test"),
    )

    assert response.status_code == 404
    assert "pms_service_capability_not_found" in response.text


def test_pms_service_permission_verify_returns_false_for_missing_permission(
    client_with_pg_db: TestClient,
) -> None:
    response = client_with_pg_db.get(
        VERIFY_PATH,
        headers=ERP_HEADERS,
        params={
            "client_code": "zz-erp-write-test-missing-service",
            "capability_code": "pms.read.items",
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()

    assert body["client_exists"] is False
    assert body["capability_exists"] is True
    assert body["permission_exists"] is False
    assert body["verified"] is False


def test_pms_service_permission_write_routes_are_registered_in_openapi() -> None:
    client = TestClient(app)

    response = client.get("/openapi.json")

    assert response.status_code == 200, response.text
    paths = response.json()["paths"]

    assert APPLY_PATH in paths
    assert "post" in paths[APPLY_PATH]
    assert VERIFY_PATH in paths
    assert "get" in paths[VERIFY_PATH]
