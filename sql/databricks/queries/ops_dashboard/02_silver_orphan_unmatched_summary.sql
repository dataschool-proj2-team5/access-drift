-- Databricks SQL ops dashboard query 02
-- Purpose: summarize Silver orphan/unmatched conditions that indicate broken pipeline joins.
-- Target catalog: access_drift_dev

WITH credentials_without_bound_principal AS (
  SELECT COUNT(*) AS issue_count
  FROM access_drift_dev.silver.silver_credentials c
  LEFT JOIN access_drift_dev.silver.silver_principals p
    ON c.bound_principal_id = p.principal_id
  WHERE p.principal_id IS NULL
),
credential_edges_without_credential AS (
  SELECT COUNT(*) AS issue_count
  FROM access_drift_dev.silver.silver_edges e
  LEFT JOIN access_drift_dev.silver.silver_credentials c
    ON e.to_type = 'credential'
   AND e.to_id = c.credential_id
  WHERE e.to_type = 'credential'
    AND c.credential_id IS NULL
),
access_edges_without_principal_or_asset AS (
  SELECT COUNT(*) AS issue_count
  FROM access_drift_dev.silver.silver_edges e
  LEFT JOIN access_drift_dev.silver.silver_principals p
    ON e.from_type = 'principal'
   AND e.from_id = p.principal_id
  LEFT JOIN access_drift_dev.silver.silver_assets a
    ON e.to_type = 'asset'
   AND e.to_id = a.asset_id
  WHERE e.relationship = 'accesses_asset'
    AND (p.principal_id IS NULL OR a.asset_id IS NULL)
),
owner_edges_without_hi_or_nhi AS (
  SELECT COUNT(*) AS issue_count
  FROM access_drift_dev.silver.silver_edges e
  LEFT JOIN access_drift_dev.silver.silver_principals owner
    ON e.from_id = owner.principal_id
   AND owner.principal_kind = 'HI'
  LEFT JOIN access_drift_dev.silver.silver_principals nhi
    ON e.to_id = nhi.principal_id
   AND nhi.principal_kind = 'NHI'
  WHERE e.relationship = 'owns_principal'
    AND (owner.principal_id IS NULL OR nhi.principal_id IS NULL)
)
SELECT check_name, issue_count
FROM (
  SELECT 'credentials_without_bound_principal' AS check_name, issue_count
  FROM credentials_without_bound_principal
  UNION ALL
  SELECT 'credential_edges_without_credential', issue_count
  FROM credential_edges_without_credential
  UNION ALL
  SELECT 'access_edges_without_principal_or_asset', issue_count
  FROM access_edges_without_principal_or_asset
  UNION ALL
  SELECT 'owner_edges_without_hi_or_nhi', issue_count
  FROM owner_edges_without_hi_or_nhi
) checks
ORDER BY check_name;
