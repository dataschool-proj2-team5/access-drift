-- Databricks SQL ops dashboard query 04
-- Purpose: verify planted positive eval cases still match Silver and Gold.
-- Target catalog: access_drift_dev

WITH positive_eval AS (
  SELECT
    case_id,
    subject_type,
    subject_id,
    asset_id,
    drift_type
  FROM access_drift_dev.eval.ground_truth_case
  WHERE is_planted_risk = true
),
silver_match AS (
  SELECT
    e.case_id,
    MAX(CASE WHEN p.principal_id IS NOT NULL THEN 1 ELSE 0 END) AS has_principal_match,
    MAX(CASE WHEN a.asset_id IS NOT NULL THEN 1 ELSE 0 END) AS has_asset_match
  FROM positive_eval e
  LEFT JOIN access_drift_dev.silver.silver_principals p
    ON e.subject_id = p.source_principal_id
   AND (
     (e.subject_type = 'nhi' AND p.principal_kind = 'NHI')
     OR (e.subject_type = 'hi' AND p.principal_kind = 'HI')
    )
  LEFT JOIN access_drift_dev.silver.silver_assets a
    ON e.asset_id = a.source_asset_id
  GROUP BY e.case_id
),
gold_match AS (
  SELECT
    e.case_id,
    MAX(CASE WHEN g.risk_case_key IS NOT NULL THEN 1 ELSE 0 END) AS has_gold_match
  FROM positive_eval e
  LEFT JOIN access_drift_dev.gold.gold_core g
    ON e.subject_type = g.subject_type
   AND e.subject_id = g.subject_source_principal_id
   AND e.asset_id = g.asset_source_id
   AND e.drift_type = g.drift_type
  GROUP BY e.case_id
)
SELECT match_target, unmatched_count
FROM (
  SELECT
    'positive_eval_total' AS match_target,
    COUNT(*) AS unmatched_count
  FROM positive_eval

  UNION ALL

  SELECT
    'positive_eval_without_silver_match',
    COUNT(DISTINCT case_id)
  FROM silver_match
  WHERE has_principal_match = 0 OR has_asset_match = 0

  UNION ALL

  SELECT
    'positive_eval_without_gold_match',
    COUNT(DISTINCT case_id)
  FROM gold_match
  WHERE has_gold_match = 0
) checks
ORDER BY match_target;
