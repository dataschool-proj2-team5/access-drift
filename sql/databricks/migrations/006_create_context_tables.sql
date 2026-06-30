-- 006_create_context_tables.sql
-- Risk Card context/reference tables.

CREATE SCHEMA IF NOT EXISTS ${catalog}.${schema};

CREATE TABLE IF NOT EXISTS ${catalog}.${schema}.asset_context (
  source_asset_id STRING NOT NULL,
  data_scope_label STRING NOT NULL,
  sensitive_data_examples ARRAY<STRING> NOT NULL,
  sensitivity_reason STRING NOT NULL,
  CONSTRAINT asset_context_pk PRIMARY KEY (source_asset_id)
)
USING DELTA;

CREATE TABLE IF NOT EXISTS ${catalog}.${schema}.assignment_routing (
  subject_type STRING NOT NULL,
  subject_id STRING NOT NULL,
  asset_id STRING NOT NULL,
  drift_type STRING NOT NULL,
  assignee_name STRING NOT NULL,
  assignee_team STRING NOT NULL,
  routing_reason STRING,
  CONSTRAINT assignment_routing_pk PRIMARY KEY (subject_type, subject_id, asset_id, drift_type)
)
USING DELTA;
