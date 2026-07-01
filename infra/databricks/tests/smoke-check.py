# Databricks notebook source
# MAGIC %md
# MAGIC # Databricks Smoke Check (Day 2~3 선결 게이트)
# MAGIC
# MAGIC 공용 catalog/schema에서 **CREATE TABLE · INSERT · MERGE INTO · SELECT** 가
# MAGIC 실제로 실행 가능한지 증명한다. 조회(SHOW GRANTS)가 아니라 **직접 실행**해 본다.
# MAGIC
# MAGIC 두 가지를 분리해서 검증한다:
# MAGIC
# MAGIC 1. **Part A — 대상 스키마별 CRUD 권한**: bronze/silver/intermediate/gold/eval **각각**에
# MAGIC    사용자별 임시 테이블을 만들어 CREATE/INSERT/MERGE/SELECT/DROP 를 직접 돌린다.
# MAGIC    → "silver 에 실제로 CREATE TABLE / MODIFY / SELECT 되는가"를 스키마 단위로 증명.
# MAGIC 2. **Part B — 기존 계약 테이블 포맷**: 이미 존재하는 silver_*, intermediate, gold 등이
# MAGIC    `DESCRIBE DETAIL` 기준 **delta 포맷**인지 확인.
# MAGIC    → "Day 3 Rule 조인 대상 테이블이 MERGE 가능한 Delta 상태인가"를 증명.
# MAGIC
# MAGIC - 각 단계를 try/except 로 감싸 "어디서 깨지는지"를 리포트로 수집한다 (첫 실패에서 멈추지 않음).
# MAGIC - 임시 테이블은 `_smoke_<user>` 접미사로 만들고 즉시 DROP → 실 데이터/네임스페이스 오염 없음.

# COMMAND ----------
dbutils.widgets.text("catalog", "access_drift")
dbutils.widgets.text("target_schemas", "bronze,silver,intermediate,gold,eval")
# 게이트 완료 기준("계약 테이블 Delta 포맷 확인")을 강제할지.
# true  = 계약 테이블이 없어(SKIP) 포맷을 못 봤으면 게이트 미완료로 실패 처리 (기본).
# false = migration 전에 권한만 보려고 돌릴 때. SKIP 을 허용하되 PASSED 로 끝내지 않고 PARTIAL.
dbutils.widgets.dropdown("fail_on_skip", "true", ["true", "false"])

CATALOG = dbutils.widgets.get("catalog")
TARGET_SCHEMAS = [s.strip() for s in dbutils.widgets.get("target_schemas").split(",") if s.strip()]
FAIL_ON_SKIP = dbutils.widgets.get("fail_on_skip") == "true"

import re
_user = spark.sql("SELECT current_user() AS u").collect()[0].u
SUFFIX = re.sub(r"[^a-z0-9]", "_", _user.split("@")[0].lower())  # 공용 클러스터 동시 실행 충돌 방지

# Day 3 Rule 조인 대상 — 존재하면 delta 포맷인지 확인한다 (없으면 SKIP)
CONTRACT_TABLES = {
    "silver": ["silver_principals", "silver_credentials", "silver_assets", "silver_edges"],
    "intermediate": ["nhi_residual_access_findings"],
    "gold": ["gold_core"],
    "eval": ["ground_truth_case"],
}

print(f"current_user   : {_user}")
print(f"catalog        : {CATALOG}")
print(f"target_schemas : {TARGET_SCHEMAS}")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 리포트 수집 헬퍼
# MAGIC 단계별 PASS / FAIL / SKIP 와 메시지를 모은다. SKIP = 권한 문제가 아니라 전제 미충족(예: 테이블 미생성).

# COMMAND ----------
results = []

class Skip(Exception):
    """전제 미충족(테이블 없음 등) — 권한 실패와 구분한다."""

def step(name, fn):
    try:
        fn()
        results.append((name, "PASS", ""))
        print(f"[PASS] {name}")
    except Skip as e:
        results.append((name, "SKIP", str(e)[:300]))
        print(f"[SKIP] {name} — {e}")
    except Exception as e:
        msg = str(e).strip().splitlines()[0][:300]  # UC 권한/포맷 에러는 보통 첫 줄에 핵심
        results.append((name, "FAIL", msg))
        print(f"[FAIL] {name}\n       {msg}")

# COMMAND ----------
# MAGIC %md
# MAGIC ## Part A — 대상 스키마별 CRUD 권한
# MAGIC 각 스키마에 `_smoke_<user>` 임시 테이블로 CREATE → INSERT → MERGE → SELECT → DROP.
# MAGIC MERGE 는 (1) target MODIFY 권한 (2) Delta 포맷 둘 다 맞아야 통과한다.

