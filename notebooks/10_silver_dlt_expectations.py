import dlt
from functools import reduce

from pyspark.sql import functions as F


SOURCE_CATALOG = spark.conf.get("silver.source_catalog")
SOURCE_SCHEMA = spark.conf.get("silver.source_schema")
SOURCE_PREFIX = spark.conf.get("silver.source_table_prefix", "")

SOURCE_TABLES = (
    "bronze_azure_applications",
    "bronze_azure_application_owners",
    "bronze_azure_password_credentials",
    "bronze_identity_lifecycle_seed",
    "bronze_assets_seed",
    "bronze_access_edges_seed",
)


def _source(table_name):
    return spark.table(
        f"{SOURCE_CATALOG}.{SOURCE_SCHEMA}.{SOURCE_PREFIX}{table_name}"
    )


def _silver_id(*parts):
    return F.sha2(F.concat_ws(":", *parts), 256)


def _require_sources(df, *source_names):
    gate = (
        dlt.read("silver_source_input_audit")
        .where(F.col("source_table").isin(*source_names))
        .agg(F.min("source_row_count").alias("minimum_source_row_count"))
    )
    return df.crossJoin(gate).drop("minimum_source_row_count")


@dlt.table(name="silver_source_input_audit", temporary=True)
@dlt.expect_all_or_fail({"source_not_empty": "source_row_count > 0"})
def silver_source_input_audit():
    rows = []
    for table_name in SOURCE_TABLES:
        rows.append(
            _source(table_name)
            .agg(F.count(F.lit(1)).alias("source_row_count"))
            .withColumn("source_table", F.lit(table_name))
            .select("source_table", "source_row_count")
        )
    return reduce(lambda left, right: left.unionByName(right), rows)


PRINCIPAL_EXPECTATIONS = {
    "required_principal_id": "principal_id IS NOT NULL AND trim(principal_id) <> ''",
    "required_source_principal_id": "source_principal_id IS NOT NULL AND trim(source_principal_id) <> ''",
    "valid_principal_kind": "principal_kind IN ('HI', 'NHI')",
    "valid_principal_type": "principal_type IN ('user', 'group', 'service_principal', 'app_registration', 'github_app', 'service_account', 'unknown')",
    "valid_principal_status": "status IN ('active', 'inactive', 'terminated', 'unknown')",
    "required_principal_observed_at": "observed_at IS NOT NULL",
    "deterministic_principal_id": "principal_id = sha2(concat_ws(':', source_system, source_principal_id, principal_type), 256)",
}


@dlt.table(name="silver_principals")
@dlt.expect_all(PRINCIPAL_EXPECTATIONS)
def silver_principals():
    applications = _source("bronze_azure_applications").select(
        _silver_id(
            F.lit("entra_id"), F.col("app_id"), F.lit("app_registration")
        ).alias("principal_id"),
        F.lit("entra_id").alias("source_system"),
        F.col("app_id").alias("source_principal_id"),
        F.lit("NHI").alias("principal_kind"),
        F.lit("app_registration").alias("principal_type"),
        F.col("display_name"),
        F.lit(None).cast("string").alias("email"),
        F.lit("active").alias("status"),
        F.lit(None).cast("date").alias("termination_date"),
        F.col("_ingestion_ts").alias("observed_at"),
    )

    lifecycle = _source("bronze_identity_lifecycle_seed")
    status = (
        F.when(F.col("employment_status") == "terminated", F.lit("terminated"))
        .when(F.col("employment_status") == "transferred", F.lit("inactive"))
        .otherwise(F.lit("active"))
    )
    humans = lifecycle.select(
        _silver_id(
            F.lit("identity_seed"),
            F.col("user_principal_name"),
            F.lit("user"),
        ).alias("principal_id"),
        F.lit("identity_seed").alias("source_system"),
        F.col("user_principal_name").alias("source_principal_id"),
        F.lit("HI").alias("principal_kind"),
        F.lit("user").alias("principal_type"),
        F.coalesce(
            F.col("display_name"), F.col("user_principal_name")
        ).alias("display_name"),
        F.col("user_principal_name").alias("email"),
        status.alias("status"),
        F.col("termination_date"),
        F.col("_ingestion_ts").alias("observed_at"),
    )
    return _require_sources(
        applications.unionByName(humans),
        "bronze_azure_applications",
        "bronze_identity_lifecycle_seed",
    )


