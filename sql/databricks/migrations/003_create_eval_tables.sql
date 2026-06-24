-- 003_create_eval_tables.sql
-- Eval tables for PoC ground truth and regression checks.
-- Detection jobs must not use these tables as input.

CREATE SCHEMA IF NOT EXISTS ${catalog}.${schema};

CREATE TABLE IF NOT EXISTS ${catalog}.${schema}.ground_truth_case (
  case_id STRING NOT NULL,
  scenario_id STRING,
  scenario_family STRING,
  subject_type STRING NOT NULL,
  subject_id STRING NOT NULL,
  asset_id STRING NOT NULL,
  drift_type STRING NOT NULL,
  is_planted_risk BOOLEAN NOT NULL,
  is_distractor BOOLEAN NOT NULL,
  pattern STRING,
  expected_severity STRING,
  label_reason STRING,
  created_at TIMESTAMP NOT NULL,
  CONSTRAINT ground_truth_case_pk PRIMARY KEY (case_id)
)
USING DELTA;
