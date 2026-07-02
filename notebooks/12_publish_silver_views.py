# Databricks notebook source
from datetime import datetime, timezone


dbutils.widgets.text("catalog", "access_drift_dev")
dbutils.widgets.text("schema", "silver")
dbutils.widgets.text("staging_prefix", "silver_dlt_")
dbutils.widgets.text("replace_existing_tables", "false")

CATALOG = dbutils.widgets.get("catalog")
SCHEMA = dbutils.widgets.get("schema")
STAGING_PREFIX = dbutils.widgets.get("staging_prefix")
REPLACE_EXISTING_TABLES = (
    dbutils.widgets.get("replace_existing_tables").strip().lower() == "true"
)

TABLES = [
    "silver_principals",
    "silver_credentials",
    "silver_assets",
    "silver_edges",
]


def q(name):
    return f"`{name}`"


def object_type(table_name):
    rows = spark.sql(
        f"""
        SELECT table_type
        FROM {q(CATALOG)}.information_schema.tables
        WHERE table_schema = '{SCHEMA}'
          AND table_name = '{table_name}'
        """
    ).collect()
    if not rows:
        return None
    return rows[0]["table_type"]


def assert_staging_exists(table_name):
    staging_name = f"{STAGING_PREFIX}{table_name.removeprefix('silver_')}"
    if object_type(staging_name) is None:
        raise RuntimeError(
            f"Silver DLT staging object not found: {CATALOG}.{SCHEMA}.{staging_name}"
        )
    return staging_name


spark.sql(f"CREATE SCHEMA IF NOT EXISTS {q(CATALOG)}.{q(SCHEMA)}")

backup_suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
published = []
backups = []

for table_name in TABLES:
    staging_name = assert_staging_exists(table_name)
    current_type = object_type(table_name)

    if current_type is not None and current_type.upper() != "VIEW":
        if not REPLACE_EXISTING_TABLES:
            raise RuntimeError(
                f"{CATALOG}.{SCHEMA}.{table_name} is {current_type}, not VIEW. "
                "Set replace_existing_tables=true only after backup/rollback review."
            )
        backup_name = f"{table_name}_legacy_{backup_suffix}"
        spark.sql(
            f"ALTER TABLE {q(CATALOG)}.{q(SCHEMA)}.{q(table_name)} "
            f"RENAME TO {q(CATALOG)}.{q(SCHEMA)}.{q(backup_name)}"
        )
        backups.append(f"{table_name}->{backup_name}")

    spark.sql(
        f"""
        CREATE OR REPLACE VIEW {q(CATALOG)}.{q(SCHEMA)}.{q(table_name)}
        AS SELECT * FROM {q(CATALOG)}.{q(SCHEMA)}.{q(staging_name)}
        """
    )
    row_count = spark.table(f"{CATALOG}.{SCHEMA}.{table_name}").count()
    published.append(f"{table_name}: {row_count} rows from {staging_name}")

print("Silver view publish complete")
for line in backups:
    print(f"backup: {line}")
for line in published:
    print(line)

dbutils.notebook.exit("\n".join(["Silver view publish complete"] + backups + published))