CREDENTIAL_EXPECTATIONS = {
    "required_credential_id": "credential_id IS NOT NULL AND trim(credential_id) <> ''",
    "required_source_credential_id": "source_credential_id IS NOT NULL AND trim(source_credential_id) <> ''",
    "required_bound_principal_id": "bound_principal_id IS NOT NULL AND trim(bound_principal_id) <> ''",
    "valid_credential_type": "credential_type IN ('client_secret', 'certificate', 'pat', 'deploy_key', 'api_key', 'unknown')",
    "valid_credential_status": "status IN ('active', 'expired', 'revoked', 'unknown')",
    "required_is_active": "is_active IS NOT NULL",
    "required_credential_observed_at": "observed_at IS NOT NULL",
    "deterministic_credential_id": "credential_id = sha2(concat_ws(':', source_system, source_credential_id, bound_principal_id), 256)",
    "valid_is_active": "is_active = (status = 'active' AND (expires_at IS NULL OR expires_at > observed_at))",
}


@dlt.table(name="silver_credentials")
@dlt.expect_all(CREDENTIAL_EXPECTATIONS)
def silver_credentials():
    source = _source("bronze_azure_password_credentials")
    principal_id = _silver_id(
        F.lit("entra_id"), F.col("app_id"), F.lit("app_registration")
    )
    result = source.select(
        _silver_id(F.lit("entra_id"), F.col("key_id"), principal_id).alias(
            "credential_id"
        ),
        F.lit("entra_id").alias("source_system"),
        F.col("key_id").alias("source_credential_id"),
        principal_id.alias("bound_principal_id"),
        F.lit("client_secret").alias("credential_type"),
        F.col("display_name"),
        F.col("status"),
        F.col("end_date_time").alias("expires_at"),
        F.when(
            (F.col("status") == "active")
            & (
                F.col("end_date_time").isNull()
                | (F.col("end_date_time") > F.col("_ingestion_ts"))
            ),
            F.lit(True),
        ).otherwise(F.lit(False)).alias("is_active"),
        F.col("_ingestion_ts").alias("observed_at"),
    )
    return _require_sources(result, "bronze_azure_password_credentials")


ASSET_EXPECTATIONS = {
    "required_asset_id": "asset_id IS NOT NULL AND trim(asset_id) <> ''",
    "required_source_asset_id": "source_asset_id IS NOT NULL AND trim(source_asset_id) <> ''",
    "valid_asset_type": "asset_type IN ('cloud_resource', 'repo', 'database', 'workspace', 'saas_app', 'unknown')",
    "valid_environment": "environment IN ('production', 'staging', 'development', 'unknown')",
    "valid_sensitivity": "sensitivity IN ('high', 'medium', 'low', 'unknown')",
    "required_asset_observed_at": "observed_at IS NOT NULL",
    "deterministic_asset_id": "asset_id = sha2(concat_ws(':', source_system, source_asset_id, asset_type), 256)",
}


@dlt.table(name="silver_assets")
@dlt.expect_all(ASSET_EXPECTATIONS)
def silver_assets():
    result = _source("bronze_assets_seed").select(
        _silver_id(
            F.lit("assets_seed"), F.col("asset_id"), F.lit("cloud_resource")
        ).alias("asset_id"),
        F.lit("assets_seed").alias("source_system"),
        F.col("asset_id").alias("source_asset_id"),
        F.lit("cloud_resource").alias("asset_type"),
        F.col("name").alias("display_name"),
        F.col("environment"),
        F.col("sensitivity"),
        F.col("_ingestion_ts").alias("observed_at"),
    )
    return _require_sources(result, "bronze_assets_seed")


EDGE_EXPECTATIONS = {
    "required_edge_id": "edge_id IS NOT NULL AND trim(edge_id) <> ''",
    "required_edge_endpoints": "from_id IS NOT NULL AND trim(from_id) <> '' AND to_id IS NOT NULL AND trim(to_id) <> ''",
    "valid_from_type": "from_type IN ('principal', 'credential', 'asset')",
    "valid_to_type": "to_type IN ('principal', 'credential', 'asset')",
    "valid_edge_status": "status IN ('active', 'inactive', 'unknown')",
    "valid_relationship_direction": "(relationship = 'owns_principal' AND from_type = 'principal' AND to_type = 'principal') OR (relationship IN ('owns_credential', 'manages_credential', 'accesses_credential') AND from_type = 'principal' AND to_type = 'credential') OR (relationship IN ('manages_asset', 'accesses_asset') AND from_type IN ('principal', 'credential') AND to_type = 'asset') OR (relationship = 'manages_principal' AND from_type = 'principal' AND to_type = 'principal') OR relationship = 'unknown'",
    "required_edge_observed_at": "observed_at IS NOT NULL",
    "deterministic_edge_id": "edge_id = sha2(concat_ws(':', source_system, from_id, relationship, to_id), 256)",
}


