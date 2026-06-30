#!/usr/bin/env bash
set -euo pipefail

CATALOG_NAME="${CATALOG_NAME:-access_drift_dev}"
SCHEMA_NAMES="${SCHEMA_NAMES:-bronze silver intermediate gold eval context}"
TABLE_NAMES="${TABLE_NAMES:-context.asset_context context.assignment_routing}"
EXTERNAL_LOCATION_NAME="${EXTERNAL_LOCATION_NAME:-access_drift_lakehouse_ext}"
CATALOG_PRIVILEGES="${CATALOG_PRIVILEGES-ALL_PRIVILEGES}"
SCHEMA_PRIVILEGES="${SCHEMA_PRIVILEGES-ALL_PRIVILEGES}"
TABLE_PRIVILEGES="${TABLE_PRIVILEGES-ALL_PRIVILEGES}"
EXTERNAL_LOCATION_PRIVILEGES="${EXTERNAL_LOCATION_PRIVILEGES-ALL_PRIVILEGES}"
WORKSPACE_ID="${WORKSPACE_ID:-7405615323116390}"
DATABRICKS_HOST="${DATABRICKS_HOST:-https://adb-${WORKSPACE_ID}.10.azuredatabricks.net}"
export DATABRICKS_HOST

if [[ -z "${PRINCIPALS:-}" ]]; then
  echo "PRINCIPALS is required. Example:" >&2
  echo "  PRINCIPALS=\"user1@example.com user2@example.com\" $0" >&2
  exit 1
fi

dbx() {
  databricks "$@"
}

json_array() {
  local out=""
  local value
  for value in "$@"; do
    if [[ -n "$out" ]]; then
      out+=","
    fi
    out+="\"${value}\""
  done
  printf '[%s]' "$out"
}

grant_privileges() {
  local securable_type="$1"
  local full_name="$2"
  local principal="$3"
  shift 3
  if [[ "$#" -eq 0 ]]; then
    echo "Skipping ${securable_type} ${full_name} for ${principal}: no privileges requested"
    return 0
  fi

  local privileges_json
  privileges_json="$(json_array "$@")"

  echo "Granting ${securable_type} ${full_name} to ${principal}: ${privileges_json}"
  dbx grants update "$securable_type" "$full_name" \
    --json "{\"changes\":[{\"principal\":\"${principal}\",\"add\":${privileges_json}}]}" >/dev/null
}

echo "Checking Azure CLI authentication..."
az account show >/dev/null 2>&1 || { echo "az login이 필요합니다." >&2; exit 1; }

TENANT_ID="$(az account show --query tenantId -o tsv)"
export ARM_TENANT_ID="$TENANT_ID"
export DATABRICKS_AUTH_TYPE=azure-cli
unset DATABRICKS_CONFIG_PROFILE
export DATABRICKS_CONFIG_FILE=/dev/null

echo "Checking Databricks authentication..."
dbx current-user me >/dev/null

declare -a catalog_privileges=()
declare -a schema_privileges=()
declare -a table_privileges=()
declare -a external_location_privileges=()
read -r -a catalog_privileges <<< "$CATALOG_PRIVILEGES"
read -r -a schema_privileges <<< "$SCHEMA_PRIVILEGES"
read -r -a table_privileges <<< "$TABLE_PRIVILEGES"
read -r -a external_location_privileges <<< "$EXTERNAL_LOCATION_PRIVILEGES"
read -r -a principals <<< "$PRINCIPALS"

for principal in "${principals[@]}"; do
  if [[ -n "$CATALOG_PRIVILEGES" ]]; then
    grant_privileges catalog "$CATALOG_NAME" "$principal" "${catalog_privileges[@]}"
  else
    echo "Skipping catalog ${CATALOG_NAME} for ${principal}: no privileges requested"
  fi

  for schema_name in $SCHEMA_NAMES; do
    if [[ -n "$SCHEMA_PRIVILEGES" ]]; then
      grant_privileges schema "${CATALOG_NAME}.${schema_name}" "$principal" "${schema_privileges[@]}"
    else
      echo "Skipping schema ${CATALOG_NAME}.${schema_name} for ${principal}: no privileges requested"
    fi
  done

  for table_name in $TABLE_NAMES; do
    if [[ -n "$TABLE_PRIVILEGES" ]]; then
      grant_privileges table "${CATALOG_NAME}.${table_name}" "$principal" "${table_privileges[@]}"
    else
      echo "Skipping table ${CATALOG_NAME}.${table_name} for ${principal}: no privileges requested"
    fi
  done

  if [[ -n "$EXTERNAL_LOCATION_PRIVILEGES" ]]; then
    grant_privileges external_location "$EXTERNAL_LOCATION_NAME" "$principal" "${external_location_privileges[@]}"
  else
    echo "Skipping external_location ${EXTERNAL_LOCATION_NAME} for ${principal}: no privileges requested"
  fi
done

echo "Catalog grants:"
dbx grants get catalog "$CATALOG_NAME"

for schema_name in $SCHEMA_NAMES; do
  echo "Schema grants: ${CATALOG_NAME}.${schema_name}"
  dbx grants get schema "${CATALOG_NAME}.${schema_name}"
done

for table_name in $TABLE_NAMES; do
  echo "Table grants: ${CATALOG_NAME}.${table_name}"
  dbx grants get table "${CATALOG_NAME}.${table_name}"
done

echo "External location grants: ${EXTERNAL_LOCATION_NAME}"
dbx grants get external_location "$EXTERNAL_LOCATION_NAME"

echo "User permission grants complete."
