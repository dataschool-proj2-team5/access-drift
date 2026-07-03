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


def _source(table_name):
    return spark.table(f"{SOURCE_CATALOG}.{SOURCE_SCHEMA}.{SOURCE_PREFIX}{table_name}")


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
    "required_source_system": "source_system IS NOT NULL AND trim(source_system) <> ''",
    "required_source_principal_id": "source_principal_id IS NOT NULL AND trim(source_principal_id) <> ''",
    "valid_principal_source_system": "source_system IN ('entra_id', 'identity_seed')",
    "valid_principal_kind": "principal_kind IN ('HI', 'NHI')",
    "valid_principal_type": "principal_type IN ('user', 'group', 'service_principal', 'app_registration', 'github_app', 'service_account', 'unknown')",
    "valid_principal_status": "status IN ('active', 'inactive', 'terminated', 'unknown')",
    "required_principal_observed_at": "observed_at IS NOT NULL",
    "deterministic_principal_id": "principal_id = sha2(concat_ws(':', source_system, source_principal_id, principal_type), 256)",
}


@dlt.table(name="silver_dlt_principals")
@dlt.expect_all(PRINCIPAL_EXPECTATIONS)
def silver_principals():
    nhi = _source("bronze_azure_applications").select(
        _silver_id(F.lit("entra_id"), F.col("app_id"), F.lit("app_registration")).alias("principal_id"),
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

    status_map = (
        F.when(F.col("employment_status") == "terminated", F.lit("terminated"))
        .when(F.col("employment_status") == "transferred", F.lit("inactive"))
        .otherwise(F.lit("active"))
    )
    human = _source("bronze_identity_lifecycle_seed").select(
        _silver_id(F.lit("identity_seed"), F.col("user_principal_name"), F.lit("user")).alias("principal_id"),
        F.lit("identity_seed").alias("source_system"),
        F.col("user_principal_name").alias("source_principal_id"),
        F.lit("HI").alias("principal_kind"),
        F.lit("user").alias("principal_type"),
        F.coalesce(F.col("display_name"), F.col("user_principal_name")).alias("display_name"),
        F.col("user_principal_name").alias("email"),
        status_map.alias("status"),
        F.col("termination_date"),
        F.col("_ingestion_ts").alias("observed_at"),
    )

    github_apps = _source("bronze_github_apps").select(
        _silver_id(F.lit("entra_id"), F.col("app_id"), F.lit("github_app")).alias("principal_id"),
        F.lit("entra_id").alias("source_system"),
        F.col("app_id").alias("source_principal_id"),
        F.lit("NHI").alias("principal_kind"),
        F.lit("github_app").alias("principal_type"),
        F.col("display_name"),
        F.col("owner_email").alias("email"),
        F.lit("active").alias("status"),
        F.lit(None).cast("date").alias("termination_date"),
        F.col("_ingestion_ts").alias("observed_at"),
    )

    google_users = _source("bronze_google_workspace_users").select(
        _silver_id(F.lit("identity_seed"), F.col("user_id"), F.lit("user")).alias("principal_id"),
        F.lit("identity_seed").alias("source_system"),
        F.col("user_id").alias("source_principal_id"),
        F.lit("HI").alias("principal_kind"),
        F.lit("user").alias("principal_type"),
        F.col("display_name"),
        F.col("email"),
        F.when(F.col("employment_status") == "terminated", F.lit("terminated"))
        .when(F.col("status") == "suspended", F.lit("inactive"))
        .otherwise(F.lit("active")).alias("status"),
        F.col("termination_date"),
        F.col("_ingestion_ts").alias("observed_at"),
    )

    slack_users = _source("bronze_slack_users").select(
        _silver_id(F.lit("identity_seed"), F.col("user_id"), F.lit("user")).alias("principal_id"),
        F.lit("identity_seed").alias("source_system"),
        F.col("user_id").alias("source_principal_id"),
        F.lit("HI").alias("principal_kind"),
        F.lit("user").alias("principal_type"),
        F.col("display_name"),
        F.col("email"),
        F.when(F.col("employment_status") == "terminated", F.lit("terminated"))
        .when(F.col("status") == "deactivated", F.lit("inactive"))
        .otherwise(F.lit("active")).alias("status"),
        F.col("termination_date"),
        F.col("_ingestion_ts").alias("observed_at"),
    )

    return _require_sources(
        nhi.unionByName(human)
        .unionByName(github_apps)
        .unionByName(google_users)
        .unionByName(slack_users),
        "bronze_azure_applications",
        "bronze_identity_lifecycle_seed",
        "bronze_github_apps",
        "bronze_google_workspace_users",
        "bronze_slack_users",
    )


CREDENTIAL_EXPECTATIONS = {
    "required_credential_id": "credential_id IS NOT NULL AND trim(credential_id) <> ''",
    "required_source_system": "source_system = 'entra_id'",
    "required_source_credential_id": "source_credential_id IS NOT NULL AND trim(source_credential_id) <> ''",
    "required_bound_principal_id": "bound_principal_id IS NOT NULL AND trim(bound_principal_id) <> ''",
    "valid_credential_type": "credential_type IN ('client_secret', 'certificate', 'pat', 'deploy_key', 'api_key', 'unknown')",
    "valid_credential_status": "status IN ('active', 'expired', 'revoked', 'unknown')",
    "required_is_active": "is_active IS NOT NULL",
    "required_credential_observed_at": "observed_at IS NOT NULL",
    "deterministic_credential_id": "credential_id = sha2(concat_ws(':', source_system, source_credential_id, bound_principal_id), 256)",
    "valid_is_active": "is_active = (status = 'active' AND (expires_at IS NULL OR expires_at > observed_at))",
}


@dlt.table(name="silver_dlt_credentials")
@dlt.expect_all(CREDENTIAL_EXPECTATIONS)
def silver_credentials():
    azure_creds = _source("bronze_azure_password_credentials").select(
        _silver_id(
            F.lit("entra_id"),
            F.col("key_id"),
            _silver_id(F.lit("entra_id"), F.col("app_id"), F.lit("app_registration")),
        ).alias("credential_id"),
        F.lit("entra_id").alias("source_system"),
        F.col("key_id").alias("source_credential_id"),
        _silver_id(F.lit("entra_id"), F.col("app_id"), F.lit("app_registration")).alias("bound_principal_id"),
        F.lit("client_secret").alias("credential_type"),
        F.col("display_name"),
        F.col("status"),
        F.col("end_date_time").alias("expires_at"),
        F.when(
            (F.col("status") == "active")
            & (F.col("end_date_time").isNull() | (F.col("end_date_time") > F.col("_ingestion_ts"))),
            F.lit(True),
        ).otherwise(F.lit(False)).alias("is_active"),
        F.col("_ingestion_ts").alias("observed_at"),
    )

    github_creds = _source("bronze_github_credentials").select(
        _silver_id(
            F.lit("entra_id"),
            F.col("credential_id"),
            _silver_id(F.lit("entra_id"), F.col("app_id"), F.lit("github_app")),
        ).alias("credential_id"),
        F.lit("entra_id").alias("source_system"),
        F.col("credential_id").alias("source_credential_id"),
        _silver_id(F.lit("entra_id"), F.col("app_id"), F.lit("github_app")).alias("bound_principal_id"),
        F.when(F.col("credential_type") == "deploy_key", F.lit("deploy_key"))
        .when(F.col("credential_type") == "pat", F.lit("pat"))
        .otherwise(F.lit("unknown")).alias("credential_type"),
        F.col("display_name"),
        F.col("status"),
        F.col("expires_at"),
        F.when(
            (F.col("status") == "active")
            & (F.col("expires_at").isNull() | (F.col("expires_at") > F.col("_ingestion_ts"))),
            F.lit(True),
        ).otherwise(F.lit(False)).alias("is_active"),
        F.col("_ingestion_ts").alias("observed_at"),
    )

    return _require_sources(
        azure_creds.unionByName(github_creds),
        "bronze_azure_password_credentials",
        "bronze_github_credentials",
    )


ASSET_EXPECTATIONS = {
    "required_asset_id": "asset_id IS NOT NULL AND trim(asset_id) <> ''",
    "required_source_system": "source_system = 'assets_seed'",
    "required_source_asset_id": "source_asset_id IS NOT NULL AND trim(source_asset_id) <> ''",
    "valid_asset_type": "asset_type IN ('cloud_resource', 'repo', 'database', 'workspace', 'saas_app', 'unknown')",
    "valid_environment": "environment IN ('production', 'staging', 'development', 'unknown')",
    "valid_sensitivity": "sensitivity IN ('critical', 'high', 'medium', 'low', 'unknown')",
    "required_asset_observed_at": "observed_at IS NOT NULL",
    "deterministic_asset_id": "asset_id = sha2(concat_ws(':', source_system, source_asset_id, asset_type), 256)",
}


@dlt.table(name="silver_dlt_assets")
@dlt.expect_all(ASSET_EXPECTATIONS)
def silver_assets():
    base_assets = _source("bronze_assets_seed").select(
        _silver_id(F.lit("assets_seed"), F.col("asset_id"), F.lit("cloud_resource")).alias("asset_id"),
        F.lit("assets_seed").alias("source_system"),
        F.col("asset_id").alias("source_asset_id"),
        F.lit("cloud_resource").alias("asset_type"),
        F.col("name").alias("display_name"),
        F.col("environment"),
        F.col("sensitivity"),
        F.col("_ingestion_ts").alias("observed_at"),
    )

    github_repos = _source("bronze_github_repos").select(
        _silver_id(F.lit("assets_seed"), F.col("repo_id"), F.lit("repo")).alias("asset_id"),
        F.lit("assets_seed").alias("source_system"),
        F.col("repo_id").alias("source_asset_id"),
        F.lit("repo").alias("asset_type"),
        F.col("name").alias("display_name"),
        F.col("environment"),
        F.col("sensitivity"),
        F.col("_ingestion_ts").alias("observed_at"),
    )

    google_assets = _source("bronze_google_workspace_assets").select(
        _silver_id(F.lit("assets_seed"), F.col("asset_id"), F.lit("workspace")).alias("asset_id"),
        F.lit("assets_seed").alias("source_system"),
        F.col("asset_id").alias("source_asset_id"),
        F.lit("workspace").alias("asset_type"),
        F.col("name").alias("display_name"),
        F.col("environment"),
        F.col("sensitivity"),
        F.col("_ingestion_ts").alias("observed_at"),
    )

    slack_channels = _source("bronze_slack_channels").select(
        _silver_id(F.lit("assets_seed"), F.col("channel_id"), F.lit("saas_app")).alias("asset_id"),
        F.lit("assets_seed").alias("source_system"),
        F.col("channel_id").alias("source_asset_id"),
        F.lit("saas_app").alias("asset_type"),
        F.col("name").alias("display_name"),
        F.col("environment"),
        F.col("sensitivity"),
        F.col("_ingestion_ts").alias("observed_at"),
    )

    return _require_sources(
        base_assets.unionByName(github_repos)
        .unionByName(google_assets)
        .unionByName(slack_channels),
        "bronze_assets_seed",
        "bronze_github_repos",
        "bronze_google_workspace_assets",
        "bronze_slack_channels",
    )


EDGE_EXPECTATIONS = {
    "required_edge_id": "edge_id IS NOT NULL AND trim(edge_id) <> ''",
    "required_source_system": "source_system IN ('entra_id', 'access_seed')",
    "required_edge_endpoints": "from_id IS NOT NULL AND trim(from_id) <> '' AND to_id IS NOT NULL AND trim(to_id) <> ''",
    "valid_from_type": "from_type IN ('principal', 'credential', 'asset')",
    "valid_to_type": "to_type IN ('principal', 'credential', 'asset')",
    "valid_edge_status": "status IN ('active', 'inactive', 'unknown')",
    "valid_relationship_direction": "(relationship = 'owns_principal' AND from_type = 'principal' AND to_type = 'principal') OR (relationship IN ('owns_credential', 'manages_credential', 'accesses_credential') AND from_type = 'principal' AND to_type = 'credential') OR (relationship IN ('manages_asset', 'accesses_asset') AND from_type IN ('principal', 'credential') AND to_type = 'asset') OR (relationship = 'manages_principal' AND from_type = 'principal' AND to_type = 'principal') OR relationship = 'unknown'",
    "required_edge_observed_at": "observed_at IS NOT NULL",
    "deterministic_edge_id": "edge_id = sha2(concat_ws(':', source_system, from_id, relationship, to_id), 256)",
    "required_active_access_last_used_at": "relationship <> 'accesses_asset' OR status <> 'active' OR last_used_at IS NOT NULL",
    "valid_last_used_at_not_future": "last_used_at IS NULL OR last_used_at <= observed_at",
}


@dlt.table(name="silver_dlt_edges")
@dlt.expect_all(EDGE_EXPECTATIONS)
def silver_edges():
    access_edges = _source("bronze_access_edges_seed").select(
        _silver_id(
            F.lit("access_seed"),
            _silver_id(F.lit("entra_id"), F.col("principal_id"), F.lit("app_registration")),
            F.lit("accesses_asset"),
            _silver_id(F.lit("assets_seed"), F.col("asset_id"), F.lit("cloud_resource")),
        ).alias("edge_id"),
        F.lit("access_seed").alias("source_system"),
        _silver_id(F.lit("entra_id"), F.col("principal_id"), F.lit("app_registration")).alias("from_id"),
        F.lit("principal").alias("from_type"),
        _silver_id(F.lit("assets_seed"), F.col("asset_id"), F.lit("cloud_resource")).alias("to_id"),
        F.lit("asset").alias("to_type"),
        F.col("relationship"),
        F.col("permission"),
        F.col("status"),
        F.col("last_used_at"),
        F.lit("bronze_access_edges_seed").alias("evidence_source"),
        F.col("_ingestion_ts").alias("observed_at"),
    )

    owner_edges = _source("bronze_azure_application_owners").select(
        _silver_id(
            F.lit("entra_id"),
            _silver_id(F.lit("identity_seed"), F.col("user_principal_name"), F.lit("user")),
            F.lit("owns_principal"),
            _silver_id(F.lit("entra_id"), F.col("app_id"), F.lit("app_registration")),
        ).alias("edge_id"),
        F.lit("entra_id").alias("source_system"),
        _silver_id(F.lit("identity_seed"), F.col("user_principal_name"), F.lit("user")).alias("from_id"),
        F.lit("principal").alias("from_type"),
        _silver_id(F.lit("entra_id"), F.col("app_id"), F.lit("app_registration")).alias("to_id"),
        F.lit("principal").alias("to_type"),
        F.lit("owns_principal").alias("relationship"),
        F.lit(None).cast("string").alias("permission"),
        F.lit("active").alias("status"),
        F.lit(None).cast("timestamp").alias("last_used_at"),
        F.lit("bronze_azure_application_owners").alias("evidence_source"),
        F.col("_ingestion_ts").alias("observed_at"),
    )

    github_owner_edges = _source("bronze_github_apps").where(F.col("owner_email").isNotNull()).select(
        _silver_id(
            F.lit("entra_id"),
            _silver_id(F.lit("identity_seed"), F.col("owner_email"), F.lit("user")),
            F.lit("owns_principal"),
            _silver_id(F.lit("entra_id"), F.col("app_id"), F.lit("github_app")),
        ).alias("edge_id"),
        F.lit("entra_id").alias("source_system"),
        _silver_id(F.lit("identity_seed"), F.col("owner_email"), F.lit("user")).alias("from_id"),
        F.lit("principal").alias("from_type"),
        _silver_id(F.lit("entra_id"), F.col("app_id"), F.lit("github_app")).alias("to_id"),
        F.lit("principal").alias("to_type"),
        F.lit("owns_principal").alias("relationship"),
        F.lit(None).cast("string").alias("permission"),
        F.lit("active").alias("status"),
        F.lit(None).cast("timestamp").alias("last_used_at"),
        F.lit("bronze_github_apps").alias("evidence_source"),
        F.col("_ingestion_ts").alias("observed_at"),
    )

    github_credential_edges = _source("bronze_github_credentials").select(
        _silver_id(
            F.lit("access_seed"),
            _silver_id(F.lit("entra_id"), F.col("app_id"), F.lit("github_app")),
            F.lit("owns_credential"),
            _silver_id(
                F.lit("entra_id"),
                F.col("credential_id"),
                _silver_id(F.lit("entra_id"), F.col("app_id"), F.lit("github_app")),
            ),
        ).alias("edge_id"),
        F.lit("access_seed").alias("source_system"),
        _silver_id(F.lit("entra_id"), F.col("app_id"), F.lit("github_app")).alias("from_id"),
        F.lit("principal").alias("from_type"),
        _silver_id(
            F.lit("entra_id"),
            F.col("credential_id"),
            _silver_id(F.lit("entra_id"), F.col("app_id"), F.lit("github_app")),
        ).alias("to_id"),
        F.lit("credential").alias("to_type"),
        F.lit("owns_credential").alias("relationship"),
        F.lit(None).cast("string").alias("permission"),
        F.col("status"),
        F.lit(None).cast("timestamp").alias("last_used_at"),
        F.lit("bronze_github_credentials").alias("evidence_source"),
        F.col("_ingestion_ts").alias("observed_at"),
    )

    github_access_edges = _source("bronze_github_access_edges").select(
        _silver_id(
            F.lit("access_seed"),
            _silver_id(F.lit("entra_id"), F.col("principal_id"), F.lit("github_app")),
            F.lit("accesses_asset"),
            _silver_id(F.lit("assets_seed"), F.col("asset_id"), F.lit("repo")),
        ).alias("edge_id"),
        F.lit("access_seed").alias("source_system"),
        _silver_id(F.lit("entra_id"), F.col("principal_id"), F.lit("github_app")).alias("from_id"),
        F.lit("principal").alias("from_type"),
        _silver_id(F.lit("assets_seed"), F.col("asset_id"), F.lit("repo")).alias("to_id"),
        F.lit("asset").alias("to_type"),
        F.col("relationship"),
        F.col("permission"),
        F.col("status"),
        F.col("last_used_at"),
        F.lit("bronze_github_access_edges").alias("evidence_source"),
        F.col("_ingestion_ts").alias("observed_at"),
    )

    google_access_edges = _source("bronze_google_workspace_access_edges").select(
        _silver_id(
            F.lit("access_seed"),
            _silver_id(F.lit("identity_seed"), F.col("principal_id"), F.lit("user")),
            F.lit("accesses_asset"),
            _silver_id(F.lit("assets_seed"), F.col("asset_id"), F.lit("workspace")),
        ).alias("edge_id"),
        F.lit("access_seed").alias("source_system"),
        _silver_id(F.lit("identity_seed"), F.col("principal_id"), F.lit("user")).alias("from_id"),
        F.lit("principal").alias("from_type"),
        _silver_id(F.lit("assets_seed"), F.col("asset_id"), F.lit("workspace")).alias("to_id"),
        F.lit("asset").alias("to_type"),
        F.col("relationship"),
        F.col("permission"),
        F.col("status"),
        F.col("last_used_at"),
        F.lit("bronze_google_workspace_access_edges").alias("evidence_source"),
        F.col("_ingestion_ts").alias("observed_at"),
    )

    slack_access_edges = _source("bronze_slack_access_edges").select(
        _silver_id(
            F.lit("access_seed"),
            _silver_id(F.lit("identity_seed"), F.col("principal_id"), F.lit("user")),
            F.lit("accesses_asset"),
            _silver_id(F.lit("assets_seed"), F.col("asset_id"), F.lit("saas_app")),
        ).alias("edge_id"),
        F.lit("access_seed").alias("source_system"),
        _silver_id(F.lit("identity_seed"), F.col("principal_id"), F.lit("user")).alias("from_id"),
        F.lit("principal").alias("from_type"),
        _silver_id(F.lit("assets_seed"), F.col("asset_id"), F.lit("saas_app")).alias("to_id"),
        F.lit("asset").alias("to_type"),
        F.col("relationship"),
        F.col("permission"),
        F.col("status"),
        F.col("last_used_at"),
        F.lit("bronze_slack_access_edges").alias("evidence_source"),
        F.col("_ingestion_ts").alias("observed_at"),
    )

    return _require_sources(
        access_edges.unionByName(owner_edges)
        .unionByName(github_owner_edges)
        .unionByName(github_credential_edges)
        .unionByName(github_access_edges)
        .unionByName(google_access_edges)
        .unionByName(slack_access_edges),
        "bronze_access_edges_seed",
        "bronze_azure_application_owners",
        "bronze_github_apps",
        "bronze_github_credentials",
        "bronze_github_access_edges",
        "bronze_google_workspace_access_edges",
        "bronze_slack_access_edges",
    )


def _audit_row(check_name, violations):
    return violations.agg(F.count(F.lit(1)).alias("violation_count")).withColumn(
        "check_name", F.lit(check_name)
    ).select("check_name", "violation_count")


def _owner_edge_kind_violations(edges, principals):
    hi_principals = principals.where("principal_kind = 'HI'").select(
        F.col("principal_id").alias("hi_principal_id")
    )
    nhi_principals = principals.where("principal_kind = 'NHI'").select(
        F.col("principal_id").alias("nhi_principal_id")
    )
    owner_edges = edges.where("relationship = 'owns_principal'")
    return (
        owner_edges.join(hi_principals, owner_edges.from_id == hi_principals.hi_principal_id, "left")
        .join(nhi_principals, owner_edges.to_id == nhi_principals.nhi_principal_id, "left")
        .where("hi_principal_id IS NULL OR nhi_principal_id IS NULL")
    )


def _credential_bound_kind_violations(credentials, principals):
    nhi_principals = principals.where("principal_kind = 'NHI'").select(
        F.col("principal_id").alias("nhi_principal_id")
    )
    return credentials.join(
        nhi_principals,
        credentials.bound_principal_id == nhi_principals.nhi_principal_id,
        "left_anti",
    )


def _owner_edges_with_principals(edges, principals):
    edge = edges.where("relationship = 'owns_principal'").alias("edge")
    owner = principals.alias("owner")
    owned = principals.alias("owned")
    return (
        edge.join(owner, F.col("edge.from_id") == F.col("owner.principal_id"), "left")
        .join(owned, F.col("edge.to_id") == F.col("owned.principal_id"), "left")
        .select(
            F.col("edge.edge_id"),
            F.col("edge.status").alias("edge_status"),
            F.col("owner.principal_id").alias("owner_principal_id"),
            F.col("owner.source_principal_id").alias("owner_source_principal_id"),
            F.col("owner.display_name").alias("owner_display_name"),
            F.col("owner.email").alias("owner_email"),
            F.col("owner.status").alias("owner_status"),
            F.col("owner.termination_date").alias("owner_termination_date"),
            F.col("owned.principal_id").alias("owned_principal_id"),
            F.col("owned.source_principal_id").alias("owned_source_principal_id"),
            F.col("owned.display_name").alias("owned_display_name"),
            F.col("owned.principal_kind").alias("owned_principal_kind"),
            F.col("owned.principal_type").alias("owned_principal_type"),
        )
    )


def _access_edges_with_refs(edges, principals, credentials, assets):
    edge = edges.where("relationship = 'accesses_asset'").alias("edge")
    from_principal = principals.alias("from_principal")
    from_credential = credentials.alias("from_credential")
    asset = assets.alias("asset")
    return (
        edge.join(
            from_principal,
            (F.col("edge.from_type") == F.lit("principal"))
            & (F.col("edge.from_id") == F.col("from_principal.principal_id")),
            "left",
        )
        .join(
            from_credential,
            (F.col("edge.from_type") == F.lit("credential"))
            & (F.col("edge.from_id") == F.col("from_credential.credential_id")),
            "left",
        )
        .join(asset, F.col("edge.to_id") == F.col("asset.asset_id"), "left")
        .select(
            F.col("edge.edge_id"),
            F.col("edge.from_id"),
            F.col("edge.from_type"),
            F.col("edge.to_id"),
            F.col("edge.to_type"),
            F.col("edge.status"),
            F.col("edge.permission"),
            F.col("edge.last_used_at"),
            F.col("edge.observed_at"),
            F.col("edge.evidence_source"),
            F.col("from_principal.principal_kind").alias("from_principal_kind"),
            F.col("from_principal.principal_type").alias("from_principal_type"),
            F.col("from_principal.source_principal_id").alias("from_source_principal_id"),
            F.col("from_principal.display_name").alias("from_display_name"),
            F.col("from_principal.status").alias("from_principal_status"),
            F.col("from_credential.credential_type").alias("from_credential_type"),
            F.col("from_credential.status").alias("from_credential_status"),
            F.col("from_credential.is_active").alias("from_credential_is_active"),
            F.col("asset.source_asset_id"),
            F.col("asset.asset_type"),
            F.col("asset.display_name").alias("asset_display_name"),
            F.col("asset.environment").alias("asset_environment"),
            F.col("asset.sensitivity").alias("asset_sensitivity"),
        )
    )


def _credential_edge_bound_principal_mismatches(edges, credentials):
    credential_edges = edges.where(
        "relationship IN ('owns_credential', 'manages_credential', 'accesses_credential') "
        "AND to_type = 'credential'"
    ).alias("edge")
    credential = credentials.alias("credential")
    return (
        credential_edges.join(
            credential,
            F.col("edge.to_id") == F.col("credential.credential_id"),
            "inner",
        )
        .where(F.col("edge.from_id") != F.col("credential.bound_principal_id"))
        .select(F.col("edge.edge_id"))
    )


def _duplicate_hi_email_violations(principals):
    return (
        principals.where("principal_kind = 'HI' AND email IS NOT NULL AND trim(email) <> ''")
        .select(F.lower(F.trim(F.col("email"))).alias("email_key"), F.col("principal_id"))
        .groupBy("email_key")
        .agg(F.countDistinct("principal_id").alias("principal_count"))
        .where("principal_count > 1")
    )


def _identity_users_missing_silver_hi(identity_users, principals):
    silver_hi = principals.where("principal_kind = 'HI'").select(
        F.col("source_system").alias("silver_source_system"),
        F.col("source_principal_id").alias("silver_source_principal_id"),
    )
    return identity_users.join(
        silver_hi,
        (F.col("silver_source_system") == F.lit("identity_seed"))
        & (F.col("silver_source_principal_id") == F.col("user_principal_name")),
        "left_anti",
    )


def _github_owner_missing_identity(github_apps, identity_users):
    identity_keys = identity_users.select(
        F.lower(F.trim(F.col("user_principal_name"))).alias("identity_email")
    )
    github_owners = github_apps.where("owner_email IS NOT NULL").select(
        F.col("owner_email"),
        F.lower(F.trim("owner_email")).alias("owner_email_key"),
    )
    return github_owners.join(
        identity_keys,
        github_owners.owner_email_key == identity_keys.identity_email,
        "left_anti",
    )


def _github_owner_status_mismatches(github_apps, principals):
    expected_status = (
        F.when(F.col("owner_employment_status") == "terminated", F.lit("terminated"))
        .when(
            F.col("owner_employment_status").isin("transferred", "inactive", "suspended", "deactivated"),
            F.lit("inactive"),
        )
        .otherwise(F.lit("active"))
    )
    owners = principals.where("principal_kind = 'HI'").select(
        F.col("source_system").alias("owner_source_system"),
        F.col("source_principal_id").alias("owner_source_principal_id"),
        F.col("principal_id").alias("owner_principal_id"),
        F.col("status").alias("silver_owner_status"),
    )
    return (
        github_apps.where("owner_email IS NOT NULL")
        .withColumn("expected_owner_status", expected_status)
        .join(
            owners,
            (F.col("owner_source_system") == F.lit("identity_seed"))
            & (F.col("owner_source_principal_id") == F.col("owner_email")),
            "left",
        )
        .where(
            F.col("owner_principal_id").isNull()
            | (F.col("expected_owner_status") != F.col("silver_owner_status"))
        )
    )


def _source_users_missing_silver_hi(source_users, source_id_col, principals):
    silver_hi = principals.where("principal_kind = 'HI'").select(
        F.col("source_system").alias("silver_source_system"),
        F.col("source_principal_id").alias("silver_source_principal_id"),
    )
    return source_users.join(
        silver_hi,
        (F.col("silver_source_system") == F.lit("identity_seed"))
        & (F.col("silver_source_principal_id") == F.col(source_id_col)),
        "left_anti",
    )


@dlt.table(name="silver_integrity_audit", temporary=True)
@dlt.expect_all_or_fail({"no_integrity_violations": "violation_count = 0"})
def silver_integrity_audit():
    principals = dlt.read("silver_dlt_principals")
    credentials = dlt.read("silver_dlt_credentials")
    assets = dlt.read("silver_dlt_assets")
    edges = dlt.read("silver_dlt_edges")
    identity_users = _source("bronze_identity_lifecycle_seed")
    github_apps = _source("bronze_github_apps")
    google_users = _source("bronze_google_workspace_users")
    slack_users = _source("bronze_slack_users")
    owner_edges = _owner_edges_with_principals(edges, principals)
    access_edges = _access_edges_with_refs(edges, principals, credentials, assets)

    checks = [
        _audit_row("duplicate_principal_id", principals.groupBy("principal_id").count().where("count > 1")),
        _audit_row("duplicate_credential_id", credentials.groupBy("credential_id").count().where("count > 1")),
        _audit_row("duplicate_asset_id", assets.groupBy("asset_id").count().where("count > 1")),
        _audit_row("duplicate_edge_id", edges.groupBy("edge_id").count().where("count > 1")),
        _audit_row(
            "credential_principal_orphan",
            credentials.join(principals, credentials.bound_principal_id == principals.principal_id, "left_anti"),
        ),
        _audit_row(
            "edge_from_principal_orphan",
            edges.where("from_type = 'principal'").join(principals, edges.from_id == principals.principal_id, "left_anti"),
        ),
        _audit_row(
            "edge_to_principal_orphan",
            edges.where("to_type = 'principal'").join(principals, edges.to_id == principals.principal_id, "left_anti"),
        ),
        _audit_row(
            "edge_to_credential_orphan",
            edges.where("to_type = 'credential'").join(credentials, edges.to_id == credentials.credential_id, "left_anti"),
        ),
        _audit_row(
            "edge_to_asset_orphan",
            edges.where("to_type = 'asset'").join(assets, edges.to_id == assets.asset_id, "left_anti"),
        ),
        _audit_row("owner_edge_not_hi_to_nhi", _owner_edge_kind_violations(edges, principals)),
        _audit_row("credential_bound_principal_not_nhi", _credential_bound_kind_violations(credentials, principals)),
        _audit_row(
            "hi_display_name_missing",
            principals.where("principal_kind = 'HI' AND (display_name IS NULL OR trim(display_name) = '')"),
        ),
        _audit_row(
            "hi_display_name_email_fallback",
            principals.where(
                "principal_kind = 'HI' "
                "AND display_name IS NOT NULL "
                "AND lower(trim(display_name)) = lower(trim(coalesce(email, source_principal_id))) "
                "AND display_name LIKE '%@%.%'"
            ),
        ),
        _audit_row(
            "owner_display_name_email_fallback",
            owner_edges.where("owner_display_name IS NOT NULL AND owner_display_name LIKE '%@%.%'"),
        ),
        _audit_row(
            "owner_display_name_missing",
            owner_edges.where("owner_display_name IS NULL OR trim(owner_display_name) = ''"),
        ),
        _audit_row("hi_principal_type_not_user", principals.where("principal_kind = 'HI' AND principal_type <> 'user'")),
        _audit_row("nhi_principal_type_user", principals.where("principal_kind = 'NHI' AND principal_type = 'user'")),
        _audit_row(
            "nhi_display_name_missing_or_id_only",
            principals.where(
                "principal_kind = 'NHI' "
                "AND (display_name IS NULL OR trim(display_name) = '' "
                "OR lower(trim(display_name)) = lower(trim(source_principal_id)))"
            ),
        ),
        _audit_row(
            "terminated_hi_missing_termination_date",
            principals.where("principal_kind = 'HI' AND status = 'terminated' AND termination_date IS NULL"),
        ),
        _audit_row("duplicate_hi_email", _duplicate_hi_email_violations(principals)),
        _audit_row("identity_lifecycle_user_missing_silver_hi", _identity_users_missing_silver_hi(identity_users, principals)),
        _audit_row("github_owner_missing_identity_lifecycle", _github_owner_missing_identity(github_apps, identity_users)),
        _audit_row("github_owner_silver_status_mismatch", _github_owner_status_mismatches(github_apps, principals)),
        _audit_row("google_user_missing_silver_hi", _source_users_missing_silver_hi(google_users, "user_id", principals)),
        _audit_row("slack_user_missing_silver_hi", _source_users_missing_silver_hi(slack_users, "user_id", principals)),
        _audit_row(
            "credential_active_flag_mismatch",
            credentials.where(
                "is_active <> CASE "
                "WHEN status = 'active' AND (expires_at IS NULL OR expires_at > observed_at) THEN true "
                "ELSE false END"
            ),
        ),
        _audit_row(
            "credential_active_but_expired",
            credentials.where("is_active = true AND expires_at IS NOT NULL AND expires_at <= observed_at"),
        ),
        _audit_row(
            "credential_secret_like_display_name",
            credentials.where(
                "display_name IS NOT NULL AND ("
                "lower(display_name) LIKE '%secretvalue%' "
                "OR lower(display_name) LIKE '%privatekey%' "
                "OR lower(display_name) LIKE '%tokenvalue%' "
                "OR display_name RLIKE '^[A-Za-z0-9+/]{32,}={0,2}$')"
            ),
        ),
        _audit_row(
            "asset_display_name_missing_or_id_only",
            assets.where(
                "display_name IS NULL OR trim(display_name) = '' "
                "OR lower(trim(display_name)) = lower(trim(source_asset_id))"
            ),
        ),
        _audit_row("owner_edge_status_not_active", edges.where("relationship = 'owns_principal' AND status <> 'active'")),
        _audit_row(
            "access_edge_missing_endpoint",
            access_edges.where(
                "(from_type = 'principal' AND from_principal_kind IS NULL) "
                "OR (from_type = 'credential' AND from_credential_type IS NULL) "
                "OR asset_type IS NULL"
            ),
        ),
        _audit_row(
            "access_edge_missing_permission",
            access_edges.where("permission IS NULL OR trim(permission) = ''"),
        ),
        _audit_row(
            "access_edge_missing_last_used_at",
            access_edges.where("status = 'active' AND last_used_at IS NULL"),
        ),
        _audit_row(
            "access_edge_last_used_in_future",
            access_edges.where("last_used_at IS NOT NULL AND last_used_at > observed_at"),
        ),
        _audit_row(
            "access_metadata_on_non_access_edge",
            edges.where(
                "relationship <> 'accesses_asset' "
                "AND ((permission IS NOT NULL AND trim(permission) <> '') OR last_used_at IS NOT NULL)"
            ),
        ),
        _audit_row(
            "credential_edge_bound_principal_mismatch",
            _credential_edge_bound_principal_mismatches(edges, credentials),
        ),
        _audit_row(
            "duplicate_semantic_edge",
            edges.groupBy("from_id", "relationship", "to_id").count().where("count > 1"),
        ),
        _audit_row(
            "access_path_owner_not_display_ready",
            owner_edges.where(
                "owner_display_name IS NULL OR trim(owner_display_name) = '' "
                "OR owner_display_name LIKE '%@%.%' "
                "OR lower(trim(owner_display_name)) = lower(trim(owner_source_principal_id))"
            ),
        ),
        _audit_row(
            "access_path_subject_not_display_ready",
            owner_edges.where(
                "owned_display_name IS NULL OR trim(owned_display_name) = '' "
                "OR lower(trim(owned_display_name)) = lower(trim(owned_source_principal_id))"
            ),
        ),
        _audit_row(
            "access_path_asset_not_display_ready",
            access_edges.where(
                "asset_display_name IS NULL OR trim(asset_display_name) = '' "
                "OR lower(trim(asset_display_name)) = lower(trim(source_asset_id))"
            ),
        ),
        _audit_row(
            "access_path_active_access_missing_permission",
            access_edges.where("status = 'active' AND (permission IS NULL OR trim(permission) = '')"),
        ),
    ]
    return reduce(lambda left, right: left.unionByName(right), checks)
