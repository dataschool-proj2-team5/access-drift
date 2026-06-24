# Databricks notebook source
# 01_synthetic_data — seed 파일을 ADLS raw/ 에 복사
# DDL은 00_apply_migrations.py 에서 처리한다.

# COMMAND ----------
dbutils.widgets.text("catalog", "access_drift")
dbutils.widgets.text("storage_account", "acdriftadls")

CATALOG = dbutils.widgets.get("catalog")
STORAGE = dbutils.widgets.get("storage_account")
RAW_BASE = f"abfss://lakehouse@{STORAGE}.dfs.core.windows.net/raw"

# bundle deploy 시 data/poc/landing/raw/ 가 /Workspace/Shared/access-drift/files/ 아래에 배포됨
SEED_BASE = "/Workspace/Shared/access-drift/files/data/poc/landing/raw"

# COMMAND ----------
import os

if not os.path.isdir(SEED_BASE):
    raise RuntimeError(
        f"Seed 파일 디렉터리를 찾을 수 없습니다: {SEED_BASE}\n"
        "bundle deploy가 완료됐는지 확인하세요."
    )
print(f"seed path OK: {SEED_BASE}")

# COMMAND ----------
# MAGIC %md ## Seed 파일 → ADLS raw/ 복사
# 기준 건수: 각 파일 10건 (data/poc/README.md 참고)
# 주의: overwrite=True — PoC seed 재생성 전용. 공용 catalog에서 다른 작업 중이면 실행 전 확인 필요.

# COMMAND ----------
seed_mappings = [
    ("azure/applications.jsonl",        f"{RAW_BASE}/azure/applications.jsonl"),
    ("azure/application_owners.jsonl",  f"{RAW_BASE}/azure/application_owners.jsonl"),
    ("azure/password_credentials.jsonl",f"{RAW_BASE}/azure/password_credentials.jsonl"),
    ("identity/lifecycle_seed.jsonl",   f"{RAW_BASE}/identity/lifecycle_seed.jsonl"),
    ("assets/assets_seed.jsonl",        f"{RAW_BASE}/assets/assets_seed.jsonl"),
    ("access/access_edges_seed.jsonl",  f"{RAW_BASE}/access/access_edges_seed.jsonl"),
]

for rel_path, dst in seed_mappings:
    src = f"file:{SEED_BASE}/{rel_path}"
    dbutils.fs.cp(src, dst, recurse=False)
    print(f"copied: {rel_path} → {dst}")

# COMMAND ----------
# MAGIC %md ## Smoke test

# COMMAND ----------
for _, dst in seed_mappings:
    files = dbutils.fs.ls(dst)
    assert len(files) == 1, f"raw seed file not found: {dst}"

print("seed upload smoke test passed")
print("seed upload complete")
