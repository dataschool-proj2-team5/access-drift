-- =============================================================================
-- [#12] DS PoC — Secret 미저장 확인 + 최소 Eval 검증 (V7·V8)
-- 대상: feat/10-gold-core-pipeline 구현
--   intermediate.nhi_residual_access_findings , gold.gold_core , eval.ground_truth_case
-- 원칙: secret value 원문 미저장 / eval 은 탐지 입력 아니라 "검증 입력"으로만 사용.
-- eval 매칭(가이드 §12): gt.subject_id = source_principal_id, gt.asset_id = source_asset_id
-- =============================================================================

-- ───────────────────────────────────────────────────────────────────────────
-- V7) Secret value 미저장 — 결과 스키마에 secret 원문 컬럼이 없는지 (0행 기대)
-- ───────────────────────────────────────────────────────────────────────────
SELECT table_schema, table_name, column_name
FROM access_drift.information_schema.columns
WHERE table_schema IN ('intermediate','gold')
  AND (lower(column_name) LIKE '%secret%value%'
       OR lower(column_name) LIKE '%password%'
       OR lower(column_name) IN ('secret','token','private_key','client_secret','key_value'));
-- PASS: 0행 (credential 은 메타데이터만 — credential_id/is_active 등, value 컬럼 없음)

-- V7b) gold 텍스트 필드에 secret 유사값이 섞이지 않았는지 (0행 기대)
SELECT risk_case_key, evidence_summary, recommended_action
FROM access_drift.gold.gold_core
WHERE evidence_summary   RLIKE '(?i)(secret|password|BEGIN PRIVATE KEY|client_secret=)'
   OR recommended_action RLIKE '(?i)(secret|password|BEGIN PRIVATE KEY|client_secret=)';
-- PASS: 0행

-- ───────────────────────────────────────────────────────────────────────────
-- V8) 최소 eval 검증 — 탐지 결과(finding) ↔ 정답지(ground_truth_case) 비교
--   finding 테이블에는 "탐지된(=flagged) 행만" 존재 → detected = finding 존재 여부.
--   eval 은 여기서 검증으로만 조인 (탐지 로직 입력 아님).
-- ───────────────────────────────────────────────────────────────────────────
WITH gt AS (
  SELECT case_id, subject_id, asset_id, drift_type, is_planted_risk, is_distractor, expected_severity
  FROM access_drift.eval.ground_truth_case
  WHERE drift_type = 'nhi_residual_access'
),
det AS (
  SELECT DISTINCT subject_source_principal_id AS subject_id, asset_source_id AS asset_id, drift_type
  FROM access_drift.intermediate.nhi_residual_access_findings
)
SELECT
  gt.case_id, gt.subject_id, gt.asset_id, gt.expected_severity,
  gt.is_planted_risk AS truth, gt.is_distractor,
  (det.subject_id IS NOT NULL) AS detected,
  CASE
    WHEN gt.is_planted_risk = true  AND det.subject_id IS NOT NULL THEN 'TP'
    WHEN gt.is_planted_risk = true  AND det.subject_id IS NULL     THEN 'FN'
    WHEN gt.is_planted_risk = false AND det.subject_id IS NOT NULL THEN 'FP'
    ELSE 'TN'
  END AS eval_result
FROM gt
LEFT JOIN det
  ON gt.subject_id = det.subject_id
 AND gt.asset_id   = det.asset_id
 AND gt.drift_type = det.drift_type
ORDER BY gt.case_id;
-- 현재 seed 기대: eval-nhi-001(HIGH)=TP, eval-nhi-002(MEDIUM)=TP, eval-nhi-003(active owner)=TN
-- PASS(PoC 최소): planted positive 전부 TP, FP 0건.

-- V8b) 집계 요약 (PASS 판정용)
WITH gt AS (
  SELECT subject_id, asset_id, drift_type, is_planted_risk
  FROM access_drift.eval.ground_truth_case WHERE drift_type = 'nhi_residual_access'
),
det AS (
  SELECT DISTINCT subject_source_principal_id AS subject_id, asset_source_id AS asset_id, drift_type
  FROM access_drift.intermediate.nhi_residual_access_findings
),
scored AS (
  SELECT gt.is_planted_risk, (det.subject_id IS NOT NULL) AS detected
  FROM gt LEFT JOIN det
    ON gt.subject_id=det.subject_id AND gt.asset_id=det.asset_id AND gt.drift_type=det.drift_type
)
SELECT
  sum(CASE WHEN is_planted_risk AND detected THEN 1 ELSE 0 END)        AS tp,
  sum(CASE WHEN is_planted_risk AND NOT detected THEN 1 ELSE 0 END)    AS fn,
  sum(CASE WHEN NOT is_planted_risk AND detected THEN 1 ELSE 0 END)    AS fp,
  sum(CASE WHEN NOT is_planted_risk AND NOT detected THEN 1 ELSE 0 END) AS tn,
  CASE WHEN sum(CASE WHEN is_planted_risk AND NOT detected THEN 1 ELSE 0 END) = 0
        AND sum(CASE WHEN NOT is_planted_risk AND detected THEN 1 ELSE 0 END) = 0
       THEN 'PASS' ELSE 'FAIL' END AS poc_eval_verdict
FROM scored;

-- ───────────────────────────────────────────────────────────────────────────
-- ▼ PR 본문에 아래 형식으로 실측값을 채워 기록 (#12 완료기준: 검증 조건·방법 기록) ▼
--
-- [V7] Secret 미저장
-- | 점검            | 결과(행수) | verdict |
-- |-----------------|-----------|---------|
-- | result 스키마 secret 컬럼 | <fill> 0  | PASS    |
-- | gold 텍스트 secret 패턴   | <fill> 0  | PASS    |
--
-- [V8] 최소 eval (eval 은 검증 입력으로만 사용 — 탐지 입력 아님)
-- | case_id      | expected | detected | result |
-- |--------------|----------|----------|--------|
-- | eval-nhi-001 | planted  | yes      | TP     |
-- | eval-nhi-002 | planted  | yes      | TP     |
-- | eval-nhi-003 | normal   | no       | TN     |
-- | summary | tp=<fill> fn=0 fp=0 tn=<fill> → poc_eval_verdict = PASS |
