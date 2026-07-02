import dlt
from pyspark.sql import functions as F
from pyspark.sql.types import MapType, StringType, StructField, StructType


RAW_BASE = spark.conf.get("bronze.raw_base_path").rstrip("/")
FIXTURE_MODE = spark.conf.get("bronze.fixture_mode", "false").lower() == "true"
SCHEMA_VERSION = "0.1.0"
NULL_SENTINEL = "__NULL__"

COMMON_COLUMNS = [
    "_src_system",
    "_src_object",
    "_src_file_path",
    "_ingestion_ts",
    "_run_id",
    "_batch_id",
    "_checksum",
    "_raw_payload",
    "_schema_version",
]

SOURCE_FILES = {
    "azure/applications.jsonl": "applications",
    "azure/application_owners.jsonl": "application_owners",
    "azure/password_credentials.jsonl": "password_credentials",
    "identity/lifecycle_seed.jsonl": "lifecycle_seed",
    "assets/assets_seed.jsonl": "assets_seed",
    "access/access_edges_seed.jsonl": "access_edges_seed",
    "github/apps.jsonl": "github_apps",
    "github/credentials.jsonl": "github_credentials",
    "github/repos.jsonl": "github_repos",
    "github/access_edges.jsonl": "github_access_edges",
    "google_workspace/users.jsonl": "google_workspace_users",
    "google_workspace/assets.jsonl": "google_workspace_assets",
    "google_workspace/access_edges.jsonl": "google_workspace_access_edges",
    "slack/users.jsonl": "slack_users",
    "slack/channels.jsonl": "slack_channels",
    "slack/access_edges.jsonl": "slack_access_edges",
}

SOURCE_FIELDS = {
    "azure/applications.jsonl": ["appId", "displayName", "createdDateTime"],
    "azure/application_owners.jsonl": ["appId", "userPrincipalName"],
    "azure/password_credentials.jsonl": [
        "appId",
        "keyId",
        "displayName",
        "endDateTime",
        "status",
    ],
    "identity/lifecycle_seed.jsonl": [
        "userPrincipalName",
        "displayName",
        "employmentStatus",
        "terminationDate",
    ],
    "assets/assets_seed.jsonl": [
        "assetId",
        "name",
        "environment",
        "sensitivity",
    ],
    "access/access_edges_seed.jsonl": [
        "principalId",
        "assetId",
        "relationship",
        "permission",
        "status",
        "lastUsedDateTime",
        "last_used_at",
    ],
    "github/apps.jsonl": [
        "appId",
        "slug",
        "displayName",
        "status",
        "ownerEmail",
        "ownerEmploymentStatus",
        "ownerTerminationDate",
    ],
    "github/credentials.jsonl": [
        "appId",
        "credentialId",
        "credentialType",
        "displayName",
        "status",
        "expiresAt",
    ],
    "github/repos.jsonl": [
        "repoId",
        "name",
        "visibility",
        "environment",
        "sensitivity",
    ],
    "github/access_edges.jsonl": [
        "principalId",
        "assetId",
        "relationship",
        "permission",
        "status",
    ],
    "google_workspace/users.jsonl": [
        "userId",
        "email",
        "displayName",
        "status",
        "employmentStatus",
        "terminationDate",
    ],
    "google_workspace/assets.jsonl": [
        "assetId",
        "name",
        "assetType",
        "environment",
        "sensitivity",
    ],
    "google_workspace/access_edges.jsonl": [
        "principalId",
        "assetId",
        "relationship",
        "permission",
        "status",
    ],
    "slack/users.jsonl": [
        "userId",
        "email",
        "displayName",
        "status",
        "employmentStatus",
        "terminationDate",
    ],
    "slack/channels.jsonl": [
        "channelId",
        "name",
        "channelType",
        "environment",
        "sensitivity",
    ],
    "slack/access_edges.jsonl": [
        "principalId",
        "assetId",
        "relationship",
        "permission",
        "status",
    ],
}


def _sql_string(value):
    return "'" + value.replace("'", "''") + "'"


def _source_col(df, name, data_type="string"):
    if name in df.columns:
        return F.col(name).cast(data_type)
    return F.lit(None).cast(data_type)


def _read_source(relative_path):
    path = f"{RAW_BASE}/{relative_path}"
    source_schema = StructType(
        [StructField(name, StringType(), True) for name in SOURCE_FIELDS[relative_path]]
        + [
            StructField("_test_case", StringType(), True),
            StructField(
                "_test_overrides", MapType(StringType(), StringType()), True
            ),
        ]
    )
    source = (
        spark.read.text(path)
        .where(F.trim(F.col("value")) != "")
        .withColumnRenamed("value", "_source_json")
        .withColumn("_parsed_source", F.from_json(F.col("_source_json"), source_schema))
        .select("*", "_parsed_source.*")
        .drop("_parsed_source")
    )
    audit = (
        dlt.read("bronze_source_input_audit")
        .where(F.col("relative_path") == relative_path)
        .select(F.col("relative_path").alias("_audit_relative_path"))
    )
    return source.crossJoin(audit), path


