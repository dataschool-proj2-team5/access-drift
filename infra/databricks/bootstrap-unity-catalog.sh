#!/usr/bin/env bash
set -euo pipefail

RESOURCE_GROUP="${RESOURCE_GROUP:-dt4_project2_team5}"
ACCESS_CONNECTOR_NAME="${ACCESS_CONNECTOR_NAME:-acdrift-uc-access}"
STORAGE_ACCOUNT_NAME="${STORAGE_ACCOUNT_NAME:-acdriftadls}"
CATALOG_NAME="${CATALOG_NAME:-access_drift}"
SCHEMA_NAMES="${SCHEMA_NAMES:-bronze silver intermediate gold eval context}"
GRANT_PRINCIPAL="${GRANT_PRINCIPAL:-}"
STORAGE_CREDENTIAL_NAME="${STORAGE_CREDENTIAL_NAME:-access_drift_storage_cred}"
CONTAINER_NAME="${CONTAINER_NAME:-lakehouse}"
EXTERNAL_LOCATION_NAME="${EXTERNAL_LOCATION_NAME:-access_drift_lakehouse_ext}"
EXTERNAL_LOCATION_URL="${EXTERNAL_LOCATION_URL:-abfss://${CONTAINER_NAME}@${STORAGE_ACCOUNT_NAME}.dfs.core.windows.net/}"
CATALOG_STORAGE_ROOT="${CATALOG_STORAGE_ROOT:-abfss://${CONTAINER_NAME}@${STORAGE_ACCOUNT_NAME}.dfs.core.windows.net/managed/${CATALOG_NAME}}"
WORKSPACE_ID="${WORKSPACE_ID:-7405615323116390}"
DATABRICKS_HOST="${DATABRICKS_HOST:-https://adb-${WORKSPACE_ID}.10.azuredatabricks.net}"
export DATABRICKS_HOST
SKIP_VALIDATION="${SKIP_VALIDATION:-false}"


PROFILE_ARGS=()
if [[ -n "${DATABRICKS_CONFIG_PROFILE:-}" ]]; then
  PROFILE_ARGS=(-p "$DATABRICKS_CONFIG_PROFILE")
fi

dbx() {
  if [[ ${#PROFILE_ARGS[@]} -gt 0 ]]; then
    databricks "${PROFILE_ARGS[@]}" "$@"
  else
    databricks "$@"
  fi
}

exists() {
  "$@" >/dev/null 2>&1
}

validation_args=()
if [[ "$SKIP_VALIDATION" == "true" ]]; then
  validation_args=(--skip-validation)
fi

with_validation_args() {
  if [[ ${#validation_args[@]} -gt 0 ]]; then
    "$@" "${validation_args[@]}"
  else
    "$@"
  fi
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

echo "Resolving Azure Databricks Access Connector..."
ACCESS_CONNECTOR_ID="$(
  az resource show \
    --resource-group "$RESOURCE_GROUP" \
    --resource-type Microsoft.Databricks/accessConnectors \
    --name "$ACCESS_CONNECTOR_NAME" \
    --query id \
    -o tsv
)"

if [[ -z "$ACCESS_CONNECTOR_ID" ]]; then
  echo "Access Connector not found: $ACCESS_CONNECTOR_NAME" >&2
  exit 1
fi

echo "Using Access Connector: $ACCESS_CONNECTOR_ID"

if exists dbx storage-credentials get "$STORAGE_CREDENTIAL_NAME"; then
  echo "Storage credential exists: $STORAGE_CREDENTIAL_NAME"
else
  echo "Creating storage credential: $STORAGE_CREDENTIAL_NAME"
  credential_json="$(
    printf '{"name":"%s","azure_managed_identity":{"access_connector_id":"%s"},"comment":"Access Drift ADLS credential"}' \
      "$STORAGE_CREDENTIAL_NAME" \
      "$ACCESS_CONNECTOR_ID"
  )"
  with_validation_args dbx storage-credentials create \
    --json "$credential_json"
fi

if exists dbx external-locations get "$EXTERNAL_LOCATION_NAME"; then
  echo "External location exists: $EXTERNAL_LOCATION_NAME"
else
  echo "Creating external location: $EXTERNAL_LOCATION_NAME -> $EXTERNAL_LOCATION_URL"
  with_validation_args dbx external-locations create "$EXTERNAL_LOCATION_NAME" "$EXTERNAL_LOCATION_URL" "$STORAGE_CREDENTIAL_NAME" \
    --comment "Access Drift lakehouse container"
fi

if exists dbx catalogs get "$CATALOG_NAME"; then
  echo "Catalog exists: $CATALOG_NAME"
else
  echo "Creating catalog: $CATALOG_NAME"
  dbx catalogs create "$CATALOG_NAME" \
    --comment "Access Drift catalog" \
    --storage-root "$CATALOG_STORAGE_ROOT"
fi

echo "Restricting catalog to workspace: $WORKSPACE_ID"
dbx catalogs update "$CATALOG_NAME" --isolation-mode ISOLATED >/dev/null
dbx workspace-bindings update-bindings catalog "$CATALOG_NAME" \
  --json "{\"add\":[{\"workspace_id\":${WORKSPACE_ID},\"binding_type\":\"BINDING_TYPE_READ_WRITE\"}]}" >/dev/null

for schema_name in $SCHEMA_NAMES; do
  if exists dbx schemas get "${CATALOG_NAME}.${schema_name}"; then
    echo "Schema exists: ${CATALOG_NAME}.${schema_name}"
  else
    echo "Creating schema: ${CATALOG_NAME}.${schema_name}"
    dbx schemas create "$schema_name" "$CATALOG_NAME" \
      --comment "Access Drift ${schema_name} schema"
  fi
done

if [[ -n "$GRANT_PRINCIPAL" ]]; then
  echo "Granting dev permissions to principal: $GRANT_PRINCIPAL"
  if ! dbx grants update catalog "$CATALOG_NAME" \
    --json "{\"changes\":[{\"principal\":\"${GRANT_PRINCIPAL}\",\"add\":[\"USE_CATALOG\"]}]}" >/dev/null; then
    echo "Failed to grant catalog permissions to: $GRANT_PRINCIPAL" >&2
    echo "Use a Unity Catalog resolvable principal, such as an account-level group, user, or service principal." >&2
    echo "Workspace-local groups can appear in 'databricks groups list' but still fail UC grants with 'Could not find principal'." >&2
    exit 1
  fi

  for schema_name in $SCHEMA_NAMES; do
    if ! dbx grants update schema "${CATALOG_NAME}.${schema_name}" \
      --json "{\"changes\":[{\"principal\":\"${GRANT_PRINCIPAL}\",\"add\":[\"USE_SCHEMA\",\"CREATE_TABLE\",\"SELECT\",\"MODIFY\"]}]}" >/dev/null; then
      echo "Failed to grant schema permissions to: $GRANT_PRINCIPAL on ${CATALOG_NAME}.${schema_name}" >&2
      echo "Use a Unity Catalog resolvable principal, such as an account-level group, user, or service principal." >&2
      echo "Workspace-local groups can appear in 'databricks groups list' but still fail UC grants with 'Could not find principal'." >&2
      exit 1
    fi
  done
else
  echo "Skipping grants. Set GRANT_PRINCIPAL to grant catalog/schema permissions."
fi

echo "Catalog grants:"
dbx grants get catalog "$CATALOG_NAME"

for schema_name in $SCHEMA_NAMES; do
  echo "Schema grants: ${CATALOG_NAME}.${schema_name}"
  dbx grants get schema "${CATALOG_NAME}.${schema_name}"
done

echo "Bootstrap complete."
