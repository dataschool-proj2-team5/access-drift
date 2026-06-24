# Databricks notebook source
# 03_silver — Bronze → Silver 공통 모델 변환

# COMMAND ----------
dbutils.widgets.text("catalog", "access_drift")

CATALOG = dbutils.widgets.get("catalog")
NOW = "current_timestamp()"

# COMMAND ----------
from pyspark.sql import functions as F

# COMMAND ----------
# MAGIC %md ## 1. silver_principals
# NHI: bronze_azure_applications
# Human: bronze_identity_lifecycle_seed (owner로 등장한 계정만)

# COMMAND ----------
nhi = spark.table(f"{CATALOG}.bronze.bronze_azure_applications").select(
    F.col("app_id").alias("principal_id"),
    F.lit("azure_ad").alias("source_system"),
    F.col("app_id").alias("source_principal_id"),
    F.lit("nhi").alias("principal_kind"),
    F.lit("azure_app_registration").alias("principal_type"),
    F.col("display_name"),
    F.lit(None).cast("string").alias("email"),
    F.lit("active").alias("status"),
    F.lit(None).cast("date").alias("termination_date"),
    F.current_timestamp().alias("observed_at"),
)

human = spark.table(f"{CATALOG}.bronze.bronze_identity_lifecycle_seed").select(
    F.col("user_principal_name").alias("principal_id"),
    F.lit("identity_seed").alias("source_system"),
    F.col("user_principal_name").alias("source_principal_id"),
    F.lit("human").alias("principal_kind"),
    F.lit("user").alias("principal_type"),
    F.col("user_principal_name").alias("display_name"),
    F.col("user_principal_name").alias("email"),
    F.col("employment_status").alias("status"),
    F.col("termination_date"),
    F.current_timestamp().alias("observed_at"),
)

(nhi.union(human)
 .write.format("delta").mode("overwrite")
 .saveAsTable(f"{CATALOG}.silver.silver_principals"))

count = spark.table(f"{CATALOG}.silver.silver_principals").count()
print(f"silver_principals: {count} rows")

# COMMAND ----------
# MAGIC %md ## 2. silver_credentials
# bronze_azure_password_credentials → NHI에 바인딩된 credential

# COMMAND ----------
creds = spark.table(f"{CATALOG}.bronze.bronze_azure_password_credentials").select(
    F.col("key_id").alias("credential_id"),
    F.lit("azure_ad").alias("source_system"),
    F.col("key_id").alias("source_credential_id"),
    F.col("app_id").alias("bound_principal_id"),
    F.lit("client_secret").alias("credential_type"),
    F.col("display_name"),
    F.col("status"),
    F.col("end_date_time").alias("expires_at"),
    F.when(F.col("status") == "active", F.lit(True)).otherwise(F.lit(False)).alias("is_active"),
    F.current_timestamp().alias("observed_at"),
)

(creds.write.format("delta").mode("overwrite")
 .saveAsTable(f"{CATALOG}.silver.silver_credentials"))

count = spark.table(f"{CATALOG}.silver.silver_credentials").count()
print(f"silver_credentials: {count} rows")

# COMMAND ----------
# MAGIC %md ## 3. silver_assets
# bronze_assets_seed → 직접 매핑

# COMMAND ----------
assets = spark.table(f"{CATALOG}.bronze.bronze_assets_seed").select(
    F.col("asset_id"),
    F.lit("assets_seed").alias("source_system"),
    F.col("asset_id").alias("source_asset_id"),
    F.lit("service").alias("asset_type"),
    F.col("name").alias("display_name"),
    F.col("environment"),
    F.col("sensitivity"),
    F.current_timestamp().alias("observed_at"),
)

(assets.write.format("delta").mode("overwrite")
 .saveAsTable(f"{CATALOG}.silver.silver_assets"))

count = spark.table(f"{CATALOG}.silver.silver_assets").count()
print(f"silver_assets: {count} rows")

# COMMAND ----------
# MAGIC %md ## 4. silver_edges
# (a) access_edges_seed: NHI → asset 접근 엣지
# (b) application_owners: human → NHI 소유 엣지

# COMMAND ----------
access_edges = spark.table(f"{CATALOG}.bronze.bronze_access_edges_seed").select(
    F.md5(F.concat_ws("|", F.col("principal_id"), F.col("asset_id"), F.lit("accesses_asset"))).alias("edge_id"),
    F.lit("access_seed").alias("source_system"),
    F.col("principal_id").alias("from_id"),
    F.lit("nhi").alias("from_type"),
    F.col("asset_id").alias("to_id"),
    F.lit("asset").alias("to_type"),
    F.col("relationship"),
    F.col("permission"),
    F.col("status"),
    F.lit("bronze_access_edges_seed").alias("evidence_source"),
    F.current_timestamp().alias("observed_at"),
)

owner_edges = spark.table(f"{CATALOG}.bronze.bronze_azure_application_owners").select(
    F.md5(F.concat_ws("|", F.col("user_principal_name"), F.col("app_id"), F.lit("owns"))).alias("edge_id"),
    F.lit("azure_ad").alias("source_system"),
    F.col("user_principal_name").alias("from_id"),
    F.lit("human").alias("from_type"),
    F.col("app_id").alias("to_id"),
    F.lit("nhi").alias("to_type"),
    F.lit("owns").alias("relationship"),
    F.lit(None).cast("string").alias("permission"),
    F.lit("active").alias("status"),
    F.lit("bronze_azure_application_owners").alias("evidence_source"),
    F.current_timestamp().alias("observed_at"),
)

(access_edges.union(owner_edges)
 .write.format("delta").mode("overwrite")
 .saveAsTable(f"{CATALOG}.silver.silver_edges"))

count = spark.table(f"{CATALOG}.silver.silver_edges").count()
print(f"silver_edges: {count} rows")

# COMMAND ----------
# MAGIC %md ## 검증

# COMMAND ----------
for tbl in ["silver_principals", "silver_credentials", "silver_assets", "silver_edges"]:
    n = spark.table(f"{CATALOG}.silver.{tbl}").count()
    print(f"{tbl}: {n} rows")

print("silver transform complete")
