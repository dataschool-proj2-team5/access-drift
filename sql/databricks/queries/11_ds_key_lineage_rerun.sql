-- =============================================================================
-- [#11] DS PoC — 키 유지 / 근거 추적 / 재실행 중복 방지 검증 (V3·V4·V6)
-- 대상: feat/10-gold-core-pipeline 구현 (moses415-cell)
--   intermediate.nhi_residual_access_findings , gold.gold_core
-- 입력: DE Silver (silver_principals/credentials/assets/edges) + Bronze(_raw_payload)
-- 실행: 05_intermediate.py / 06_gold.py 적재 후. catalog = access_drift.
-- =============================================================================

-- ───────────────────────────────────────────────────────────────────────────
-- V3) 키 유지: gold → finding 연결이 끊기지 않는지 (BROKEN 0건 기대)
-- ───────────────────────────────────────────────────────────────────────────
SELECT
  g.risk_case_key,
  g.finding_id,
  f.finding_id AS finding_match,
  CASE
    WHEN f.finding_id IS NULL THEN 'BROKEN_finding'
    WHEN g.risk_case_key <> f.risk_case_key THEN 'KEY_MISMATCH'
    ELSE 'OK'
  END AS key_chain
FROM access_drift.gold.gold_core g
LEFT JOIN access_drift.intermediate.nhi_residual_access_findings f
  ON g.finding_id = f.finding_id;
-- PASS: 전 행 key_chain='OK'

-- V3b) 평가 조인 키 일관성: gold ↔ finding 의 (subject_source_id, asset_source_id, drift_type)
SELECT
  g.risk_case_key,
  g.subject_source_principal_id, f.subject_source_principal_id AS f_subject,
  g.asset_source_id,             f.asset_source_id             AS f_asset,
  g.drift_type,                  f.drift_type                  AS f_drift,
  CASE WHEN g.subject_source_principal_id = f.subject_source_principal_id
        AND g.asset_source_id = f.asset_source_id
        AND g.drift_type = f.drift_type
       THEN 'OK' ELSE 'MISMATCH' END AS key_consistency
FROM access_drift.gold.gold_core g
JOIN access_drift.intermediate.nhi_residual_access_findings f
  ON g.finding_id = f.finding_id;
-- PASS: 전 행 'OK'

-- ───────────────────────────────────────────────────────────────────────────
-- V4) 근거 추적: gold 의 edge id 2개가 silver_edges 에 실재할 뿐 아니라
--     relationship/방향(from→to)/status 가 gold 의 owner·NHI·asset 노드와
--     실제로 일치하는지까지 검증 → VALID 가 아닌 행 0건 기대
--   owner_edge : owns_principal, owner_principal_id → subject_principal_id, active
--   access_edge: accesses_asset, subject_principal_id → asset_id,          active
-- ───────────────────────────────────────────────────────────────────────────
WITH gold_edges AS (
  SELECT risk_case_key, 'owner(owns_principal)' AS edge_role,
         owner_edge_id AS edge_id, 'owns_principal' AS exp_relationship,
         owner_principal_id AS exp_from_id, subject_principal_id AS exp_to_id
  FROM access_drift.gold.gold_core
  UNION ALL
  SELECT risk_case_key, 'access(accesses_asset)',
         access_edge_id, 'accesses_asset',
         subject_principal_id AS exp_from_id, asset_id AS exp_to_id
  FROM access_drift.gold.gold_core
)
SELECT
  ge.risk_case_key, ge.edge_role, ge.edge_id,
  e.relationship, e.from_id, e.to_id, e.status,
  CASE
    WHEN e.edge_id IS NULL                       THEN 'ORPHAN'           -- 엣지 자체가 없음
    WHEN e.relationship <> ge.exp_relationship   THEN 'WRONG_RELATION'   -- 관계 종류 불일치
    WHEN e.from_id <> ge.exp_from_id
      OR e.to_id   <> ge.exp_to_id               THEN 'WRONG_ENDPOINTS'  -- 잇는 노드 불일치
    WHEN coalesce(lower(e.status),'') <> 'active' THEN 'INACTIVE_EDGE'    -- 비활성 경로
    ELSE 'VALID'
  END AS lineage
FROM gold_edges ge
LEFT JOIN access_drift.silver.silver_edges e ON e.edge_id = ge.edge_id;
-- PASS: 전 행 lineage='VALID' (존재 + 관계 + 방향(from→to) + status=active 모두 일치)

-- V4b) gold → Silver 노드 → Bronze 원천 역추적 (source id 기준)
--   subject_source_principal_id = silver_principals.source_principal_id = bronze app_id
--   (⚠️ CONFIRM: silver source_principal_id 가 bronze_azure_applications.app_id 와 동일 키인지)
SELECT
  g.risk_case_key,
  g.subject_source_principal_id,
  p.principal_id              AS silver_principal_traced,
  a.asset_id                  AS silver_asset_traced,
  b.app_id                    AS bronze_app_traced,
  CASE WHEN p.principal_id IS NULL OR a.asset_id IS NULL THEN 'SILVER_BROKEN'
       WHEN b.app_id IS NULL THEN 'BRONZE_UNTRACED(ok-for-PoC)'
       ELSE 'TRACED_TO_BRONZE' END AS lineage_depth
FROM access_drift.gold.gold_core g
LEFT JOIN access_drift.silver.silver_principals p ON g.subject_source_principal_id = p.source_principal_id
LEFT JOIN access_drift.silver.silver_assets     a ON g.asset_source_id            = a.source_asset_id
LEFT JOIN access_drift.bronze.bronze_azure_applications b ON g.subject_source_principal_id = b.app_id;
-- PASS(PoC): 최소 Silver 노드까지 역추적. Bronze까지 닿으면 더 좋음.

-- ───────────────────────────────────────────────────────────────────────────
-- V6) 재실행 중복 방지: 파이프라인 2회 실행 후 rows=distinct_key 기대(중복 0),
--     그리고 1회차와 2회차 rows 가 동일해야 함(overwrite/결정적 key → 누적 없음)
-- ───────────────────────────────────────────────────────────────────────────
SELECT 'gold_core' AS tbl,
       count(*) AS rows, count(DISTINCT risk_case_key) AS distinct_key,
       CASE WHEN count(*) = count(DISTINCT risk_case_key) THEN 'PASS' ELSE 'DUP' END AS no_dup_verdict
FROM access_drift.gold.gold_core
UNION ALL
SELECT 'finding',
       count(*), count(DISTINCT risk_case_key),
       CASE WHEN count(*) = count(DISTINCT risk_case_key) THEN 'PASS' ELSE 'DUP' END
FROM access_drift.intermediate.nhi_residual_access_findings;

-- V6 판정 절차 (쿼리만으로 "전후 동일"을 자동 판정할 수 없음 — 두 run 사이 상태가 필요):
--   1) 파이프라인 1회 실행 → 위 쿼리 실행 → rows 기록
--   2) 파이프라인 재실행      → 위 쿼리 실행 → rows 기록
--   3) 1차 rows == 2차 rows AND no_dup_verdict='PASS' 이면 V6 PASS
--
-- ▼ PR 본문에 아래 형식으로 실측값을 채워 기록 (#11 완료기준: 결과 표로 정리) ▼
-- | run   | gold_core rows | finding rows | no_dup | 비고                 |
-- |-------|----------------|--------------|--------|----------------------|
-- | 1st   | <fill>         | <fill>       | PASS   |                      |
-- | 2nd   | <fill>         | <fill>       | PASS   | 재실행 후 누적 없음  |
-- | verdict | PASS — no duplicate accumulation                          |
