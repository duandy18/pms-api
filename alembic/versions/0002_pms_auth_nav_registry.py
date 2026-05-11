"""pms auth navigation registry

Revision ID: 0002_pms_auth_nav_registry
Revises: 0001_pms_owner_baseline_schema
Create Date: 2026-05-12 03:40:00.000000

"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0002_pms_auth_nav_registry"
down_revision: str | Sequence[str] | None = "0001_pms_owner_baseline_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "permissions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.PrimaryKeyConstraint("id", name="permissions_pkey"),
        sa.UniqueConstraint("name", name="permissions_name_key"),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("full_name", sa.String(length=128), nullable=True),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id", name="users_pkey"),
        sa.UniqueConstraint("username", name="users_username_key"),
    )

    op.create_table(
        "user_permissions",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("permission_id", sa.Integer(), nullable=False),
        sa.Column(
            "granted_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_user_permissions_user_id_users",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["permission_id"],
            ["permissions.id"],
            name="fk_user_permissions_permission_id_permissions",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("user_id", "permission_id", name="pk_user_permissions"),
    )
    op.create_index("ix_user_permissions_permission_id", "user_permissions", ["permission_id"])

    op.create_table(
        "page_registry",
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("read_permission_id", sa.Integer(), nullable=True),
        sa.Column("write_permission_id", sa.Integer(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("parent_code", sa.String(length=64), nullable=True),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("domain_code", sa.String(length=32), nullable=False),
        sa.Column("show_in_topbar", sa.Boolean(), nullable=False),
        sa.Column("show_in_sidebar", sa.Boolean(), nullable=False),
        sa.Column("inherit_permissions", sa.Boolean(), nullable=False),
        sa.CheckConstraint("domain_code IN ('pms')", name="ck_page_registry_domain_code"),
        sa.CheckConstraint("level IN (1, 2, 3)", name="ck_page_registry_level"),
        sa.CheckConstraint(
            "((level = 1 AND parent_code IS NULL) OR (level IN (2, 3) AND parent_code IS NOT NULL))",
            name="ck_page_registry_parent_level_consistency",
        ),
        sa.CheckConstraint(
            "("
            "(inherit_permissions = TRUE AND read_permission_id IS NULL AND write_permission_id IS NULL) "
            "OR "
            "(inherit_permissions = FALSE AND read_permission_id IS NOT NULL AND write_permission_id IS NOT NULL)"
            ")",
            name="ck_page_registry_permission_inherit_consistency",
        ),
        sa.ForeignKeyConstraint(
            ["parent_code"],
            ["page_registry.code"],
            name="fk_page_registry_parent_code_page_registry",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["read_permission_id"],
            ["permissions.id"],
            name="fk_page_registry_read_permission_id_permissions",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["write_permission_id"],
            ["permissions.id"],
            name="fk_page_registry_write_permission_id_permissions",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("code", name="pk_page_registry"),
    )
    op.create_index("ix_page_registry_parent_code", "page_registry", ["parent_code"])

    op.create_table(
        "page_route_prefixes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("page_code", sa.String(length=64), nullable=False),
        sa.Column("route_prefix", sa.String(length=255), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.ForeignKeyConstraint(
            ["page_code"],
            ["page_registry.code"],
            name="fk_page_route_prefixes_page_code_page_registry",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_page_route_prefixes"),
        sa.UniqueConstraint("route_prefix", name="uq_page_route_prefixes_route_prefix"),
    )
    op.create_index("ix_page_route_prefixes_page_code", "page_route_prefixes", ["page_code"])

    op.execute(
        """
        INSERT INTO permissions (name)
        VALUES
          ('page.pms.read'),
          ('page.pms.write')
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
            'pms',
            '商品中心',
            NULL,
            1,
            'pms',
            TRUE,
            TRUE,
            FALSE,
            (SELECT id FROM permissions WHERE name = 'page.pms.read'),
            (SELECT id FROM permissions WHERE name = 'page.pms.write'),
            10,
            TRUE
          ),
          ('pms.items', '商品主数据', 'pms', 2, 'pms', FALSE, TRUE, TRUE, NULL, NULL, 10, TRUE),
          ('pms.item_barcodes', '商品条码', 'pms', 2, 'pms', FALSE, TRUE, TRUE, NULL, NULL, 20, TRUE),
          ('pms.item_uoms', '包装单位', 'pms', 2, 'pms', FALSE, TRUE, TRUE, NULL, NULL, 30, TRUE),
          ('pms.brands', '品牌管理', 'pms', 2, 'pms', FALSE, TRUE, TRUE, NULL, NULL, 40, TRUE),
          ('pms.categories', '商品分类编码', 'pms', 2, 'pms', FALSE, TRUE, TRUE, NULL, NULL, 50, TRUE),
          ('pms.item_attributes', '属性模板', 'pms', 2, 'pms', FALSE, TRUE, TRUE, NULL, NULL, 60, TRUE),
          ('pms.sku_coding', 'SKU编码', 'pms', 2, 'pms', FALSE, TRUE, TRUE, NULL, NULL, 70, TRUE)
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
        VALUES
          ('pms.items', '/items', 10, TRUE),
          ('pms.item_barcodes', '/item-barcodes', 20, TRUE),
          ('pms.item_uoms', '/item-uoms', 30, TRUE),
          ('pms.brands', '/pms/brands', 40, TRUE),
          ('pms.categories', '/pms/categories', 50, TRUE),
          ('pms.item_attributes', '/pms/item-attribute-defs', 60, TRUE),
          ('pms.sku_coding', '/items/sku-coding', 70, TRUE)
        ON CONFLICT (route_prefix) DO UPDATE SET
          page_code = EXCLUDED.page_code,
          sort_order = EXCLUDED.sort_order,
          is_active = EXCLUDED.is_active
        """
    )


def downgrade() -> None:
    op.drop_index("ix_page_route_prefixes_page_code", table_name="page_route_prefixes")
    op.drop_table("page_route_prefixes")

    op.drop_index("ix_page_registry_parent_code", table_name="page_registry")
    op.drop_table("page_registry")

    op.drop_index("ix_user_permissions_permission_id", table_name="user_permissions")
    op.drop_table("user_permissions")
    op.drop_table("users")
    op.drop_table("permissions")
