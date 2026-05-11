#!/usr/bin/env bash
set -Eeuo pipefail

# PMS split export/import script.
#
# Purpose:
# - Export PMS owner tables from the current WMS database.
# - Build / upgrade a target PMS database.
# - Import PMS owner data into the target PMS database.
# - Validate row counts, sequence positions, and FK boundary.
#
# Boundary:
# - This script migrates PMS owner tables only.
# - It does not export/import suppliers.
# - items.supplier_id remains a nullable scalar.
# - It must not create PMS -> non-PMS physical FKs.
#
# Default mode is local dry-run:
#   source = postgres://wms:wms@127.0.0.1:5433/wms
#   target = pms_dryrun
#
# Formal migration should pass explicit PMS_SPLIT_* env vars.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

SOURCE_PSQL_DSN="${PMS_SPLIT_SOURCE_PSQL_DSN:-postgres://wms:wms@127.0.0.1:5433/wms}"

TARGET_DB_NAME="${PMS_SPLIT_TARGET_DB_NAME:-pms_dryrun}"
TARGET_PSQL_DSN="${PMS_SPLIT_TARGET_PSQL_DSN:-postgres://wms:wms@127.0.0.1:5433/${TARGET_DB_NAME}}"
TARGET_SQLA_DSN="${PMS_SPLIT_TARGET_SQLA_DSN:-postgresql+psycopg://wms:wms@127.0.0.1:5433/${TARGET_DB_NAME}}"

ADMIN_HOST="${PMS_SPLIT_ADMIN_HOST:-127.0.0.1}"
ADMIN_PORT="${PMS_SPLIT_ADMIN_PORT:-5433}"
ADMIN_USER="${PMS_SPLIT_ADMIN_USER:-wms}"
ADMIN_DB="${PMS_SPLIT_ADMIN_DB:-postgres}"

RESET_TARGET="${PMS_SPLIT_RESET_TARGET:-1}"
ALLOW_NON_EMPTY_TARGET="${PMS_SPLIT_ALLOW_NON_EMPTY_TARGET:-0}"
EXPORT_DIR="${PMS_SPLIT_EXPORT_DIR:-/tmp/pms_split_export_$(date +%Y%m%d_%H%M%S)}"

PYTHON_BIN="${PYTHON_BIN:-.venv/bin/python}"

PMS_TABLES=(
  pms_brands
  pms_business_categories
  item_attribute_defs
  item_attribute_options
  items
  item_uoms
  item_sku_codes
  item_barcodes
  item_attribute_values
  sku_code_templates
  sku_code_template_segments
)

log() {
  printf '\n===== %s =====\n' "$*"
}

psql_source() {
  psql -v ON_ERROR_STOP=1 "${SOURCE_PSQL_DSN}" "$@"
}

psql_target() {
  psql -v ON_ERROR_STOP=1 "${TARGET_PSQL_DSN}" "$@"
}

copy_source() {
  local query="$1"
  local file="$2"
  psql_source -c "\\copy (${query}) TO '${file}' CSV HEADER"
}

copy_target() {
  local table_and_columns="$1"
  local file="$2"
  psql_target -c "\\copy ${table_and_columns} FROM '${file}' CSV HEADER"
}

target_total_rows() {
  psql -At "${TARGET_PSQL_DSN}" -v ON_ERROR_STOP=1 -c "
    select coalesce(sum(row_count), 0)::bigint
    from (
      select count(*) as row_count from pms_brands
      union all select count(*) from pms_business_categories
      union all select count(*) from item_attribute_defs
      union all select count(*) from item_attribute_options
      union all select count(*) from items
      union all select count(*) from item_uoms
      union all select count(*) from item_sku_codes
      union all select count(*) from item_barcodes
      union all select count(*) from item_attribute_values
      union all select count(*) from sku_code_templates
      union all select count(*) from sku_code_template_segments
    ) s;
  "
}

