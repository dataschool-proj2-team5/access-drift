# Databricks notebook source
from datetime import datetime, timezone


dbutils.widgets.text("catalog", "access_drift_dev")
dbutils.widgets.text("bronze_schema", "bronze")
dbutils.widgets.text("cutover_enabled", "false")
dbutils.widgets.text("replace_existing_tables", "false")

CATALOG = dbutils.widgets.get("catalog")
BRONZE_SCHEMA = dbutils.widgets.get("bronze_schema")
CUTOVER_ENABLED = dbutils.widgets.get("cutover_enabled").strip().lower() == "true"
REPLACE_EXISTING_TABLES = (
    dbutils.widgets.get("replace_existing_tables").strip().lower() == "true"
)

BRONZE_TABLES = [
    "bronze_azure_applications",
    "bronze_azure_application_owners",
    "bronze_azure_password_credentials",
    "bronze_identity_lifecycle_seed",
    "bronze_assets_seed",
    "bronze_access_edges_seed",
    "bronze_github_apps",
    "bronze_github_credentials",
    "bronze_github_repos",
    "bronze_github_access_edges",
    "bronze_google_workspace_users",
    "bronze_google_workspace_assets",
    "bronze_google_workspace_access_edges",
    "bronze_slack_users",
    "bronze_slack_channels",
    "bronze_slack_access_edges",
]


def q(name):
    return f"`{name}`"


def object_type(schema_name, object_name):
    rows = spark.sql(
        f"""
        SELECT table_type
        FROM {q(CATALOG)}.information_schema.tables
        WHERE table_schema = '{schema_name}'
          AND table_name = '{object_name}'
        """
    ).collect()
    if not rows:
        return None
    return rows[0]["table_type"]


def show_grants(object_kind, full_name):
    try:
        return [
            row.asDict(recursive=True)
            for row in spark.sql(f"SHOW GRANTS ON {object_kind} {full_name}").collect()
        ]
    except Exception as exc:
        return [{"error": str(exc)}]


def row_count(full_name):
    try:
        return spark.table(full_name).count()
    except Exception as exc:
        return f"ERROR: {exc}"


if not CUTOVER_ENABLED:
    dbutils.notebook.exit("DLT cutover preparation skipped")

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {q(CATALOG)}.{q(BRONZE_SCHEMA)}")

existing = []
for table_name in BRONZE_TABLES:
    current_type = object_type(BRONZE_SCHEMA, table_name)
    if current_type is not None:
        full_name = f"{q(CATALOG)}.{q(BRONZE_SCHEMA)}.{q(table_name)}"
        existing.append(
            {
                "table_name": table_name,
                "table_type": current_type,
                "row_count": row_count(f"{CATALOG}.{BRONZE_SCHEMA}.{table_name}"),
                "grants": show_grants("TABLE", full_name),
            }
        )

if not existing:
    dbutils.notebook.exit("No existing Bronze tables to rename")

print("Existing Bronze objects before DLT cutover:")
for item in existing:
    print(
        f"- {BRONZE_SCHEMA}.{item['table_name']} "
        f"type={item['table_type']} rows={item['row_count']}"
    )

if not REPLACE_EXISTING_TABLES:
    names = ", ".join(item["table_name"] for item in existing)
    raise RuntimeError(
        "Existing Bronze objects block DLT ownership. "
        "Set replace_existing_tables=true after reviewing backup/rollback. "
        f"objects={names}"
    )

backup_suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
renamed = []
for item in existing:
    table_name = item["table_name"]
    backup_name = f"{table_name}_legacy_{backup_suffix}"
    source = f"{q(CATALOG)}.{q(BRONZE_SCHEMA)}.{q(table_name)}"
    target = f"{q(CATALOG)}.{q(BRONZE_SCHEMA)}.{q(backup_name)}"
    object_keyword = "VIEW" if item["table_type"].upper() == "VIEW" else "TABLE"
    spark.sql(f"ALTER {object_keyword} {source} RENAME TO {target}")
    renamed.append(f"{table_name}->{backup_name}")

print("Bronze legacy rename complete")
for line in renamed:
    print(line)

dbutils.notebook.exit("\n".join(["Bronze legacy rename complete"] + renamed))
