# Databricks notebook source
# 01_synthetic_data — DDL 적용 + seed 파일을 ADLS raw/ 에 적재

# COMMAND ----------
dbutils.widgets.text("catalog", "access_drift")
dbutils.widgets.text("storage_account", "acdriftadls")

CATALOG = dbutils.widgets.get("catalog")
STORAGE = dbutils.widgets.get("storage_account")
RAW_BASE = f"abfss://lakehouse@{STORAGE}.dfs.core.windows.net/raw"

# bundle deploy 시 data/poc/landing/raw/ 가 /Workspace/Shared/access-drift/files/ 아래에 배포됨
SEED_BASE = "/Workspace/Shared/access-drift/files/data/poc/landing/raw"

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
# MAGIC %md ## 4. Eval DDL
# 권위 있는 원본: sql/databricks/migrations/003_create_eval_tables.sql

# COMMAND ----------
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.eval")
spark.sql(f"""
  CREATE TABLE IF NOT EXISTS {CATALOG}.eval.ground_truth_case (
    case_id STRING NOT NULL, scenario_id STRING, scenario_family STRING,
    subject_type STRING NOT NULL, subject_id STRING NOT NULL, asset_id STRING NOT NULL,
    drift_type STRING NOT NULL, is_planted_risk BOOLEAN NOT NULL, is_distractor BOOLEAN NOT NULL,
    pattern STRING, expected_severity STRING, label_reason STRING, created_at TIMESTAMP NOT NULL
  ) USING DELTA
""")
print("eval tables ready")

# COMMAND ----------
# MAGIC %md ## 5. Seed 경로 확인

# COMMAND ----------
try:
    dbutils.fs.ls(SEED_BASE)
    print(f"seed path OK: {SEED_BASE}")
except Exception as e:
    raise RuntimeError(
        f"Seed 파일을 찾을 수 없습니다: {SEED_BASE}\n"
        "bundle deploy가 완료됐는지 확인하세요.\n"
        f"원인: {e}"
    )

# COMMAND ----------
# MAGIC %md ## 6. Seed 파일 → ADLS raw/ 복사

# COMMAND ----------
seed_mappings = [
    (f"{SEED_BASE}/azure/applications.jsonl",       f"{RAW_BASE}/azure/applications.jsonl"),
    (f"{SEED_BASE}/azure/application_owners.jsonl", f"{RAW_BASE}/azure/application_owners.jsonl"),
    (f"{SEED_BASE}/azure/password_credentials.jsonl", f"{RAW_BASE}/azure/password_credentials.jsonl"),
    (f"{SEED_BASE}/identity/lifecycle_seed.jsonl",  f"{RAW_BASE}/identity/lifecycle_seed.jsonl"),
    (f"{SEED_BASE}/assets/assets_seed.jsonl",       f"{RAW_BASE}/assets/assets_seed.jsonl"),
    (f"{SEED_BASE}/access/access_edges_seed.jsonl", f"{RAW_BASE}/access/access_edges_seed.jsonl"),
]

for src, dst in seed_mappings:
    dbutils.fs.cp(src, dst, recurse=False)
    print(f"copied: {src.split('/')[-1]} → {dst}")

print("seed upload complete")
