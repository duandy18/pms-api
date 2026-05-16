# tests/api/test_pms_service_permission_contract.py
from __future__ import annotations

from pathlib import Path

from app.db.metadata import metadata
from app.service_auth.models import (
    PmsServiceCapability,
    PmsServiceCapabilityRoute,
    PmsServiceClient,
    PmsServicePermission,
)

ROOT = Path(__file__).resolve().parents[2]
PERMISSION_MIGRATION = ROOT / "alembic/versions/0005_pms_service_permission_execution_tables.py"
CATALOG_MIGRATION = ROOT / "alembic/versions/0006_pms_service_capability_catalog.py"

EXPECTED_CLIENT_CODES = {
    "wms-service",
    "oms-service",
    "procurement-service",
    "logistics-service",
}

EXPECTED_PERMISSION_CAPABILITY_CODES = {
    "pms.read.items",
    "pms.read.uoms",
    "pms.read.sku_codes",
    "pms.read.barcodes",
    "pms.read.suppliers",
}

EXPECTED_CATALOG_CAPABILITY_CODES = EXPECTED_PERMISSION_CAPABILITY_CODES | {
    "pms.read.health",
}


def _constraint_names(table_name: str) -> set[str]:
    return {constraint.name for constraint in metadata.tables[table_name].constraints}


def test_pms_service_permission_tables_are_registered_in_metadata() -> None:
    assert PmsServiceCapability.__tablename__ == "pms_service_capabilities"
    assert PmsServiceCapabilityRoute.__tablename__ == "pms_service_capability_routes"
    assert PmsServiceClient.__tablename__ == "pms_service_clients"
    assert PmsServicePermission.__tablename__ == "pms_service_permissions"

    assert "pms_service_capabilities" in metadata.tables
    assert "pms_service_capability_routes" in metadata.tables
    assert "pms_service_clients" in metadata.tables
    assert "pms_service_permissions" in metadata.tables


def test_pms_service_capabilities_table_contract() -> None:
    table = metadata.tables["pms_service_capabilities"]

    assert {
        "id",
        "capability_code",
        "capability_name",
        "resource_code",
        "description",
        "is_active",
        "created_at",
        "updated_at",
    } == set(table.c.keys())

    assert table.c.capability_code.type.length == 128
    assert table.c.capability_name.type.length == 128
    assert table.c.resource_code.type.length == 64
    assert table.c.description.type.length == 255
    assert str(table.c.is_active.server_default.arg) == "true"
    assert str(table.c.created_at.server_default.arg) == "CURRENT_TIMESTAMP"
    assert str(table.c.updated_at.server_default.arg) == "CURRENT_TIMESTAMP"

    constraint_names = _constraint_names("pms_service_capabilities")
    assert "pk_pms_service_capabilities" in constraint_names
    assert "uq_pms_service_capabilities_capability_code" in constraint_names
    assert "ck_pms_service_capabilities_capability_code_not_blank" in constraint_names
    assert "ck_pms_service_capabilities_capability_name_not_blank" in constraint_names
    assert "ck_pms_service_capabilities_resource_code_not_blank" in constraint_names

    index_names = {index.name for index in table.indexes}
    assert "ix_pms_service_capabilities_resource_code" in index_names


def test_pms_service_capability_routes_table_contract() -> None:
    table = metadata.tables["pms_service_capability_routes"]

    assert {
        "id",
        "capability_code",
        "http_method",
        "route_path",
        "route_name",
        "auth_required",
        "is_active",
        "created_at",
    } == set(table.c.keys())

    assert table.c.capability_code.type.length == 128
    assert table.c.http_method.type.length == 16
    assert table.c.route_path.type.length == 255
    assert table.c.route_name.type.length == 128
    assert str(table.c.auth_required.server_default.arg) == "true"
    assert str(table.c.is_active.server_default.arg) == "true"
    assert str(table.c.created_at.server_default.arg) == "CURRENT_TIMESTAMP"

    foreign_keys = list(table.c.capability_code.foreign_keys)
    assert len(foreign_keys) == 1
    assert foreign_keys[0].column.table.name == "pms_service_capabilities"
    assert foreign_keys[0].column.name == "capability_code"
    assert foreign_keys[0].ondelete == "RESTRICT"
    assert foreign_keys[0].constraint.name == "fk_pms_service_capability_routes_capability_code"

    constraint_names = _constraint_names("pms_service_capability_routes")
    assert "pk_pms_service_capability_routes" in constraint_names
    assert "uq_pms_service_capability_routes_method_path" in constraint_names
    assert "ck_pms_service_capability_routes_capability_code_not_blank" in constraint_names
    assert "ck_pms_service_capability_routes_http_method_not_blank" in constraint_names
    assert "ck_pms_service_capability_routes_route_path_not_blank" in constraint_names
    assert "ck_pms_service_capability_routes_route_name_not_blank" in constraint_names

    index_names = {index.name for index in table.indexes}
    assert "ix_pms_service_capability_routes_capability_code" in index_names


