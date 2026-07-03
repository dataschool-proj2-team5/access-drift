# Databricks notebook source
dbutils.widgets.text("catalog", "access_drift_dev")
dbutils.widgets.text("source_schema", "bronze")
dbutils.widgets.text("target_schema", "dlt_test")

CATALOG = dbutils.widgets.get("catalog")
SOURCE_SCHEMA = dbutils.widgets.get("source_schema")
TARGET_SCHEMA = dbutils.widgets.get("target_schema")

# COMMAND ----------
from pyspark.sql import functions as F


SOURCE_TABLES = (
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
)


def _write_fixture(df, fixture_kind, source_table):
    target = f"{CATALOG}.{TARGET_SCHEMA}.silver_{fixture_kind}_{source_table}"
    (
        df.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(target)
    )
    print(f"{target}: {spark.table(target).count()} rows")


def _invalid_row(source_table, df):
    row = df.limit(1)
    if source_table == "bronze_azure_applications":
        return row.withColumn("app_id", F.lit(None).cast("string"))
    if source_table == "bronze_azure_application_owners":
        return row.withColumn("app_id", F.lit("missing-application")).withColumn(
            "user_principal_name", F.lit("missing-owner@example.invalid")
        )
    if source_table == "bronze_azure_password_credentials":
        return (
            row.withColumn("app_id", F.lit("missing-application"))
            .withColumn("key_id", F.lit(None).cast("string"))
            .withColumn("status", F.lit("invalid-status"))
        )
    if source_table == "bronze_identity_lifecycle_seed":
        return row.withColumn("user_principal_name", F.lit(None).cast("string"))
    if source_table == "bronze_assets_seed":
        return (
            row.withColumn("asset_id", F.lit(None).cast("string"))
            .withColumn("environment", F.lit("invalid-environment"))
            .withColumn("sensitivity", F.lit("invalid-sensitivity"))
        )
    if source_table == "bronze_access_edges_seed":
        return (
            row.withColumn("principal_id", F.lit("missing-principal"))
            .withColumn("asset_id", F.lit("missing-asset"))
            .withColumn("relationship", F.lit("invalid-relationship"))
            .withColumn("status", F.lit("invalid-status"))
        )
    if source_table == "bronze_github_apps":
        return row.withColumn("app_id", F.lit(None).cast("string"))
    if source_table == "bronze_github_credentials":
        return (
            row.withColumn("app_id", F.lit("missing-github-app"))
            .withColumn("credential_id", F.lit(None).cast("string"))
            .withColumn("credential_type", F.lit("invalid-credential-type"))
            .withColumn("status", F.lit("invalid-status"))
        )
    if source_table == "bronze_github_repos":
        return (
            row.withColumn("repo_id", F.lit(None).cast("string"))
            .withColumn("environment", F.lit("invalid-environment"))
            .withColumn("sensitivity", F.lit("invalid-sensitivity"))
        )
    if source_table == "bronze_github_access_edges":
        return (
            row.withColumn("principal_id", F.lit("missing-github-app"))
            .withColumn("asset_id", F.lit("missing-repo"))
            .withColumn("relationship", F.lit("invalid-relationship"))
            .withColumn("status", F.lit("invalid-status"))
        )
    if source_table == "bronze_google_workspace_users":
        return row.withColumn("user_id", F.lit(None).cast("string"))
    if source_table == "bronze_google_workspace_assets":
        return (
            row.withColumn("asset_id", F.lit(None).cast("string"))
            .withColumn("environment", F.lit("invalid-environment"))
            .withColumn("sensitivity", F.lit("invalid-sensitivity"))
        )
    if source_table == "bronze_google_workspace_access_edges":
        return (
            row.withColumn("principal_id", F.lit("missing-google-user"))
            .withColumn("asset_id", F.lit("missing-workspace"))
            .withColumn("relationship", F.lit("invalid-relationship"))
            .withColumn("status", F.lit("invalid-status"))
        )
    if source_table == "bronze_slack_users":
        return row.withColumn("user_id", F.lit(None).cast("string"))
    if source_table == "bronze_slack_channels":
        return (
            row.withColumn("channel_id", F.lit(None).cast("string"))
            .withColumn("environment", F.lit("invalid-environment"))
            .withColumn("sensitivity", F.lit("invalid-sensitivity"))
        )
    if source_table == "bronze_slack_access_edges":
        return (
            row.withColumn("principal_id", F.lit("missing-slack-user"))
            .withColumn("asset_id", F.lit("missing-channel"))
            .withColumn("relationship", F.lit("invalid-relationship"))
            .withColumn("status", F.lit("invalid-status"))
        )
    raise ValueError(f"unsupported fixture source: {source_table}")


for table_name in SOURCE_TABLES:
    source = spark.table(f"{CATALOG}.{SOURCE_SCHEMA}.{table_name}")
    if source.limit(1).count() == 0:
        raise RuntimeError(f"fixture source is empty: {table_name}")

    _write_fixture(source, "valid", table_name)
    _write_fixture(source.unionByName(_invalid_row(table_name, source)), "invalid", table_name)

    empty_source = source.limit(0) if table_name == SOURCE_TABLES[0] else source
    _write_fixture(empty_source, "empty", table_name)

# COMMAND ----------
expected = len(SOURCE_TABLES) * 3
actual = len(
    [
        table
        for table in spark.catalog.listTables(f"{CATALOG}.{TARGET_SCHEMA}")
        if table.name.startswith("silver_valid_bronze_")
        or table.name.startswith("silver_invalid_bronze_")
        or table.name.startswith("silver_empty_bronze_")
    ]
)
assert actual >= expected, f"expected at least {expected} fixture tables, got {actual}"

summary = [
    "silver DLT fixture setup passed",
    f"source={CATALOG}.{SOURCE_SCHEMA}",
    f"target={CATALOG}.{TARGET_SCHEMA}",
    f"fixture_tables={expected}",
]
print("\n".join(summary))
dbutils.notebook.exit("\n".join(summary))