def _apply_fixture_override(df, column_name, data_type):
    if not FIXTURE_MODE:
        return df

    override_value = F.element_at(F.col("_test_override_map"), F.lit(column_name))
    return df.withColumn(
        column_name,
        F.when(override_value == NULL_SENTINEL, F.lit(None).cast(data_type))
        .when(override_value.isNotNull(), override_value.cast(data_type))
        .otherwise(F.col(column_name)),
    )


def _add_metadata(df, src_system, src_object, file_path):
    raw_payload = F.col("_source_json")

    if FIXTURE_MODE and "_test_overrides" in df.columns:
        override_map = F.col("_test_overrides")
    else:
        override_map = F.lit(None).cast("MAP<STRING,STRING>")

    result = (
        df.withColumn("_test_override_map", override_map)
        .withColumn("_src_system", F.lit(src_system))
        .withColumn("_src_object", F.lit(src_object))
        .withColumn("_src_file_path", F.lit(file_path))
        .withColumn("_ingestion_ts", F.current_timestamp())
        .withColumn("_run_id", F.lit(None).cast("string"))
        .withColumn("_batch_id", F.lit(None).cast("string"))
        .withColumn("_raw_payload", raw_payload)
        .withColumn("_schema_version", F.lit(SCHEMA_VERSION))
    )

    for column_name, data_type in {
        "_src_system": "string",
        "_src_object": "string",
        "_src_file_path": "string",
        "_ingestion_ts": "timestamp",
        "_run_id": "string",
        "_batch_id": "string",
        "_raw_payload": "string",
        "_schema_version": "string",
    }.items():
        result = _apply_fixture_override(result, column_name, data_type)

    result = result.withColumn("_checksum", F.md5(F.col("_raw_payload")))
    return _apply_fixture_override(result, "_checksum", "string")


def _finalize(df, business_columns):
    selected = df.select(
        *COMMON_COLUMNS,
        *business_columns.keys(),
        "_test_override_map",
    )
    for column_name, data_type in business_columns.items():
        selected = _apply_fixture_override(selected, column_name, data_type)
    return selected.drop("_test_override_map")


def _forbidden_fields_expression():
    forbidden_names = [
        "risk_score",
        "riskScore",
        "severity",
        "finding_id",
        "findingId",
        "recommended_action",
        "recommendedAction",
        "why_risky",
        "whyRisky",
        "is_planted_risk",
        "isPlantedRisk",
        "is_distractor",
        "isDistractor",
        "expected_severity",
        "expectedSeverity",
        "seed_finding_type",
        "seedFindingType",
        "truth_class",
        "truthClass",
        "secret",
        "secret_value",
        "secretValue",
        "client_secret",
        "clientSecret",
        "token",
        "token_value",
        "tokenValue",
        "access_token",
        "accessToken",
        "refresh_token",
        "refreshToken",
        "private_key",
        "privateKey",
        "private_key_value",
        "privateKeyValue",
    ]
    field_checks = " AND ".join(
        f"NOT array_contains(json_object_keys(_raw_payload), '{name}')"
        for name in forbidden_names
    )
    return f"coalesce(({field_checks}), true)"


def _common_expectations(src_system, src_object, file_path):
    return {
        "valid_src_system": f"_src_system = {_sql_string(src_system)}",
        "valid_src_object": f"_src_object = {_sql_string(src_object)}",
        "valid_src_file_path": (
            f"_src_file_path IS NULL OR _src_file_path = {_sql_string(file_path)}"
        ),
        "valid_ingestion_ts": (
            "_ingestion_ts IS NOT NULL AND typeof(_ingestion_ts) = 'timestamp'"
        ),
        "valid_raw_payload": (
            "_raw_payload IS NOT NULL AND trim(_raw_payload) <> '' "
            "AND trim(_raw_payload) LIKE '{%' "
            "AND get_json_object(_raw_payload, '$') IS NOT NULL"
        ),
        "valid_checksum": (
            "_checksum IS NULL OR _checksum = md5(_raw_payload)"
        ),
        "valid_schema_version": f"_schema_version = '{SCHEMA_VERSION}'",
    }


FORBIDDEN_DROP = {"no_forbidden_fields": _forbidden_fields_expression()}


def _source_value(raw_name, bronze_name):
    return f"get_json_object(_raw_payload, '$.{raw_name}') <=> {bronze_name}"


def _timestamp_value(raw_name, bronze_name):
    raw_value = f"get_json_object(_raw_payload, '$.{raw_name}')"
    return (
        f"{raw_value} IS NULL OR "
        f"({bronze_name} IS NOT NULL AND "
        f"{bronze_name} = try_to_timestamp({raw_value}))"
    )


