-- DS Silver 조인 샘플
-- 목적: DS팀이 PoC에서 바로 사용할 수 있는 Silver 중심 조회/조인 예시를 제공한다.
-- 범위: 쿼리 샘플만 포함한다. view 생성, Intermediate/Gold 로직, eval 기반 탐지 입력은 포함하지 않는다.

-- =====================================================================
-- 샘플 1. NHI + credential metadata
-- 목적:
--   - silver_principals에서 NHI principal을 조회할 수 있는지 확인한다.
--   - credential metadata가 Silver 내부 id로 연결되는지 확인한다.
-- 확인 입력:
--   - access_drift.silver.silver_principals
--   - access_drift.silver.silver_credentials
-- 조인 규칙:
--   - p.principal_id = c.bound_principal_id
--   - 여기서는 p.source_principal_id로 조인하지 않는다.
--   - 결과 확인은 p.source_principal_id(app_id) 기준으로 읽되, Silver 내부 조인은 해시 id를 사용한다.
-- 기대 확인 결과:
--   - silver_principals에서 NHI row가 조회된다.
--   - PoC seed 기준으로 joined_credential_rows는 0보다 커야 한다.
--   - unmatched_credential_rows는 0이어야 한다.
--   - principal_id와 bound_principal_id는 null이 아니어야 한다.
-- =====================================================================
SELECT
  p.source_system,
  p.source_principal_id AS app_id,
  p.principal_id,
  p.principal_type,
  p.display_name AS principal_display_name,
  p.status AS principal_status,
  c.source_credential_id AS key_id,
  c.credential_id,
  c.credential_type,
  c.display_name AS credential_display_name,
  c.status AS credential_status,
  c.expires_at,
  c.is_active,
  c.observed_at AS credential_observed_at
FROM access_drift.silver.silver_principals AS p
LEFT JOIN access_drift.silver.silver_credentials AS c
  ON p.principal_id = c.bound_principal_id
WHERE p.principal_kind = 'NHI'
  AND p.principal_type = 'app_registration'
ORDER BY p.source_principal_id, c.source_credential_id;

SELECT
  COUNT(*) AS nhi_principal_rows,
  COUNT(c.credential_id) AS joined_credential_rows,
  SUM(CASE WHEN p.principal_id IS NULL THEN 1 ELSE 0 END) AS null_principal_id_rows,
  SUM(CASE WHEN c.credential_id IS NULL THEN 1 ELSE 0 END) AS unmatched_credential_rows,
  SUM(CASE WHEN c.bound_principal_id IS NULL THEN 1 ELSE 0 END) AS null_bound_principal_id_rows
FROM access_drift.silver.silver_principals AS p
LEFT JOIN access_drift.silver.silver_credentials AS c
  ON p.principal_id = c.bound_principal_id
WHERE p.principal_kind = 'NHI'
  AND p.principal_type = 'app_registration';

-- =====================================================================
-- 샘플 2. NHI + owner context
-- 목적:
--   - owner context가 principal -> principal edge로 표현되는지 확인한다.
--   - relationship, from_type, to_type를 함께 확인하는 예시를 제공한다.
-- 확인 입력:
--   - access_drift.silver.silver_edges
--   - access_drift.silver.silver_principals
-- 조인 규칙:
--   - e.from_id = owner principal_id
--   - e.to_id = NHI principal_id
--   - relationship = 'owns_principal'
--   - from_type = 'principal'
--   - to_type = 'principal'
-- 기대 확인 결과:
--   - owner_principal_id와 nhi_principal_id는 null이 아니어야 한다.
--   - PoC seed 기준으로 owner_edge_rows는 0보다 커야 한다.
--   - unmatched_owner_rows와 unmatched_nhi_rows는 0이어야 한다.
-- =====================================================================
SELECT
  owner.source_principal_id AS owner_upn,
  owner.principal_id AS owner_principal_id,
  owner.status AS owner_status,
  owner.termination_date AS owner_termination_date,
  nhi.source_principal_id AS app_id,
  nhi.principal_id AS nhi_principal_id,
  nhi.display_name AS nhi_display_name,
  e.relationship,
  e.from_type,
  e.to_type,
  e.status AS edge_status,
  e.evidence_source,
  e.observed_at AS edge_observed_at
