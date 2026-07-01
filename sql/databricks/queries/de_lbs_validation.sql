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
WHERE sensitivity NOT IN ('high', 'medium', 'low', 'unknown')
GROUP BY sensitivity;

-- 4. Credential -> principal reference check
SELECT COUNT(*) AS credentials_without_bound_principal
FROM access_drift_dev.silver.silver_credentials c
LEFT JOIN access_drift_dev.silver.silver_principals p
  ON c.bound_principal_id = p.principal_id
WHERE p.principal_id IS NULL;

-- 5. Access edge -> principal/asset reference check
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

-- 6. Owner edge -> HI/NHI principal reference check
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

-- 7. Eval positive case -> Silver principal/asset match check
-- GitHub/Google Workspace/Slack 확장 seed는 아직 Bronze/Silver 변환 대상이 아니므로
-- 현재 Silver가 커버하는 Entra/asset seed 기반 eval만 검증한다.
SELECT COUNT(*) AS silver_covered_positive_eval_without_silver_match
FROM access_drift_dev.eval.ground_truth_case g
LEFT JOIN access_drift_dev.silver.silver_principals p
  ON g.subject_id = p.source_principal_id
 AND p.principal_kind = 'NHI'
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

-- 8. Context asset_context -> Silver asset match check
-- SaaS 확장 seed는 context/eval에는 포함되지만 아직 Silver 변환 대상이 아니므로 제외한다.
SELECT COUNT(*) AS silver_covered_context_assets_without_silver_match
FROM access_drift_dev.context.asset_context c
LEFT JOIN access_drift_dev.silver.silver_assets a
  ON c.source_asset_id = a.source_asset_id
WHERE c.source_asset_id NOT LIKE 'gh-%'
  AND c.source_asset_id NOT LIKE 'gws-%'
  AND c.source_asset_id NOT LIKE 'slack-%'
  AND a.asset_id IS NULL;

-- 9. Context assignment_routing -> Eval match check
-- assignment_routing은 eval key와 같은 source key를 써야 한다.
SELECT COUNT(*) AS assignment_routing_without_eval_match
FROM access_drift_dev.context.assignment_routing r
LEFT JOIN access_drift_dev.eval.ground_truth_case g
  ON r.subject_type = g.subject_type
 AND r.subject_id = g.subject_id
 AND r.asset_id = g.asset_id
 AND r.drift_type = g.drift_type
WHERE g.case_id IS NULL;

-- 10. Eval -> Context assignment_routing match check
-- Eval에 있는 케이스는 조치 담당자 라우팅 context를 가져야 한다.
SELECT COUNT(*) AS eval_without_assignment_routing_match
FROM access_drift_dev.eval.ground_truth_case g
LEFT JOIN access_drift_dev.context.assignment_routing r
  ON r.subject_type = g.subject_type
 AND r.subject_id = g.subject_id
 AND r.asset_id = g.asset_id
 AND r.drift_type = g.drift_type
WHERE r.subject_id IS NULL;