print_counts() {
  local dsn="$1"
  psql -P pager=off "${dsn}" -c "
    select 'items' as table_name, count(*) from items
    union all select 'item_uoms', count(*) from item_uoms
    union all select 'item_barcodes', count(*) from item_barcodes
    union all select 'item_sku_codes', count(*) from item_sku_codes
    union all select 'pms_brands', count(*) from pms_brands
    union all select 'pms_business_categories', count(*) from pms_business_categories
    union all select 'item_attribute_defs', count(*) from item_attribute_defs
    union all select 'item_attribute_options', count(*) from item_attribute_options
    union all select 'item_attribute_values', count(*) from item_attribute_values
    union all select 'sku_code_templates', count(*) from sku_code_templates
    union all select 'sku_code_template_segments', count(*) from sku_code_template_segments
    order by table_name;
  "
}

print_max_ids() {
  local dsn="$1"
  psql -P pager=off "${dsn}" -c "
    select 'items' as table_name, max(id)::bigint as max_id from items
    union all select 'item_uoms', max(id)::bigint from item_uoms
    union all select 'item_barcodes', max(id)::bigint from item_barcodes
    union all select 'item_sku_codes', max(id)::bigint from item_sku_codes
    union all select 'pms_brands', max(id)::bigint from pms_brands
    union all select 'pms_business_categories', max(id)::bigint from pms_business_categories
    union all select 'item_attribute_defs', max(id)::bigint from item_attribute_defs
    union all select 'item_attribute_options', max(id)::bigint from item_attribute_options
    union all select 'item_attribute_values', max(id)::bigint from item_attribute_values
    union all select 'sku_code_templates', max(id)::bigint from sku_code_templates
    union all select 'sku_code_template_segments', max(id)::bigint from sku_code_template_segments
    order by table_name;
  "
}

print_non_pms_fks() {
  local dsn="$1"
  psql -P pager=off "${dsn}" -c "
    with pms_tables(table_name) as (
      values
        ('items'),
        ('item_uoms'),
        ('item_barcodes'),
        ('item_sku_codes'),
        ('pms_brands'),
        ('pms_business_categories'),
        ('item_attribute_defs'),
        ('item_attribute_options'),
        ('item_attribute_values'),
        ('sku_code_templates'),
        ('sku_code_template_segments')
    )
    select
      c.conname,
      c.conrelid::regclass::text as pms_table,
      c.confrelid::regclass::text as referenced_table,
      pg_get_constraintdef(c.oid) as constraint_def
    from pg_constraint c
    join pms_tables p on p.table_name = c.conrelid::regclass::text
    where c.contype = 'f'
      and not exists (
        select 1 from pms_tables p2
        where p2.table_name = c.confrelid::regclass::text
      )
    order by pms_table, conname;
  "
}

log "settings"
cat <<TXT
SOURCE_PSQL_DSN=${SOURCE_PSQL_DSN}
TARGET_DB_NAME=${TARGET_DB_NAME}
TARGET_PSQL_DSN=${TARGET_PSQL_DSN}
TARGET_SQLA_DSN=${TARGET_SQLA_DSN}
RESET_TARGET=${RESET_TARGET}
ALLOW_NON_EMPTY_TARGET=${ALLOW_NON_EMPTY_TARGET}
EXPORT_DIR=${EXPORT_DIR}
TXT

mkdir -p "${EXPORT_DIR}"

if [[ "${RESET_TARGET}" == "1" ]]; then
  log "reset target PMS DB"
  PGPASSWORD="${PGPASSWORD:-wms}" psql \
    -h "${ADMIN_HOST}" \
    -p "${ADMIN_PORT}" \
    -U "${ADMIN_USER}" \
    "${ADMIN_DB}" \
    -c "DROP DATABASE IF EXISTS ${TARGET_DB_NAME};"

  PGPASSWORD="${PGPASSWORD:-wms}" psql \
    -h "${ADMIN_HOST}" \
    -p "${ADMIN_PORT}" \
    -U "${ADMIN_USER}" \
    "${ADMIN_DB}" \
    -c "CREATE DATABASE ${TARGET_DB_NAME};"
fi

log "upgrade target PMS DB"
PMS_DATABASE_URL="${TARGET_SQLA_DSN}" PYTHONPATH=. "${PYTHON_BIN}" -m alembic upgrade head

