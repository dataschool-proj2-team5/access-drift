# Databricks notebook source
# 07_verify_gold_core_pipeline
# Runs the PoC pipeline through Gold Core and prints verification queries.
# This notebook is for manual Databricks validation before opening a PR.

# COMMAND ----------
# MAGIC %md
# MAGIC # Gold Core Pipeline Manual Verification
# MAGIC
# MAGIC 이 노트북은 #10 Gold Core 파이프라인을 PR로 올리기 전에 Databricks에서 직접 확인하기 위한 수동 검증용 노트북입니다.
# MAGIC
# MAGIC 확인하려는 것:
# MAGIC
# MAGIC - Bronze/Silver 이후 Intermediate와 Gold Core까지 에러 없이 실행되는지
# MAGIC - `access_drift.intermediate.nhi_residual_access_findings`에 finding이 생성되는지
# MAGIC - `access_drift.gold.gold_core`에 Risk Card 최소 필드가 생성되는지
# MAGIC - Gold 결과가 후속 eval 비교 key와 맞게 연결되는지
# MAGIC - 재실행 시 `risk_case_key`가 중복 누적되지 않는지
# MAGIC
# MAGIC 주의:
# MAGIC
# MAGIC - 이 노트북은 검증 편의를 위해 `04_eval_seed.ipynb`를 실행하고 마지막에 eval 비교를 보여줍니다.
# MAGIC - 실제 탐지 노트북인 `05_intermediate.py`, `06_gold.py`는 eval 테이블을 읽지 않습니다.
# MAGIC - `01_synthetic_data.ipynb`와 이후 적재 노트북은 PoC seed 데이터를 다시 적재할 수 있으므로 공용 workspace에서 실행 전 팀 작업 중인 데이터를 덮어써도 되는지 확인하세요.

# COMMAND ----------
dbutils.widgets.text("catalog", "access_drift")
dbutils.widgets.text("run_id", "manual-gold-core-verify")
dbutils.widgets.text("base_path", "/Workspace/Shared/access-drift/files/notebooks")

CATALOG = dbutils.widgets.get("catalog")
RUN_ID = dbutils.widgets.get("run_id") or "manual-gold-core-verify"
BASE_PATH = dbutils.widgets.get("base_path").rstrip("/")

print(f"catalog={CATALOG}")
print(f"run_id={RUN_ID}")
print(f"base_path={BASE_PATH}")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 1. Pipeline 실행
# MAGIC
# MAGIC Bundle pipeline과 같은 순서로 노트북을 실행합니다.
# MAGIC
# MAGIC - `00_apply_migrations.ipynb`: Bronze/Silver/Eval/Intermediate/Gold 테이블 생성
# MAGIC - `01_synthetic_data.ipynb`: PoC seed raw 파일 준비
# MAGIC - `02_ingest.ipynb`: raw JSONL을 Bronze로 적재
# MAGIC - `03_silver.ipynb`: Bronze를 Silver 4테이블로 정규화
# MAGIC - `04_eval_seed.ipynb`: 후속 검증용 eval 정답지 적재
# MAGIC - `05_intermediate.py`: Silver facts만 읽어서 NHI residual access finding 생성
# MAGIC - `06_gold.py`: Intermediate finding을 Gold Core Risk Card 결과로 변환

# COMMAND ----------
# Run the same notebook sequence used by the bundle pipeline.
# Eval is loaded after Silver for verification only; Intermediate/Gold notebooks do not read eval.
steps = [
    ("00_apply_migrations.ipynb", {}),
    ("01_synthetic_data.ipynb", {}),
    ("02_ingest.ipynb", {}),
    ("03_silver.ipynb", {}),
    ("04_eval_seed.ipynb", {}),
    ("05_intermediate.py", {"run_id": RUN_ID}),
    ("06_gold.py", {"run_id": RUN_ID}),
]

for notebook_name, extra_args in steps:
    path = f"{BASE_PATH}/{notebook_name}"
    args = {"catalog": CATALOG, **extra_args}
    print(f"Running {path} with args={args}")
    result = dbutils.notebook.run(path, timeout_seconds=0, arguments=args)
    print(f"{notebook_name}: {result}")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 2. Row Count 확인
# MAGIC
# MAGIC #10 완료 기준의 최소 확인입니다.
# MAGIC
# MAGIC - Intermediate finding이 1건 이상이어야 합니다.
# MAGIC - Gold Core 결과가 1건 이상이어야 합니다.
# MAGIC - 현재 PoC seed 기준 예상값은 2건입니다.

# COMMAND ----------
from pyspark.sql import functions as F

intermediate_table = f"{CATALOG}.intermediate.nhi_residual_access_findings"
gold_table = f"{CATALOG}.gold.gold_core"
eval_table = f"{CATALOG}.eval.ground_truth_case"

