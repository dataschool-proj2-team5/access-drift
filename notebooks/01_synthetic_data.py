# Databricks notebook source
# 01_synthetic_data — DDL 적용 + seed 데이터를 ADLS raw/ 에 적재

# COMMAND ----------
dbutils.widgets.text("catalog", "access_drift")
dbutils.widgets.text("storage_account", "acdriftadls")

CATALOG = dbutils.widgets.get("catalog")
STORAGE = dbutils.widgets.get("storage_account")
RAW_BASE = f"abfss://lakehouse@{STORAGE}.dfs.core.windows.net/raw"

# COMMAND ----------
# MAGIC %md ## 1. 스키마 생성

# COMMAND ----------
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.bronze")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.silver")
print("schemas ready")

# COMMAND ----------
# MAGIC %md ## 2. Bronze DDL
# 권위 있는 원본: sql/databricks/migrations/001_create_bronze_tables.sql

# COMMAND ----------
META = """
  _src_system       STRING NOT NULL,
  _src_object       STRING NOT NULL,
  _src_file_path    STRING,
  _ingestion_ts     TIMESTAMP NOT NULL,
  _run_id           STRING,
  _batch_id         STRING,
  _checksum         STRING,
  _raw_payload      STRING NOT NULL,
  _schema_version   STRING NOT NULL,
"""

bronze_ddl = [
    f"""CREATE TABLE IF NOT EXISTS {CATALOG}.bronze.bronze_azure_applications (
      {META}
      app_id STRING, display_name STRING, created_at TIMESTAMP
    ) USING DELTA""",
    f"""CREATE TABLE IF NOT EXISTS {CATALOG}.bronze.bronze_azure_application_owners (
      {META}
      app_id STRING, user_principal_name STRING
    ) USING DELTA""",
    f"""CREATE TABLE IF NOT EXISTS {CATALOG}.bronze.bronze_azure_password_credentials (
      {META}
      app_id STRING, key_id STRING, display_name STRING, end_date_time TIMESTAMP, status STRING
    ) USING DELTA""",
    f"""CREATE TABLE IF NOT EXISTS {CATALOG}.bronze.bronze_identity_lifecycle_seed (
      {META}
      user_principal_name STRING, employment_status STRING, termination_date DATE
    ) USING DELTA""",
    f"""CREATE TABLE IF NOT EXISTS {CATALOG}.bronze.bronze_assets_seed (
      {META}
      asset_id STRING, name STRING, environment STRING, sensitivity STRING
    ) USING DELTA""",
    f"""CREATE TABLE IF NOT EXISTS {CATALOG}.bronze.bronze_access_edges_seed (
      {META}
      principal_id STRING, asset_id STRING, relationship STRING, permission STRING, status STRING
    ) USING DELTA""",
]
for ddl in bronze_ddl:
    spark.sql(ddl)
print("bronze tables ready")

# COMMAND ----------
# MAGIC %md ## 3. Silver DDL
# 권위 있는 원본: sql/databricks/migrations/002_create_silver_tables.sql

# COMMAND ----------
silver_ddl = [
    f"""CREATE TABLE IF NOT EXISTS {CATALOG}.silver.silver_principals (
      principal_id STRING NOT NULL, source_system STRING NOT NULL,
      source_principal_id STRING NOT NULL, principal_kind STRING NOT NULL,
      principal_type STRING NOT NULL, display_name STRING, email STRING,
      status STRING NOT NULL, termination_date DATE, observed_at TIMESTAMP NOT NULL
    ) USING DELTA""",
    f"""CREATE TABLE IF NOT EXISTS {CATALOG}.silver.silver_credentials (
      credential_id STRING NOT NULL, source_system STRING NOT NULL,
      source_credential_id STRING NOT NULL, bound_principal_id STRING NOT NULL,
      credential_type STRING NOT NULL, display_name STRING,
      status STRING NOT NULL, expires_at TIMESTAMP, is_active BOOLEAN NOT NULL,
      observed_at TIMESTAMP NOT NULL
    ) USING DELTA""",
    f"""CREATE TABLE IF NOT EXISTS {CATALOG}.silver.silver_assets (
      asset_id STRING NOT NULL, source_system STRING NOT NULL,
      source_asset_id STRING NOT NULL, asset_type STRING NOT NULL,
      display_name STRING, environment STRING NOT NULL, sensitivity STRING NOT NULL,
      observed_at TIMESTAMP NOT NULL
    ) USING DELTA""",
    f"""CREATE TABLE IF NOT EXISTS {CATALOG}.silver.silver_edges (
      edge_id STRING NOT NULL, source_system STRING NOT NULL,
      from_id STRING NOT NULL, from_type STRING NOT NULL,
      to_id STRING NOT NULL, to_type STRING NOT NULL,
      relationship STRING NOT NULL, permission STRING,
      status STRING NOT NULL, evidence_source STRING, observed_at TIMESTAMP NOT NULL
    ) USING DELTA""",
]
for ddl in silver_ddl:
    spark.sql(ddl)
