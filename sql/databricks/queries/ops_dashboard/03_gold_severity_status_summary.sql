-- Databricks SQL ops dashboard query 03
-- Purpose: summarize Gold severity and action status for dashboard widgets.
-- Target catalog: access_drift_dev

WITH gold_with_action AS (
  SELECT
    g.risk_case_key,
    g.severity,
    COALESCE(s.status, 'open') AS action_status
  FROM access_drift_dev.gold.gold_core g
  LEFT JOIN access_drift_dev.app.risk_action_state s
    ON g.risk_case_key = s.risk_case_key
)
SELECT summary_type, summary_key, row_count
FROM (
  SELECT
    'severity' AS summary_type,
    severity AS summary_key,
    COUNT(*) AS row_count
  FROM gold_with_action
  GROUP BY severity

  UNION ALL

  SELECT
    'action_status' AS summary_type,
    action_status AS summary_key,
    COUNT(*) AS row_count
  FROM gold_with_action
  GROUP BY action_status

  UNION ALL

  SELECT
    'severity_status' AS summary_type,
    CONCAT(severity, ' | ', action_status) AS summary_key,
    COUNT(*) AS row_count
  FROM gold_with_action
  GROUP BY severity, action_status
) summary
ORDER BY summary_type, summary_key;
