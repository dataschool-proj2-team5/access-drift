-- DE retry/idempotency validation queries.
-- Default target: access_drift_dev.
-- Run this after each retry scenario and compare the result snapshots manually.

-- 1. Bronze row counts
SELECT 'bronze_azure_applications' AS table_name, COUNT(*) AS row_count
FROM access_drift_dev.bronze.bronze_azure_applications
UNION ALL
SELECT 'bronze_azure_application_owners', COUNT(*)
FROM access_drift_dev.bronze.bronze_azure_application_owners
UNION ALL
SELECT 'bronze_azure_password_credentials', COUNT(*)
FROM access_drift_dev.bronze.bronze_azure_password_credentials
UNION ALL
SELECT 'bronze_identity_lifecycle_seed', COUNT(*)
FROM access_drift_dev.bronze.bronze_identity_lifecycle_seed
UNION ALL
SELECT 'bronze_assets_seed', COUNT(*)
FROM access_drift_dev.bronze.bronze_assets_seed
UNION ALL
SELECT 'bronze_access_edges_seed', COUNT(*)
FROM access_drift_dev.bronze.bronze_access_edges_seed
ORDER BY table_name;

-- 2. Silver row counts and deterministic key counts
SELECT 'silver_principals' AS table_name, COUNT(*) AS row_count, COUNT(DISTINCT principal_id) AS distinct_key_count
FROM access_drift_dev.silver.silver_principals
UNION ALL
SELECT 'silver_credentials', COUNT(*), COUNT(DISTINCT credential_id)
FROM access_drift_dev.silver.silver_credentials
UNION ALL
SELECT 'silver_assets', COUNT(*), COUNT(DISTINCT asset_id)
FROM access_drift_dev.silver.silver_assets
UNION ALL
SELECT 'silver_edges', COUNT(*), COUNT(DISTINCT edge_id)
FROM access_drift_dev.silver.silver_edges
ORDER BY table_name;

-- 3. Eval and context row counts and key counts
SELECT 'eval.ground_truth_case' AS table_name, COUNT(*) AS row_count, COUNT(DISTINCT case_id) AS distinct_key_count
FROM access_drift_dev.eval.ground_truth_case
UNION ALL
SELECT 'context.asset_context', COUNT(*), COUNT(DISTINCT source_asset_id)
FROM access_drift_dev.context.asset_context
UNION ALL
SELECT
  'context.assignment_routing',
  COUNT(*),
  COUNT(DISTINCT CONCAT(subject_type, '|', subject_id, '|', asset_id, '|', drift_type))
FROM access_drift_dev.context.assignment_routing
ORDER BY table_name;

-- 4. Silver required key null checks
SELECT 'silver_principals' AS table_name, COUNT(*) AS invalid_rows
FROM access_drift_dev.silver.silver_principals
WHERE principal_id IS NULL
   OR source_system IS NULL
   OR source_principal_id IS NULL
   OR principal_kind IS NULL
   OR principal_type IS NULL
   OR status IS NULL
   OR observed_at IS NULL
UNION ALL
SELECT 'silver_credentials', COUNT(*)
FROM access_drift_dev.silver.silver_credentials
WHERE credential_id IS NULL
   OR source_system IS NULL
   OR source_credential_id IS NULL
   OR bound_principal_id IS NULL
   OR credential_type IS NULL
   OR status IS NULL
   OR is_active IS NULL
   OR observed_at IS NULL
UNION ALL
SELECT 'silver_assets', COUNT(*)
FROM access_drift_dev.silver.silver_assets
WHERE asset_id IS NULL
   OR source_system IS NULL
   OR source_asset_id IS NULL
   OR asset_type IS NULL
   OR environment IS NULL
   OR sensitivity IS NULL
   OR observed_at IS NULL
UNION ALL
SELECT 'silver_edges', COUNT(*)
FROM access_drift_dev.silver.silver_edges
WHERE edge_id IS NULL
   OR source_system IS NULL
   OR from_id IS NULL
   OR from_type IS NULL
   OR to_id IS NULL
   OR to_type IS NULL
   OR relationship IS NULL
   OR status IS NULL
   OR observed_at IS NULL
