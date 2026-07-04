-- Databricks SQL ops dashboard query 06
-- Purpose: summarize action state, action events, and stale state risk_case_keys.
-- Target catalog: access_drift_dev

WITH stale_state AS (
  SELECT COUNT(*) AS stale_count
  FROM access_drift_dev.app.risk_action_state s
  LEFT JOIN access_drift_dev.gold.gold_core g
    ON s.risk_case_key = g.risk_case_key
  WHERE g.risk_case_key IS NULL
)
SELECT summary_type, summary_key, row_count
FROM (
  SELECT
    'risk_action_state_total' AS summary_type,
    'all' AS summary_key,
    COUNT(*) AS row_count
  FROM access_drift_dev.app.risk_action_state

  UNION ALL

  SELECT
    'risk_action_state_status' AS summary_type,
    status AS summary_key,
    COUNT(*) AS row_count
  FROM access_drift_dev.app.risk_action_state
  GROUP BY status

  UNION ALL

  SELECT
    'risk_action_event_total' AS summary_type,
    'all' AS summary_key,
    COUNT(*) AS row_count
  FROM access_drift_dev.app.risk_action_event

  UNION ALL

  SELECT
    'risk_action_event_type' AS summary_type,
    event_type AS summary_key,
    COUNT(*) AS row_count
  FROM access_drift_dev.app.risk_action_event
  GROUP BY event_type

  UNION ALL

  SELECT
    'stale_risk_action_state' AS summary_type,
    'missing_gold_match' AS summary_key,
    stale_count AS row_count
  FROM stale_state
) summary
ORDER BY summary_type, summary_key;
