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


-- 13. DLT preflight validation summary
-- DLT 전환 전 현재 Bronze/Silver 데이터가 DLT expectation과 integrity audit의
-- 핵심 조건을 만족하는지 read-only로 확인한다.
-- PASS 기준: 모든 violation_count = 0
WITH
bronze_source_counts AS (
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
),
bronze_payloads AS (
  SELECT _raw_payload FROM access_drift_dev.bronze.bronze_azure_applications
  UNION ALL SELECT _raw_payload FROM access_drift_dev.bronze.bronze_azure_application_owners
  UNION ALL SELECT _raw_payload FROM access_drift_dev.bronze.bronze_azure_password_credentials
  UNION ALL SELECT _raw_payload FROM access_drift_dev.bronze.bronze_identity_lifecycle_seed
  UNION ALL SELECT _raw_payload FROM access_drift_dev.bronze.bronze_assets_seed
  UNION ALL SELECT _raw_payload FROM access_drift_dev.bronze.bronze_access_edges_seed
  UNION ALL SELECT _raw_payload FROM access_drift_dev.bronze.bronze_github_apps
  UNION ALL SELECT _raw_payload FROM access_drift_dev.bronze.bronze_github_credentials
  UNION ALL SELECT _raw_payload FROM access_drift_dev.bronze.bronze_github_repos
  UNION ALL SELECT _raw_payload FROM access_drift_dev.bronze.bronze_github_access_edges
  UNION ALL SELECT _raw_payload FROM access_drift_dev.bronze.bronze_google_workspace_users
  UNION ALL SELECT _raw_payload FROM access_drift_dev.bronze.bronze_google_workspace_assets
  UNION ALL SELECT _raw_payload FROM access_drift_dev.bronze.bronze_google_workspace_access_edges
  UNION ALL SELECT _raw_payload FROM access_drift_dev.bronze.bronze_slack_users
  UNION ALL SELECT _raw_payload FROM access_drift_dev.bronze.bronze_slack_channels
  UNION ALL SELECT _raw_payload FROM access_drift_dev.bronze.bronze_slack_access_edges
),
principals AS (
  SELECT * FROM access_drift_dev.silver.silver_principals
),
credentials AS (
  SELECT * FROM access_drift_dev.silver.silver_credentials
),
assets AS (
  SELECT * FROM access_drift_dev.silver.silver_assets
),
edges AS (
  SELECT * FROM access_drift_dev.silver.silver_edges
),
checks AS (
  SELECT 'bronze_source_not_empty' AS check_name, COUNT(*) AS violation_count
  FROM bronze_source_counts
  WHERE row_count = 0

  UNION ALL
  SELECT 'bronze_required_business_key_null', COUNT(*)
  FROM (
    SELECT app_id AS required_key
    FROM access_drift_dev.bronze.bronze_azure_applications
    UNION ALL
    SELECT app_id FROM access_drift_dev.bronze.bronze_azure_application_owners
    UNION ALL
    SELECT user_principal_name FROM access_drift_dev.bronze.bronze_azure_application_owners
    UNION ALL
    SELECT app_id FROM access_drift_dev.bronze.bronze_azure_password_credentials
    UNION ALL
    SELECT key_id FROM access_drift_dev.bronze.bronze_azure_password_credentials
    UNION ALL
    SELECT user_principal_name FROM access_drift_dev.bronze.bronze_identity_lifecycle_seed
    UNION ALL
    SELECT asset_id FROM access_drift_dev.bronze.bronze_assets_seed
    UNION ALL
    SELECT principal_id FROM access_drift_dev.bronze.bronze_access_edges_seed
    UNION ALL
    SELECT asset_id FROM access_drift_dev.bronze.bronze_access_edges_seed
    UNION ALL
    SELECT relationship FROM access_drift_dev.bronze.bronze_access_edges_seed
  ) required_keys
  WHERE required_key IS NULL OR trim(required_key) = ''

  UNION ALL
  SELECT 'bronze_forbidden_payload_field', COUNT(*)
  FROM bronze_payloads
  WHERE _raw_payload LIKE '%is_planted_risk%'
     OR _raw_payload LIKE '%expected_severity%'
     OR _raw_payload LIKE '%truth_class%'
     OR _raw_payload LIKE '%secretValue%'
     OR _raw_payload LIKE '%tokenValue%'
     OR _raw_payload LIKE '%privateKey%'

  UNION ALL
  SELECT 'silver_principal_required_null', COUNT(*)
  FROM principals
  WHERE principal_id IS NULL OR trim(principal_id) = ''
     OR source_system IS NULL OR trim(source_system) = ''
     OR source_principal_id IS NULL OR trim(source_principal_id) = ''
     OR principal_kind IS NULL
     OR principal_type IS NULL
     OR status IS NULL
     OR observed_at IS NULL

  UNION ALL
  SELECT 'silver_credential_required_null', COUNT(*)
  FROM credentials
  WHERE credential_id IS NULL OR trim(credential_id) = ''
     OR source_system IS NULL OR trim(source_system) = ''
     OR source_credential_id IS NULL OR trim(source_credential_id) = ''
     OR bound_principal_id IS NULL OR trim(bound_principal_id) = ''
     OR credential_type IS NULL
     OR status IS NULL
     OR is_active IS NULL
     OR observed_at IS NULL

  UNION ALL
  SELECT 'silver_asset_required_null', COUNT(*)
  FROM assets
  WHERE asset_id IS NULL OR trim(asset_id) = ''
     OR source_system IS NULL OR trim(source_system) = ''
     OR source_asset_id IS NULL OR trim(source_asset_id) = ''
     OR asset_type IS NULL
     OR environment IS NULL
     OR sensitivity IS NULL
     OR observed_at IS NULL

  UNION ALL
  SELECT 'silver_edge_required_null', COUNT(*)
  FROM edges
  WHERE edge_id IS NULL OR trim(edge_id) = ''
     OR source_system IS NULL OR trim(source_system) = ''
     OR from_id IS NULL OR trim(from_id) = ''
     OR from_type IS NULL
     OR to_id IS NULL OR trim(to_id) = ''
     OR to_type IS NULL
     OR relationship IS NULL
     OR status IS NULL
     OR observed_at IS NULL

  UNION ALL
  SELECT 'silver_principal_enum_invalid', COUNT(*)
  FROM principals
  WHERE source_system NOT IN ('entra_id', 'identity_seed')
     OR principal_kind NOT IN ('HI', 'NHI')
     OR principal_type NOT IN ('user', 'group', 'service_principal', 'app_registration', 'github_app', 'service_account', 'unknown')
     OR status NOT IN ('active', 'inactive', 'terminated', 'unknown')

  UNION ALL
  SELECT 'silver_credential_enum_or_active_invalid', COUNT(*)
  FROM credentials
  WHERE source_system <> 'entra_id'
     OR credential_type NOT IN ('client_secret', 'certificate', 'pat', 'deploy_key', 'api_key', 'unknown')
     OR status NOT IN ('active', 'expired', 'revoked', 'unknown')
     OR is_active <> CASE
       WHEN status = 'active' AND (expires_at IS NULL OR expires_at > observed_at) THEN true
       ELSE false
     END

  UNION ALL
  SELECT 'silver_asset_enum_invalid', COUNT(*)
  FROM assets
  WHERE source_system <> 'assets_seed'
     OR asset_type NOT IN ('cloud_resource', 'repo', 'database', 'workspace', 'saas_app', 'unknown')
     OR environment NOT IN ('production', 'staging', 'development', 'unknown')
     OR sensitivity NOT IN ('critical', 'high', 'medium', 'low', 'unknown')

  UNION ALL
  SELECT 'silver_edge_enum_or_direction_invalid', COUNT(*)
  FROM edges
  WHERE source_system NOT IN ('entra_id', 'access_seed')
     OR from_type NOT IN ('principal', 'credential', 'asset')
     OR to_type NOT IN ('principal', 'credential', 'asset')
     OR status NOT IN ('active', 'inactive', 'unknown')
     OR NOT (
       (relationship = 'owns_principal' AND from_type = 'principal' AND to_type = 'principal')
       OR (relationship IN ('owns_credential', 'manages_credential', 'accesses_credential') AND from_type = 'principal' AND to_type = 'credential')
       OR (relationship IN ('manages_asset', 'accesses_asset') AND from_type IN ('principal', 'credential') AND to_type = 'asset')
       OR (relationship = 'manages_principal' AND from_type = 'principal' AND to_type = 'principal')
       OR relationship = 'unknown'
     )

  UNION ALL
  SELECT 'silver_principal_id_mismatch', COUNT(*)
  FROM principals
  WHERE principal_id <> sha2(concat_ws(':', source_system, source_principal_id, principal_type), 256)

  UNION ALL
  SELECT 'silver_credential_id_mismatch', COUNT(*)
  FROM credentials
  WHERE credential_id <> sha2(concat_ws(':', source_system, source_credential_id, bound_principal_id), 256)

  UNION ALL
  SELECT 'silver_asset_id_mismatch', COUNT(*)
  FROM assets
  WHERE asset_id <> sha2(concat_ws(':', source_system, source_asset_id, asset_type), 256)

  UNION ALL
  SELECT 'silver_edge_id_mismatch', COUNT(*)
  FROM edges
  WHERE edge_id <> sha2(concat_ws(':', source_system, from_id, relationship, to_id), 256)

  UNION ALL
  SELECT 'duplicate_principal_id', COUNT(*)
  FROM (
    SELECT principal_id
    FROM principals
    GROUP BY principal_id
    HAVING COUNT(*) > 1
  ) duplicate_principals

  UNION ALL
  SELECT 'duplicate_credential_id', COUNT(*)
  FROM (
    SELECT credential_id
    FROM credentials
    GROUP BY credential_id
    HAVING COUNT(*) > 1
  ) duplicate_credentials

  UNION ALL
  SELECT 'duplicate_asset_id', COUNT(*)
  FROM (
    SELECT asset_id
    FROM assets
    GROUP BY asset_id
    HAVING COUNT(*) > 1
  ) duplicate_assets

  UNION ALL
  SELECT 'duplicate_edge_id', COUNT(*)
  FROM (
    SELECT edge_id
    FROM edges
    GROUP BY edge_id
    HAVING COUNT(*) > 1
  ) duplicate_edges

  UNION ALL
  SELECT 'credential_principal_orphan', COUNT(*)
  FROM credentials c
  LEFT JOIN principals p
    ON c.bound_principal_id = p.principal_id
  WHERE p.principal_id IS NULL

  UNION ALL
  SELECT 'edge_from_principal_orphan', COUNT(*)
  FROM edges e
  LEFT JOIN principals p
    ON e.from_id = p.principal_id
  WHERE e.from_type = 'principal'
    AND p.principal_id IS NULL

  UNION ALL
  SELECT 'edge_to_principal_orphan', COUNT(*)
  FROM edges e
  LEFT JOIN principals p
    ON e.to_id = p.principal_id
  WHERE e.to_type = 'principal'
    AND p.principal_id IS NULL

  UNION ALL
  SELECT 'edge_to_credential_orphan', COUNT(*)
  FROM edges e
  LEFT JOIN credentials c
    ON e.to_id = c.credential_id
  WHERE e.to_type = 'credential'
    AND c.credential_id IS NULL

  UNION ALL
  SELECT 'edge_to_asset_orphan', COUNT(*)
  FROM edges e
  LEFT JOIN assets a
    ON e.to_id = a.asset_id
  WHERE e.to_type = 'asset'
    AND a.asset_id IS NULL

  UNION ALL
  SELECT 'owner_edge_not_hi_to_nhi', COUNT(*)
  FROM edges e
  LEFT JOIN principals owner
    ON e.from_id = owner.principal_id
   AND owner.principal_kind = 'HI'
  LEFT JOIN principals app
    ON e.to_id = app.principal_id
   AND app.principal_kind = 'NHI'
  WHERE e.relationship = 'owns_principal'
    AND (owner.principal_id IS NULL OR app.principal_id IS NULL)

  UNION ALL
  SELECT 'credential_bound_principal_not_nhi', COUNT(*)
  FROM credentials c
  LEFT JOIN principals p
    ON c.bound_principal_id = p.principal_id
   AND p.principal_kind = 'NHI'
  WHERE p.principal_id IS NULL

  UNION ALL
  SELECT 'access_metadata_on_non_access_edge', COUNT(*)
  FROM edges
  WHERE relationship <> 'accesses_asset'
    AND (
      (permission IS NOT NULL AND trim(permission) <> '')
      OR last_used_at IS NOT NULL
    )
)
SELECT check_name, violation_count
FROM checks
ORDER BY check_name;
