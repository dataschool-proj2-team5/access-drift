# Databricks notebook source
dbutils.widgets.text("catalog", "access_drift_dev")
dbutils.widgets.text("schema", "dlt_test")
dbutils.widgets.text("event_log_schema", "dlt_test")
dbutils.widgets.text("event_log_table", "bronze_dlt_expectations_event_log")
dbutils.widgets.text("update_id", "")
dbutils.widgets.text("expected_case", "valid")

# COMMAND ----------
import json

from pyspark.sql import functions as F


CATALOG = dbutils.widgets.get("catalog")
SCHEMA = dbutils.widgets.get("schema")
EVENT_LOG_SCHEMA = dbutils.widgets.get("event_log_schema")
EVENT_LOG_TABLE = dbutils.widgets.get("event_log_table")
UPDATE_ID = dbutils.widgets.get("update_id").strip()
EXPECTED_CASE = dbutils.widgets.get("expected_case").strip().lower()

TABLES = [
    "bronze_azure_applications",
    "bronze_azure_application_owners",
    "bronze_azure_password_credentials",
    "bronze_identity_lifecycle_seed",
    "bronze_assets_seed",
    "bronze_access_edges_seed",
]
KNOWN_DATASETS = set(TABLES + ["bronze_source_input_audit"])
FLOW_COUNT_KEYS = ("num_output_rows", "output_rows", "num_output_records")
DROPPED_COUNT_KEYS = ("dropped_records", "num_dropped_records", "dropped_rows")
PASSED_COUNT_KEYS = ("passed_records", "passedRows", "passed_records_count")
FAILED_COUNT_KEYS = ("failed_records", "failedRows", "failed_records_count")

EXPECTED_OUTPUT_COUNTS = {
    "valid": {
        "bronze_azure_applications": 1,
        "bronze_azure_application_owners": 1,
        "bronze_azure_password_credentials": 1,
        "bronze_identity_lifecycle_seed": 1,
        "bronze_assets_seed": 1,
        "bronze_access_edges_seed": 1,
    },
    "invalid": {
        "bronze_azure_applications": 11,
        "bronze_azure_application_owners": 3,
        "bronze_azure_password_credentials": 4,
        "bronze_identity_lifecycle_seed": 3,
        "bronze_assets_seed": 2,
        "bronze_access_edges_seed": 5,
    },
}
EXPECTED_INVALID_FAILED_RECORDS = {
    "bronze_azure_applications": {
        "no_forbidden_fields": 7,
        "valid_src_system": 1,
        "valid_src_object": 1,
        "valid_src_file_path": 1,
        "valid_ingestion_ts": 1,
        "valid_checksum": 1,
        "valid_raw_payload": 1,
        "valid_schema_version": 1,
        "ready_app_id": 1,
        "parsed_created_at": 1,
        "preserved_app_id": 2,
        "preserved_display_name": 2,
    },
    "bronze_azure_application_owners": {
        "ready_owner_app_id": 1,
        "ready_owner_user_principal_name": 1,
        "preserved_user_principal_name": 1,
    },
    "bronze_azure_password_credentials": {
        "ready_credential_app_id": 1,
        "ready_credential_key_id": 1,
        "parsed_end_date_time": 1,
        "preserved_status": 1,
    },
    "bronze_identity_lifecycle_seed": {
        "ready_user_principal_name": 1,
        "parsed_termination_date": 1,
        "preserved_employment_status": 1,
    },
    "bronze_assets_seed": {
        "ready_asset_id": 1,
        "preserved_name": 1,
    },
    "bronze_access_edges_seed": {
        "ready_access_principal_id": 1,
        "ready_access_asset_id": 1,
        "ready_access_relationship": 1,
        "parsed_last_used_at": 1,
        "preserved_permission": 1,
    },
}
EXPECTED_INVALID_WARNED_ROWS = {
    "bronze_azure_applications": 11,
    "bronze_azure_application_owners": 3,
    "bronze_azure_password_credentials": 4,
    "bronze_identity_lifecycle_seed": 3,
    "bronze_assets_seed": 2,
    "bronze_access_edges_seed": 5,
}


def _safe_int(value):
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str) and value.strip():
        return int(value)
    return None


def _max_assign(target, key, value):
    parsed = _safe_int(value)
    if parsed is None:
        return
    current = target.get(key)
    if current is None or parsed > current:
        target[key] = parsed


def _get_dataset_metrics(metrics, dataset_name):
    return metrics.setdefault(
        dataset_name,
        {
            "output_rows": None,
            "dropped_records": None,
            "expectations": {},
        },
    )


def _extract_known_dataset(node, inherited_dataset):
    if not isinstance(node, dict):
        return inherited_dataset
    for key in ("dataset", "dataset_name", "flow_name", "name"):
        candidate = node.get(key)
        if isinstance(candidate, str):
            candidate_suffix = candidate.split(".")[-1]
            if candidate_suffix in KNOWN_DATASETS:
                return candidate_suffix
    return inherited_dataset


def _extract_counter(node, keys):
    if not isinstance(node, dict):
        return None
    for key in keys:
        if key in node:
            value = _safe_int(node[key])
            if value is not None:
                return value
    return None


