# Databricks notebook source
dbutils.widgets.text("catalog", "access_drift_dev")
dbutils.widgets.text("schema", "bronze")

# COMMAND ----------
import json

from pyspark.sql import functions as F


CATALOG = dbutils.widgets.get("catalog")
SCHEMA = dbutils.widgets.get("schema")
TABLES = [
    "bronze_azure_applications",
    "bronze_azure_application_owners",
    "bronze_azure_password_credentials",
    "bronze_identity_lifecycle_seed",
    "bronze_assets_seed",
    "bronze_access_edges_seed",
]


def _quote_sql(value):
    return "'" + value.replace("'", "''") + "'"


table_name_sql = ", ".join(_quote_sql(table_name) for table_name in TABLES)
metadata_rows = (
    spark.sql(
        f"""
        SELECT table_name, last_altered
        FROM {CATALOG}.information_schema.tables
        WHERE table_schema = {_quote_sql(SCHEMA)}
          AND table_name IN ({table_name_sql})
        """
    )
    .collect()
)
metadata = {
    row["table_name"]: {
        "last_altered": row["last_altered"].isoformat()
        if row["last_altered"] is not None
        else None
    }
    for row in metadata_rows
}

tables = {}
for table_name in TABLES:
    table_fqn = f"{CATALOG}.{SCHEMA}.{table_name}"
    if not spark.catalog.tableExists(table_fqn):
        raise AssertionError(f"기존 Bronze table이 없습니다: {table_fqn}")

    row_count = spark.table(table_fqn).agg(F.count(F.lit(1)).alias("row_count")).first()[
        "row_count"
    ]
    history_row = spark.sql(f"DESCRIBE HISTORY {table_fqn} LIMIT 1").first()
    tables[table_name] = {
        "row_count": int(row_count),
        "last_altered": metadata.get(table_name, {}).get("last_altered"),
        "history_version": int(history_row["version"]) if history_row is not None else None,
    }

result = {
    "catalog": CATALOG,
    "schema": SCHEMA,
    "tables": tables,
}
result_json = json.dumps(result, ensure_ascii=False, sort_keys=True)
print(result_json)
dbutils.notebook.exit(result_json)
