from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from src.data_loader import (
    DatabricksConfig,
    _execute_databricks_statement,
    _load_databricks_config,
    _qualified_name,
)


UI_TO_STORED_STATUS = {
    "Open": "open",
    "In Review": "reviewing",
    "Resolved": "resolved",
}
STORED_TO_UI_STATUS = {value: key for key, value in UI_TO_STORED_STATUS.items()}


@dataclass(frozen=True)
class ActionStateWriteResult:
    persisted: bool
    message: str
    event_id: str | None = None


def get_databricks_action_config() -> DatabricksConfig | None:
    return _load_databricks_config()


def can_write_action_state(config: DatabricksConfig | None, using_mock: bool) -> bool:
    return config is not None and not using_mock


def persist_review_status_change(
    config: DatabricksConfig,
    *,
    risk_case_key: str,
    previous_status: str,
    new_status: str,
) -> ActionStateWriteResult:
    previous_stored = to_stored_status(previous_status)
    new_stored = to_stored_status(new_status)
    if previous_stored == new_stored:
        return ActionStateWriteResult(False, "Review status was unchanged.")

    event_id = f"evt-{uuid4()}"
    action_state_table = _qualified_name(config.catalog, config.app_schema, "risk_action_state")
    action_event_table = _qualified_name(config.catalog, config.app_schema, "risk_action_event")

    _execute_databricks_statement(
        config,
        f"""
        MERGE INTO {action_state_table} AS target
        USING (
          SELECT
            {sql_string(risk_case_key)} AS risk_case_key,
            {sql_string(new_stored)} AS status,
            {sql_string(config.actor_id)} AS updated_by
        ) AS source
        ON target.risk_case_key = source.risk_case_key
        WHEN MATCHED THEN UPDATE SET
          target.status = source.status,
          target.updated_by = source.updated_by,
          target.updated_at = current_timestamp()
        WHEN NOT MATCHED THEN INSERT (
          risk_case_key,
          status,
          updated_by,
          updated_at
        ) VALUES (
          source.risk_case_key,
          source.status,
          source.updated_by,
          current_timestamp()
        )
        """,
    )

    _execute_databricks_statement(
        config,
        f"""
        INSERT INTO {action_event_table} (
          event_id,
          risk_case_key,
          event_type,
          previous_status,
          new_status,
          actor_id,
          actor_name,
          event_at,
          note
        )
        VALUES (
          {sql_string(event_id)},
          {sql_string(risk_case_key)},
          'status_changed',
          {sql_string(previous_stored)},
          {sql_string(new_stored)},
          {sql_string(config.actor_id)},
          {sql_string(config.actor_name)},
          current_timestamp(),
          {sql_string(f"Review status changed from {previous_status} to {new_status} in Streamlit dashboard.")}
        )
        """,
    )

    return ActionStateWriteResult(True, "Review status saved to Databricks.", event_id)


def to_stored_status(status: str) -> str:
    normalized = str(status).strip()
    if normalized in UI_TO_STORED_STATUS:
        return UI_TO_STORED_STATUS[normalized]
    lowered = normalized.lower().replace(" ", "_")
    if lowered in STORED_TO_UI_STATUS:
        return lowered
    raise ValueError(f"Unsupported review status: {status}")


def sql_string(value: object) -> str:
    if value is None:
        return "NULL"
    text = str(value).replace("'", "''")
    return f"'{text}'"