FROM access_drift.silver.silver_edges AS e
LEFT JOIN access_drift.silver.silver_principals AS owner
  ON e.from_id = owner.principal_id
LEFT JOIN access_drift.silver.silver_principals AS nhi
  ON e.to_id = nhi.principal_id
WHERE e.relationship = 'owns_principal'
  AND e.from_type = 'principal'
  AND e.to_type = 'principal'
  AND nhi.principal_kind = 'NHI'
  AND nhi.principal_type = 'app_registration'
ORDER BY nhi.source_principal_id, owner.source_principal_id;

WITH owner_edges AS (
  SELECT
    edge_id,
    from_id,
    to_id
  FROM access_drift.silver.silver_edges
  WHERE relationship = 'owns_principal'
    AND from_type = 'principal'
    AND to_type = 'principal'
)
SELECT
  COUNT(*) AS owner_edge_rows,
  SUM(CASE WHEN owner.principal_id IS NULL THEN 1 ELSE 0 END) AS unmatched_owner_rows,
  SUM(CASE WHEN nhi.principal_id IS NULL THEN 1 ELSE 0 END) AS unmatched_nhi_rows
FROM owner_edges AS e
LEFT JOIN access_drift.silver.silver_principals AS owner
  ON e.from_id = owner.principal_id
LEFT JOIN access_drift.silver.silver_principals AS nhi
  ON e.to_id = nhi.principal_id
  AND nhi.principal_kind = 'NHI'
  AND nhi.principal_type = 'app_registration';

-- =====================================================================
-- 샘플 3. NHI + asset access edge
-- 목적:
--   - NHI에서 asset으로 가는 access가 principal -> asset으로 표현되는지 확인한다.
--   - relationship와 노드 방향 조건을 함께 써서 asset context를 조인하는 예시를 제공한다.
-- 확인 입력:
--   - access_drift.silver.silver_principals
--   - access_drift.silver.silver_edges
--   - access_drift.silver.silver_assets
-- 조인 규칙:
--   - p.principal_id = e.from_id
--   - a.asset_id = e.to_id
--   - relationship = 'accesses_asset'
--   - from_type = 'principal'
--   - to_type = 'asset'
-- 기대 확인 결과:
--   - 정상 edge라면 asset row가 null asset_id 없이 조인되어야 한다.
--   - PoC seed 기준으로 nhi_asset_edge_rows는 0보다 커야 한다.
--   - unmatched_asset_rows는 0이어야 한다.
--   - 결과에서 production/high sensitivity asset이 어떻게 보이는지 확인한다.
-- =====================================================================
SELECT
  p.source_principal_id AS app_id,
  p.principal_id,
  p.display_name AS nhi_display_name,
  e.relationship,
  e.permission,
  e.status AS edge_status,
  a.source_asset_id,
  a.asset_id,
  a.display_name AS asset_display_name,
  a.environment,
  a.sensitivity,
  a.observed_at AS asset_observed_at
FROM access_drift.silver.silver_principals AS p
LEFT JOIN access_drift.silver.silver_edges AS e
  ON p.principal_id = e.from_id
LEFT JOIN access_drift.silver.silver_assets AS a
  ON e.to_id = a.asset_id
WHERE p.principal_kind = 'NHI'
  AND p.principal_type = 'app_registration'
  AND e.relationship = 'accesses_asset'
  AND e.from_type = 'principal'
  AND e.to_type = 'asset'
ORDER BY p.source_principal_id, a.source_asset_id;

