"""add PMS IAM snapshot read-v1 capability

Revision ID: 0007_pms_iam_snapshot
Revises: 0006_pms_service_catalog
Create Date: 2026-05-18 14:12:00.000000

"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op


revision: str = "0007_pms_iam_snapshot"
down_revision: str | Sequence[str] | None = "0006_pms_service_catalog"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO pms_service_clients (
          client_code,
          client_name,
          description,
          is_active
        )
        VALUES (
          'erp-service',
          'ERP Service',
          'ERP 调用 PMS 配置/治理能力的调用方',
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
        INSERT INTO pms_service_capabilities (
          capability_code,
          capability_name,
          resource_code,
          description,
          is_active
        )
        VALUES (
          'pms.read.iam_snapshot',
          'Read PMS IAM snapshot',
          'iam_snapshot',
          'ERP 读取 PMS 用户、权限和页面权限只读快照',
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
        VALUES (
          'pms.read.iam_snapshot',
          'GET',
          '/system/read/v1/iam-snapshot',
          'get_pms_iam_snapshot',
          TRUE,
          TRUE
        )
        ON CONFLICT (http_method, route_path) DO UPDATE
        SET
          capability_code = EXCLUDED.capability_code,
          route_name = EXCLUDED.route_name,
          auth_required = EXCLUDED.auth_required,
          is_active = EXCLUDED.is_active
        """
    )

    op.execute(
        """
        INSERT INTO pms_service_permissions (
          client_id,
          capability_code,
          description,
          is_active
        )
        SELECT
          c.id,
          'pms.read.iam_snapshot',
          'ERP 读取 PMS IAM 只读快照',
          TRUE
        FROM pms_service_clients c
        WHERE c.client_code = 'erp-service'
        ON CONFLICT (client_id, capability_code) DO UPDATE
        SET
          description = EXCLUDED.description,
          is_active = EXCLUDED.is_active
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM pms_service_permissions
        WHERE capability_code = 'pms.read.iam_snapshot'
        """
    )

    op.execute(
        """
        DELETE FROM pms_service_capability_routes
        WHERE http_method = 'GET'
          AND route_path = '/system/read/v1/iam-snapshot'
        """
    )

    op.execute(
        """
        DELETE FROM pms_service_capabilities
        WHERE capability_code = 'pms.read.iam_snapshot'
        """
    )
