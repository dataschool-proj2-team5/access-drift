# Databricks notebook source
# 03_silver — Bronze → Silver 공통 모델 변환
# 계약 기준: docs/contracts/silver-schema.md

# COMMAND ----------
dbutils.widgets.text("catalog", "access_drift")

CATALOG = dbutils.widgets.get("catalog")

# COMMAND ----------
from pyspark.sql import functions as F

def silver_id(*parts):
    """sha256(part1:part2:...) — Silver ID 생성 규칙"""
    return F.sha2(F.concat_ws(":", *parts), 256)

# COMMAND ----------
# MAGIC %md ## 1. silver_principals
# NHI: bronze_azure_applications → principal_kind=NHI, principal_type=app_registration
# HI : bronze_identity_lifecycle_seed → principal_kind=HI, principal_type=user

# COMMAND ----------
nhi = spark.table(f"{CATALOG}.bronze.bronze_azure_applications").select(
    silver_id(F.lit("azure_ad"), F.col("app_id"), F.lit("app_registration")).alias("principal_id"),
    F.lit("azure_ad").alias("source_system"),
    F.col("app_id").alias("source_principal_id"),
    F.lit("NHI").alias("principal_kind"),
    F.lit("app_registration").alias("principal_type"),
    F.col("display_name"),
    F.lit(None).cast("string").alias("email"),
    F.lit("active").alias("status"),
    F.lit(None).cast("date").alias("termination_date"),
    F.current_timestamp().alias("observed_at"),
)

status_map = F.when(F.col("employment_status") == "terminated", F.lit("terminated")) \
              .when(F.col("employment_status") == "transferred", F.lit("inactive")) \
              .otherwise(F.lit("active"))

human = spark.table(f"{CATALOG}.bronze.bronze_identity_lifecycle_seed").select(
    silver_id(F.lit("identity_seed"), F.col("user_principal_name"), F.lit("user")).alias("principal_id"),
    F.lit("identity_seed").alias("source_system"),
    F.col("user_principal_name").alias("source_principal_id"),
    F.lit("HI").alias("principal_kind"),
    F.lit("user").alias("principal_type"),
    F.col("user_principal_name").alias("display_name"),
    F.col("user_principal_name").alias("email"),
    status_map.alias("status"),
    F.col("termination_date"),
    F.current_timestamp().alias("observed_at"),
)

(nhi.union(human)
 .write.format("delta").mode("overwrite")
 .saveAsTable(f"{CATALOG}.silver.silver_principals"))
print(f"silver_principals: {spark.table(f'{CATALOG}.silver.silver_principals').count()} rows")

# COMMAND ----------
# MAGIC %md ## 2. silver_credentials
# bound_principal_id = silver principal_id (sha256), is_active = status=active AND not expired

# COMMAND ----------
creds = spark.table(f"{CATALOG}.bronze.bronze_azure_password_credentials").select(
    silver_id(
        F.lit("azure_ad"),
        F.col("key_id"),
        silver_id(F.lit("azure_ad"), F.col("app_id"), F.lit("app_registration"))
    ).alias("credential_id"),
    F.lit("azure_ad").alias("source_system"),
    F.col("key_id").alias("source_credential_id"),
    silver_id(F.lit("azure_ad"), F.col("app_id"), F.lit("app_registration")).alias("bound_principal_id"),
    F.lit("client_secret").alias("credential_type"),
    F.col("display_name"),
    F.col("status"),
    F.col("end_date_time").alias("expires_at"),
    F.when(
        (F.col("status") == "active") &
        (F.col("end_date_time").isNull() | (F.col("end_date_time") > F.current_timestamp())),
        F.lit(True)
    ).otherwise(F.lit(False)).alias("is_active"),
    F.current_timestamp().alias("observed_at"),
)

(creds.write.format("delta").mode("overwrite")
 .saveAsTable(f"{CATALOG}.silver.silver_credentials"))
print(f"silver_credentials: {spark.table(f'{CATALOG}.silver.silver_credentials').count()} rows")

# COMMAND ----------
# MAGIC %md ## 3. silver_assets
# asset_type=cloud_resource, asset_id=sha256