ORDER BY table_name;

-- 5. Silver orphan reference checks
SELECT 'credentials_without_bound_principal' AS check_name, COUNT(*) AS invalid_rows
FROM access_drift_dev.silver.silver_credentials c
LEFT JOIN access_drift_dev.silver.silver_principals p
  ON c.bound_principal_id = p.principal_id
WHERE p.principal_id IS NULL
UNION ALL
SELECT 'access_edges_without_principal_or_asset', COUNT(*)
FROM access_drift_dev.silver.silver_edges e
LEFT JOIN access_drift_dev.silver.silver_principals p
  ON e.from_type = 'principal'
 AND e.from_id = p.principal_id
LEFT JOIN access_drift_dev.silver.silver_assets a
  ON e.to_type = 'asset'
 AND e.to_id = a.asset_id
WHERE e.relationship = 'accesses_asset'
  AND (p.principal_id IS NULL OR a.asset_id IS NULL)
UNION ALL
SELECT 'owner_edges_without_hi_or_nhi', COUNT(*)
FROM access_drift_dev.silver.silver_edges e
LEFT JOIN access_drift_dev.silver.silver_principals owner
  ON e.from_id = owner.principal_id
 AND owner.principal_kind = 'HI'
LEFT JOIN access_drift_dev.silver.silver_principals app
  ON e.to_id = app.principal_id
 AND app.principal_kind = 'NHI'
WHERE e.relationship = 'owns_principal'
  AND (owner.principal_id IS NULL OR app.principal_id IS NULL)
ORDER BY check_name;

-- 6. Eval/context matching checks
SELECT 'positive_eval_without_silver_match' AS check_name, COUNT(*) AS invalid_rows
FROM access_drift_dev.eval.ground_truth_case g
LEFT JOIN access_drift_dev.silver.silver_principals p
  ON g.subject_id = p.source_principal_id
 AND p.principal_kind = 'NHI'
LEFT JOIN access_drift_dev.silver.silver_assets a
  ON g.asset_id = a.source_asset_id
WHERE g.is_planted_risk = true
  AND (p.principal_id IS NULL OR a.asset_id IS NULL)
UNION ALL
SELECT 'asset_context_without_silver_asset', COUNT(*)
FROM access_drift_dev.context.asset_context ac
LEFT JOIN access_drift_dev.silver.silver_assets a
  ON ac.source_asset_id = a.source_asset_id
WHERE a.asset_id IS NULL
UNION ALL
SELECT 'assignment_routing_without_eval_case', COUNT(*)
FROM access_drift_dev.context.assignment_routing ar
LEFT JOIN access_drift_dev.eval.ground_truth_case g
  ON ar.subject_type = g.subject_type
 AND ar.subject_id = g.subject_id
 AND ar.asset_id = g.asset_id
 AND ar.drift_type = g.drift_type
WHERE g.case_id IS NULL
ORDER BY check_name;

-- 7. Representative demo case keys
SELECT
  g.case_id,
  g.subject_type,
  g.subject_id,
  g.asset_id,
  g.drift_type,
  p.principal_id,
  a.asset_id AS silver_asset_id,
  ac.data_scope_label,
  ar.assignee_team
FROM access_drift_dev.eval.ground_truth_case g
LEFT JOIN access_drift_dev.silver.silver_principals p
  ON g.subject_id = p.source_principal_id
 AND p.principal_kind = 'NHI'
LEFT JOIN access_drift_dev.silver.silver_assets a
  ON g.asset_id = a.source_asset_id
LEFT JOIN access_drift_dev.context.asset_context ac
  ON g.asset_id = ac.source_asset_id
LEFT JOIN access_drift_dev.context.assignment_routing ar
  ON g.subject_type = ar.subject_type
 AND g.subject_id = ar.subject_id
 AND g.asset_id = ar.asset_id
 AND g.drift_type = ar.drift_type
WHERE g.subject_id = 'd8f4a5b6-7c8d-4e91-9f02-1a2b3c4d5e6f'
  AND g.asset_id = 'asset-customer-export-storage-prod'
  AND g.drift_type = 'nhi_residual_access';
