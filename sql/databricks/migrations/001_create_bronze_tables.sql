-- 001_create_bronze_tables.sql
-- Bronze source tables for source-shaped landing data.
-- These tables preserve source records before Silver normalization.

CREATE SCHEMA IF NOT EXISTS ${catalog}.${schema};

CREATE TABLE IF NOT EXISTS ${catalog}.${schema}.bronze_azure_applications (
  _src_system STRING NOT NULL,
  _src_object STRING NOT NULL,
  _src_file_path STRING,
  _ingestion_ts TIMESTAMP NOT NULL,
  _run_id STRING,
  _batch_id STRING,
  _checksum STRING,
  _raw_payload STRING NOT NULL,
  _schema_version STRING NOT NULL,
  app_id STRING,
  display_name STRING,
  created_at TIMESTAMP
)
USING DELTA;

CREATE TABLE IF NOT EXISTS ${catalog}.${schema}.bronze_azure_application_owners (
  _src_system STRING NOT NULL,
  _src_object STRING NOT NULL,
  _src_file_path STRING,
  _ingestion_ts TIMESTAMP NOT NULL,
  _run_id STRING,
  _batch_id STRING,
  _checksum STRING,
  _raw_payload STRING NOT NULL,
  _schema_version STRING NOT NULL,
  app_id STRING,
  user_principal_name STRING
)
USING DELTA;

CREATE TABLE IF NOT EXISTS ${catalog}.${schema}.bronze_azure_password_credentials (
  _src_system STRING NOT NULL,
  _src_object STRING NOT NULL,
  _src_file_path STRING,
  _ingestion_ts TIMESTAMP NOT NULL,
  _run_id STRING,
  _batch_id STRING,
  _checksum STRING,
  _raw_payload STRING NOT NULL,
  _schema_version STRING NOT NULL,
  app_id STRING,
  key_id STRING,
  display_name STRING,
  end_date_time TIMESTAMP,
  status STRING
)
USING DELTA;

CREATE TABLE IF NOT EXISTS ${catalog}.${schema}.bronze_identity_lifecycle_seed (
  _src_system STRING NOT NULL,
  _src_object STRING NOT NULL,
  _src_file_path STRING,
  _ingestion_ts TIMESTAMP NOT NULL,
  _run_id STRING,
  _batch_id STRING,
  _checksum STRING,
  _raw_payload STRING NOT NULL,
  _schema_version STRING NOT NULL,
  user_principal_name STRING,
  display_name STRING,
  employment_status STRING,
  termination_date DATE
)
USING DELTA;

CREATE TABLE IF NOT EXISTS ${catalog}.${schema}.bronze_assets_seed (
  _src_system STRING NOT NULL,
  _src_object STRING NOT NULL,
  _src_file_path STRING,
  _ingestion_ts TIMESTAMP NOT NULL,
  _run_id STRING,
  _batch_id STRING,
  _checksum STRING,
  _raw_payload STRING NOT NULL,
  _schema_version STRING NOT NULL,
  asset_id STRING,
  name STRING,
  environment STRING,
  sensitivity STRING
)
USING DELTA;

CREATE TABLE IF NOT EXISTS ${catalog}.${schema}.bronze_access_edges_seed (
  _src_system STRING NOT NULL,
  _src_object STRING NOT NULL,
  _src_file_path STRING,
  _ingestion_ts TIMESTAMP NOT NULL,
  _run_id STRING,
  _batch_id STRING,
  _checksum STRING,
  _raw_payload STRING NOT NULL,
  _schema_version STRING NOT NULL,
  principal_id STRING,
  asset_id STRING,
  relationship STRING,
  permission STRING,
  status STRING,
  last_used_at TIMESTAMP
)
USING DELTA;
