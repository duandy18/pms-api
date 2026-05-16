"""pms service permission execution tables

Revision ID: 0005_pms_service_auth_tables
Revises: 0004_pms_admin_user_management
Create Date: 2026-05-16 13:45:00.000000

"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0005_pms_service_auth_tables"
down_revision: str | Sequence[str] | None = "0004_pms_admin_user_management"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "pms_service_clients",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("client_code", sa.String(length=64), nullable=False),
        sa.Column("client_name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id", name="pk_pms_service_clients"),
        sa.UniqueConstraint("client_code", name="uq_pms_service_clients_client_code"),
        sa.CheckConstraint(
            "btrim(client_code) <> ''",
            name="ck_pms_service_clients_client_code_not_blank",
        ),
        sa.CheckConstraint(
            "btrim(client_name) <> ''",
            name="ck_pms_service_clients_client_name_not_blank",
        ),
    )

    op.create_table(
        "pms_service_permissions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("capability_code", sa.String(length=128), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "granted_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["client_id"],
            ["pms_service_clients.id"],
            name="fk_pms_service_permissions_client_id_pms_service_clients",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_pms_service_permissions"),
        sa.UniqueConstraint(
            "client_id",
            "capability_code",
            name="uq_pms_service_permissions_client_capability",
        ),
        sa.CheckConstraint(
            "btrim(capability_code) <> ''",
            name="ck_pms_service_permissions_capability_code_not_blank",
        ),
    )
    op.create_index(
        "ix_pms_service_permissions_client_id",
        "pms_service_permissions",
        ["client_id"],
    )
    op.create_index(
        "ix_pms_service_permissions_capability_code",
        "pms_service_permissions",
        ["capability_code"],
    )

    op.execute(
        """
        INSERT INTO pms_service_clients (
          client_code,
          client_name,
          description,
          is_active
        )
        VALUES
          (
            'wms-service',
            'WMS Service',
            'WMS 调用 PMS 商品主数据能力',
            TRUE
          ),
          (
            'oms-service',
            'OMS Service',
            'OMS 调用 PMS 商品主数据能力',
            TRUE
          ),
          (
            'procurement-service',
            'Procurement Service',
            'Procurement 调用 PMS 商品和供应商能力',
            TRUE
          ),
          (
            'logistics-service',
            'Logistics Service',
            'Logistics 调用 PMS 商品主数据能力',
            TRUE
          )
        ON CONFLICT (client_code) DO UPDATE
        SET
          client_name = EXCLUDED.client_name,
          description = EXCLUDED.description,
          is_active = EXCLUDED.is_active
        """
    )

    op.execute(
        """
        WITH desired_permissions AS (
          SELECT
            'wms-service' AS client_code,
            'pms.read.items' AS capability_code,
            '读取 PMS 商品基础数据' AS description
          UNION ALL
          SELECT
            'wms-service',
            'pms.read.uoms',
            '读取 PMS 商品包装单位'
          UNION ALL
          SELECT
            'wms-service',
            'pms.read.sku_codes',
            '读取 PMS SKU 编码'
          UNION ALL
          SELECT
            'wms-service',
            'pms.read.barcodes',
            '读取 PMS 商品条码'
          UNION ALL
          SELECT
            'wms-service',
            'pms.read.suppliers',
            '读取 PMS 供应商'
          UNION ALL
          SELECT
            'oms-service',
            'pms.read.items',
            '读取 PMS 商品基础数据'
          UNION ALL
          SELECT
            'oms-service',
            'pms.read.sku_codes',
            '读取 PMS SKU 编码'
          UNION ALL
          SELECT
            'oms-service',
            'pms.read.barcodes',
            '读取 PMS 商品条码'
          UNION ALL
          SELECT
            'procurement-service',
            'pms.read.items',
            '读取 PMS 商品基础数据'
          UNION ALL
          SELECT
            'procurement-service',
            'pms.read.suppliers',
            '读取 PMS 供应商'
          UNION ALL
          SELECT
            'logistics-service',
            'pms.read.items',
            '读取 PMS 商品基础数据'
        )
        INSERT INTO pms_service_permissions (
          client_id,
          capability_code,
          description,
          is_active
        )
        SELECT
          c.id,
          p.capability_code,
          p.description,
          TRUE
        FROM desired_permissions p
        JOIN pms_service_clients c
          ON c.client_code = p.client_code
        ON CONFLICT (client_id, capability_code) DO UPDATE
        SET
          description = EXCLUDED.description,
          is_active = EXCLUDED.is_active
        """
    )


def downgrade() -> None:
    op.drop_index(
        "ix_pms_service_permissions_capability_code",
        table_name="pms_service_permissions",
    )
    op.drop_index(
        "ix_pms_service_permissions_client_id",
        table_name="pms_service_permissions",
    )
    op.drop_table("pms_service_permissions")
    op.drop_table("pms_service_clients")
