-- 009_create_rag_chain_tables.sql
-- DS RAG chain output tables.
-- rag.doc_chunks(008)는 검색용 corpus, 아래 두 테이블은 RAG 체인 결과/평가 결과다.
-- Risk Card 현재값(gold_core)에서 질의를 만들고, 근거 기반 권장 조치와 citation을 여기 적재한다.

CREATE SCHEMA IF NOT EXISTS ${catalog}.${schema};

-- RAG 체인이 finding 1건마다 생성한 근거 기반 권장 조치.
-- answer_source 로 rag 생성인지 deterministic fallback인지 구분한다.
CREATE TABLE IF NOT EXISTS ${catalog}.${schema}.recommended_action (
  risk_case_key STRING NOT NULL,
  finding_id STRING NOT NULL,
  drift_type STRING NOT NULL,
  query_text STRING NOT NULL,
  answer_text STRING NOT NULL,
  answer_source STRING NOT NULL,          -- 'rag' | 'deterministic_fallback'
  citations STRING NOT NULL,              -- JSON array of chunk_id
  citation_titles STRING NOT NULL,        -- JSON array of source_title
  retrieved_chunk_ids STRING NOT NULL,    -- JSON array of chunk_id (검색된 전체)
  num_retrieved INT NOT NULL,
  llm_endpoint STRING NOT NULL,           -- 생성에 사용한 endpoint (fallback이면 'none')
  generated_at TIMESTAMP NOT NULL,
  run_id STRING NOT NULL,
  CONSTRAINT recommended_action_pk PRIMARY KEY (risk_case_key)
)
USING DELTA;

-- RAG 평가 결과. eval set 케이스별 retrieval/citation/groundedness 지표를 적재한다.
-- 탐지 파이프라인은 이 테이블을 읽지 않는다(eval 격리 원칙).
CREATE TABLE IF NOT EXISTS ${catalog}.${schema}.eval_results (
  eval_case_id STRING NOT NULL,
  drift_type STRING NOT NULL,
  question STRING NOT NULL,
  retrieved_chunk_ids STRING NOT NULL,    -- JSON array
  expected_doc_ids STRING NOT NULL,       -- JSON array
  retrieval_hit BOOLEAN NOT NULL,         -- expected_doc_id 중 하나라도 top-k에 포함
  has_citation BOOLEAN NOT NULL,          -- 응답에 citation이 붙었는지
  answer_source STRING NOT NULL,          -- 'rag' | 'deterministic_fallback'
  groundedness DOUBLE,                    -- Agent Evaluation judge 점수(없으면 null)
  correctness DOUBLE,                     -- Agent Evaluation judge 점수(없으면 null)
  answer_text STRING NOT NULL,
  llm_endpoint STRING NOT NULL,
  evaluated_at TIMESTAMP NOT NULL,
  run_id STRING NOT NULL,
  CONSTRAINT rag_eval_results_pk PRIMARY KEY (eval_case_id)
)
USING DELTA;
