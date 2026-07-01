-- 008_create_rag_tables.sql
-- RAG / AI Runbook source document chunk table.

CREATE SCHEMA IF NOT EXISTS ${catalog}.${schema};

CREATE TABLE IF NOT EXISTS ${catalog}.${schema}.doc_chunks (
  chunk_id STRING NOT NULL,
  doc_id STRING NOT NULL,
  provider STRING NOT NULL,
  service STRING NOT NULL,
  doc_type STRING NOT NULL,
  drift_type STRING NOT NULL,
  action_type STRING NOT NULL,
  chunk_text STRING NOT NULL,
  chunk_hash STRING NOT NULL,
  chunk_order INT NOT NULL,
  source_title STRING NOT NULL,
  source_uri STRING NOT NULL,
  effective_date DATE NOT NULL,
  generated_at TIMESTAMP NOT NULL,
  run_id STRING NOT NULL,
  CONSTRAINT doc_chunks_pk PRIMARY KEY (chunk_id)
)
USING DELTA;

ALTER TABLE ${catalog}.${schema}.doc_chunks
SET TBLPROPERTIES (delta.enableChangeDataFeed = true);