WITH nhi_asset_edges AS (
  SELECT
    edge_id,
    from_id,
    to_id
  FROM access_drift.silver.silver_edges
  WHERE relationship = 'accesses_asset'
    AND from_type = 'principal'
    AND to_type = 'asset'
)
SELECT
  COUNT(*) AS nhi_asset_edge_rows,
  SUM(CASE WHEN p.principal_id IS NULL THEN 1 ELSE 0 END) AS unmatched_principal_rows,
  SUM(CASE WHEN a.asset_id IS NULL THEN 1 ELSE 0 END) AS unmatched_asset_rows,
  SUM(CASE WHEN a.source_asset_id IS NULL THEN 1 ELSE 0 END) AS null_source_asset_id_rows
FROM nhi_asset_edges AS e
LEFT JOIN access_drift.silver.silver_principals AS p
  ON p.principal_id = e.from_id
  AND p.principal_kind = 'NHI'
  AND p.principal_type = 'app_registration'
LEFT JOIN access_drift.silver.silver_assets AS a
  ON e.to_id = a.asset_id
;

-- =====================================================================
-- 샘플 4. Eval ground truth vs Silver source id mapping
-- 목적:
--   - eval의 subject_id, asset_id가 Silver source id와 매칭되는지 확인한다.
--   - eval이 탐지 입력이 아니라 검증 전용임을 분리해서 보여준다.
-- 확인 입력:
--   - access_drift.eval.ground_truth_case
--   - access_drift.silver.silver_principals
--   - access_drift.silver.silver_assets
-- 조인 규칙:
--   - gt.subject_id = p.source_principal_id
--   - gt.asset_id = a.source_asset_id
--   - gt.subject_id를 p.principal_id와 직접 조인하지 않는다.
-- 기대 확인 결과:
--   - matched_principal_rows와 matched_asset_rows는 ground_truth_rows와 같아야 한다.
--   - unmatched_principal_rows와 unmatched_asset_rows는 0이어야 한다.
--   - subject_type는 eval 메타데이터로만 남아야 하며 Silver 탐지 로직을 구동하면 안 된다.
-- =====================================================================
SELECT
  gt.case_id,
  gt.subject_type,
  gt.subject_id AS eval_subject_id,
  p.principal_id AS silver_principal_id,
  p.source_principal_id AS silver_source_principal_id,
  gt.asset_id AS eval_asset_id,
  a.asset_id AS silver_asset_id,
  a.source_asset_id AS silver_source_asset_id,
  gt.drift_type,
  gt.is_planted_risk,
  gt.is_distractor,
  gt.expected_severity,
  gt.label_reason
FROM access_drift.eval.ground_truth_case AS gt
LEFT JOIN access_drift.silver.silver_principals AS p
  ON gt.subject_id = p.source_principal_id
  AND p.principal_kind = 'NHI'
  AND p.principal_type = 'app_registration'
LEFT JOIN access_drift.silver.silver_assets AS a
  ON gt.asset_id = a.source_asset_id
WHERE gt.subject_type = 'nhi'
ORDER BY gt.case_id;

SELECT
  COUNT(*) AS ground_truth_rows,
  SUM(CASE WHEN p.principal_id IS NOT NULL THEN 1 ELSE 0 END) AS matched_principal_rows,
  SUM(CASE WHEN a.asset_id IS NOT NULL THEN 1 ELSE 0 END) AS matched_asset_rows,
  SUM(CASE WHEN p.principal_id IS NULL THEN 1 ELSE 0 END) AS unmatched_principal_rows,
  SUM(CASE WHEN a.asset_id IS NULL THEN 1 ELSE 0 END) AS unmatched_asset_rows
FROM access_drift.eval.ground_truth_case AS gt
LEFT JOIN access_drift.silver.silver_principals AS p
  ON gt.subject_id = p.source_principal_id
  AND p.principal_kind = 'NHI'
  AND p.principal_type = 'app_registration'
LEFT JOIN access_drift.silver.silver_assets AS a
  ON gt.asset_id = a.source_asset_id
WHERE gt.subject_type = 'nhi';