def _date_value(raw_name, bronze_name):
    raw_value = f"get_json_object(_raw_payload, '$.{raw_name}')"
    return (
        f"{raw_value} IS NULL OR "
        f"({bronze_name} IS NOT NULL AND "
        f"{bronze_name} = try_cast({raw_value} AS DATE))"
    )


@dlt.view(name="bronze_source_input_audit")
@dlt.expect_all_or_fail({"source_not_empty": "source_row_count > 0"})
def bronze_source_input_audit():
    audit_rows = []
    for relative_path, source_object in SOURCE_FILES.items():
        path = f"{RAW_BASE}/{relative_path}"
        row_count = (
            spark.read.text(path)
            .where(F.trim(F.col("value")) != "")
            .agg(F.count(F.lit(1)).alias("source_row_count"))
            .withColumn("relative_path", F.lit(relative_path))
            .withColumn("source_object", F.lit(source_object))
            .select("relative_path", "source_object", "source_row_count")
        )
        audit_rows.append(row_count)

    result = audit_rows[0]
    for audit_row in audit_rows[1:]:
        result = result.unionByName(audit_row)
    return result


def _build_applications():
    df, path = _read_source("azure/applications.jsonl")
    df = _add_metadata(df, "entra_id", "applications", path)
    df = (
        df.withColumn("app_id", _source_col(df, "appId"))
        .withColumn("display_name", _source_col(df, "displayName"))
        .withColumn(
            "created_at", F.try_to_timestamp(_source_col(df, "createdDateTime"))
        )
    )
    return _finalize(
        df,
        {"app_id": "string", "display_name": "string", "created_at": "timestamp"},
    )


def _build_application_owners():
    df, path = _read_source("azure/application_owners.jsonl")
    df = _add_metadata(df, "entra_id", "application_owners", path)
    df = (
        df.withColumn("app_id", _source_col(df, "appId"))
        .withColumn("user_principal_name", _source_col(df, "userPrincipalName"))
    )
    return _finalize(
        df, {"app_id": "string", "user_principal_name": "string"}
    )


def _build_password_credentials():
    df, path = _read_source("azure/password_credentials.jsonl")
    df = _add_metadata(df, "entra_id", "password_credentials", path)
    df = (
        df.withColumn("app_id", _source_col(df, "appId"))
        .withColumn("key_id", _source_col(df, "keyId"))
        .withColumn("display_name", _source_col(df, "displayName"))
        .withColumn(
            "end_date_time", F.try_to_timestamp(_source_col(df, "endDateTime"))
        )
        .withColumn("status", _source_col(df, "status"))
    )
    return _finalize(
        df,
        {
            "app_id": "string",
            "key_id": "string",
            "display_name": "string",
            "end_date_time": "timestamp",
            "status": "string",
        },
    )


def _build_lifecycle_seed():
    df, path = _read_source("identity/lifecycle_seed.jsonl")
    df = _add_metadata(df, "identity_seed", "lifecycle_seed", path)
    df = (
        df.withColumn("_termination_date_raw", _source_col(df, "terminationDate"))
        .withColumn("user_principal_name", _source_col(df, "userPrincipalName"))
        .withColumn("display_name", _source_col(df, "displayName"))
        .withColumn("employment_status", _source_col(df, "employmentStatus"))
        .withColumn(
            "termination_date", F.expr("try_cast(_termination_date_raw AS DATE)")
        )
    )
    return _finalize(
        df,
        {
            "user_principal_name": "string",
            "display_name": "string",
            "employment_status": "string",
            "termination_date": "date",
        },
    )


def _build_assets_seed():
    df, path = _read_source("assets/assets_seed.jsonl")
    df = _add_metadata(df, "assets_seed", "assets_seed", path)
    df = (
        df.withColumn("asset_id", _source_col(df, "assetId"))
        .withColumn("name", _source_col(df, "name"))
        .withColumn("environment", _source_col(df, "environment"))
        .withColumn("sensitivity", _source_col(df, "sensitivity"))
    )
    return _finalize(
        df,
        {
            "asset_id": "string",
            "name": "string",
            "environment": "string",
            "sensitivity": "string",
        },
    )


def _build_access_edges_seed():
    df, path = _read_source("access/access_edges_seed.jsonl")
    df = _add_metadata(df, "access_seed", "access_edges_seed", path)
    raw_last_used = F.coalesce(
        _source_col(df, "lastUsedDateTime"), _source_col(df, "last_used_at")
    )
    df = (
        df.withColumn("principal_id", _source_col(df, "principalId"))
        .withColumn("asset_id", _source_col(df, "assetId"))
        .withColumn("relationship", _source_col(df, "relationship"))
        .withColumn("permission", _source_col(df, "permission"))
        .withColumn("status", _source_col(df, "status"))
        .withColumn("last_used_at", F.try_to_timestamp(raw_last_used))
    )
    return _finalize(
        df,
        {
            "principal_id": "string",
            "asset_id": "string",
            "relationship": "string",
            "permission": "string",
            "status": "string",
            "last_used_at": "timestamp",
        },
    )