# COMMAND ----------
assets = spark.table(f"{CATALOG}.bronze.bronze_assets_seed").select(
    silver_id(F.lit("assets_seed"), F.col("asset_id"), F.lit("cloud_resource")).alias("asset_id"),
    F.lit("assets_seed").alias("source_system"),
    F.col("asset_id").alias("source_asset_id"),
    F.lit("cloud_resource").alias("asset_type"),
    F.col("name").alias("display_name"),
    F.col("environment"),
    F.col("sensitivity"),
    F.current_timestamp().alias("observed_at"),
)

(assets.write.format("delta").mode("overwrite")
 .saveAsTable(f"{CATALOG}.silver.silver_assets"))
print(f"silver_assets: {spark.table(f'{CATALOG}.silver.silver_assets').count()} rows")

# COMMAND ----------
# MAGIC %md ## 4. silver_edges
# (a) access_edges: principal → asset, relationship=accesses_asset
# (b) owner_edges: human principal → NHI principal, relationship=owns_principal
# from_type/to_type: principal | asset (계약 기준)

# COMMAND ----------
# NHI silver principal_id 계산 helper (inline)
nhi_pid = silver_id(F.lit("azure_ad"), F.col("principal_id"), F.lit("app_registration"))
nhi_asset_id = silver_id(F.lit("assets_seed"), F.col("asset_id"), F.lit("cloud_resource"))

access_edges_raw = spark.table(f"{CATALOG}.bronze.bronze_access_edges_seed")
access_edges = access_edges_raw.select(
    silver_id(
        F.lit("access_seed"),
        silver_id(F.lit("azure_ad"), F.col("principal_id"), F.lit("app_registration")),
        F.lit("accesses_asset"),
        silver_id(F.lit("assets_seed"), F.col("asset_id"), F.lit("cloud_resource"))
    ).alias("edge_id"),
    F.lit("access_seed").alias("source_system"),
    silver_id(F.lit("azure_ad"), F.col("principal_id"), F.lit("app_registration")).alias("from_id"),
    F.lit("principal").alias("from_type"),
    silver_id(F.lit("assets_seed"), F.col("asset_id"), F.lit("cloud_resource")).alias("to_id"),
    F.lit("asset").alias("to_type"),
    F.col("relationship"),
    F.col("permission"),
    F.col("status"),
    F.lit("bronze_access_edges_seed").alias("evidence_source"),
    F.current_timestamp().alias("observed_at"),
)

owner_edges_raw = spark.table(f"{CATALOG}.bronze.bronze_azure_application_owners")
owner_edges = owner_edges_raw.select(
    silver_id(
        F.lit("azure_ad"),
        silver_id(F.lit("identity_seed"), F.col("user_principal_name"), F.lit("user")),
        F.lit("owns_principal"),
        silver_id(F.lit("azure_ad"), F.col("app_id"), F.lit("app_registration"))
    ).alias("edge_id"),
    F.lit("azure_ad").alias("source_system"),
    silver_id(F.lit("identity_seed"), F.col("user_principal_name"), F.lit("user")).alias("from_id"),
    F.lit("principal").alias("from_type"),
    silver_id(F.lit("azure_ad"), F.col("app_id"), F.lit("app_registration")).alias("to_id"),
    F.lit("principal").alias("to_type"),
    F.lit("owns_principal").alias("relationship"),
    F.lit(None).cast("string").alias("permission"),
    F.lit("active").alias("status"),
    F.lit("bronze_azure_application_owners").alias("evidence_source"),
    F.current_timestamp().alias("observed_at"),
)

(access_edges.union(owner_edges)
 .write.format("delta").mode("overwrite")
 .saveAsTable(f"{CATALOG}.silver.silver_edges"))
print(f"silver_edges: {spark.table(f'{CATALOG}.silver.silver_edges').count()} rows")

# COMMAND ----------
# MAGIC %md ## 검증

# COMMAND ----------
expected_counts = {
    "silver_principals": 20,
    "silver_credentials": 10,
    "silver_assets": 10,
    "silver_edges": 20,
}

for table, expected in expected_counts.items():
    actual = spark.table(f"{CATALOG}.silver.{table}").count()
    assert actual == expected, f"{table} expected {expected}, got {actual}"
    print(f"{table}: {actual} rows")

active_credentials = spark.table(f"{CATALOG}.silver.silver_credentials").where("is_active = true").count()
assert active_credentials > 0, "expected at least one active credential"

spark.table(f"{CATALOG}.silver.silver_principals").select("principal_id","principal_kind","principal_type","status").show(truncate=False)
print("silver smoke test passed")
print("silver transform complete")
