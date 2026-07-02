-- Databricks SQL ops dashboard query 05
-- Purpose: verify Gold rows have Risk Card context and assignment coverage.
-- Target catalog: access_drift_dev

WITH gold_with_context AS (
  SELECT
    g.risk_case_key,
    c.source_asset_id AS matched_context_asset_id,
    r.subject_id AS matched_assignment_subject_id
  FROM access_drift_dev.gold.gold_core g
  LEFT JOIN access_drift_dev.context.asset_context c
    ON g.asset_source_id = c.source_asset_id
  LEFT JOIN access_drift_dev.context.assignment_routing r
    ON g.subject_type = r.subject_type
   AND g.subject_source_principal_id = r.subject_id
   AND g.asset_source_id = r.asset_id
   AND g.drift_type = r.drift_type
)
SELECT coverage_type, covered_count, missing_count, coverage_pct
FROM (
  SELECT
    'asset_context' AS coverage_type,
    COUNT_IF(matched_context_asset_id IS NOT NULL) AS covered_count,
    COUNT_IF(matched_context_asset_id IS NULL) AS missing_count,
    ROUND(100.0 * COUNT_IF(matched_context_asset_id IS NOT NULL) / NULLIF(COUNT(*), 0), 1) AS coverage_pct
  FROM gold_with_context

  UNION ALL

  SELECT
    'assignment_routing' AS coverage_type,
    COUNT_IF(matched_assignment_subject_id IS NOT NULL) AS covered_count,
    COUNT_IF(matched_assignment_subject_id IS NULL) AS missing_count,
    ROUND(100.0 * COUNT_IF(matched_assignment_subject_id IS NOT NULL) / NULLIF(COUNT(*), 0), 1) AS coverage_pct
  FROM gold_with_context
) coverage
ORDER BY coverage_type;
