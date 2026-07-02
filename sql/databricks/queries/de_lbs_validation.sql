-- DE Landing/Bronze/Silver validation queries.
-- Default target: access_drift_dev.
-- If validating PoC, replace access_drift_dev with access_drift.

-- 1. Bronze/Silver row counts
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
UNION ALL
SELECT 'bronze_github_apps', COUNT(*)
FROM access_drift_dev.bronze.bronze_github_apps
UNION ALL
SELECT 'bronze_github_credentials', COUNT(*)
FROM access_drift_dev.bronze.bronze_github_credentials
UNION ALL
SELECT 'bronze_github_repos', COUNT(*)
FROM access_drift_dev.bronze.bronze_github_repos
UNION ALL
SELECT 'bronze_github_access_edges', COUNT(*)
FROM access_drift_dev.bronze.bronze_github_access_edges
UNION ALL
SELECT 'bronze_google_workspace_users', COUNT(*)
FROM access_drift_dev.bronze.bronze_google_workspace_users
UNION ALL
SELECT 'bronze_google_workspace_assets', COUNT(*)
FROM access_drift_dev.bronze.bronze_google_workspace_assets
UNION ALL
SELECT 'bronze_google_workspace_access_edges', COUNT(*)
FROM access_drift_dev.bronze.bronze_google_workspace_access_edges
UNION ALL
SELECT 'bronze_slack_users', COUNT(*)
FROM access_drift_dev.bronze.bronze_slack_users
UNION ALL
SELECT 'bronze_slack_channels', COUNT(*)
FROM access_drift_dev.bronze.bronze_slack_channels
UNION ALL
SELECT 'bronze_slack_access_edges', COUNT(*)
FROM access_drift_dev.bronze.bronze_slack_access_edges
UNION ALL
SELECT 'silver_principals', COUNT(*)
FROM access_drift_dev.silver.silver_principals
UNION ALL
SELECT 'silver_credentials', COUNT(*)
FROM access_drift_dev.silver.silver_credentials
UNION ALL
SELECT 'silver_assets', COUNT(*)
FROM access_drift_dev.silver.silver_assets
UNION ALL
SELECT 'silver_edges', COUNT(*)
FROM access_drift_dev.silver.silver_edges
ORDER BY table_name;

-- 2. Silver required key null checks
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

-- 3. Enum and relationship value checks
SELECT 'silver_principals.principal_kind' AS check_name, principal_kind AS value, COUNT(*) AS row_count
FROM access_drift_dev.silver.silver_principals
WHERE principal_kind NOT IN ('HI', 'NHI')
GROUP BY principal_kind
UNION ALL
SELECT 'silver_principals.principal_type', principal_type, COUNT(*)
FROM access_drift_dev.silver.silver_principals
WHERE principal_type NOT IN ('user', 'group', 'service_principal', 'app_registration', 'github_app', 'service_account', 'unknown')
GROUP BY principal_type
UNION ALL
SELECT 'silver_credentials.credential_type', credential_type, COUNT(*)
FROM access_drift_dev.silver.silver_credentials
WHERE credential_type NOT IN ('client_secret', 'certificate', 'pat', 'deploy_key', 'api_key', 'unknown')
GROUP BY credential_type
UNION ALL
SELECT 'silver_edges.relationship', relationship, COUNT(*)
FROM access_drift_dev.silver.silver_edges
WHERE relationship NOT IN (
  'owns_principal',
  'owns_credential',
  'manages_principal',
  'manages_credential',
  'accesses_credential',
  'manages_asset',
  'accesses_asset',
  'unknown'
)
GROUP BY relationship
UNION ALL
SELECT 'silver_assets.sensitivity', sensitivity, COUNT(*)
FROM access_drift_dev.silver.silver_assets
WHERE sensitivity NOT IN ('critical', 'high', 'medium', 'low', 'unknown')
GROUP BY sensitivity;

-- 4. Credential -> principal reference check
SELECT COUNT(*) AS credentials_without_bound_principal
FROM access_drift_dev.silver.silver_credentials c
LEFT JOIN access_drift_dev.silver.silver_principals p
  ON c.bound_principal_id = p.principal_id
WHERE p.principal_id IS NULL;

-- 5. Credential edge -> credential reference check
SELECT COUNT(*) AS credential_edges_without_credential
FROM access_drift_dev.silver.silver_edges e
LEFT JOIN access_drift_dev.silver.silver_credentials c
  ON e.to_type = 'credential'
 AND e.to_id = c.credential_id
WHERE e.to_type = 'credential'
  AND c.credential_id IS NULL;

-- 6. Access edge -> principal/asset reference check
SELECT COUNT(*) AS access_edges_without_principal_or_asset
FROM access_drift_dev.silver.silver_edges e
LEFT JOIN access_drift_dev.silver.silver_principals p
  ON e.from_type = 'principal'
 AND e.from_id = p.principal_id
LEFT JOIN access_drift_dev.silver.silver_assets a
  ON e.to_type = 'asset'
 AND e.to_id = a.asset_id
