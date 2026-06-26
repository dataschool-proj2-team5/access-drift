-- 004_create_intermediate_tables.sql
-- PoC NHI residual access finding table.

CREATE SCHEMA IF NOT EXISTS ${catalog}.${schema};

CREATE TABLE IF NOT EXISTS ${catalog}.${schema}.nhi_residual_access_findings (
  finding_id STRING NOT NULL,
  risk_case_key STRING NOT NULL,
  drift_type STRING NOT NULL,
  subject_type STRING NOT NULL,
  owner_principal_id STRING NOT NULL,
  owner_source_principal_id STRING NOT NULL,
  subject_principal_id STRING NOT NULL,
  subject_source_principal_id STRING NOT NULL,
  credential_id STRING NOT NULL,
  asset_id STRING NOT NULL,
  asset_source_id STRING NOT NULL,
  owner_edge_id STRING NOT NULL,
  access_edge_id STRING NOT NULL,
  permission STRING,
  owner_status STRING NOT NULL,
  credential_is_active BOOLEAN NOT NULL,
  asset_environment STRING NOT NULL,
  asset_sensitivity STRING NOT NULL,
  detected_at TIMESTAMP NOT NULL,
  run_id STRING NOT NULL,
  CONSTRAINT nhi_residual_access_findings_pk PRIMARY KEY (finding_id)
)
USING DELTA;