intermediate_count = spark.table(intermediate_table).count()
gold_count = spark.table(gold_table).count()

print(f"{intermediate_table}: {intermediate_count} rows")
print(f"{gold_table}: {gold_count} rows")

assert intermediate_count >= 1, "expected at least one intermediate finding"
assert gold_count >= 1, "expected at least one gold_core row"

# COMMAND ----------
# MAGIC %md
# MAGIC ## Gold Core Sample
# MAGIC
# MAGIC Risk Card에서 바로 읽을 수 있어야 하는 최소 필드를 보여줍니다.
# MAGIC
# MAGIC 여기서 봐야 할 핵심:
# MAGIC
# MAGIC - 어떤 NHI가 남아 있는지: `subject_source_principal_id`, `subject_display_name`
# MAGIC - 어떤 자산에 닿는지: `asset_source_id`, `asset_display_name`
# MAGIC - 왜 위험한지: `severity`, `evidence_summary`
# MAGIC - 다음 조치가 무엇인지: `recommended_action`

# COMMAND ----------
display(
    spark.table(gold_table)
    .select(
        "risk_case_key",
        "subject_type",
        "subject_source_principal_id",
        "subject_display_name",
        "asset_source_id",
        "asset_display_name",
        "severity",
        "evidence_summary",
        "recommended_action",
        "run_id",
    )
    .orderBy("subject_source_principal_id", "asset_source_id")
)

# COMMAND ----------
# MAGIC %md
# MAGIC ## Eval Key Comparison
# MAGIC
# MAGIC This comparison is verification-only. Detection notebooks do not read eval.
# MAGIC
# MAGIC Gold 결과와 eval 정답지는 아래 key로 비교합니다.
# MAGIC
# MAGIC ```text
# MAGIC gold.subject_type = eval.subject_type
# MAGIC gold.subject_source_principal_id = eval.subject_id
# MAGIC gold.asset_source_id = eval.asset_id
# MAGIC gold.drift_type = eval.drift_type
# MAGIC ```
# MAGIC
# MAGIC 이 비교는 탐지 입력이 아니라 “생성된 Gold 결과가 의도한 seed 정답과 맞는지” 확인하는 후속 검증입니다.

# COMMAND ----------
gold = spark.table(gold_table).alias("gold")
truth = spark.table(eval_table).alias("truth")

eval_comparison = (
    gold.join(
        truth,
        (F.col("gold.subject_type") == F.col("truth.subject_type")) &
        (F.col("gold.subject_source_principal_id") == F.col("truth.subject_id")) &
        (F.col("gold.asset_source_id") == F.col("truth.asset_id")) &
        (F.col("gold.drift_type") == F.col("truth.drift_type")),
        "left",
    )
    .select(
        F.col("gold.subject_source_principal_id"),
        F.col("gold.asset_source_id"),
        F.col("gold.drift_type"),
        F.col("gold.severity"),
        F.col("truth.case_id"),
        F.col("truth.is_planted_risk"),
        F.col("truth.expected_severity"),
        F.col("truth.label_reason"),
    )
    .orderBy("subject_source_principal_id", "asset_source_id")
)

display(eval_comparison)

matched_truth_rows = eval_comparison.where(F.col("case_id").isNotNull()).count()
print(f"gold rows matched to eval truth: {matched_truth_rows} / {gold_count}")

# COMMAND ----------
# MAGIC %md
# MAGIC ## Duplicate And Required Field Checks
# MAGIC
# MAGIC 마지막으로 PR에 기록할 수 있는 품질 체크를 수행합니다.
# MAGIC
# MAGIC - `risk_case_key` 중복이 없어야 합니다.
# MAGIC - Risk Card 최소 필드는 null이면 안 됩니다.
# MAGIC - `owner_edge_id`, `access_edge_id`, `credential_id`는 Silver 근거 추적을 위해 필요합니다.

# COMMAND ----------
required_columns = [
    "risk_case_key",
    "finding_id",
    "subject_display_name",
    "asset_display_name",
    "severity",
    "evidence_summary",
    "recommended_action",
    "owner_edge_id",
    "access_edge_id",
    "credential_id",
]

gold_df = spark.table(gold_table)

duplicate_keys = gold_df.groupBy("risk_case_key").count().where("count > 1").count()
missing_required = gold_df.where(
    F.expr(" OR ".join(f"{column} IS NULL" for column in required_columns))
).count()

print(f"duplicate risk_case_key rows: {duplicate_keys}")
print(f"gold rows with missing required fields: {missing_required}")

assert duplicate_keys == 0, f"duplicate risk_case_key rows: {duplicate_keys}"
assert missing_required == 0, f"gold rows with missing required fields: {missing_required}"

print("Gold Core pipeline verification passed")
