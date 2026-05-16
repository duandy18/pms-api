"""pms service capability catalog

Revision ID: 0006_pms_service_catalog
Revises: 0005_pms_service_auth_tables
Create Date: 2026-05-16 14:10:00.000000

"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0006_pms_service_catalog"
down_revision: str | Sequence[str] | None = "0005_pms_service_auth_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "pms_service_capabilities",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("capability_code", sa.String(length=128), nullable=False),
        sa.Column("capability_name", sa.String(length=128), nullable=False),
        sa.Column("resource_code", sa.String(length=64), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id", name="pk_pms_service_capabilities"),
        sa.UniqueConstraint(
            "capability_code",
            name="uq_pms_service_capabilities_capability_code",
        ),
        sa.CheckConstraint(
            "btrim(capability_code) <> ''",
            name="ck_pms_service_capabilities_capability_code_not_blank",
        ),
        sa.CheckConstraint(
            "btrim(capability_name) <> ''",
            name="ck_pms_service_capabilities_capability_name_not_blank",
        ),
        sa.CheckConstraint(
            "btrim(resource_code) <> ''",
            name="ck_pms_service_capabilities_resource_code_not_blank",
        ),
    )
    op.create_index(
        "ix_pms_service_capabilities_resource_code",
        "pms_service_capabilities",
        ["resource_code"],
    )

    op.execute(
        """
        INSERT INTO pms_service_capabilities (
          capability_code,
          capability_name,
          resource_code,
          description,
          is_active
        )
        VALUES
          (
            'pms.read.health',
            'PMS read-v1 health',
            'health',
            'PMS read-v1 health endpoint',
            TRUE
          ),
          (
            'pms.read.items',
            'Read PMS items',
            'items',
            '读取 PMS 商品基础、策略和报表元数据',
            TRUE
          ),
          (
            'pms.read.uoms',
            'Read PMS UOMs',
            'uoms',
            '读取 PMS 商品包装单位和默认单位',
            TRUE
          ),
          (
            'pms.read.sku_codes',
            'Read PMS SKU codes',
            'sku_codes',
            '读取 PMS SKU 编码和出库默认编码解析',
            TRUE
          ),
          (
            'pms.read.barcodes',
            'Read PMS barcodes',
            'barcodes',
            '读取 PMS 商品条码和条码探测能力',
            TRUE
          ),
          (
            'pms.read.suppliers',
            'Read PMS suppliers',
            'suppliers',
            '读取 PMS 供应商基础数据',
            TRUE
          )
        ON CONFLICT (capability_code) DO UPDATE
        SET
          capability_name = EXCLUDED.capability_name,
          resource_code = EXCLUDED.resource_code,
          description = EXCLUDED.description,
          is_active = EXCLUDED.is_active,
          updated_at = CURRENT_TIMESTAMP
        """
    )

    op.create_table(
        "pms_service_capability_routes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("capability_code", sa.String(length=128), nullable=False),
        sa.Column("http_method", sa.String(length=16), nullable=False),
        sa.Column("route_path", sa.String(length=255), nullable=False),
        sa.Column("route_name", sa.String(length=128), nullable=False),
        sa.Column("auth_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["capability_code"],
            ["pms_service_capabilities.capability_code"],
            name="fk_pms_service_capability_routes_capability_code",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_pms_service_capability_routes"),
        sa.UniqueConstraint(
            "http_method",
            "route_path",
            name="uq_pms_service_capability_routes_method_path",
        ),
        sa.CheckConstraint(
            "btrim(capability_code) <> ''",
            name="ck_pms_service_capability_routes_capability_code_not_blank",
        ),
        sa.CheckConstraint(
            "btrim(http_method) <> ''",
            name="ck_pms_service_capability_routes_http_method_not_blank",
        ),
        sa.CheckConstraint(
            "btrim(route_path) <> ''",
            name="ck_pms_service_capability_routes_route_path_not_blank",
        ),
        sa.CheckConstraint(
            "btrim(route_name) <> ''",
            name="ck_pms_service_capability_routes_route_name_not_blank",
        ),
    )
    op.create_index(
        "ix_pms_service_capability_routes_capability_code",
        "pms_service_capability_routes",
        ["capability_code"],
    )

    op.execute(
        """
        INSERT INTO pms_service_capability_routes (
          capability_code,
          http_method,
          route_path,
          route_name,
          auth_required,
          is_active
        )
        VALUES
          ('pms.read.health', 'GET', '/pms/read/v1/health', 'read_v1_health', FALSE, TRUE),

          ('pms.read.items', 'GET', '/pms/read/v1/projection-feed/items', 'projection_feed_items', TRUE, TRUE),
          ('pms.read.items', 'GET', '/pms/read/v1/items/basic', 'list_item_basics', TRUE, TRUE),
          ('pms.read.items', 'GET', '/pms/read/v1/items/basic/{item_id}', 'get_item_basic', TRUE, TRUE),
          ('pms.read.items', 'POST', '/pms/read/v1/items/basic/batch', 'batch_item_basics', TRUE, TRUE),
          ('pms.read.items', 'GET', '/pms/read/v1/items/policy-by-sku', 'get_item_policy_by_sku', TRUE, TRUE),
          ('pms.read.items', 'GET', '/pms/read/v1/items/{item_id}/policy', 'get_item_policy', TRUE, TRUE),
          ('pms.read.items', 'POST', '/pms/read/v1/items/policies/batch', 'batch_item_policies', TRUE, TRUE),
          ('pms.read.items', 'GET', '/pms/read/v1/items/report-search', 'search_report_items', TRUE, TRUE),
          ('pms.read.items', 'POST', '/pms/read/v1/items/report-meta/batch', 'batch_item_report_meta', TRUE, TRUE),

          ('pms.read.uoms', 'GET', '/pms/read/v1/projection-feed/uoms', 'projection_feed_uoms', TRUE, TRUE),
          ('pms.read.uoms', 'GET', '/pms/read/v1/items/{item_id}/uoms', 'list_item_uoms', TRUE, TRUE),
          ('pms.read.uoms', 'GET', '/pms/read/v1/uoms/{item_uom_id}', 'get_uom', TRUE, TRUE),
          ('pms.read.uoms', 'POST', '/pms/read/v1/uoms/query', 'query_uoms', TRUE, TRUE),
          ('pms.read.uoms', 'POST', '/pms/read/v1/items/uom-defaults/batch', 'batch_uom_defaults', TRUE, TRUE),

          ('pms.read.barcodes', 'GET', '/pms/read/v1/projection-feed/barcodes', 'projection_feed_barcodes', TRUE, TRUE),
          ('pms.read.barcodes', 'GET', '/pms/read/v1/barcodes/{barcode_id}', 'get_barcode', TRUE, TRUE),
          ('pms.read.barcodes', 'GET', '/pms/read/v1/items/{item_id}/barcodes', 'list_item_barcodes', TRUE, TRUE),
          ('pms.read.barcodes', 'POST', '/pms/read/v1/barcodes/query', 'query_barcodes', TRUE, TRUE),
          ('pms.read.barcodes', 'POST', '/pms/read/v1/barcodes/probe', 'probe_barcode', TRUE, TRUE),

          ('pms.read.sku_codes', 'GET', '/pms/read/v1/projection-feed/sku-codes', 'projection_feed_sku_codes', TRUE, TRUE),
          ('pms.read.sku_codes', 'GET', '/pms/read/v1/sku-codes/resolve-outbound-default', 'resolve_outbound_default_sku_code', TRUE, TRUE),
          ('pms.read.sku_codes', 'GET', '/pms/read/v1/sku-codes/{sku_code_id}', 'get_sku_code', TRUE, TRUE),
          ('pms.read.sku_codes', 'GET', '/pms/read/v1/items/{item_id}/sku-codes', 'list_item_sku_codes', TRUE, TRUE),
          ('pms.read.sku_codes', 'POST', '/pms/read/v1/sku-codes/query', 'query_sku_codes', TRUE, TRUE),

          ('pms.read.suppliers', 'GET', '/pms/read/v1/projection-feed/suppliers', 'projection_feed_suppliers', TRUE, TRUE),
          ('pms.read.suppliers', 'GET', '/pms/read/v1/suppliers', 'list_read_suppliers', TRUE, TRUE),
          ('pms.read.suppliers', 'GET', '/pms/read/v1/suppliers/{supplier_id}', 'get_read_supplier', TRUE, TRUE)
        ON CONFLICT (http_method, route_path) DO UPDATE
        SET
          capability_code = EXCLUDED.capability_code,
          route_name = EXCLUDED.route_name,
          auth_required = EXCLUDED.auth_required,
          is_active = EXCLUDED.is_active
        """
    )

    op.create_foreign_key(
        "fk_pms_service_permissions_capability_code",
        "pms_service_permissions",
        "pms_service_capabilities",
        ["capability_code"],
        ["capability_code"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_pms_service_permissions_capability_code",
        "pms_service_permissions",
        type_="foreignkey",
    )

    op.drop_index(
        "ix_pms_service_capability_routes_capability_code",
        table_name="pms_service_capability_routes",
    )
    op.drop_table("pms_service_capability_routes")

    op.drop_index(
        "ix_pms_service_capabilities_resource_code",
        table_name="pms_service_capabilities",
    )
    op.drop_table("pms_service_capabilities")
