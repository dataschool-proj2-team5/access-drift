-- 007_create_app_tables.sql
-- App-owned tables for user interaction state.
-- risk_action_state and risk_action_event are not pipeline seed or Gold overwrite targets.

CREATE SCHEMA IF NOT EXISTS ${catalog}.${schema};

CREATE TABLE IF NOT EXISTS ${catalog}.${schema}.risk_action_state (
  risk_case_key STRING NOT NULL,
  status STRING NOT NULL,
  reviewer_name STRING,
  reviewer_team STRING,
  updated_by STRING,
  updated_at TIMESTAMP NOT NULL,
  note STRING,
  CONSTRAINT risk_action_state_pk PRIMARY KEY (risk_case_key)
)
USING DELTA;

CREATE TABLE IF NOT EXISTS ${catalog}.${schema}.risk_action_event (
  event_id STRING NOT NULL,
  risk_case_key STRING NOT NULL,
  event_type STRING NOT NULL,
  previous_status STRING,
  new_status STRING,
  actor_id STRING,
  actor_name STRING,
  event_at TIMESTAMP NOT NULL,
  note STRING,
  CONSTRAINT risk_action_event_pk PRIMARY KEY (event_id)
)
USING DELTA;
