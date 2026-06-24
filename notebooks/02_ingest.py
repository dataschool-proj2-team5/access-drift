# Databricks notebook source
# 02_ingest — ADLS raw/ JSONL → Bronze Delta 적재

# COMMAND ----------
dbutils.widgets.text("catalog", "access_drift")
dbutils.widgets.text("storage_account", "acdriftadls")

CATALOG = dbutils.widgets.get("catalog")
STORAGE = dbutils.widgets.get("storage_account")
RAW_BASE = f"abfss://lakehouse@{STORAGE}.dfs.core.windows.net/raw"

# COMMAND ----------
from pyspark.sql import functions as F
import hashlib

SCHEMA_VERSION = "0.1.0"

def add_meta(df, src_system, src_object, file_path):
    return (
        df
        .withColumn("_src_system",     F.lit(src_system))
        .withColumn("_src_object",     F.lit(src_object))
        .withColumn("_src_file_path",  F.lit(file_path))
        .withColumn("_ingestion_ts",   F.current_timestamp())
        .withColumn("_run_id",         F.lit(dbutils.notebook.entry_point.getDbutils().notebook().getContext().currentRunId().getOrElse(None)))
        .withColumn("_batch_id",       F.date_format(F.current_timestamp(), "yyyyMMddHHmmss"))
        .withColumn("_raw_payload",    F.to_json(F.struct([c for c in df.columns])))
        .withColumn("_checksum",       F.md5(F.to_json(F.struct([c for c in df.columns]))))
        .withColumn("_schema_version", F.lit(SCHEMA_VERSION))
    )

# COMMAND ----------
# MAGIC %md ## azure/applications → bronze_azure_applications

# COMMAND ----------
path = f"{RAW_BASE}/azure/applications.jsonl"
df = spark.read.json(path)
df = add_meta(df, "azure_ad", "applications", path)
df = (df
      .withColumnRenamed("appId", "app_id")
      .withColumnRenamed("displayName", "display_name")
      .withColumn("created_at", F.to_timestamp("createdDateTime"))
      .drop("createdDateTime"))

(df.select(
    "_src_system","_src_object","_src_file_path","_ingestion_ts",
    "_run_id","_batch_id","_checksum","_raw_payload","_schema_version",
    "app_id","display_name","created_at"
).write.format("delta").mode("overwrite")
 .saveAsTable(f"{CATALOG}.bronze.bronze_azure_applications"))
print(f"bronze_azure_applications: {df.count()} rows")

# COMMAND ----------
# MAGIC %md ## azure/application_owners → bronze_azure_application_owners

# COMMAND ----------
path = f"{RAW_BASE}/azure/application_owners.jsonl"
df = spark.read.json(path)
df = add_meta(df, "azure_ad", "application_owners", path)
df = (df
      .withColumnRenamed("appId", "app_id")
      .withColumnRenamed("userPrincipalName", "user_principal_name"))

(df.select(
    "_src_system","_src_object","_src_file_path","_ingestion_ts",
    "_run_id","_batch_id","_checksum","_raw_payload","_schema_version",
    "app_id","user_principal_name"
).write.format("delta").mode("overwrite")
 .saveAsTable(f"{CATALOG}.bronze.bronze_azure_application_owners"))
print(f"bronze_azure_application_owners: {df.count()} rows")

# COMMAND ----------
# MAGIC %md ## azure/password_credentials → bronze_azure_password_credentials

# COMMAND ----------
path = f"{RAW_BASE}/azure/password_credentials.jsonl"
df = spark.read.json(path)
df = add_meta(df, "azure_ad", "password_credentials", path)
df = (df
      .withColumnRenamed("appId", "app_id")
      .withColumnRenamed("keyId", "key_id")
      .withColumnRenamed("displayName", "display_name")
      .withColumn("end_date_time", F.to_timestamp("endDateTime"))
      .drop("endDateTime"))

(df.select(
    "_src_system","_src_object","_src_file_path","_ingestion_ts",
    "_run_id","_batch_id","_checksum","_raw_payload","_schema_version",
    "app_id","key_id","display_name","end_date_time","status"
).write.format("delta").mode("overwrite")
 .saveAsTable(f"{CATALOG}.bronze.bronze_azure_password_credentials"))
print(f"bronze_azure_password_credentials: {df.count()} rows")

# COMMAND ----------
# MAGIC %md ## identity/lifecycle_seed → bronze_identity_lifecycle_seed

# COMMAND ----------
path = f"{RAW_BASE}/identity/lifecycle_seed.jsonl"
df = spark.read.json(path)
df = add_meta(df, "identity_seed", "lifecycle_seed", path)
df = (df
      .withColumnRenamed("userPrincipalName", "user_principal_name")
      .withColumnRenamed("employmentStatus", "employment_status")
      .withColumn("termination_date", F.to_date("terminationDate"))
      .drop("terminationDate"))

(df.select(
    "_src_system","_src_object","_src_file_path","_ingestion_ts",
    "_run_id","_batch_id","_checksum","_raw_payload","_schema_version",
    "user_principal_name","employment_status","termination_date"
).write.format("delta").mode("overwrite")
 .saveAsTable(f"{CATALOG}.bronze.bronze_identity_lifecycle_seed"))
print(f"bronze_identity_lifecycle_seed: {df.count()} rows")

# COMMAND ----------
# MAGIC %md ## assets/assets_seed → bronze_assets_seed

# COMMAND ----------
path = f"{RAW_BASE}/assets/assets_seed.jsonl"
df = spark.read.json(path)
df = add_meta(df, "assets_seed", "assets_seed", path)
df = (df
      .withColumnRenamed("assetId", "asset_id")
      .withColumnRenamed("name", "name")
      .withColumnRenamed("environment", "environment")
      .withColumnRenamed("sensitivity", "sensitivity"))

(df.select(
    "_src_system","_src_object","_src_file_path","_ingestion_ts",
    "_run_id","_batch_id","_checksum","_raw_payload","_schema_version",
    "asset_id","name","environment","sensitivity"
).write.format("delta").mode("overwrite")
 .saveAsTable(f"{CATALOG}.bronze.bronze_assets_seed"))
print(f"bronze_assets_seed: {df.count()} rows")

# COMMAND ----------
# MAGIC %md ## access/access_edges_seed → bronze_access_edges_seed

# COMMAND ----------
path = f"{RAW_BASE}/access/access_edges_seed.jsonl"
df = spark.read.json(path)
df = add_meta(df, "access_seed", "access_edges_seed", path)
df = (df
      .withColumnRenamed("principalId", "principal_id")
      .withColumnRenamed("assetId", "asset_id")
      .withColumnRenamed("relationship", "relationship")
      .withColumnRenamed("permission", "permission")
      .withColumnRenamed("status", "status"))

(df.select(
    "_src_system","_src_object","_src_file_path","_ingestion_ts",
    "_run_id","_batch_id","_checksum","_raw_payload","_schema_version",
    "principal_id","asset_id","relationship","permission","status"
).write.format("delta").mode("overwrite")
 .saveAsTable(f"{CATALOG}.bronze.bronze_access_edges_seed"))
print(f"bronze_access_edges_seed: {df.count()} rows")

# COMMAND ----------
print("ingest complete")