def _build_github_apps():
    df, path = _read_source("github/apps.jsonl")
    df = _add_metadata(df, "github_seed", "github_apps", path)
    df = (
        df.withColumn("app_id", _source_col(df, "appId"))
        .withColumn("slug", _source_col(df, "slug"))
        .withColumn("display_name", _source_col(df, "displayName"))
        .withColumn("status", _source_col(df, "status"))
        .withColumn("owner_email", _source_col(df, "ownerEmail"))
        .withColumn("owner_employment_status", _source_col(df, "ownerEmploymentStatus"))
        .withColumn(
            "owner_termination_date",
            F.expr("try_cast(ownerTerminationDate AS DATE)"),
        )
    )
    return _finalize(
        df,
        {
            "app_id": "string",
            "slug": "string",
            "display_name": "string",
            "status": "string",
            "owner_email": "string",
            "owner_employment_status": "string",
            "owner_termination_date": "date",
        },
    )


def _build_github_credentials():
    df, path = _read_source("github/credentials.jsonl")
    df = _add_metadata(df, "github_seed", "github_credentials", path)
    df = (
        df.withColumn("app_id", _source_col(df, "appId"))
        .withColumn("credential_id", _source_col(df, "credentialId"))
        .withColumn("credential_type", _source_col(df, "credentialType"))
        .withColumn("display_name", _source_col(df, "displayName"))
        .withColumn("status", _source_col(df, "status"))
        .withColumn("expires_at", F.try_to_timestamp(_source_col(df, "expiresAt")))
    )
    return _finalize(
        df,
        {
            "app_id": "string",
            "credential_id": "string",
            "credential_type": "string",
            "display_name": "string",
            "status": "string",
            "expires_at": "timestamp",
        },
    )


def _build_github_repos():
    df, path = _read_source("github/repos.jsonl")
    df = _add_metadata(df, "github_seed", "github_repos", path)
    df = (
        df.withColumn("repo_id", _source_col(df, "repoId"))
        .withColumn("name", _source_col(df, "name"))
        .withColumn("visibility", _source_col(df, "visibility"))
        .withColumn("environment", _source_col(df, "environment"))
        .withColumn("sensitivity", _source_col(df, "sensitivity"))
    )
    return _finalize(
        df,
        {
            "repo_id": "string",
            "name": "string",
            "visibility": "string",
            "environment": "string",
            "sensitivity": "string",
        },
    )


def _build_access_edge_source(relative_path, src_system, src_object):
    df, path = _read_source(relative_path)
    df = _add_metadata(df, src_system, src_object, path)
    df = (
        df.withColumn("principal_id", _source_col(df, "principalId"))
        .withColumn("asset_id", _source_col(df, "assetId"))
        .withColumn("relationship", _source_col(df, "relationship"))
        .withColumn("permission", _source_col(df, "permission"))
        .withColumn("status", _source_col(df, "status"))
    )
    return _finalize(
        df,
        {
            "principal_id": "string",
            "asset_id": "string",
            "relationship": "string",
            "permission": "string",
            "status": "string",
        },
    )


def _build_user_source(relative_path, src_system, src_object):
    df, path = _read_source(relative_path)
    df = _add_metadata(df, src_system, src_object, path)
    df = (
        df.withColumn("user_id", _source_col(df, "userId"))
        .withColumn("email", _source_col(df, "email"))
        .withColumn("display_name", _source_col(df, "displayName"))
        .withColumn("status", _source_col(df, "status"))
        .withColumn("employment_status", _source_col(df, "employmentStatus"))
        .withColumn("termination_date", F.expr("try_cast(terminationDate AS DATE)"))
    )
    return _finalize(
        df,
        {
            "user_id": "string",
            "email": "string",
            "display_name": "string",
            "status": "string",
            "employment_status": "string",
            "termination_date": "date",
        },
    )


def _build_workspace_assets():
    df, path = _read_source("google_workspace/assets.jsonl")
    df = _add_metadata(df, "google_workspace_seed", "google_workspace_assets", path)
    df = (
        df.withColumn("asset_id", _source_col(df, "assetId"))
        .withColumn("name", _source_col(df, "name"))
        .withColumn("asset_type", _source_col(df, "assetType"))
        .withColumn("environment", _source_col(df, "environment"))
        .withColumn("sensitivity", _source_col(df, "sensitivity"))
    )
    return _finalize(
        df,
        {
            "asset_id": "string",
            "name": "string",
            "asset_type": "string",
            "environment": "string",
            "sensitivity": "string",
        },
    )


