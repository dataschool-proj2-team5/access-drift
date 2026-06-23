#!/usr/bin/env bash
set -euo pipefail

RESOURCE_GROUP="${RESOURCE_GROUP:-dt4_project2_team5}"
ACCESS_CONNECTOR_NAME="${ACCESS_CONNECTOR_NAME:-acdrift-uc-access}"
STORAGE_ACCOUNT_NAME="${STORAGE_ACCOUNT_NAME:-acdriftadls}"
CATALOG_NAME="${CATALOG_NAME:-access_drift}"
STORAGE_CREDENTIAL_NAME="${STORAGE_CREDENTIAL_NAME:-access_drift_storage_cred}"
CATALOG_STORAGE_ROOT="${CATALOG_STORAGE_ROOT:-abfss://gold@${STORAGE_ACCOUNT_NAME}.dfs.core.windows.net/managed/${CATALOG_NAME}}"
WORKSPACE_ID="${WORKSPACE_ID:-7405615323116390}"
SKIP_VALIDATION="${SKIP_VALIDATION:-false}"

CONTAINERS=(landing bronze silver intermediate gold)

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
    printf '{"name":"%s","azure_managed_identity":{"access_connector_id":"%s"},"comment":"Access Drift PoC ADLS credential"}' \
      "$STORAGE_CREDENTIAL_NAME" \
      "$ACCESS_CONNECTOR_ID"
  )"
  with_validation_args dbx storage-credentials create \
    --json "$credential_json"
fi

for container in "${CONTAINERS[@]}"; do
  location_name="access_drift_${container}_ext"
  location_url="abfss://${container}@${STORAGE_ACCOUNT_NAME}.dfs.core.windows.net/"

  if exists dbx external-locations get "$location_name"; then
    echo "External location exists: $location_name"
  else
    echo "Creating external location: $location_name -> $location_url"
    with_validation_args dbx external-locations create "$location_name" "$location_url" "$STORAGE_CREDENTIAL_NAME" \
      --comment "Access Drift ${container} container"
  fi
done

if exists dbx catalogs get "$CATALOG_NAME"; then
  echo "Catalog exists: $CATALOG_NAME"
else
  echo "Creating catalog: $CATALOG_NAME"
  dbx catalogs create "$CATALOG_NAME" \
    --comment "Access Drift PoC catalog" \
    --storage-root "$CATALOG_STORAGE_ROOT"
fi

echo "Restricting catalog to workspace: $WORKSPACE_ID"
dbx catalogs update "$CATALOG_NAME" --isolation-mode ISOLATED >/dev/null
dbx workspace-bindings update-bindings catalog "$CATALOG_NAME" \
  --json "{\"add\":[{\"workspace_id\":${WORKSPACE_ID},\"binding_type\":\"BINDING_TYPE_READ_WRITE\"}]}" >/dev/null

for schema in "${CONTAINERS[@]}"; do
  full_name="${CATALOG_NAME}.${schema}"
  if exists dbx schemas get "$full_name"; then
    echo "Schema exists: $full_name"
  else
    echo "Creating schema: $full_name"
    dbx schemas create "$schema" "$CATALOG_NAME" --comment "Access Drift ${schema} schema"
  fi
done

echo "Unity Catalog bootstrap complete."