def _record_expectation_metrics(dataset_metrics, expectation):
    if not isinstance(expectation, dict):
        return
    expectation_name = expectation.get("name")
    if not isinstance(expectation_name, str):
        return
    expectation_metrics = dataset_metrics["expectations"].setdefault(
        expectation_name,
        {"passed_records": None, "failed_records": None},
    )
    _max_assign(
        expectation_metrics,
        "passed_records",
        _extract_counter(expectation, PASSED_COUNT_KEYS),
    )
    _max_assign(
        expectation_metrics,
        "failed_records",
        _extract_counter(expectation, FAILED_COUNT_KEYS),
    )


def _walk_details(node, metrics, inherited_dataset=None):
    if isinstance(node, dict):
        dataset_name = _extract_known_dataset(node, inherited_dataset)
        if dataset_name in KNOWN_DATASETS:
            dataset_metrics = _get_dataset_metrics(metrics, dataset_name)
            _max_assign(dataset_metrics, "output_rows", _extract_counter(node, FLOW_COUNT_KEYS))
            _max_assign(
                dataset_metrics,
                "dropped_records",
                _extract_counter(node, DROPPED_COUNT_KEYS),
            )

            data_quality = node.get("data_quality")
            if isinstance(data_quality, dict):
                expectations = data_quality.get("expectations")
                if isinstance(expectations, list):
                    for expectation in expectations:
                        _record_expectation_metrics(dataset_metrics, expectation)
            if "name" in node and (
                any(key in node for key in PASSED_COUNT_KEYS)
                or any(key in node for key in FAILED_COUNT_KEYS)
            ):
                _record_expectation_metrics(dataset_metrics, node)

        for value in node.values():
            _walk_details(value, metrics, dataset_name)
    elif isinstance(node, list):
        for item in node:
            _walk_details(item, metrics, inherited_dataset)


def _load_event_metrics():
    event_log_fqn = f"{CATALOG}.{EVENT_LOG_SCHEMA}.{EVENT_LOG_TABLE}"
    details_field = spark.table(event_log_fqn).schema["details"]
    if details_field.dataType.typeName() == "string":
        details_column = F.col("details").alias("details_json")
    else:
        details_column = F.to_json(F.col("details")).alias("details_json")
    rows = (
        spark.table(event_log_fqn)
        .where(F.col("event_type") == "flow_progress")
        .where(F.col("origin.update_id") == UPDATE_ID)
        .select(details_column)
        .collect()
    )
    if not rows:
        raise AssertionError(
            f"Event log row를 찾지 못했습니다: update_id={UPDATE_ID}, table={event_log_fqn}"
        )

    metrics = {}
    for row in rows:
        payload = json.loads(row["details_json"])
        _walk_details(payload, metrics)
    return metrics, len(rows)


def _load_table_counts():
    counts = {}
    for table_name in TABLES:
        table_fqn = f"{CATALOG}.{SCHEMA}.{table_name}"
        if not spark.catalog.tableExists(table_fqn):
            counts[table_name] = None
            continue
        counts[table_name] = spark.table(table_fqn).count()
    return counts


def _failed_sum(dataset_metrics):
    expectations = dataset_metrics.get("expectations", {})
    return sum(
        expectation.get("failed_records") or 0
        for expectation in expectations.values()
    )


def _failed_expectations(dataset_metrics):
    return {
        name: expectation.get("failed_records") or 0
        for name, expectation in dataset_metrics.get("expectations", {}).items()
        if (expectation.get("failed_records") or 0) > 0
    }


def _validate_valid_case(table_counts, flow_metrics):
    failures = []
    for table_name, expected_count in EXPECTED_OUTPUT_COUNTS["valid"].items():
        actual_count = table_counts.get(table_name)
        if actual_count != expected_count:
            failures.append(
                f"{table_name} output count mismatch: expected={expected_count} actual={actual_count}"
            )

        dataset_metrics = flow_metrics.get(table_name)
        if dataset_metrics is None:
            failures.append(f"{table_name} flow_progress metric가 없습니다.")
            continue
        if dataset_metrics.get("dropped_records") not in (0, None):
            failures.append(
                f"{table_name} dropped_records mismatch: expected=0 actual={dataset_metrics.get('dropped_records')}"
            )
        if _failed_sum(dataset_metrics) != 0:
            failures.append(
                f"{table_name} failed expectation count mismatch: expected=0 actual={_failed_sum(dataset_metrics)}"
            )

    audit_expectation = (
        flow_metrics.get("bronze_source_input_audit", {})
        .get("expectations", {})
        .get("source_not_empty")
    )
    if not audit_expectation:
        failures.append("bronze_source_input_audit.source_not_empty metric가 없습니다.")
    elif (audit_expectation.get("failed_records") or 0) != 0 or (
        audit_expectation.get("passed_records") or 0
    ) != 6:
        failures.append(
            "source_not_empty metric mismatch: "
            f"expected_failed=0 actual_failed={audit_expectation.get('failed_records')} "
            f"expected_passed=6 actual_passed={audit_expectation.get('passed_records')}"
        )
    return failures


