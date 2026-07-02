-- 002_create_silver_tables.sql
-- Silver common model tables.

CREATE SCHEMA IF NOT EXISTS ${catalog}.${schema};

CREATE TABLE IF NOT EXISTS ${catalog}.${schema}.silver_principals (
  principal_id STRING NOT NULL,
  source_system STRING NOT NULL,
  source_principal_id STRING NOT NULL,
  principal_kind STRING NOT NULL,
  principal_type STRING NOT NULL,
  display_name STRING,
  email STRING,
  status STRING NOT NULL,
  termination_date DATE,
  observed_at TIMESTAMP NOT NULL,
  CONSTRAINT silver_principals_pk PRIMARY KEY (principal_id)
)
USING DELTA;

CREATE TABLE IF NOT EXISTS ${catalog}.${schema}.silver_credentials (
  credential_id STRING NOT NULL,
  source_system STRING NOT NULL,
  source_credential_id STRING NOT NULL,
  bound_principal_id STRING NOT NULL,
  credential_type STRING NOT NULL,
  display_name STRING,
  status STRING NOT NULL,
  expires_at TIMESTAMP,
  is_active BOOLEAN NOT NULL,
  observed_at TIMESTAMP NOT NULL,
  CONSTRAINT silver_credentials_pk PRIMARY KEY (credential_id)
)
USING DELTA;

CREATE TABLE IF NOT EXISTS ${catalog}.${schema}.silver_assets (
  asset_id STRING NOT NULL,
  source_system STRING NOT NULL,
  source_asset_id STRING NOT NULL,
  asset_type STRING NOT NULL,
  display_name STRING,
  environment STRING NOT NULL,
  sensitivity STRING NOT NULL,
  observed_at TIMESTAMP NOT NULL,
  CONSTRAINT silver_assets_pk PRIMARY KEY (asset_id)
)
USING DELTA;

CREATE TABLE IF NOT EXISTS ${catalog}.${schema}.silver_edges (
  edge_id STRING NOT NULL,
  source_system STRING NOT NULL,
  from_id STRING NOT NULL,
  from_type STRING NOT NULL,
  to_id STRING NOT NULL,
  to_type STRING NOT NULL,
  relationship STRING NOT NULL,
  permission STRING,
  status STRING NOT NULL,
  last_used_at TIMESTAMP,
  evidence_source STRING,
  observed_at TIMESTAMP NOT NULL,
  CONSTRAINT silver_edges_pk PRIMARY KEY (edge_id)
)
USING DELTA;