@dlt.table(name="silver_edges")
@dlt.expect_all(EDGE_EXPECTATIONS)
def silver_edges():
    access = _source("bronze_access_edges_seed").select(
        _silver_id(
            F.lit("access_seed"),
            _silver_id(
                F.lit("entra_id"),
                F.col("principal_id"),
                F.lit("app_registration"),
            ),
            F.lit("accesses_asset"),
            _silver_id(
                F.lit("assets_seed"),
                F.col("asset_id"),
                F.lit("cloud_resource"),
            ),
        ).alias("edge_id"),
        F.lit("access_seed").alias("source_system"),
        _silver_id(
            F.lit("entra_id"),
            F.col("principal_id"),
            F.lit("app_registration"),
        ).alias("from_id"),
        F.lit("principal").alias("from_type"),
        _silver_id(
            F.lit("assets_seed"),
            F.col("asset_id"),
            F.lit("cloud_resource"),
        ).alias("to_id"),
        F.lit("asset").alias("to_type"),
        F.col("relationship"),
        F.col("permission"),
        F.col("status"),
        F.lit("bronze_access_edges_seed").alias("evidence_source"),
        F.col("_ingestion_ts").alias("observed_at"),
    )

    owners = _source("bronze_azure_application_owners").select(
        _silver_id(
            F.lit("entra_id"),
            _silver_id(
                F.lit("identity_seed"),
                F.col("user_principal_name"),
                F.lit("user"),
            ),
            F.lit("owns_principal"),
            _silver_id(
                F.lit("entra_id"),
                F.col("app_id"),
                F.lit("app_registration"),
            ),
        ).alias("edge_id"),
        F.lit("entra_id").alias("source_system"),
        _silver_id(
            F.lit("identity_seed"),
            F.col("user_principal_name"),
            F.lit("user"),
        ).alias("from_id"),
        F.lit("principal").alias("from_type"),
        _silver_id(
            F.lit("entra_id"), F.col("app_id"), F.lit("app_registration")
        ).alias("to_id"),
        F.lit("principal").alias("to_type"),
        F.lit("owns_principal").alias("relationship"),
        F.lit(None).cast("string").alias("permission"),
        F.lit("active").alias("status"),
        F.lit("bronze_azure_application_owners").alias("evidence_source"),
        F.col("_ingestion_ts").alias("observed_at"),
    )
    return _require_sources(
        access.unionByName(owners),
        "bronze_access_edges_seed",
        "bronze_azure_application_owners",
    )


def _audit_row(check_name, violations):
    return violations.agg(F.count(F.lit(1)).alias("violation_count")).withColumn(
        "check_name", F.lit(check_name)
    ).select("check_name", "violation_count")


@dlt.table(name="silver_integrity_audit", temporary=True)
@dlt.expect_all_or_fail({"no_integrity_violations": "violation_count = 0"})
def silver_integrity_audit():
    principals = dlt.read("silver_principals")
    credentials = dlt.read("silver_credentials")
    assets = dlt.read("silver_assets")
    edges = dlt.read("silver_edges")

    checks = [
        _audit_row(
            "duplicate_principal_id",
            principals.groupBy("principal_id").count().where("count > 1"),
        ),
        _audit_row(
            "duplicate_credential_id",
            credentials.groupBy("credential_id").count().where("count > 1"),
        ),
        _audit_row(
            "duplicate_asset_id",
            assets.groupBy("asset_id").count().where("count > 1"),
        ),
        _audit_row(
            "duplicate_edge_id",
            edges.groupBy("edge_id").count().where("count > 1"),
        ),
        _audit_row(
            "credential_principal_orphan",
            credentials.join(
                principals,
                credentials.bound_principal_id == principals.principal_id,
                "left_anti",
            ),
        ),
        _audit_row(
            "edge_from_principal_orphan",
            edges.where("from_type = 'principal'").join(
                principals, edges.from_id == principals.principal_id, "left_anti"
            ),
        ),
        _audit_row(
            "edge_to_principal_orphan",
            edges.where("to_type = 'principal'").join(
                principals, edges.to_id == principals.principal_id, "left_anti"
            ),
        ),
        _audit_row(
            "edge_to_asset_orphan",
            edges.where("to_type = 'asset'").join(
                assets, edges.to_id == assets.asset_id, "left_anti"
            ),
        ),
    ]
    return reduce(lambda left, right: left.unionByName(right), checks)