WHERE e.relationship = 'accesses_asset'
  AND (p.principal_id IS NULL OR a.asset_id IS NULL);

-- 7. Owner edge -> HI/NHI principal reference check
SELECT COUNT(*) AS owner_edges_without_hi_or_nhi
FROM access_drift_dev.silver.silver_edges e
LEFT JOIN access_drift_dev.silver.silver_principals owner
  ON e.from_id = owner.principal_id
 AND owner.principal_kind = 'HI'
LEFT JOIN access_drift_dev.silver.silver_principals app
  ON e.to_id = app.principal_id
 AND app.principal_kind = 'NHI'
WHERE e.relationship = 'owns_principal'
  AND (owner.principal_id IS NULL OR app.principal_id IS NULL);


-- 8. GitHub owner edge -> owner status check
SELECT COUNT(*) AS github_owner_edges_missing_or_null_owner_status
FROM access_drift_dev.bronze.bronze_github_apps g
LEFT JOIN access_drift_dev.silver.silver_principals owner
  ON owner.source_principal_id = g.owner_email
 AND owner.principal_kind = 'HI'
LEFT JOIN access_drift_dev.silver.silver_principals app
  ON app.source_principal_id = g.app_id
 AND app.principal_type = 'github_app'
LEFT JOIN access_drift_dev.silver.silver_edges e
  ON e.from_id = owner.principal_id
 AND e.to_id = app.principal_id
 AND e.relationship = 'owns_principal'
WHERE g.owner_email IS NOT NULL
  AND (
    owner.principal_id IS NULL
    OR owner.status IS NULL
    OR app.principal_id IS NULL
    OR e.edge_id IS NULL
  );

-- 9. Eval positive case -> Silver principal/asset match check
SELECT COUNT(*) AS positive_eval_without_silver_match

FROM access_drift_dev.eval.ground_truth_case g
LEFT JOIN access_drift_dev.silver.silver_principals p
  ON g.subject_id = p.source_principal_id
 AND (
   (g.subject_type = 'nhi' AND p.principal_kind = 'NHI')
   OR (g.subject_type = 'hi' AND p.principal_kind = 'HI')
 )
LEFT JOIN access_drift_dev.silver.silver_assets a
  ON g.asset_id = a.source_asset_id
WHERE g.is_planted_risk = true
  AND g.subject_id NOT LIKE 'gh-%'
  AND g.subject_id NOT LIKE 'gws-%'
  AND g.subject_id NOT LIKE 'slack-%'
  AND g.asset_id NOT LIKE 'gh-%'
  AND g.asset_id NOT LIKE 'gws-%'
  AND g.asset_id NOT LIKE 'slack-%'
  AND (p.principal_id IS NULL OR a.asset_id IS NULL);


-- 10. Context asset_context -> Silver asset match check
SELECT COUNT(*) AS context_assets_without_silver_match
FROM access_drift_dev.context.asset_context c
LEFT JOIN access_drift_dev.silver.silver_assets a
  ON c.source_asset_id = a.source_asset_id
WHERE a.asset_id IS NULL;

-- 11. Context assignment_routing -> Eval match check

-- assignment_routing은 eval key와 같은 source key를 써야 한다.
SELECT COUNT(*) AS assignment_routing_without_eval_match
FROM access_drift_dev.context.assignment_routing r
LEFT JOIN access_drift_dev.eval.ground_truth_case g
  ON r.subject_type = g.subject_type
 AND r.subject_id = g.subject_id
 AND r.asset_id = g.asset_id
 AND r.drift_type = g.drift_type
WHERE g.case_id IS NULL;


-- 12. Eval -> Context assignment_routing match check

-- Eval에 있는 케이스는 조치 담당자 라우팅 context를 가져야 한다.
SELECT COUNT(*) AS eval_without_assignment_routing_match
FROM access_drift_dev.eval.ground_truth_case g
LEFT JOIN access_drift_dev.context.assignment_routing r
  ON r.subject_type = g.subject_type
 AND r.subject_id = g.subject_id
 AND r.asset_id = g.asset_id
 AND r.drift_type = g.drift_type
WHERE r.subject_id IS NULL;

-- 10. Access edge common metadata coverage by source
-- accesses_asset edge는 source와 무관하게 permission/status/last_used_at을 제공해야 한다.
SELECT
  evidence_source,
  COUNT(*) AS total_access_edges,
  SUM(CASE WHEN permission IS NULL OR trim(permission) = '' THEN 1 ELSE 0 END) AS missing_permission,
  SUM(CASE WHEN status IS NULL OR trim(status) = '' THEN 1 ELSE 0 END) AS missing_status,
  SUM(CASE WHEN last_used_at IS NULL THEN 1 ELSE 0 END) AS missing_last_used_at
FROM access_drift_dev.silver.silver_edges
WHERE relationship = 'accesses_asset'
GROUP BY evidence_source
ORDER BY evidence_source;