log "target emptiness guard"
target_rows="$(target_total_rows)"
echo "target_total_rows=${target_rows}"
if [[ "${target_rows}" != "0" && "${ALLOW_NON_EMPTY_TARGET}" != "1" ]]; then
  echo "ERROR: target PMS tables are not empty. Set PMS_SPLIT_ALLOW_NON_EMPTY_TARGET=1 only if this is intentional." >&2
  exit 23
fi

log "export PMS owner data from source"
copy_source "select id, name_cn, code, is_active, is_locked, sort_order, remark, created_at, updated_at from pms_brands order by id" "${EXPORT_DIR}/pms_brands.csv"
copy_source "select id, parent_id, level, product_kind, category_name, category_code, path_code, is_leaf, is_active, is_locked, sort_order, remark, created_at, updated_at from pms_business_categories order by level asc, id asc" "${EXPORT_DIR}/pms_business_categories.csv"
copy_source "select id, code, name_cn, name_en, product_kind, value_type, unit, is_sku_segment, is_active, sort_order, remark, created_at, updated_at, selection_mode, is_item_required, is_sku_required, is_locked from item_attribute_defs order by id" "${EXPORT_DIR}/item_attribute_defs.csv"
copy_source "select id, attribute_def_id, option_code, option_name, is_active, sort_order, created_at, updated_at, is_locked from item_attribute_options order by id" "${EXPORT_DIR}/item_attribute_options.csv"
copy_source "select id, sku, name, created_at, updated_at, spec, enabled, supplier_id, shelf_life_value, shelf_life_unit, lot_source_policy, expiry_policy, derivation_allowed, uom_governance_enabled, brand_id, category_id from items order by id" "${EXPORT_DIR}/items.csv"
copy_source "select id, item_id, uom, ratio_to_base, display_name, is_base, is_purchase_default, is_inbound_default, is_outbound_default, created_at, updated_at, net_weight_kg from item_uoms order by id" "${EXPORT_DIR}/item_uoms.csv"
copy_source "select id, item_id, code, code_type, is_primary, is_active, effective_from, effective_to, remark, created_at, updated_at from item_sku_codes order by id" "${EXPORT_DIR}/item_sku_codes.csv"
copy_source "select id, item_id, barcode, active, created_at, is_primary, updated_at, item_uom_id, symbology from item_barcodes order by id" "${EXPORT_DIR}/item_barcodes.csv"
copy_source "select id, item_id, attribute_def_id, value_text, value_number, value_bool, value_option_id, value_option_code_snapshot, value_unit_snapshot, created_at, updated_at from item_attribute_values order by id" "${EXPORT_DIR}/item_attribute_values.csv"
copy_source "select id, template_code, product_kind, template_name, prefix, separator, is_active, remark, created_at, updated_at from sku_code_templates order by id" "${EXPORT_DIR}/sku_code_templates.csv"
copy_source "select id, template_id, segment_key, source_type, is_required, is_multi_select, sort_order, created_at, updated_at, attribute_def_id from sku_code_template_segments order by id" "${EXPORT_DIR}/sku_code_template_segments.csv"

