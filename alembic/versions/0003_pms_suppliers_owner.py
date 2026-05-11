"""pms suppliers owner

Revision ID: 0003_pms_suppliers_owner
Revises: 0002_pms_auth_nav_registry
Create Date: 2026-05-12 04:30:00.000000

"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0003_pms_suppliers_owner"
down_revision: str | Sequence[str] | None = "0002_pms_auth_nav_registry"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "suppliers",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("website", sa.String(length=255), nullable=True),
        sa.CheckConstraint("btrim(code) <> ''", name="ck_suppliers_code_nonblank"),
        sa.CheckConstraint("code = btrim(code)", name="ck_suppliers_code_trimmed"),
        sa.CheckConstraint("code = upper(code)", name="ck_suppliers_code_upper"),
        sa.CheckConstraint("btrim(name) <> ''", name="ck_suppliers_name_nonblank"),
        sa.CheckConstraint("name = btrim(name)", name="ck_suppliers_name_trimmed"),
        sa.PrimaryKeyConstraint("id", name="suppliers_pkey"),
        sa.UniqueConstraint("name", name="uq_suppliers_name"),
        sa.UniqueConstraint("code", name="uq_suppliers_code"),
    )
    op.create_index("ix_suppliers_active", "suppliers", ["active"])
    op.create_index("ix_suppliers_name", "suppliers", ["name"])

    op.create_table(
        "supplier_contacts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("supplier_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("wechat", sa.String(length=64), nullable=True),
        sa.Column("role", sa.String(length=32), nullable=False, server_default=sa.text("'other'")),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(
            ["supplier_id"],
            ["suppliers.id"],
            name="supplier_contacts_supplier_id_fkey",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="supplier_contacts_pkey"),
    )
    op.create_index("ix_supplier_contacts_supplier_id", "supplier_contacts", ["supplier_id"])
    op.create_index(
        "uq_supplier_contacts_primary_per_supplier",
        "supplier_contacts",
        ["supplier_id"],
        unique=True,
        postgresql_where=sa.text("is_primary = true"),
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
          ('pms.suppliers', '供应商管理', 'pms', 2, 'pms', FALSE, TRUE, TRUE, NULL, NULL, 80, TRUE)
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
        VALUES ('pms.suppliers', '/pms/suppliers', 80, TRUE)
        ON CONFLICT (route_prefix) DO UPDATE SET
          page_code = EXCLUDED.page_code,
          sort_order = EXCLUDED.sort_order,
          is_active = EXCLUDED.is_active
        """
    )


def downgrade() -> None:
    op.execute("DELETE FROM page_route_prefixes WHERE route_prefix = '/pms/suppliers'")
    op.execute("DELETE FROM page_registry WHERE code = 'pms.suppliers'")

    op.drop_index("uq_supplier_contacts_primary_per_supplier", table_name="supplier_contacts")
    op.drop_index("ix_supplier_contacts_supplier_id", table_name="supplier_contacts")
    op.drop_table("supplier_contacts")

    op.drop_index("ix_suppliers_name", table_name="suppliers")
    op.drop_index("ix_suppliers_active", table_name="suppliers")
    op.drop_table("suppliers")
