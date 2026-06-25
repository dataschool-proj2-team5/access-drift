# Databricks notebook source
# 05_intermediate — Silver facts -> NHI residual access findings
# Contract: docs/contracts/poc-intermediate-gold-schema.md
# Eval is intentionally not read by this notebook.

# COMMAND ----------
dbutils.widgets.text("catalog", "access_drift")
dbutils.widgets.text("run_id", "poc")

CATALOG = dbutils.widgets.get("catalog")
RUN_ID = dbutils.widgets.get("run_id") or "poc"

# COMMAND ----------
from pyspark.sql import functions as F

principals = spark.table(f"{CATALOG}.silver.silver_principals")
credentials = spark.table(f"{CATALOG}.silver.silver_credentials")
assets = spark.table(f"{CATALOG}.silver.silver_assets")
edges = spark.table(f"{CATALOG}.silver.silver_edges")

owners = principals.where(
    (F.col("principal_kind") == "HI") &
    (F.col("status") == "terminated")
).alias("owner")

nhis = principals.where(
    (F.col("principal_kind") == "NHI") &
    (F.col("principal_type") == "app_registration") &
    (F.col("status") == "active")
).alias("nhi")

active_credentials = credentials.where(
    (F.col("status") == "active") &
    (F.col("is_active") == F.lit(True))
).alias("credential")

owner_edges = edges.where(
    (F.col("relationship") == "owns_principal") &
    (F.col("from_type") == "principal") &
    (F.col("to_type") == "principal") &
    (F.col("status") == "active")
).alias("owner_edge")

access_edges = edges.where(
    (F.col("relationship") == "accesses_asset") &
    (F.col("from_type") == "principal") &
    (F.col("to_type") == "asset") &
    (F.col("status") == "active")
).alias("access_edge")

asset_nodes = assets.alias("asset")

# COMMAND ----------
joined = (
    owner_edges
    .join(owners, F.col("owner_edge.from_id") == F.col("owner.principal_id"), "inner")
    .join(nhis, F.col("owner_edge.to_id") == F.col("nhi.principal_id"), "inner")
    .join(
        active_credentials,
        F.col("credential.bound_principal_id") == F.col("nhi.principal_id"),
        "inner",
    )
    .join(
        access_edges,
        F.col("access_edge.from_id") == F.col("nhi.principal_id"),
        "inner",
    )
    .join(asset_nodes, F.col("access_edge.to_id") == F.col("asset.asset_id"), "inner")
)

risk_case_key = F.sha2(F.concat_ws(
    ":",
    F.lit("nhi"),
    F.col("nhi.source_principal_id"),
    F.col("asset.source_asset_id"),
    F.lit("nhi_residual_access"),
), 256)

findings = joined.select(
    F.sha2(F.concat_ws(":", F.lit("finding"), risk_case_key), 256).alias("finding_id"),
    risk_case_key.alias("risk_case_key"),
    F.lit("nhi_residual_access").alias("drift_type"),
    F.lit("nhi").alias("subject_type"),
    F.col("owner.principal_id").alias("owner_principal_id"),
    F.col("owner.source_principal_id").alias("owner_source_principal_id"),
    F.col("nhi.principal_id").alias("subject_principal_id"),
    F.col("nhi.source_principal_id").alias("subject_source_principal_id"),
    F.col("credential.credential_id").alias("credential_id"),
    F.col("asset.asset_id").alias("asset_id"),
    F.col("asset.source_asset_id").alias("asset_source_id"),
    F.col("owner_edge.edge_id").alias("owner_edge_id"),
    F.col("access_edge.edge_id").alias("access_edge_id"),
    F.col("access_edge.permission").alias("permission"),
    F.col("owner.status").alias("owner_status"),
    F.col("credential.is_active").alias("credential_is_active"),
    F.col("asset.environment").alias("asset_environment"),
    F.col("asset.sensitivity").alias("asset_sensitivity"),
    F.current_timestamp().alias("detected_at"),
    F.lit(RUN_ID).alias("run_id"),
)

# COMMAND ----------
target = f"{CATALOG}.intermediate.nhi_residual_access_findings"
findings.write.mode("overwrite").insertInto(target)

result = spark.table(target)
count = result.count()
assert count >= 1, "expected at least one NHI residual access finding"

duplicate_keys = result.groupBy("risk_case_key").count().where("count > 1").count()
assert duplicate_keys == 0, f"duplicate risk_case_key rows: {duplicate_keys}"

required = [
    "finding_id", "risk_case_key", "owner_principal_id", "subject_principal_id",
    "credential_id", "asset_id", "owner_edge_id", "access_edge_id",
]
missing_required = result.where(
    F.expr(" OR ".join(f"{column} IS NULL" for column in required))
).count()
assert missing_required == 0, f"rows with missing required evidence: {missing_required}"

result.orderBy("subject_source_principal_id").show(truncate=False)
print(f"intermediate findings: {count} rows")
print("intermediate smoke test passed")