log "import PMS owner data into target"
copy_target "pms_brands (id, name_cn, code, is_active, is_locked, sort_order, remark, created_at, updated_at)" "${EXPORT_DIR}/pms_brands.csv"
copy_target "pms_business_categories (id, parent_id, level, product_kind, category_name, category_code, path_code, is_leaf, is_active, is_locked, sort_order, remark, created_at, updated_at)" "${EXPORT_DIR}/pms_business_categories.csv"
copy_target "item_attribute_defs (id, code, name_cn, name_en, product_kind, value_type, unit, is_sku_segment, is_active, sort_order, remark, created_at, updated_at, selection_mode, is_item_required, is_sku_required, is_locked)" "${EXPORT_DIR}/item_attribute_defs.csv"
copy_target "item_attribute_options (id, attribute_def_id, option_code, option_name, is_active, sort_order, created_at, updated_at, is_locked)" "${EXPORT_DIR}/item_attribute_options.csv"
copy_target "items (id, sku, name, created_at, updated_at, spec, enabled, supplier_id, shelf_life_value, shelf_life_unit, lot_source_policy, expiry_policy, derivation_allowed, uom_governance_enabled, brand_id, category_id)" "${EXPORT_DIR}/items.csv"
copy_target "item_uoms (id, item_id, uom, ratio_to_base, display_name, is_base, is_purchase_default, is_inbound_default, is_outbound_default, created_at, updated_at, net_weight_kg)" "${EXPORT_DIR}/item_uoms.csv"
copy_target "item_sku_codes (id, item_id, code, code_type, is_primary, is_active, effective_from, effective_to, remark, created_at, updated_at)" "${EXPORT_DIR}/item_sku_codes.csv"
copy_target "item_barcodes (id, item_id, barcode, active, created_at, is_primary, updated_at, item_uom_id, symbology)" "${EXPORT_DIR}/item_barcodes.csv"
copy_target "item_attribute_values (id, item_id, attribute_def_id, value_text, value_number, value_bool, value_option_id, value_option_code_snapshot, value_unit_snapshot, created_at, updated_at)" "${EXPORT_DIR}/item_attribute_values.csv"
copy_target "sku_code_templates (id, template_code, product_kind, template_name, prefix, separator, is_active, remark, created_at, updated_at)" "${EXPORT_DIR}/sku_code_templates.csv"
copy_target "sku_code_template_segments (id, template_id, segment_key, source_type, is_required, is_multi_select, sort_order, created_at, updated_at, attribute_def_id)" "${EXPORT_DIR}/sku_code_template_segments.csv"

log "reset target sequences"
psql_target -c "
  select setval(pg_get_serial_sequence('pms_brands','id'), coalesce((select max(id) from pms_brands), 1), (select count(*) > 0 from pms_brands));
  select setval(pg_get_serial_sequence('pms_business_categories','id'), coalesce((select max(id) from pms_business_categories), 1), (select count(*) > 0 from pms_business_categories));
  select setval(pg_get_serial_sequence('item_attribute_defs','id'), coalesce((select max(id) from item_attribute_defs), 1), (select count(*) > 0 from item_attribute_defs));
  select setval(pg_get_serial_sequence('item_attribute_options','id'), coalesce((select max(id) from item_attribute_options), 1), (select count(*) > 0 from item_attribute_options));
  select setval(pg_get_serial_sequence('items','id'), coalesce((select max(id) from items), 1), (select count(*) > 0 from items));
  select setval(pg_get_serial_sequence('item_uoms','id'), coalesce((select max(id) from item_uoms), 1), (select count(*) > 0 from item_uoms));
  select setval(pg_get_serial_sequence('item_sku_codes','id'), coalesce((select max(id) from item_sku_codes), 1), (select count(*) > 0 from item_sku_codes));
  select setval(pg_get_serial_sequence('item_barcodes','id'), coalesce((select max(id) from item_barcodes), 1), (select count(*) > 0 from item_barcodes));
  select setval(pg_get_serial_sequence('item_attribute_values','id'), coalesce((select max(id) from item_attribute_values), 1), (select count(*) > 0 from item_attribute_values));
  select setval(pg_get_serial_sequence('sku_code_templates','id'), coalesce((select max(id) from sku_code_templates), 1), (select count(*) > 0 from sku_code_templates));
  select setval(pg_get_serial_sequence('sku_code_template_segments','id'), coalesce((select max(id) from sku_code_template_segments), 1), (select count(*) > 0 from sku_code_template_segments));
"

log "source row counts"
print_counts "${SOURCE_PSQL_DSN}"

log "target row counts"
print_counts "${TARGET_PSQL_DSN}"

log "target max ids"
print_max_ids "${TARGET_PSQL_DSN}"

log "target PMS FK to non-PMS tables should be empty"
print_non_pms_fks "${TARGET_PSQL_DSN}"

log "target alembic-check"
PMS_DATABASE_URL="${TARGET_SQLA_DSN}" PYTHONPATH=. "${PYTHON_BIN}" -m alembic check

log "done"
echo "EXPORT_DIR=${EXPORT_DIR}"
