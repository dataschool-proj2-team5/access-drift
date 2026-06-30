-- 007_create_app_tables.sql
-- App-owned tables for user interaction state.
-- risk_action_state is not a pipeline seed or Gold overwrite target.

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
