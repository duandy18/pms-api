"""pms admin user management

Revision ID: 0004_pms_admin_user_management
Revises: 0003_pms_suppliers_owner
Create Date: 2026-05-12 09:45:00.000000

"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op


revision: str = "0004_pms_admin_user_management"
down_revision: str | Sequence[str] | None = "0003_pms_suppliers_owner"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("ck_page_registry_domain_code", "page_registry", type_="check")
    op.create_check_constraint(
        "ck_page_registry_domain_code",
        "page_registry",
        "domain_code IN ('pms', 'admin')",
    )

    op.execute(
        """
        INSERT INTO permissions (name)
        VALUES
          ('page.admin.read'),
          ('page.admin.write')
        ON CONFLICT (name) DO NOTHING
        """
    )

    op.execute(
        """
        INSERT INTO page_registry (
          code,
          name,
          parent_code,
          level,
          domain_code,
          show_in_topbar,
          show_in_sidebar,
          inherit_permissions,
          read_permission_id,
          write_permission_id,
          sort_order,
          is_active
        )
        VALUES
          (
            'admin',
            '系统管理',
            NULL,
            1,
            'admin',
            TRUE,
            TRUE,
            FALSE,
            (SELECT id FROM permissions WHERE name = 'page.admin.read'),
            (SELECT id FROM permissions WHERE name = 'page.admin.write'),
            90,
            TRUE
          ),
          (
            'admin.users',
            '用户管理',
            'admin',
            2,
            'admin',
            FALSE,
            TRUE,
            TRUE,
            NULL,
            NULL,
            10,
            TRUE
          )
        ON CONFLICT (code) DO UPDATE SET
          name = EXCLUDED.name,
          parent_code = EXCLUDED.parent_code,
          level = EXCLUDED.level,
          domain_code = EXCLUDED.domain_code,
          show_in_topbar = EXCLUDED.show_in_topbar,
          show_in_sidebar = EXCLUDED.show_in_sidebar,
          inherit_permissions = EXCLUDED.inherit_permissions,
          read_permission_id = EXCLUDED.read_permission_id,
          write_permission_id = EXCLUDED.write_permission_id,
          sort_order = EXCLUDED.sort_order,
          is_active = EXCLUDED.is_active
        """
    )

    op.execute(
        """
        INSERT INTO page_route_prefixes (page_code, route_prefix, sort_order, is_active)
        VALUES ('admin.users', '/admin/users', 10, TRUE)
        ON CONFLICT (route_prefix) DO UPDATE SET
          page_code = EXCLUDED.page_code,
          sort_order = EXCLUDED.sort_order,
          is_active = EXCLUDED.is_active
        """
    )

    op.execute(
        """
        INSERT INTO user_permissions (user_id, permission_id)
        SELECT u.id, p.id
          FROM users u
          JOIN permissions p
            ON p.name IN ('page.admin.read', 'page.admin.write')
         WHERE u.username = 'admin'
        ON CONFLICT (user_id, permission_id) DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute("DELETE FROM page_route_prefixes WHERE route_prefix = '/admin/users'")
    op.execute("DELETE FROM page_registry WHERE code IN ('admin.users', 'admin')")
    op.execute(
        """
        DELETE FROM permissions
        WHERE name IN ('page.admin.read', 'page.admin.write')
        """
    )

    op.drop_constraint("ck_page_registry_domain_code", "page_registry", type_="check")
    op.create_check_constraint(
        "ck_page_registry_domain_code",
        "page_registry",
        "domain_code IN ('pms')",
    )