def _validate_invalid_case(table_counts, flow_metrics):
    failures = []
    for table_name, expected_count in EXPECTED_OUTPUT_COUNTS["invalid"].items():
        actual_count = table_counts.get(table_name)
        if actual_count != expected_count:
            failures.append(
                f"{table_name} output count mismatch: expected={expected_count} actual={actual_count}"
            )

        dataset_metrics = flow_metrics.get(table_name)
        if dataset_metrics is None:
            failures.append(f"{table_name} flow_progress metric가 없습니다.")
            continue

        if table_name == "bronze_azure_applications":
            actual_drop_failures = (
                dataset_metrics.get("expectations", {})
                .get("no_forbidden_fields", {})
                .get("failed_records")
            )
            if actual_drop_failures != 7:
                failures.append(
                    "bronze_azure_applications forbidden drop mismatch: "
                    f"expected=7 actual={actual_drop_failures}"
                )
        elif dataset_metrics.get("dropped_records") not in (0, None):
            failures.append(
                f"{table_name} dropped_records mismatch: expected=0 actual={dataset_metrics.get('dropped_records')}"
            )

        actual_failed_expectations = _failed_expectations(dataset_metrics)
        expected_failed_expectations = EXPECTED_INVALID_FAILED_RECORDS[table_name]
        if actual_failed_expectations != expected_failed_expectations:
            failures.append(
                f"{table_name} failed expectation mismatch: "
                f"expected={expected_failed_expectations} actual={actual_failed_expectations}"
            )
        if table_counts.get(table_name) != EXPECTED_INVALID_WARNED_ROWS[table_name]:
            failures.append(
                f"{table_name} warned/output row mismatch: "
                f"expected={EXPECTED_INVALID_WARNED_ROWS[table_name]} actual={table_counts.get(table_name)}"
            )

    audit_expectation = (
        flow_metrics.get("bronze_source_input_audit", {})
        .get("expectations", {})
        .get("source_not_empty")
    )
    if not audit_expectation:
        failures.append("bronze_source_input_audit.source_not_empty metric가 없습니다.")
    elif (audit_expectation.get("failed_records") or 0) != 0 or (
        audit_expectation.get("passed_records") or 0
    ) != 6:
        failures.append(
            "source_not_empty metric mismatch: "
            f"expected_failed=0 actual_failed={audit_expectation.get('failed_records')} "
            f"expected_passed=6 actual_passed={audit_expectation.get('passed_records')}"
        )
    return failures


def _validate_empty_source_case(flow_metrics):
    failures = []
    source_not_empty_expectations = {
        dataset_name: dataset_metrics.get("expectations", {}).get("source_not_empty")
        for dataset_name, dataset_metrics in flow_metrics.items()
        if dataset_metrics.get("expectations", {}).get("source_not_empty") is not None
    }
    if not source_not_empty_expectations:
        failures.append("source_not_empty metric가 없습니다.")
        return failures

    audit_expectation = source_not_empty_expectations.get("bronze_source_input_audit")
    if audit_expectation:
        if (audit_expectation.get("failed_records") or 0) != 1 or (
            audit_expectation.get("passed_records") or 0
        ) != 5:
            failures.append(
                "bronze_source_input_audit.source_not_empty metric mismatch: "
                f"expected_failed=1 actual_failed={audit_expectation.get('failed_records')} "
                f"expected_passed=5 actual_passed={audit_expectation.get('passed_records')}"
            )
        return failures

    failed_datasets = [
        dataset_name
        for dataset_name, expectation in source_not_empty_expectations.items()
        if (expectation.get("failed_records") or 0) > 0
    ]
    if not failed_datasets:
        failures.append(
            "source_not_empty propagated failure metric를 찾지 못했습니다."
        )
    return failures


if EXPECTED_CASE not in {"valid", "invalid", "empty-source"}:
    raise AssertionError(f"지원하지 않는 expected_case 입니다: {EXPECTED_CASE}")

if not UPDATE_ID:
    raise AssertionError("update_id parameter가 비어 있습니다.")

table_counts = _load_table_counts()
flow_metrics, flow_progress_event_count = _load_event_metrics()

if EXPECTED_CASE == "valid":
    failures = _validate_valid_case(table_counts, flow_metrics)
elif EXPECTED_CASE == "invalid":
    failures = _validate_invalid_case(table_counts, flow_metrics)
else:
    failures = _validate_empty_source_case(flow_metrics)

result = {
    "catalog": CATALOG,
    "schema": SCHEMA,
    "event_log_schema": EVENT_LOG_SCHEMA,
    "event_log_table": EVENT_LOG_TABLE,
    "expected_case": EXPECTED_CASE,
    "update_id": UPDATE_ID,
    "table_counts": table_counts,
    "flow_progress_event_count": flow_progress_event_count,
    "flow_metrics": flow_metrics,
    "failures": failures,
}

result_json = json.dumps(result, ensure_ascii=False, sort_keys=True)
print(result_json)
if failures:
    raise AssertionError(result_json)
dbutils.notebook.exit(result_json)