# COMMAND ----------
def run_crud(schema):
    tbl = f"{CATALOG}.{schema}._smoke_{SUFFIX}"
    p = f"{schema}: "

    def _use():
        # USE SCHEMA 는 스키마 이름 하나만 받는다(catalog.schema 를 넘기면 UC_INVALID_NAMESPACE).
        # USE CATALOG 로 카탈로그 컨텍스트를 잡은 뒤 USE SCHEMA 로 스키마를 잡는다.
        spark.sql(f"USE CATALOG {CATALOG}")
        spark.sql(f"USE SCHEMA {schema}")
    step(p + "USE SCHEMA", _use)

    def _create():
        # 계약 DDL과 동일하게 USING DELTA + NOT NULL + PRIMARY KEY 까지 검증한다.
        # → 공용 클러스터/UC 에서 PK 제약 생성이 실제로 되는지 확인.
        spark.sql(f"DROP TABLE IF EXISTS {tbl}")
        spark.sql(f"""
            CREATE TABLE {tbl} (
              id STRING NOT NULL,
              payload STRING,
              updated_at TIMESTAMP NOT NULL,
              CONSTRAINT smoke_pk_{SUFFIX} PRIMARY KEY (id)
            ) USING DELTA
        """)
    step(p + "CREATE TABLE (Delta + PK)", _create)

    def _insert():
        spark.sql(f"""
            INSERT INTO {tbl} VALUES
              ('k1', 'v1', current_timestamp()),
              ('k2', 'v2', current_timestamp())
        """)
    step(p + "INSERT", _insert)

    def _merge():
        src = spark.createDataFrame(
            [("k1", "v1-updated"), ("k3", "v3-new")], "id string, payload string"
        )
        src.createOrReplaceTempView(f"smoke_src_{SUFFIX}")
        spark.sql(f"""
            MERGE INTO {tbl} AS t
            USING smoke_src_{SUFFIX} AS s
            ON t.id = s.id
            WHEN MATCHED THEN UPDATE SET t.payload = s.payload, t.updated_at = current_timestamp()
            WHEN NOT MATCHED THEN INSERT (id, payload, updated_at)
                VALUES (s.id, s.payload, current_timestamp())
        """)
    step(p + "MERGE INTO", _merge)

    def _select():
        rows = {r.id: r.payload for r in spark.sql(f"SELECT id, payload FROM {tbl}").collect()}
        assert rows.get("k1") == "v1-updated", f"k1 not updated: {rows.get('k1')}"
        assert rows.get("k2") == "v2",         f"k2 changed: {rows.get('k2')}"
        assert rows.get("k3") == "v3-new",     f"k3 not inserted: {rows.get('k3')}"
        assert len(rows) == 3,                 f"expected 3 rows, got {len(rows)}"
    step(p + "SELECT + MERGE 결과 검증", _select)

    def _drop():
        spark.sql(f"DROP TABLE IF EXISTS {tbl}")
    step(p + "DROP TABLE (cleanup)", _drop)

for schema in TARGET_SCHEMAS:
    run_crud(schema)

# COMMAND ----------
# MAGIC %md
# MAGIC ## Part B — 기존 계약 테이블 포맷 (Day 3 Rule 대상)
# MAGIC 이미 만들어진 silver_*, intermediate, gold 등이 **delta** 포맷인지 `DESCRIBE DETAIL` 로 확인.
# MAGIC 테이블이 아직 없으면 SKIP (migration 미실행) — 권한 실패와 구분한다.

# COMMAND ----------
def check_format(schema, table):
    fq = f"{CATALOG}.{schema}.{table}"

    def _fmt():
        try:
            detail = spark.sql(f"DESCRIBE DETAIL {fq}").collect()[0]
        except Exception as e:
            first = str(e).splitlines()[0]
            if "NOT_FOUND" in first.upper() or "cannot be found" in first.lower():
                raise Skip("테이블 없음 — migration 미실행")
            raise
        fmt = (detail.format or "").lower()
        assert fmt == "delta", f"format={fmt} (delta 아님 → MERGE 불가)"
        # 참고용: 프로토콜 버전도 같이 출력
        print(f"       {fq}: format=delta, "
              f"minReaderVersion={getattr(detail, 'minReaderVersion', '?')}, "
              f"minWriterVersion={getattr(detail, 'minWriterVersion', '?')}")
    step(f"format: {schema}.{table}", _fmt)

for schema, tables in CONTRACT_TABLES.items():
    if schema in TARGET_SCHEMAS:
        for table in tables:
            check_format(schema, table)

# COMMAND ----------
# MAGIC %md
# MAGIC ## 결과 요약

# COMMAND ----------
from pyspark.sql import Row
report = spark.createDataFrame([Row(step=n, status=s, detail=d) for n, s, d in results])
display(report)

n_pass = sum(1 for _, s, _ in results if s == "PASS")
skipped = [n for n, s, _ in results if s == "SKIP"]
failed = [n for n, s, _ in results if s == "FAIL"]
print(f"PASS={n_pass}  SKIP={len(skipped)}  FAIL={len(failed)}")

# 1) 권한/포맷 실패는 무조건 게이트 실패
if failed:
    raise AssertionError(
        "smoke check FAILED: " + ", ".join(failed) +
        "\n  → MERGE/CREATE 실패 시: 해당 스키마 CREATE TABLE·MODIFY 권한 / Delta 포맷 / 클러스터 access mode 확인"
    )

# 2) SKIP 이 있으면 게이트 완료 기준("계약 테이블 Delta 포맷 확인")을 못 채운 것 → PARTIAL
if skipped:
    msg = (
        "smoke check PARTIAL — 권한 CRUD 는 통과했으나 계약 테이블 포맷을 확인 못 함 (SKIP): "
        + ", ".join(skipped)
        + "\n  → migration(00_apply_migrations) 실행 후 재실행해야 게이트 완료"
    )
    if FAIL_ON_SKIP:
        raise AssertionError(msg)
    print(msg)
else:
    print("smoke check PASSED — 대상 스키마 CRUD + 계약 테이블 포맷 모두 OK")