def _build_slack_channels():
    df, path = _read_source("slack/channels.jsonl")
    df = _add_metadata(df, "slack_seed", "slack_channels", path)
    df = (
        df.withColumn("channel_id", _source_col(df, "channelId"))
        .withColumn("name", _source_col(df, "name"))
        .withColumn("channel_type", _source_col(df, "channelType"))
        .withColumn("environment", _source_col(df, "environment"))
        .withColumn("sensitivity", _source_col(df, "sensitivity"))
    )
    return _finalize(
        df,
        {
            "channel_id": "string",
            "name": "string",
            "channel_type": "string",
            "environment": "string",
            "sensitivity": "string",
        },
    )


APPLICATIONS_PATH = f"{RAW_BASE}/azure/applications.jsonl"
APPLICATIONS_HARD = {
    **_common_expectations("entra_id", "applications", APPLICATIONS_PATH),
    "valid_app_id_type": "typeof(app_id) = 'string'",
    "valid_display_name_type": "typeof(display_name) = 'string'",
    "valid_created_at_type": "typeof(created_at) = 'timestamp'",
    "preserved_app_id": _source_value("appId", "app_id"),
    "preserved_display_name": _source_value("displayName", "display_name"),
    "parsed_created_at": _timestamp_value("createdDateTime", "created_at"),
}
APPLICATIONS_WARN = {"ready_app_id": "app_id IS NOT NULL AND trim(app_id) <> ''"}

OWNERS_PATH = f"{RAW_BASE}/azure/application_owners.jsonl"
OWNERS_HARD = {
    **_common_expectations("entra_id", "application_owners", OWNERS_PATH),
    "valid_app_id_type": "typeof(app_id) = 'string'",
    "valid_user_principal_name_type": "typeof(user_principal_name) = 'string'",
    "preserved_app_id": _source_value("appId", "app_id"),
    "preserved_user_principal_name": _source_value(
        "userPrincipalName", "user_principal_name"
    ),
}
OWNERS_WARN = {
    "ready_owner_app_id": "app_id IS NOT NULL AND trim(app_id) <> ''",
    "ready_owner_user_principal_name": (
        "user_principal_name IS NOT NULL AND trim(user_principal_name) <> ''"
    ),
}

PASSWORDS_PATH = f"{RAW_BASE}/azure/password_credentials.jsonl"
PASSWORDS_HARD = {
    **_common_expectations("entra_id", "password_credentials", PASSWORDS_PATH),
    "valid_app_id_type": "typeof(app_id) = 'string'",
    "valid_key_id_type": "typeof(key_id) = 'string'",
    "valid_display_name_type": "typeof(display_name) = 'string'",
    "valid_end_date_time_type": "typeof(end_date_time) = 'timestamp'",
    "valid_status_type": "typeof(status) = 'string'",
    "preserved_app_id": _source_value("appId", "app_id"),
    "preserved_key_id": _source_value("keyId", "key_id"),
    "preserved_display_name": _source_value("displayName", "display_name"),
    "parsed_end_date_time": _timestamp_value("endDateTime", "end_date_time"),
    "preserved_status": _source_value("status", "status"),
}
PASSWORDS_WARN = {
    "ready_credential_app_id": "app_id IS NOT NULL AND trim(app_id) <> ''",
    "ready_credential_key_id": "key_id IS NOT NULL AND trim(key_id) <> ''",
}

LIFECYCLE_PATH = f"{RAW_BASE}/identity/lifecycle_seed.jsonl"
LIFECYCLE_HARD = {
    **_common_expectations("identity_seed", "lifecycle_seed", LIFECYCLE_PATH),
    "valid_user_principal_name_type": "typeof(user_principal_name) = 'string'",
    "valid_display_name_type": "typeof(display_name) = 'string'",
    "valid_employment_status_type": "typeof(employment_status) = 'string'",
    "valid_termination_date_type": "typeof(termination_date) = 'date'",
    "preserved_user_principal_name": _source_value(
        "userPrincipalName", "user_principal_name"
    ),
    "preserved_display_name": _source_value("displayName", "display_name"),
    "preserved_employment_status": _source_value(
        "employmentStatus", "employment_status"
    ),
    "parsed_termination_date": _date_value("terminationDate", "termination_date"),
}
LIFECYCLE_WARN = {
    "ready_user_principal_name": (
        "user_principal_name IS NOT NULL AND trim(user_principal_name) <> ''"
    ),
    "ready_display_name": "display_name IS NOT NULL AND trim(display_name) <> ''",
}

ASSETS_PATH = f"{RAW_BASE}/assets/assets_seed.jsonl"
ASSETS_HARD = {
    **_common_expectations("assets_seed", "assets_seed", ASSETS_PATH),
    "valid_asset_id_type": "typeof(asset_id) = 'string'",
    "valid_name_type": "typeof(name) = 'string'",
    "valid_environment_type": "typeof(environment) = 'string'",
    "valid_sensitivity_type": "typeof(sensitivity) = 'string'",
    "preserved_asset_id": _source_value("assetId", "asset_id"),
    "preserved_name": _source_value("name", "name"),
    "preserved_environment": _source_value("environment", "environment"),
    "preserved_sensitivity": _source_value("sensitivity", "sensitivity"),
}
ASSETS_WARN = {"ready_asset_id": "asset_id IS NOT NULL AND trim(asset_id) <> ''"}

