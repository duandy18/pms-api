#!/usr/bin/env bash
set -Eeuo pipefail

SOURCE_DSN="${PMS_SUPPLIER_SOURCE_PSQL_DSN:-postgres://wms:wms@127.0.0.1:5433/wms}"
TARGET_DSN="${PMS_SUPPLIER_TARGET_PSQL_DSN:-postgres://pms:pms@127.0.0.1:5433/pms}"
EXPORT_DIR="${PMS_SUPPLIER_EXPORT_DIR:-/tmp/pms_suppliers_export_$(date +%Y%m%d_%H%M%S)}"

mkdir -p "${EXPORT_DIR}"

echo "===== settings ====="
echo "SOURCE_DSN=${SOURCE_DSN}"
echo "TARGET_DSN=${TARGET_DSN}"
echo "EXPORT_DIR=${EXPORT_DIR}"

EXPORT_SQL="${EXPORT_DIR}/export_suppliers.sql"
IMPORT_SQL="${EXPORT_DIR}/import_suppliers.sql"

cat > "${EXPORT_SQL}" <<SQL
\\copy (SELECT id, name, code, active, created_at, updated_at, website FROM suppliers ORDER BY id) TO '${EXPORT_DIR}/suppliers.csv' CSV HEADER
\\copy (SELECT id, supplier_id, name, phone, email, wechat, role, is_primary, active, created_at, updated_at FROM supplier_contacts ORDER BY id) TO '${EXPORT_DIR}/supplier_contacts.csv' CSV HEADER
SQL

cat > "${IMPORT_SQL}" <<SQL
BEGIN;
TRUNCATE supplier_contacts, suppliers RESTART IDENTITY CASCADE;
\\copy suppliers (id, name, code, active, created_at, updated_at, website) FROM '${EXPORT_DIR}/suppliers.csv' CSV HEADER
\\copy supplier_contacts (id, supplier_id, name, phone, email, wechat, role, is_primary, active, created_at, updated_at) FROM '${EXPORT_DIR}/supplier_contacts.csv' CSV HEADER
SELECT setval(pg_get_serial_sequence('suppliers', 'id'), COALESCE((SELECT MAX(id) FROM suppliers), 0) + 1, false);
SELECT setval(pg_get_serial_sequence('supplier_contacts', 'id'), COALESCE((SELECT MAX(id) FROM supplier_contacts), 0) + 1, false);
COMMIT;
SQL

echo
echo "===== export suppliers from WMS ====="
psql -v ON_ERROR_STOP=1 "${SOURCE_DSN}" -f "${EXPORT_SQL}"

echo
echo "===== import suppliers into PMS ====="
psql -v ON_ERROR_STOP=1 "${TARGET_DSN}" -f "${IMPORT_SQL}"

echo
echo "===== row count check ====="
psql -P pager=off -v ON_ERROR_STOP=1 "${SOURCE_DSN}" -c "
SELECT 'source_suppliers' AS table_name, count(*) FROM suppliers
UNION ALL
SELECT 'source_supplier_contacts', count(*) FROM supplier_contacts
ORDER BY table_name;
"

psql -P pager=off -v ON_ERROR_STOP=1 "${TARGET_DSN}" -c "
SELECT 'target_suppliers' AS table_name, count(*) FROM suppliers
UNION ALL
SELECT 'target_supplier_contacts', count(*) FROM supplier_contacts
ORDER BY table_name;
"

echo
echo "SUPPLIER_EXPORT_DIR=${EXPORT_DIR}"
