# Databricks notebook source
dbutils.widgets.text("fixture_source_root", "data/dlt-test")
dbutils.widgets.text(
    "fixture_workspace_root", "/Workspace/Shared/access-drift/files"
)
dbutils.widgets.text(
    "fixture_raw_root",
    "abfss://lakehouse@acdriftadls.dfs.core.windows.net/raw/dlt-test",
)

FIXTURE_SOURCE_ROOT = dbutils.widgets.get("fixture_source_root").strip("/")
FIXTURE_WORKSPACE_ROOT = dbutils.widgets.get("fixture_workspace_root").rstrip("/")
FIXTURE_RAW_ROOT = dbutils.widgets.get("fixture_raw_root").rstrip("/")
WORKSPACE_SOURCE_ROOT = f"{FIXTURE_WORKSPACE_ROOT}/{FIXTURE_SOURCE_ROOT}"

# COMMAND ----------
import os


SOURCE_FILES = [
    "azure/applications.jsonl",
    "azure/application_owners.jsonl",
    "azure/password_credentials.jsonl",
    "identity/lifecycle_seed.jsonl",
    "assets/assets_seed.jsonl",
    "access/access_edges_seed.jsonl",
]

copied_files = []
for fixture_kind in ("valid", "invalid", "empty-source"):
    for relative_path in SOURCE_FILES:
        source = (
            f"{WORKSPACE_SOURCE_ROOT}/{fixture_kind}/landing/raw/{relative_path}"
        )
        destination = (
            f"{FIXTURE_RAW_ROOT}/{fixture_kind}/landing/raw/{relative_path}"
        )

        if not os.path.isfile(source):
            raise RuntimeError(f"DLT fixture 파일을 찾을 수 없습니다: {source}")

        dbutils.fs.mkdirs(destination.rsplit("/", 1)[0])
        dbutils.fs.rm(destination, recurse=False)
        dbutils.fs.cp(f"file:{source}", destination, recurse=False)
        copied_files.append(destination)
        print(f"copied: {fixture_kind}/{relative_path} -> {destination}")

# COMMAND ----------
for destination in copied_files:
    parent, filename = destination.rsplit("/", 1)
    uploaded_names = [item.name.rstrip("/") for item in dbutils.fs.ls(parent)]
    assert filename in uploaded_names, f"DLT fixture가 없습니다: {destination}"

summary = [
    "bronze DLT fixture setup passed",
    f"copied_files={len(copied_files)}",
    f"fixture_raw_root={FIXTURE_RAW_ROOT}",
]
print("\n".join(summary))
dbutils.notebook.exit("\n".join(summary))
