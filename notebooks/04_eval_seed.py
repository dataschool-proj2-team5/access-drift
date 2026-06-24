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
print(f"ground_truth_case: {count} rows")
spark.table(f"{CATALOG}.eval.ground_truth_case").show(truncate=False)
