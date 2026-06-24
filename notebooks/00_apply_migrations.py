# Databricks notebook source
# 00_apply_migrations — sql/databricks/migrations/*.sql 을 순서대로 실행
# DDL 원본: sql/databricks/migrations/
# 이 노트북은 스키마/테이블 생성만 담당한다. 데이터 적재는 하지 않는다.

# COMMAND ----------
dbutils.widgets.text("catalog", "access_drift")

CATALOG = dbutils.widgets.get("catalog")
MIGRATIONS_BASE = "/Workspace/Shared/access-drift/files/sql/databricks/migrations"

# COMMAND ----------
import os

if not os.path.isdir(MIGRATIONS_BASE):
    raise RuntimeError(
        f"Migration 파일 디렉터리를 찾을 수 없습니다: {MIGRATIONS_BASE}\n"
        "bundle deploy가 완료됐는지 확인하세요."
    )

# COMMAND ----------
# migration 파일별 변수 치환 정의
def strip_line_comments(sql: str) -> str:
    return "\n".join(
        line for line in sql.splitlines()
        if not line.strip().startswith("--")
    )

migrations = [
    ("001_create_bronze_tables.sql", {"catalog": CATALOG, "schema": "bronze"}),
    ("002_create_silver_tables.sql", {"catalog": CATALOG, "schema": "silver"}),
    ("003_create_eval_tables.sql",   {"catalog": CATALOG}),
]

for filename, variables in migrations:
    path = os.path.join(MIGRATIONS_BASE, filename)
    with open(path) as f:
        sql = f.read()

    for key, value in variables.items():
        sql = sql.replace(f"${{{key}}}", value)

    sql = strip_line_comments(sql)
    statements = [
        s.strip() for s in sql.split(";")
        if s.strip()
    ]

    for stmt in statements:
        spark.sql(stmt)

    print(f"{filename}: {len(statements)} statements applied")

# COMMAND ----------
# MAGIC %md ## Smoke test

# COMMAND ----------
expected_tables = {
    "bronze": [
        "bronze_azure_applications",
        "bronze_azure_application_owners",
        "bronze_azure_password_credentials",
        "bronze_identity_lifecycle_seed",
        "bronze_assets_seed",
        "bronze_access_edges_seed",
    ],
    "silver": [
        "silver_principals",
        "silver_credentials",
        "silver_assets",
        "silver_edges",
    ],
    "eval": [
        "ground_truth_case",
    ],
}

for schema, tables in expected_tables.items():
    existing = {
        row.tableName
        for row in spark.sql(f"SHOW TABLES IN {CATALOG}.{schema}").collect()
    }
    missing = sorted(set(tables) - existing)
    assert not missing, f"Missing tables in {CATALOG}.{schema}: {missing}"

print("migration smoke test passed")
print("migrations complete")
