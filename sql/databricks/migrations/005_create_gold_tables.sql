-- 005_create_gold_tables.sql
-- PoC Risk Card core table.

CREATE SCHEMA IF NOT EXISTS ${catalog}.${schema};

CREATE TABLE IF NOT EXISTS ${catalog}.${schema}.gold_core (
  risk_case_key STRING NOT NULL,
  finding_id STRING NOT NULL,
  drift_type STRING NOT NULL,
  subject_type STRING NOT NULL,
  subject_principal_id STRING NOT NULL,
  subject_source_principal_id STRING NOT NULL,
  subject_display_name STRING NOT NULL,
  owner_principal_id STRING NOT NULL,
  owner_display_name STRING NOT NULL,
  asset_id STRING NOT NULL,
  asset_source_id STRING NOT NULL,
  asset_display_name STRING NOT NULL,
  asset_environment STRING NOT NULL,
  asset_sensitivity STRING NOT NULL,
  severity STRING NOT NULL,
  evidence_summary STRING NOT NULL,
  recommended_action STRING NOT NULL,
  owner_edge_id STRING NOT NULL,
  access_edge_id STRING NOT NULL,
  credential_id STRING NOT NULL,
  detected_at TIMESTAMP NOT NULL,
  run_id STRING NOT NULL,
  CONSTRAINT gold_core_pk PRIMARY KEY (risk_case_key)
)
USING DELTA;
