# tests/api/test_pms_service_permission_runtime_contract.py
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from app.pms.system.service_auth.deps import (
    PMS_SERVICE_CLIENT_HEADER,
    require_pms_service_capability,
)
from app.pms.system.service_auth.models import (
    PmsServiceCapability,
    PmsServiceClient,
    PmsServicePermission,
)
from app.pms.system.service_auth.services import PmsServicePermissionService


def _sqlite_session() -> Session:
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def _register_sqlite_functions(dbapi_connection, _connection_record) -> None:
        dbapi_connection.create_function(
            "btrim",
            1,
            lambda value: "" if value is None else str(value).strip(),
        )

    PmsServiceCapability.__table__.create(engine)
    PmsServiceClient.__table__.create(engine)
    PmsServicePermission.__table__.create(engine)
    return Session(bind=engine)


def _seed_permission(
    db: Session,
    *,
    client_code: str,
    capability_code: str,
    capability_active: bool = True,
    client_active: bool = True,
    permission_active: bool = True,
) -> None:
    capability = PmsServiceCapability(
        capability_code=capability_code,
        capability_name=f"{capability_code} name",
        resource_code=capability_code.split(".")[-1],
        is_active=capability_active,
    )
    db.add(capability)
    db.flush()

    client = PmsServiceClient(
        client_code=client_code,
        client_name=f"{client_code} name",
        is_active=client_active,
    )
    db.add(client)
    db.flush()

    permission = PmsServicePermission(
        client_id=int(client.id),
        capability_code=capability_code,
        is_active=permission_active,
    )
    db.add(permission)
    db.commit()


def test_pms_service_permission_service_allows_active_client_and_capability() -> None:
    with _sqlite_session() as db:
        _seed_permission(
            db,
            client_code="wms-service",
            capability_code="pms.read.items",
        )

        service = PmsServicePermissionService(db)

        assert service.is_allowed(
            client_code=" wms-service ",
            capability_code=" pms.read.items ",
        )


def test_pms_service_permission_service_rejects_missing_inactive_or_ungranted() -> None:
    with _sqlite_session() as db:
        _seed_permission(
            db,
            client_code="inactive-capability-client",
            capability_code="pms.read.inactive_capability",
            capability_active=False,
        )
        _seed_permission(
            db,
            client_code="inactive-client",
            capability_code="pms.read.inactive_client",
            client_active=False,
        )
        _seed_permission(
            db,
            client_code="inactive-permission",
            capability_code="pms.read.inactive_permission",
            permission_active=False,
        )
        _seed_permission(
            db,
            client_code="wms-service",
            capability_code="pms.read.items",
        )

        service = PmsServicePermissionService(db)

        assert not service.is_allowed(client_code=None, capability_code="pms.read.items")
        assert not service.is_allowed(client_code="wms-service", capability_code=None)
        assert not service.is_allowed(client_code="unknown-service", capability_code="pms.read.items")
        assert not service.is_allowed(
            client_code="inactive-capability-client",
            capability_code="pms.read.inactive_capability",
        )
        assert not service.is_allowed(
            client_code="inactive-client",
            capability_code="pms.read.inactive_client",
        )
        assert not service.is_allowed(
            client_code="inactive-permission",
            capability_code="pms.read.inactive_permission",
        )
        assert not service.is_allowed(client_code="wms-service", capability_code="pms.read.suppliers")


class FakePermissionService:
    def __init__(self, *, allowed: bool) -> None:
        self.allowed = allowed
        self.calls: list[tuple[str | None, str | None]] = []

    def is_allowed(self, *, client_code: str | None, capability_code: str | None) -> bool:
        self.calls.append((client_code, capability_code))
        return self.allowed


def test_pms_service_permission_dependency_uses_service_client_header() -> None:
    assert PMS_SERVICE_CLIENT_HEADER == "X-Service-Client"

    dependency = require_pms_service_capability("pms.read.items")
    service = FakePermissionService(allowed=True)

    dependency(
        x_service_client="wms-service",
        service=service,  # type: ignore[arg-type]
    )

    assert service.calls == [("wms-service", "pms.read.items")]


def test_pms_service_permission_dependency_rejects_missing_service_client_header() -> None:
    dependency = require_pms_service_capability("pms.read.items")
    service = FakePermissionService(allowed=True)

    try:
        dependency(
            x_service_client=None,
            service=service,  # type: ignore[arg-type]
        )
    except HTTPException as exc:
        assert exc.status_code == 401
        assert exc.detail == "pms_service_client_required"
    else:
        raise AssertionError("missing X-Service-Client should be rejected")


def test_pms_service_permission_dependency_rejects_denied_capability() -> None:
    dependency = require_pms_service_capability("pms.read.suppliers")
    service = FakePermissionService(allowed=False)

    try:
        dependency(
            x_service_client="wms-service",
            service=service,  # type: ignore[arg-type]
        )
    except HTTPException as exc:
        assert exc.status_code == 403
        assert exc.detail == "pms_service_permission_denied"
    else:
        raise AssertionError("denied service permission should be rejected")