print("silver tables ready")

# COMMAND ----------
# MAGIC %md ## 4. Seed 데이터 → ADLS raw/

# COMMAND ----------
import json

seed_files = {
    f"{RAW_BASE}/azure/applications.jsonl": [
        {"appId": "a1b2c3d4-1234-5678-abcd-ef0123456789", "displayName": "payment-service-prod", "createdDateTime": "2022-03-10T09:00:00Z"},
        {"appId": "b2c3d4e5-2345-6789-bcde-f01234567890", "displayName": "hr-portal-staging",    "createdDateTime": "2022-05-18T10:30:00Z"},
        {"appId": "c3d4e5f6-3456-7890-cdef-012345678901", "displayName": "analytics-dev",         "createdDateTime": "2023-01-12T08:45:00Z"},
    ],
    f"{RAW_BASE}/azure/application_owners.jsonl": [
        {"appId": "a1b2c3d4-1234-5678-abcd-ef0123456789", "userPrincipalName": "kim.minsu@company.com"},
        {"appId": "b2c3d4e5-2345-6789-bcde-f01234567890", "userPrincipalName": "lee.jiyeon@company.com"},
        {"appId": "c3d4e5f6-3456-7890-cdef-012345678901", "userPrincipalName": "park.sungjun@company.com"},
        {"appId": "d4e5f6a7-4567-8901-defa-123456789012", "userPrincipalName": "choi.hyunwoo@company.com"},
        {"appId": "e5f6a7b8-5678-9012-efab-234567890123", "userPrincipalName": "yoon.minjae@company.com"},
        {"appId": "f6a7b8c9-6789-0123-fabc-345678901234", "userPrincipalName": "jung.eunji@company.com"},
        {"appId": "a7b8c9d0-7890-1234-abcd-456789012345", "userPrincipalName": "shin.dahee@company.com"},
        {"appId": "b8c9d0e1-8901-2345-bcde-567890123456", "userPrincipalName": "lim.seongho@company.com"},
        {"appId": "c9d0e1f2-9012-3456-cdef-678901234567", "userPrincipalName": "kang.minji@company.com"},
        {"appId": "d0e1f2a3-0123-4567-defa-789012345678", "userPrincipalName": "oh.jungwon@company.com"},
    ],
    f"{RAW_BASE}/azure/password_credentials.jsonl": [
        {"appId": "a1b2c3d4-1234-5678-abcd-ef0123456789", "keyId": "key-001", "displayName": "prod-secret",    "endDateTime": "2027-12-31T00:00:00Z", "status": "active"},
        {"appId": "b2c3d4e5-2345-6789-bcde-f01234567890", "keyId": "key-002", "displayName": "staging-secret", "endDateTime": "2026-06-30T00:00:00Z", "status": "active"},
        {"appId": "c3d4e5f6-3456-7890-cdef-012345678901", "keyId": "key-003", "displayName": "dev-secret",     "endDateTime": "2026-01-01T00:00:00Z", "status": "active"},
    ],
    f"{RAW_BASE}/identity/lifecycle_seed.jsonl": [
        {"userPrincipalName": "kim.minsu@company.com",   "employmentStatus": "terminated",  "terminationDate": "2024-01-15"},
        {"userPrincipalName": "lee.jiyeon@company.com",  "employmentStatus": "terminated",  "terminationDate": "2024-03-01"},
        {"userPrincipalName": "park.sungjun@company.com","employmentStatus": "transferred", "terminationDate": None},
    ],
    f"{RAW_BASE}/assets/assets_seed.jsonl": [
        {"assetId": "asset-payment-api",       "name": "payment-api",       "environment": "production",  "sensitivity": "high"},
        {"assetId": "asset-hr-portal",         "name": "hr-portal",         "environment": "staging",     "sensitivity": "medium"},
        {"assetId": "asset-analytics-engine",  "name": "analytics-engine",  "environment": "development", "sensitivity": "low"},
    ],
    f"{RAW_BASE}/access/access_edges_seed.jsonl": [
        {"principalId": "a1b2c3d4-1234-5678-abcd-ef0123456789", "assetId": "asset-payment-api",      "relationship": "accesses_asset", "permission": "invoke", "status": "active"},
        {"principalId": "b2c3d4e5-2345-6789-bcde-f01234567890", "assetId": "asset-hr-portal",        "relationship": "accesses_asset", "permission": "invoke", "status": "active"},
        {"principalId": "c3d4e5f6-3456-7890-cdef-012345678901", "assetId": "asset-analytics-engine", "relationship": "accesses_asset", "permission": "invoke", "status": "active"},
    ],
}

for path, records in seed_files.items():
    content = "\n".join(json.dumps(r, ensure_ascii=False) for r in records)
    dbutils.fs.put(path, content, overwrite=True)
    print(f"written {len(records)} records → {path}")

print("seed upload complete")
