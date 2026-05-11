"""pms owner baseline schema

Revision ID: 0001_pms_owner_baseline_schema
Revises:
Create Date: 2026-05-11 18:20:00.000000

"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0001_pms_owner_baseline_schema"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


LOT_SOURCE_POLICY = postgresql.ENUM(
    "INTERNAL_ONLY",
    "SUPPLIER_ONLY",
    name="lot_source_policy",
    create_type=False,
)

EXPIRY_POLICY = postgresql.ENUM(
    "NONE",
    "REQUIRED",
    name="expiry_policy",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()

    LOT_SOURCE_POLICY.create(bind, checkfirst=True)
    EXPIRY_POLICY.create(bind, checkfirst=True)

    op.create_table(
        "pms_brands",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name_cn", sa.String(length=128), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_locked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id", name="pms_brands_pkey"),
        sa.UniqueConstraint("name_cn", name="uq_pms_brands_name_cn"),
        sa.UniqueConstraint("code", name="uq_pms_brands_code"),
    )

    op.create_table(
        "pms_business_categories",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("product_kind", sa.String(length=16), nullable=False),
        sa.Column("category_name", sa.String(length=128), nullable=False),
        sa.Column("category_code", sa.String(length=32), nullable=False),
        sa.Column("path_code", sa.String(length=255), nullable=False),
        sa.Column("is_leaf", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_locked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("level in (1, 2, 3)", name="ck_pms_business_categories_level"),
        sa.CheckConstraint(
            "product_kind in ('FOOD', 'SUPPLY', 'OTHER')",
            name="ck_pms_business_categories_product_kind",
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["pms_business_categories.id"],
            name="fk_pms_business_categories_parent",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pms_business_categories_pkey"),
        sa.UniqueConstraint("parent_id", "category_code", name="uq_pms_business_categories_parent_code"),
        sa.UniqueConstraint("path_code", name="uq_pms_business_categories_path_code"),
    )
    op.create_index("ix_pms_business_categories_parent_id", "pms_business_categories", ["parent_id"])
    op.create_index("ix_pms_business_categories_product_kind", "pms_business_categories", ["product_kind"])

    op.create_table(
        "items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("sku", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("spec", sa.String(length=128), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("supplier_id", sa.Integer(), nullable=True),
        sa.Column("shelf_life_value", sa.Integer(), nullable=True),
        sa.Column("shelf_life_unit", sa.String(length=16), nullable=True),
        sa.Column("lot_source_policy", LOT_SOURCE_POLICY, nullable=False),
        sa.Column("expiry_policy", EXPIRY_POLICY, nullable=False),
        sa.Column("derivation_allowed", sa.Boolean(), nullable=False),
        sa.Column("uom_governance_enabled", sa.Boolean(), nullable=False),
        sa.Column("brand_id", sa.Integer(), nullable=True),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.CheckConstraint(
            "expiry_policy = 'REQUIRED' OR (shelf_life_value IS NULL AND shelf_life_unit IS NULL)",
            name="ck_items_expiry_policy_vs_shelf_life",
        ),
        sa.CheckConstraint(
            "(shelf_life_value IS NULL) = (shelf_life_unit IS NULL)",
            name="ck_items_shelf_life_pair",
        ),
        sa.CheckConstraint(
            "shelf_life_unit IS NULL OR shelf_life_unit in ('DAY', 'WEEK', 'MONTH', 'YEAR')",
            name="ck_items_shelf_life_unit_enum",
        ),
        sa.CheckConstraint(
            "shelf_life_value IS NULL OR shelf_life_value > 0",
            name="ck_items_shelf_life_value_pos",
        ),
        sa.ForeignKeyConstraint(["brand_id"], ["pms_brands.id"], name="fk_items_brand", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["category_id"], ["pms_business_categories.id"], name="fk_items_category", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="items_pkey"),
        sa.UniqueConstraint("sku", name="items_sku_key"),
    )
    op.create_index("ix_items_brand_id", "items", ["brand_id"])
    op.create_index("ix_items_category_id", "items", ["category_id"])
    op.create_index("ix_items_supplier_id", "items", ["supplier_id"])

    op.create_table(
        "item_uoms",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("uom", sa.String(length=16), nullable=False),
        sa.Column("ratio_to_base", sa.Integer(), nullable=False),
        sa.Column("display_name", sa.String(length=32), nullable=True),
        sa.Column("is_base", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_purchase_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_inbound_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_outbound_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column(
            "net_weight_kg",
            sa.Numeric(10, 3),
            nullable=True,
            comment="净重（kg）。基础包装为真相源；非基础包装默认可按 ratio_to_base 推导；不含包材。",
        ),
        sa.CheckConstraint("ratio_to_base >= 1", name="ck_item_uoms_ratio_ge_1"),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"], name="item_uoms_item_id_fkey", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="item_uoms_pkey"),
        sa.UniqueConstraint("id", "item_id", name="uq_item_uoms_id_item_id"),
        sa.UniqueConstraint("item_id", "uom", name="uq_item_uoms_item_uom"),
    )
    op.create_index("uq_item_uoms_one_base_per_item", "item_uoms", ["item_id"], unique=True, postgresql_where=sa.text("is_base = true"))
    op.create_index("uq_item_uoms_one_inbound_default_per_item", "item_uoms", ["item_id"], unique=True, postgresql_where=sa.text("is_inbound_default = true"))
    op.create_index("uq_item_uoms_one_outbound_default_per_item", "item_uoms", ["item_id"], unique=True, postgresql_where=sa.text("is_outbound_default = true"))
    op.create_index("uq_item_uoms_one_purchase_default_per_item", "item_uoms", ["item_id"], unique=True, postgresql_where=sa.text("is_purchase_default = true"))

    op.create_table(
        "item_sku_codes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=128), nullable=False),
        sa.Column("code_type", sa.String(length=16), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("remark", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("length(trim(code)) > 0", name="ck_item_sku_codes_code_non_empty"),
        sa.CheckConstraint("code_type in ('PRIMARY', 'ALIAS', 'LEGACY', 'MANUAL')", name="ck_item_sku_codes_code_type"),
        sa.CheckConstraint("(is_primary = false) OR (is_active = true)", name="ck_item_sku_codes_primary_active"),
        sa.CheckConstraint("(is_primary = false) OR (effective_to IS NULL)", name="ck_item_sku_codes_primary_no_effective_to"),
        sa.CheckConstraint("((code_type = 'PRIMARY') = (is_primary = true))", name="ck_item_sku_codes_primary_type_matches_flag"),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"], name="fk_item_sku_codes_item", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="item_sku_codes_pkey"),
        sa.UniqueConstraint("code", name="uq_item_sku_codes_code"),
        sa.UniqueConstraint("id", "item_id", name="uq_item_sku_codes_id_item_id"),
    )
    op.create_index("ix_item_sku_codes_item_id", "item_sku_codes", ["item_id"])
    op.create_index("uq_item_sku_codes_one_primary_per_item", "item_sku_codes", ["item_id"], unique=True, postgresql_where=sa.text("is_primary = true"))

    op.create_table(
        "item_barcodes",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("barcode", sa.Text(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("item_uom_id", sa.Integer(), nullable=False),
        sa.Column("symbology", sa.Text(), nullable=False, server_default=sa.text("'CUSTOM'"), comment="条码码制/来源：EAN13 / EAN8 / UPC / UPC12 / GS1 / CUSTOM ..."),
        sa.CheckConstraint("NOT is_primary OR active", name="ck_item_barcodes_primary_must_be_active"),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"], name="item_barcodes_item_id_fkey", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["item_uom_id", "item_id"], ["item_uoms.id", "item_uoms.item_id"], name="fk_item_barcodes_item_uom_pair"),
        sa.PrimaryKeyConstraint("id", name="item_barcodes_pkey"),
        sa.UniqueConstraint("barcode", name="uq_item_barcodes_barcode"),
    )
    op.create_index("ix_item_barcodes_item_id", "item_barcodes", ["item_id"])
    op.create_index("ix_item_barcodes_item_uom_id", "item_barcodes", ["item_uom_id"])
    op.create_index("uq_item_barcodes_primary", "item_barcodes", ["item_id"], unique=True, postgresql_where=sa.text("is_primary = true"))

    op.create_table(
        "item_attribute_defs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name_cn", sa.String(length=128), nullable=False),
        sa.Column("name_en", sa.String(length=128), nullable=True),
        sa.Column("product_kind", sa.String(length=16), nullable=False),
        sa.Column("value_type", sa.String(length=16), nullable=False),
        sa.Column("unit", sa.String(length=16), nullable=True),
        sa.Column("is_sku_segment", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("selection_mode", sa.String(length=16), nullable=False, server_default=sa.text("'SINGLE'")),
        sa.Column("is_item_required", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_sku_required", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_locked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.CheckConstraint("product_kind in ('FOOD', 'SUPPLY', 'OTHER', 'COMMON')", name="ck_item_attribute_defs_product_kind"),
        sa.CheckConstraint("selection_mode in ('SINGLE', 'MULTI')", name="ck_item_attribute_defs_selection_mode"),
        sa.CheckConstraint("value_type in ('TEXT', 'NUMBER', 'OPTION', 'BOOL')", name="ck_item_attribute_defs_value_type"),
        sa.PrimaryKeyConstraint("id", name="item_attribute_defs_pkey"),
        sa.UniqueConstraint("product_kind", "code", name="uq_item_attribute_defs_product_kind_code"),
    )
    op.create_index("ix_item_attribute_defs_product_kind", "item_attribute_defs", ["product_kind"])

    op.create_table(
        "item_attribute_options",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("attribute_def_id", sa.Integer(), nullable=False),
        sa.Column("option_code", sa.String(length=64), nullable=False),
        sa.Column("option_name", sa.String(length=128), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("is_locked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.ForeignKeyConstraint(["attribute_def_id"], ["item_attribute_defs.id"], name="fk_item_attribute_options_def", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="item_attribute_options_pkey"),
        sa.UniqueConstraint("attribute_def_id", "option_code", name="uq_item_attribute_options_def_code"),
    )
    op.create_index("ix_item_attribute_options_def_id", "item_attribute_options", ["attribute_def_id"])

    op.create_table(
        "item_attribute_values",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("attribute_def_id", sa.Integer(), nullable=False),
        sa.Column("value_text", sa.Text(), nullable=True),
        sa.Column("value_number", sa.Numeric(18, 6), nullable=True),
        sa.Column("value_bool", sa.Boolean(), nullable=True),
        sa.Column("value_option_id", sa.Integer(), nullable=True),
        sa.Column("value_option_code_snapshot", sa.String(length=64), nullable=True),
        sa.Column("value_unit_snapshot", sa.String(length=16), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["attribute_def_id"], ["item_attribute_defs.id"], name="fk_item_attribute_values_def", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"], name="fk_item_attribute_values_item", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["value_option_id"], ["item_attribute_options.id"], name="fk_item_attribute_values_option", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="item_attribute_values_pkey"),
    )
    op.create_index("ix_item_attribute_values_def_id", "item_attribute_values", ["attribute_def_id"])
    op.create_index("ix_item_attribute_values_item_id", "item_attribute_values", ["item_id"])
    op.create_index("uq_item_attribute_values_item_def_option", "item_attribute_values", ["item_id", "attribute_def_id", "value_option_id"], unique=True, postgresql_where=sa.text("value_option_id IS NOT NULL"))
    op.create_index("uq_item_attribute_values_item_def_scalar", "item_attribute_values", ["item_id", "attribute_def_id"], unique=True, postgresql_where=sa.text("value_option_id IS NULL"))

    op.create_table(
        "sku_code_templates",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("template_code", sa.String(length=64), nullable=False),
        sa.Column("product_kind", sa.String(length=16), nullable=False),
        sa.Column("template_name", sa.String(length=128), nullable=False),
        sa.Column("prefix", sa.String(length=16), nullable=False, server_default=sa.text("'SKU'")),
        sa.Column("separator", sa.String(length=8), nullable=False, server_default=sa.text("'-'")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("product_kind in ('FOOD', 'SUPPLY')", name="ck_sku_code_templates_product_kind"),
        sa.PrimaryKeyConstraint("id", name="sku_code_templates_pkey"),
        sa.UniqueConstraint("template_code", name="uq_sku_code_templates_template_code"),
    )

    op.create_table(
        "sku_code_template_segments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("template_id", sa.Integer(), nullable=False),
        sa.Column("segment_key", sa.String(length=32), nullable=False),
        sa.Column("source_type", sa.String(length=16), nullable=False),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_multi_select", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("attribute_def_id", sa.Integer(), nullable=True),
        sa.CheckConstraint(
            "(source_type = 'ATTRIBUTE_OPTION' and attribute_def_id is not null) or (source_type <> 'ATTRIBUTE_OPTION' and attribute_def_id is null)",
            name="ck_sku_code_template_segments_attribute_def",
        ),
        sa.CheckConstraint(
            "source_type in ('BRAND', 'CATEGORY', 'ATTRIBUTE_OPTION', 'TEXT', 'SPEC')",
            name="ck_sku_code_template_segments_source_type",
        ),
        sa.ForeignKeyConstraint(["attribute_def_id"], ["item_attribute_defs.id"], name="fk_sku_code_template_segments_attribute_def", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["template_id"], ["sku_code_templates.id"], name="sku_code_template_segments_template_id_fkey", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="sku_code_template_segments_pkey"),
        sa.UniqueConstraint("template_id", "segment_key", name="uq_sku_code_template_segments_template_key"),
    )
    op.create_index("ix_sku_code_template_segments_attribute_def_id", "sku_code_template_segments", ["attribute_def_id"])
    op.create_index("ix_sku_code_template_segments_template_id", "sku_code_template_segments", ["template_id"])


def downgrade() -> None:
    op.drop_table("sku_code_template_segments")
    op.drop_table("sku_code_templates")
    op.drop_table("item_attribute_values")
    op.drop_table("item_attribute_options")
    op.drop_table("item_attribute_defs")
    op.drop_table("item_barcodes")
    op.drop_table("item_sku_codes")
    op.drop_table("item_uoms")
    op.drop_table("items")
    op.drop_table("pms_business_categories")
    op.drop_table("pms_brands")

    bind = op.get_bind()
    EXPIRY_POLICY.drop(bind, checkfirst=True)
    LOT_SOURCE_POLICY.drop(bind, checkfirst=True)
