-- 008_create_rag_tables.sql
-- RAG / AI Runbook evidence tables.

CREATE SCHEMA IF NOT EXISTS ${catalog}.${schema};

CREATE TABLE IF NOT EXISTS ${catalog}.${schema}.risk_case_documents (
  risk_case_key STRING NOT NULL,
  finding_id STRING NOT NULL,
  document_title STRING NOT NULL,
  document_text STRING NOT NULL,
  source_table_refs ARRAY<STRING> NOT NULL,
  evidence_keys MAP<STRING, STRING> NOT NULL,
  generated_at TIMESTAMP NOT NULL,
  run_id STRING NOT NULL,
  CONSTRAINT risk_case_documents_pk PRIMARY KEY (risk_case_key)
)
USING DELTA;

CREATE TABLE IF NOT EXISTS ${catalog}.${schema}.knowledge_chunks (
  chunk_id STRING NOT NULL,
  risk_case_key STRING NOT NULL,
  chunk_text STRING NOT NULL,
  chunk_hash STRING NOT NULL,
  chunk_order INT NOT NULL,
  source_title STRING NOT NULL,
  source_uri STRING NOT NULL,
  source_table_refs ARRAY<STRING> NOT NULL,
  evidence_keys MAP<STRING, STRING> NOT NULL,
  generated_at TIMESTAMP NOT NULL,
  CONSTRAINT knowledge_chunks_pk PRIMARY KEY (chunk_id)
)
USING DELTA;