ACCESS_PATH = f"{RAW_BASE}/access/access_edges_seed.jsonl"
ACCESS_HARD = {
    **_common_expectations("access_seed", "access_edges_seed", ACCESS_PATH),
    "valid_principal_id_type": "typeof(principal_id) = 'string'",
    "valid_asset_id_type": "typeof(asset_id) = 'string'",
    "valid_relationship_type": "typeof(relationship) = 'string'",
    "valid_permission_type": "typeof(permission) = 'string'",
    "valid_status_type": "typeof(status) = 'string'",
    "valid_last_used_at_type": "typeof(last_used_at) = 'timestamp'",
    "preserved_principal_id": _source_value("principalId", "principal_id"),
    "preserved_asset_id": _source_value("assetId", "asset_id"),
    "preserved_relationship": _source_value("relationship", "relationship"),
    "preserved_permission": _source_value("permission", "permission"),
    "preserved_status": _source_value("status", "status"),
    "parsed_last_used_at": (
        "coalesce(get_json_object(_raw_payload, '$.lastUsedDateTime'), "
        "get_json_object(_raw_payload, '$.last_used_at')) IS NULL OR "
        "(last_used_at IS NOT NULL AND last_used_at = try_to_timestamp(coalesce("
        "get_json_object(_raw_payload, '$.lastUsedDateTime'), "
        "get_json_object(_raw_payload, '$.last_used_at'))))"
    ),
}
ACCESS_WARN = {
    "ready_access_principal_id": (
        "principal_id IS NOT NULL AND trim(principal_id) <> ''"
    ),
    "ready_access_asset_id": "asset_id IS NOT NULL AND trim(asset_id) <> ''",
    "ready_access_relationship": (
        "relationship IS NOT NULL AND trim(relationship) <> ''"
    ),
}


def _simple_hard(src_system, src_object, relative_path, type_checks, preserve_checks):
    return {
        **_common_expectations(src_system, src_object, f"{RAW_BASE}/{relative_path}"),
        **type_checks,
        **preserve_checks,
    }


GITHUB_APPS_HARD = _simple_hard(
    "github_seed",
    "github_apps",
    "github/apps.jsonl",
    {
        "valid_app_id_type": "typeof(app_id) = 'string'",
        "valid_display_name_type": "typeof(display_name) = 'string'",
        "valid_owner_email_type": "typeof(owner_email) = 'string'",
        "valid_owner_termination_date_type": "typeof(owner_termination_date) = 'date'",
    },
    {
        "preserved_app_id": _source_value("appId", "app_id"),
        "preserved_display_name": _source_value("displayName", "display_name"),
        "preserved_owner_email": _source_value("ownerEmail", "owner_email"),
        "parsed_owner_termination_date": _date_value(
            "ownerTerminationDate", "owner_termination_date"
        ),
    },
)
GITHUB_APPS_WARN = {"ready_app_id": "app_id IS NOT NULL AND trim(app_id) <> ''"}

GITHUB_CREDENTIALS_HARD = _simple_hard(
    "github_seed",
    "github_credentials",
    "github/credentials.jsonl",
    {
        "valid_app_id_type": "typeof(app_id) = 'string'",
        "valid_credential_id_type": "typeof(credential_id) = 'string'",
        "valid_expires_at_type": "typeof(expires_at) = 'timestamp'",
    },
    {
        "preserved_app_id": _source_value("appId", "app_id"),
        "preserved_credential_id": _source_value("credentialId", "credential_id"),
        "parsed_expires_at": _timestamp_value("expiresAt", "expires_at"),
    },
)
GITHUB_CREDENTIALS_WARN = {
    "ready_credential_app_id": "app_id IS NOT NULL AND trim(app_id) <> ''",
    "ready_credential_id": "credential_id IS NOT NULL AND trim(credential_id) <> ''",
}

GITHUB_REPOS_HARD = _simple_hard(
    "github_seed",
    "github_repos",
    "github/repos.jsonl",
    {
        "valid_repo_id_type": "typeof(repo_id) = 'string'",
        "valid_name_type": "typeof(name) = 'string'",
        "valid_sensitivity_type": "typeof(sensitivity) = 'string'",
    },
    {
        "preserved_repo_id": _source_value("repoId", "repo_id"),
        "preserved_name": _source_value("name", "name"),
        "preserved_sensitivity": _source_value("sensitivity", "sensitivity"),
    },
)
GITHUB_REPOS_WARN = {"ready_repo_id": "repo_id IS NOT NULL AND trim(repo_id) <> ''"}

