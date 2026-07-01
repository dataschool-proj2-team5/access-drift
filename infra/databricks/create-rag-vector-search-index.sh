#!/usr/bin/env bash
set -euo pipefail

WORKSPACE_ID="${WORKSPACE_ID:-7405615323116390}"
DATABRICKS_HOST="${DATABRICKS_HOST:-https://adb-${WORKSPACE_ID}.10.azuredatabricks.net}"
ENDPOINT_NAME="${ENDPOINT_NAME:-access-drift-rag-dev}"
INDEX_NAME="${INDEX_NAME:-access_drift_dev.rag.knowledge_chunks_index}"
SOURCE_TABLE="${SOURCE_TABLE:-access_drift_dev.rag.knowledge_chunks}"
PRIMARY_KEY="${PRIMARY_KEY:-chunk_id}"
EMBEDDING_MODEL_ENDPOINT_NAME="${EMBEDDING_MODEL_ENDPOINT_NAME:-databricks-gte-large-en}"
PIPELINE_TYPE="${PIPELINE_TYPE:-TRIGGERED}"

export DATABRICKS_HOST

echo "Checking Azure CLI authentication..."
az account show >/dev/null 2>&1 || { echo "az login이 필요합니다." >&2; exit 1; }

TENANT_ID="$(az account show --query tenantId -o tsv)"
export ARM_TENANT_ID="$TENANT_ID"
export DATABRICKS_AUTH_TYPE=azure-cli
unset DATABRICKS_CONFIG_PROFILE
export DATABRICKS_CONFIG_FILE=/dev/null

dbx() {
  databricks "$@"
}

echo "Checking Databricks authentication..."
dbx current-user me >/dev/null

if dbx vector-search-endpoints get-endpoint "$ENDPOINT_NAME" >/dev/null 2>&1; then
  echo "Vector Search endpoint exists: $ENDPOINT_NAME"
else
  echo "Creating Vector Search endpoint: $ENDPOINT_NAME"
  dbx vector-search-endpoints create-endpoint "$ENDPOINT_NAME" STANDARD
fi

if dbx vector-search-indexes get-index "$INDEX_NAME" >/dev/null 2>&1; then
  echo "Vector Search index exists: $INDEX_NAME"
else
  echo "Creating Delta Sync Vector Search index: $INDEX_NAME"
  dbx vector-search-indexes create-index "$INDEX_NAME" "$ENDPOINT_NAME" "$PRIMARY_KEY" DELTA_SYNC \
    --json "{
      \"delta_sync_index_spec\": {
        \"source_table\": \"${SOURCE_TABLE}\",
        \"pipeline_type\": \"${PIPELINE_TYPE}\",
        \"embedding_source_columns\": [
          {
            \"name\": \"chunk_text\",
            \"embedding_model_endpoint_name\": \"${EMBEDDING_MODEL_ENDPOINT_NAME}\"
          }
        ],
        \"columns_to_sync\": [
          \"chunk_id\",
          \"risk_case_key\",
          \"chunk_text\",
          \"chunk_hash\",
          \"chunk_order\",
          \"source_title\",
          \"source_uri\",
          \"source_table_refs\",
          \"evidence_keys\",
          \"generated_at\"
        ]
      }
    }"
fi

echo "Vector Search endpoint:"
dbx vector-search-endpoints get-endpoint "$ENDPOINT_NAME"

echo "Vector Search index:"
dbx vector-search-indexes get-index "$INDEX_NAME"
