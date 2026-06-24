# Databricks notebook source
# 04_eval_seed — eval/ground_truth_case.jsonl → access_drift.eval.ground_truth_case 적재
# 주의: 탐지 파이프라인(ingest/silver/intermediate/gold)은 이 테이블을 입력으로 사용하지 않는다.

# COMMAND ----------
dbutils.widgets.text("catalog", "access_drift")

CATALOG = dbutils.widgets.get("catalog")
EVAL_SEED_PATH = "/Workspace/Shared/access-drift/files/data/poc/eval/ground_truth_case.jsonl"

# COMMAND ----------
try:
    dbutils.fs.ls(EVAL_SEED_PATH)
    print(f"eval seed path OK: {EVAL_SEED_PATH}")
except Exception as e:
    raise RuntimeError(
        f"Eval seed 파일을 찾을 수 없습니다: {EVAL_SEED_PATH}\n"
        "bundle deploy가 완료됐는지 확인하세요.\n"
        f"원인: {e}"
    )

# COMMAND ----------
from pyspark.sql import functions as F

df = (spark.read.json(EVAL_SEED_PATH)
      .withColumn("created_at", F.to_timestamp("created_at")))

(df.select(
    "case_id","scenario_id","scenario_family",
    "subject_type","subject_id","asset_id",
    "drift_type","is_planted_risk","is_distractor",
    "pattern","expected_severity","label_reason","created_at"
).write.format("delta").mode("overwrite")
 .saveAsTable(f"{CATALOG}.eval.ground_truth_case"))

count = spark.table(f"{CATALOG}.eval.ground_truth_case").count()
assert count == 3, f"ground_truth_case expected 3, got {count}"
print(f"ground_truth_case: {count} rows")
spark.table(f"{CATALOG}.eval.ground_truth_case").show(truncate=False)

positive_count = spark.table(f"{CATALOG}.eval.ground_truth_case").where("is_planted_risk = true").count()
normal_count = spark.table(f"{CATALOG}.eval.ground_truth_case").where("is_planted_risk = false AND is_distractor = false").count()
assert positive_count == 2, f"positive ground truth expected 2, got {positive_count}"
assert normal_count == 1, f"normal ground truth expected 1, got {normal_count}"

# COMMAND ----------
# MAGIC %md ## eval ↔ Silver 매칭 검증
# subject_id = silver_principals.source_principal_id 로 조인 가능해야 함
# 이 notebook은 silver_task 이후 실행되므로 매칭 결과가 존재해야 함

# COMMAND ----------
match_df = spark.sql(f"""
  SELECT
    g.case_id,
    g.subject_id,
    g.asset_id,
    g.is_planted_risk,
    g.expected_severity,
    p.principal_id   AS silver_principal_id,
    p.principal_kind,
    p.status         AS principal_status,
    a.asset_id       AS silver_asset_id,
    a.sensitivity
  FROM {CATALOG}.eval.ground_truth_case g
  LEFT JOIN {CATALOG}.silver.silver_principals p
    ON g.subject_id = p.source_principal_id AND p.principal_kind = 'NHI'
  LEFT JOIN {CATALOG}.silver.silver_assets a
    ON g.asset_id = a.source_asset_id
  ORDER BY g.case_id
""")
match_df.show(truncate=False)

missing_matches = match_df.where("silver_principal_id IS NULL OR silver_asset_id IS NULL").count()
assert missing_matches == 0, f"eval↔silver unmatched rows: {missing_matches}"

print("eval seed smoke test passed")
print("eval↔silver match check complete")