ACCESS_EDGE_HARD = {
    "valid_principal_id_type": "typeof(principal_id) = 'string'",
    "valid_asset_id_type": "typeof(asset_id) = 'string'",
    "valid_relationship_type": "typeof(relationship) = 'string'",
    "valid_permission_type": "typeof(permission) = 'string'",
    "valid_status_type": "typeof(status) = 'string'",
    "preserved_principal_id": _source_value("principalId", "principal_id"),
    "preserved_asset_id": _source_value("assetId", "asset_id"),
    "preserved_relationship": _source_value("relationship", "relationship"),
    "preserved_permission": _source_value("permission", "permission"),
    "preserved_status": _source_value("status", "status"),
}
ACCESS_EDGE_WARN = {
    "ready_principal_id": "principal_id IS NOT NULL AND trim(principal_id) <> ''",
    "ready_asset_id": "asset_id IS NOT NULL AND trim(asset_id) <> ''",
    "ready_relationship": "relationship IS NOT NULL AND trim(relationship) <> ''",
}

GITHUB_ACCESS_HARD = _simple_hard(
    "github_seed",
    "github_access_edges",
    "github/access_edges.jsonl",
    ACCESS_EDGE_HARD,
    {},
)
GOOGLE_ACCESS_HARD = _simple_hard(
    "google_workspace_seed",
    "google_workspace_access_edges",
    "google_workspace/access_edges.jsonl",
    ACCESS_EDGE_HARD,
    {},
)
SLACK_ACCESS_HARD = _simple_hard(
    "slack_seed",
    "slack_access_edges",
    "slack/access_edges.jsonl",
    ACCESS_EDGE_HARD,
    {},
)

USER_HARD = {
    "valid_user_id_type": "typeof(user_id) = 'string'",
    "valid_email_type": "typeof(email) = 'string'",
    "valid_display_name_type": "typeof(display_name) = 'string'",
    "valid_termination_date_type": "typeof(termination_date) = 'date'",
    "preserved_user_id": _source_value("userId", "user_id"),
    "preserved_email": _source_value("email", "email"),
    "preserved_display_name": _source_value("displayName", "display_name"),
    "parsed_termination_date": _date_value("terminationDate", "termination_date"),
}
USER_WARN = {
    "ready_user_id": "user_id IS NOT NULL AND trim(user_id) <> ''",
    "ready_email": "email IS NOT NULL AND trim(email) <> ''",
}

GOOGLE_USERS_HARD = _simple_hard(
    "google_workspace_seed",
    "google_workspace_users",
    "google_workspace/users.jsonl",
    USER_HARD,
    {},
)
SLACK_USERS_HARD = _simple_hard(
    "slack_seed",
    "slack_users",
    "slack/users.jsonl",
    USER_HARD,
    {},
)

GOOGLE_ASSETS_HARD = _simple_hard(
    "google_workspace_seed",
    "google_workspace_assets",
    "google_workspace/assets.jsonl",
    {
        "valid_asset_id_type": "typeof(asset_id) = 'string'",
        "valid_name_type": "typeof(name) = 'string'",
        "valid_asset_type_type": "typeof(asset_type) = 'string'",
        "valid_sensitivity_type": "typeof(sensitivity) = 'string'",
    },
    {
        "preserved_asset_id": _source_value("assetId", "asset_id"),
        "preserved_asset_type": _source_value("assetType", "asset_type"),
        "preserved_name": _source_value("name", "name"),
    },
)
GOOGLE_ASSETS_WARN = {
    "ready_asset_id": "asset_id IS NOT NULL AND trim(asset_id) <> ''"
}

SLACK_CHANNELS_HARD = _simple_hard(
    "slack_seed",
    "slack_channels",
    "slack/channels.jsonl",
    {
        "valid_channel_id_type": "typeof(channel_id) = 'string'",
        "valid_name_type": "typeof(name) = 'string'",
        "valid_channel_type_type": "typeof(channel_type) = 'string'",
        "valid_sensitivity_type": "typeof(sensitivity) = 'string'",
    },
    {
        "preserved_channel_id": _source_value("channelId", "channel_id"),
        "preserved_channel_type": _source_value("channelType", "channel_type"),
        "preserved_name": _source_value("name", "name"),
    },
)
SLACK_CHANNELS_WARN = {
    "ready_channel_id": "channel_id IS NOT NULL AND trim(channel_id) <> ''"
}


@dlt.table(name="bronze_azure_applications")
@dlt.expect_all_or_drop(FORBIDDEN_DROP)
@dlt.expect_all(APPLICATIONS_HARD)
@dlt.expect_all(APPLICATIONS_WARN)
def bronze_azure_applications():
    return _build_applications()


@dlt.table(name="bronze_azure_application_owners")
@dlt.expect_all_or_drop(FORBIDDEN_DROP)
@dlt.expect_all(OWNERS_HARD)
@dlt.expect_all(OWNERS_WARN)
def bronze_azure_application_owners():
    return _build_application_owners()


