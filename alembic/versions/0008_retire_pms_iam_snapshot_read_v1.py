"""retire PMS IAM snapshot read-v1 capability

Revision ID: 0008_retire_pms_iam_snapshot
Revises: 0007_pms_iam_snapshot
Create Date: 2026-05-19 14:25:00.000000

"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op


revision: str = "0008_retire_pms_iam_snapshot"
down_revision: str | Sequence[str] | None = "0007_pms_iam_snapshot"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """
    ERP is the IAM owner in the target architecture.

    This migration removes the retired read-v1 IAM snapshot capability and its
    ERP service permission. PMS keeps user / permission runtime tables for local
    execution, but no longer exposes users / user_permissions as an owner
    snapshot to ERP.
    """

    op.execute(
        """
        DELETE FROM pms_service_permissions
        WHERE capability_code = 'pms.read.iam_snapshot'
        """
    )

    op.execute(
        """
        DELETE FROM pms_service_capability_routes
        WHERE capability_code = 'pms.read.iam_snapshot'
           OR (http_method = 'GET' AND route_path = '/system/read/v1/iam-snapshot')
        """
    )

    op.execute(
        """
        DELETE FROM pms_service_capabilities
        WHERE capability_code = 'pms.read.iam_snapshot'
        """
    )


def downgrade() -> None:
    """
    Downgrade restores only service-auth catalog rows.

    The Python read-v1 endpoint is removed by this change set; do not use
    downgrade as a compatibility path in normal development.
    """

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