def test_pms_service_clients_table_contract() -> None:
    table = metadata.tables["pms_service_clients"]

    assert {
        "id",
        "client_code",
        "client_name",
        "description",
        "is_active",
        "created_at",
    } == set(table.c.keys())

    assert table.c.client_code.type.length == 64
    assert table.c.client_name.type.length == 128
    assert table.c.description.type.length == 255
    assert str(table.c.is_active.server_default.arg) == "true"
    assert str(table.c.created_at.server_default.arg) == "CURRENT_TIMESTAMP"

    constraint_names = _constraint_names("pms_service_clients")
    assert "pk_pms_service_clients" in constraint_names
    assert "uq_pms_service_clients_client_code" in constraint_names
    assert "ck_pms_service_clients_client_code_not_blank" in constraint_names
    assert "ck_pms_service_clients_client_name_not_blank" in constraint_names


def test_pms_service_permissions_table_contract() -> None:
    table = metadata.tables["pms_service_permissions"]

    assert {
        "id",
        "client_id",
        "capability_code",
        "description",
        "is_active",
        "granted_at",
    } == set(table.c.keys())

    assert table.c.capability_code.type.length == 128
    assert table.c.description.type.length == 255
    assert str(table.c.is_active.server_default.arg) == "true"
    assert str(table.c.granted_at.server_default.arg) == "CURRENT_TIMESTAMP"

    target_tables = {foreign_key.column.table.name for foreign_key in table.foreign_keys}
    assert target_tables == {
        "pms_service_clients",
        "pms_service_capabilities",
    }

    capability_fks = [
        foreign_key
        for foreign_key in table.c.capability_code.foreign_keys
        if foreign_key.column.table.name == "pms_service_capabilities"
    ]
    assert len(capability_fks) == 1
    assert capability_fks[0].column.name == "capability_code"
    assert capability_fks[0].ondelete == "RESTRICT"
    assert capability_fks[0].constraint.name == "fk_pms_service_permissions_capability_code"

    constraint_names = _constraint_names("pms_service_permissions")
    assert "pk_pms_service_permissions" in constraint_names
    assert "uq_pms_service_permissions_client_capability" in constraint_names
    assert "ck_pms_service_permissions_capability_code_not_blank" in constraint_names

    index_names = {index.name for index in table.indexes}
    assert "ix_pms_service_permissions_client_id" in index_names
    assert "ix_pms_service_permissions_capability_code" in index_names


def test_pms_service_permissions_do_not_reuse_user_permission_tables() -> None:
    table = metadata.tables["pms_service_permissions"]

    assert "permission_id" not in table.c
    assert "user_id" not in table.c


def test_pms_service_permission_migration_contains_initial_grants() -> None:
    text = PERMISSION_MIGRATION.read_text(encoding="utf-8")

    assert 'down_revision: str | Sequence[str] | None = "0004_pms_admin_user_management"' in text
    assert '"pms_service_clients"' in text
    assert '"pms_service_permissions"' in text
    assert "fk_pms_service_permissions_client_id_pms_service_clients" in text
    assert "uq_pms_service_permissions_client_capability" in text

    for client_code in EXPECTED_CLIENT_CODES:
        assert client_code in text

    for capability_code in EXPECTED_PERMISSION_CAPABILITY_CODES:
        assert capability_code in text


def test_pms_service_capability_catalog_migration_contains_catalog_and_routes() -> None:
    text = CATALOG_MIGRATION.read_text(encoding="utf-8")

    assert 'down_revision: str | Sequence[str] | None = "0005_pms_service_auth_tables"' in text
    assert '"pms_service_capabilities"' in text
    assert '"pms_service_capability_routes"' in text
    assert "fk_pms_service_permissions_capability_code" in text
    assert "fk_pms_service_capability_routes_capability_code" in text
    assert "uq_pms_service_capability_routes_method_path" in text

    for capability_code in EXPECTED_CATALOG_CAPABILITY_CODES:
        assert capability_code in text

    assert "/pms/read/v1/health" in text
    assert "/pms/read/v1/items/basic" in text
    assert "/pms/read/v1/items/basic/{item_id}" in text
    assert "/pms/read/v1/uoms/{item_uom_id}" in text
    assert "/pms/read/v1/barcodes/{barcode_id}" in text
    assert "/pms/read/v1/sku-codes/{sku_code_id}" in text
    assert "/pms/read/v1/suppliers/{supplier_id}" in text
