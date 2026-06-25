# Databricks notebook source
# 06_gold — Intermediate findings -> Risk Card core
# Contract: docs/contracts/poc-intermediate-gold-schema.md
# Eval is intentionally not read by this notebook.

# COMMAND ----------
dbutils.widgets.text("catalog", "access_drift")
dbutils.widgets.text("run_id", "poc")

CATALOG = dbutils.widgets.get("catalog")
RUN_ID = dbutils.widgets.get("run_id") or "poc"

# COMMAND ----------
from pyspark.sql import functions as F

findings = spark.table(
    f"{CATALOG}.intermediate.nhi_residual_access_findings"
).alias("finding")
principals = spark.table(f"{CATALOG}.silver.silver_principals")
assets = spark.table(f"{CATALOG}.silver.silver_assets")

subjects = principals.alias("subject")
owners = principals.alias("owner")
asset_nodes = assets.alias("asset")

joined = (
    findings
    .join(subjects, F.col("finding.subject_principal_id") == F.col("subject.principal_id"), "inner")
    .join(owners, F.col("finding.owner_principal_id") == F.col("owner.principal_id"), "inner")
    .join(asset_nodes, F.col("finding.asset_id") == F.col("asset.asset_id"), "inner")
)

subject_name = F.coalesce(
    F.col("subject.display_name"), F.col("finding.subject_source_principal_id")
)
owner_name = F.coalesce(
    F.col("owner.display_name"), F.col("finding.owner_principal_id")
)
asset_name = F.coalesce(
    F.col("asset.display_name"), F.col("finding.asset_source_id")
)
severity = F.upper(F.col("finding.asset_sensitivity"))
evidence_summary = F.concat(
    F.lit("퇴사자 "), owner_name,
    F.lit("가 소유한 활성 App Registration "), subject_name,
    F.lit("에 유효한 credential이 남아 있고 "), asset_name,
    F.lit(" 자산 접근 경로가 활성 상태입니다."),
)

gold = joined.select(
    F.col("finding.risk_case_key"),
    F.col("finding.finding_id"),
    F.col("finding.drift_type"),
    F.col("finding.subject_type"),
    F.col("finding.subject_principal_id"),
    F.col("finding.subject_source_principal_id"),
    subject_name.alias("subject_display_name"),
    F.col("finding.owner_principal_id"),
    owner_name.alias("owner_display_name"),
    F.col("finding.asset_id"),
    F.col("finding.asset_source_id"),
    asset_name.alias("asset_display_name"),
    F.col("finding.asset_environment"),
    F.col("finding.asset_sensitivity"),
    severity.alias("severity"),
    evidence_summary.alias("evidence_summary"),
    F.lit(
        "현재 담당자와 사용 여부를 확인한 뒤 credential을 rotation 또는 revoke하고 "
        "불필요한 자산 권한을 회수합니다."
    ).alias("recommended_action"),
    F.col("finding.owner_edge_id"),
    F.col("finding.access_edge_id"),
    F.col("finding.credential_id"),
    F.col("finding.detected_at"),
    F.lit(RUN_ID).alias("run_id"),
)

# COMMAND ----------
target = f"{CATALOG}.gold.gold_core"
gold.write.mode("overwrite").insertInto(target)

result = spark.table(target)
count = result.count()
assert count >= 1, "expected at least one Gold Core row"

duplicate_keys = result.groupBy("risk_case_key").count().where("count > 1").count()
assert duplicate_keys == 0, f"duplicate Gold risk_case_key rows: {duplicate_keys}"

required = [
    "risk_case_key", "finding_id", "subject_display_name", "asset_display_name",
    "severity", "evidence_summary", "recommended_action",
]
missing_required = result.where(
    F.expr(" OR ".join(f"{column} IS NULL" for column in required))
).count()
assert missing_required == 0, f"Gold rows with missing Risk Card fields: {missing_required}"

result.select(
    "risk_case_key", "subject_display_name", "asset_display_name", "severity",
    "evidence_summary", "recommended_action",
).orderBy("subject_display_name").show(truncate=False)
print(f"gold_core: {count} rows")
print("gold smoke test passed")