@dlt.table(name="bronze_azure_password_credentials")
@dlt.expect_all_or_drop(FORBIDDEN_DROP)
@dlt.expect_all(PASSWORDS_HARD)
@dlt.expect_all(PASSWORDS_WARN)
def bronze_azure_password_credentials():
    return _build_password_credentials()


@dlt.table(name="bronze_identity_lifecycle_seed")
@dlt.expect_all_or_drop(FORBIDDEN_DROP)
@dlt.expect_all(LIFECYCLE_HARD)
@dlt.expect_all(LIFECYCLE_WARN)
def bronze_identity_lifecycle_seed():
    return _build_lifecycle_seed()


@dlt.table(name="bronze_assets_seed")
@dlt.expect_all_or_drop(FORBIDDEN_DROP)
@dlt.expect_all(ASSETS_HARD)
@dlt.expect_all(ASSETS_WARN)
def bronze_assets_seed():
    return _build_assets_seed()


@dlt.table(name="bronze_access_edges_seed")
@dlt.expect_all_or_drop(FORBIDDEN_DROP)
@dlt.expect_all(ACCESS_HARD)
@dlt.expect_all(ACCESS_WARN)
def bronze_access_edges_seed():
    return _build_access_edges_seed()


@dlt.table(name="bronze_github_apps")
@dlt.expect_all_or_drop(FORBIDDEN_DROP)
@dlt.expect_all(GITHUB_APPS_HARD)
@dlt.expect_all(GITHUB_APPS_WARN)
def bronze_github_apps():
    return _build_github_apps()


@dlt.table(name="bronze_github_credentials")
@dlt.expect_all_or_drop(FORBIDDEN_DROP)
@dlt.expect_all(GITHUB_CREDENTIALS_HARD)
@dlt.expect_all(GITHUB_CREDENTIALS_WARN)
def bronze_github_credentials():
    return _build_github_credentials()


@dlt.table(name="bronze_github_repos")
@dlt.expect_all_or_drop(FORBIDDEN_DROP)
@dlt.expect_all(GITHUB_REPOS_HARD)
@dlt.expect_all(GITHUB_REPOS_WARN)
def bronze_github_repos():
    return _build_github_repos()


@dlt.table(name="bronze_github_access_edges")
@dlt.expect_all_or_drop(FORBIDDEN_DROP)
@dlt.expect_all(GITHUB_ACCESS_HARD)
@dlt.expect_all(ACCESS_EDGE_WARN)
def bronze_github_access_edges():
    return _build_access_edge_source(
        "github/access_edges.jsonl", "github_seed", "github_access_edges"
    )


@dlt.table(name="bronze_google_workspace_users")
@dlt.expect_all_or_drop(FORBIDDEN_DROP)
@dlt.expect_all(GOOGLE_USERS_HARD)
@dlt.expect_all(USER_WARN)
def bronze_google_workspace_users():
    return _build_user_source(
        "google_workspace/users.jsonl",
        "google_workspace_seed",
        "google_workspace_users",
    )


@dlt.table(name="bronze_google_workspace_assets")
@dlt.expect_all_or_drop(FORBIDDEN_DROP)
@dlt.expect_all(GOOGLE_ASSETS_HARD)
@dlt.expect_all(GOOGLE_ASSETS_WARN)
def bronze_google_workspace_assets():
    return _build_workspace_assets()


@dlt.table(name="bronze_google_workspace_access_edges")
@dlt.expect_all_or_drop(FORBIDDEN_DROP)
@dlt.expect_all(GOOGLE_ACCESS_HARD)
@dlt.expect_all(ACCESS_EDGE_WARN)
def bronze_google_workspace_access_edges():
    return _build_access_edge_source(
        "google_workspace/access_edges.jsonl",
        "google_workspace_seed",
        "google_workspace_access_edges",
    )


@dlt.table(name="bronze_slack_users")
@dlt.expect_all_or_drop(FORBIDDEN_DROP)
@dlt.expect_all(SLACK_USERS_HARD)
@dlt.expect_all(USER_WARN)
def bronze_slack_users():
    return _build_user_source("slack/users.jsonl", "slack_seed", "slack_users")


@dlt.table(name="bronze_slack_channels")
@dlt.expect_all_or_drop(FORBIDDEN_DROP)
@dlt.expect_all(SLACK_CHANNELS_HARD)
@dlt.expect_all(SLACK_CHANNELS_WARN)
def bronze_slack_channels():
    return _build_slack_channels()


@dlt.table(name="bronze_slack_access_edges")
@dlt.expect_all_or_drop(FORBIDDEN_DROP)
@dlt.expect_all(SLACK_ACCESS_HARD)
@dlt.expect_all(ACCESS_EDGE_WARN)
def bronze_slack_access_edges():
    return _build_access_edge_source(
        "slack/access_edges.jsonl", "slack_seed", "slack_access_edges"
    )
