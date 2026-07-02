-- Silver semantic audit queries.
-- Default target: access_drift_dev.
--
-- Purpose:
--   Silver가 "row가 만들어졌다" 수준을 넘어 Gold/Risk Card/Access Path가
--   믿고 사용할 수 있는 의미 품질을 갖췄는지 확인한다.
--
-- PASS 기준:
--   원칙적으로 violation_count = 0.
--   severity = WARN 항목은 현재 데이터/정책 확정 전 검토용이며,
--   FAIL 항목은 DLT silver_integrity_audit 승격 후보로 본다.
--
-- Output:
--   check_name      : 검증 이름
--   severity        : FAIL 또는 WARN
--   violation_count : 위반 row 수
--   sample_keys     : 문제 row 추적용 샘플 key

WITH
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
eval_cases AS (
  SELECT * FROM access_drift_dev.eval.ground_truth_case
),
identity_users AS (
  SELECT
    user_principal_name AS source_id,
    display_name,
    employment_status,
    termination_date
  FROM access_drift_dev.bronze.bronze_identity_lifecycle_seed
),
github_apps AS (
  SELECT * FROM access_drift_dev.bronze.bronze_github_apps
),
google_users AS (
  SELECT * FROM access_drift_dev.bronze.bronze_google_workspace_users
),
slack_users AS (
  SELECT * FROM access_drift_dev.bronze.bronze_slack_users
),
all_source_humans AS (
  SELECT
    'identity_lifecycle' AS source_table,
    user_principal_name AS source_id,
    user_principal_name AS email,
    display_name,
    employment_status,
    termination_date
  FROM access_drift_dev.bronze.bronze_identity_lifecycle_seed
  UNION ALL
  SELECT
    'google_workspace_users',
    user_id,
    email,
    display_name,
    employment_status,
    termination_date
  FROM access_drift_dev.bronze.bronze_google_workspace_users
  UNION ALL
  SELECT
    'slack_users',
    user_id,
    email,
    display_name,
    employment_status,
    termination_date
  FROM access_drift_dev.bronze.bronze_slack_users
),
owner_edges AS (
  SELECT
    e.edge_id,
    e.from_id AS owner_principal_id,
    e.to_id AS owned_principal_id,
    owner.source_system AS owner_source_system,
    owner.source_principal_id AS owner_source_principal_id,
    owner.display_name AS owner_display_name,
    owner.email AS owner_email,
    owner.status AS owner_status,
    owner.termination_date AS owner_termination_date,
    owned.source_system AS owned_source_system,
    owned.source_principal_id AS owned_source_principal_id,
    owned.display_name AS owned_display_name,
    owned.principal_type AS owned_principal_type,
    owned.principal_kind AS owned_principal_kind
  FROM edges e
  LEFT JOIN principals owner
    ON e.from_id = owner.principal_id
  LEFT JOIN principals owned
    ON e.to_id = owned.principal_id
  WHERE e.relationship = 'owns_principal'
),
access_edges AS (
  SELECT
    e.*,
    fp.principal_kind AS from_principal_kind,
    fp.principal_type AS from_principal_type,
    fp.source_principal_id AS from_source_principal_id,
    fp.display_name AS from_display_name,
    fp.status AS from_principal_status,
    c.credential_type AS from_credential_type,
    c.status AS from_credential_status,
    c.is_active AS from_credential_is_active,
    a.source_asset_id,
    a.asset_type,
    a.display_name AS asset_display_name,
    a.environment AS asset_environment,
    a.sensitivity AS asset_sensitivity
  FROM edges e
  LEFT JOIN principals fp
    ON e.from_type = 'principal'
   AND e.from_id = fp.principal_id
  LEFT JOIN credentials c
    ON e.from_type = 'credential'
   AND e.from_id = c.credential_id
  LEFT JOIN assets a
    ON e.to_type = 'asset'
   AND e.to_id = a.asset_id
  WHERE e.relationship = 'accesses_asset'
),
positive_graph AS (
  SELECT
    ae.edge_id,
    subject.source_principal_id AS subject_id,
    asset.source_asset_id AS asset_id,
    owner.source_principal_id AS owner_id,
    subject.principal_id AS subject_principal_id,
    asset.asset_id AS silver_asset_id,
    owner.principal_id AS owner_principal_id,
    cred.credential_id,
    owner.status AS owner_status,
    subject.status AS subject_status,
    cred.is_active AS credential_is_active,
    ae.status AS access_status,
    asset.sensitivity
  FROM access_edges ae
  JOIN principals subject
    ON ae.from_type = 'principal'
   AND ae.from_id = subject.principal_id
   AND subject.principal_kind = 'NHI'
  JOIN assets asset
    ON ae.to_id = asset.asset_id
  LEFT JOIN owner_edges oe
    ON oe.owned_principal_id = subject.principal_id
  LEFT JOIN principals owner
    ON oe.owner_principal_id = owner.principal_id
  LEFT JOIN credentials cred
    ON cred.bound_principal_id = subject.principal_id
   AND cred.is_active = true
  WHERE owner.status = 'terminated'
    AND subject.status = 'active'
    AND cred.is_active = true
    AND ae.status = 'active'
    AND asset.sensitivity IN ('critical', 'high', 'medium')
),
violations AS (
  -- Principal display and identity semantics
  SELECT
    'hi_display_name_missing' AS check_name,
    'FAIL' AS severity,
    principal_id AS object_key,
    concat('source=', source_system, ', source_id=', source_principal_id) AS detail
  FROM principals
  WHERE principal_kind = 'HI'
    AND (display_name IS NULL OR trim(display_name) = '')

  UNION ALL
  SELECT
    'hi_display_name_email_fallback',
    'FAIL',
    principal_id,
    concat('display_name=', display_name, ', email=', coalesce(email, 'NULL'))
  FROM principals
  WHERE principal_kind = 'HI'
    AND display_name IS NOT NULL
    AND lower(trim(display_name)) = lower(trim(coalesce(email, source_principal_id)))
    AND display_name LIKE '%@%.%'

  UNION ALL
  SELECT
    'owner_display_name_email_fallback',
    'FAIL',
    edge_id,
    concat('owner=', owner_source_principal_id, ', display_name=', owner_display_name)
  FROM owner_edges
  WHERE owner_display_name IS NOT NULL
    AND owner_display_name LIKE '%@%.%'

  UNION ALL
  SELECT
    'owner_display_name_missing',
    'FAIL',
    edge_id,
    concat('owner=', coalesce(owner_source_principal_id, 'NULL'), ', owned=', coalesce(owned_source_principal_id, 'NULL'))
  FROM owner_edges
  WHERE owner_display_name IS NULL OR trim(owner_display_name) = ''

  UNION ALL
  SELECT
    'hi_email_missing_or_invalid',
    'WARN',
    principal_id,
    concat('source=', source_system, ', source_id=', source_principal_id, ', email=', coalesce(email, 'NULL'))
  FROM principals
  WHERE principal_kind = 'HI'
    AND (email IS NULL OR trim(email) = '' OR email NOT LIKE '%@%.%')

  UNION ALL
  SELECT
    'hi_principal_type_not_user',
    'FAIL',
    principal_id,
    concat('principal_type=', principal_type, ', source_id=', source_principal_id)
  FROM principals
  WHERE principal_kind = 'HI'
    AND principal_type <> 'user'

  UNION ALL
  SELECT
    'nhi_principal_type_user',
    'FAIL',
    principal_id,
    concat('principal_type=', principal_type, ', source_id=', source_principal_id)
  FROM principals
  WHERE principal_kind = 'NHI'
    AND principal_type = 'user'

  UNION ALL
  SELECT
    'nhi_display_name_missing_or_id_only',
    'FAIL',
    principal_id,
    concat('source_id=', source_principal_id, ', display_name=', coalesce(display_name, 'NULL'))
  FROM principals
  WHERE principal_kind = 'NHI'
    AND (
      display_name IS NULL
      OR trim(display_name) = ''
      OR lower(trim(display_name)) = lower(trim(source_principal_id))
    )

  UNION ALL
  SELECT
    'terminated_hi_missing_termination_date',
    'FAIL',
    principal_id,
    concat('source_id=', source_principal_id, ', status=', status)
  FROM principals
  WHERE principal_kind = 'HI'
    AND status = 'terminated'
    AND termination_date IS NULL

  UNION ALL
  SELECT
    'non_terminated_hi_has_past_termination_date',
    'WARN',
    principal_id,
    concat('source_id=', source_principal_id, ', status=', status, ', termination_date=', cast(termination_date AS string))
  FROM principals
  WHERE principal_kind = 'HI'
    AND status <> 'terminated'
    AND termination_date IS NOT NULL
    AND termination_date <= current_date()

  UNION ALL
  SELECT
    'duplicate_hi_email',
    'FAIL',
    lower(trim(email)),
    concat('principal_count=', cast(COUNT(DISTINCT principal_id) AS string))
  FROM principals
  WHERE principal_kind = 'HI'
    AND email IS NOT NULL
    AND trim(email) <> ''
  GROUP BY lower(trim(email))
  HAVING COUNT(DISTINCT principal_id) > 1

  UNION ALL
  SELECT
    'principal_display_contains_hash_like_value',
    'WARN',
    principal_id,
    concat('display_name=', display_name)
  FROM principals
  WHERE display_name RLIKE '^[a-f0-9]{32,}$'
     OR display_name RLIKE '^sha256'

  -- Source coverage and source-specific human consistency
  UNION ALL
  SELECT
    'identity_lifecycle_user_missing_silver_hi',
    'FAIL',
    i.source_id,
    concat('display_name=', coalesce(i.display_name, 'NULL'))
  FROM identity_users i
  LEFT JOIN principals p
    ON p.source_system = 'identity_seed'
   AND p.source_principal_id = i.source_id
   AND p.principal_kind = 'HI'
  WHERE p.principal_id IS NULL

  UNION ALL
  SELECT
    'github_owner_missing_identity_lifecycle',
    'FAIL',
    g.owner_email,
    concat('app_id=', g.app_id, ', owner_status=', coalesce(g.owner_employment_status, 'NULL'))
  FROM github_apps g
  LEFT JOIN identity_users i
    ON lower(trim(g.owner_email)) = lower(trim(i.source_id))
  WHERE g.owner_email IS NOT NULL
    AND i.source_id IS NULL

  UNION ALL
  SELECT
    'github_owner_silver_status_mismatch',
    'FAIL',
    g.app_id,
    concat(
      'owner=', g.owner_email,
      ', bronze_status=', coalesce(g.owner_employment_status, 'NULL'),
      ', silver_status=', coalesce(owner.status, 'NULL')
    )
  FROM github_apps g
  LEFT JOIN principals owner
    ON owner.source_system = 'identity_seed'
   AND owner.source_principal_id = g.owner_email
   AND owner.principal_kind = 'HI'
  WHERE g.owner_email IS NOT NULL
    AND (
      owner.principal_id IS NULL
      OR (
        CASE
          WHEN g.owner_employment_status = 'terminated' THEN 'terminated'
          WHEN g.owner_employment_status IN ('transferred', 'inactive', 'suspended', 'deactivated') THEN 'inactive'
          ELSE 'active'
        END
      ) <> owner.status
    )

  UNION ALL
  SELECT
    'google_user_missing_silver_hi',
    'FAIL',
    gu.user_id,
    concat('email=', coalesce(gu.email, 'NULL'), ', display_name=', coalesce(gu.display_name, 'NULL'))
  FROM google_users gu
  LEFT JOIN principals p
    ON p.source_system = 'identity_seed'
   AND p.source_principal_id = gu.user_id
   AND p.principal_kind = 'HI'
  WHERE p.principal_id IS NULL

  UNION ALL
  SELECT
    'slack_user_missing_silver_hi',
    'FAIL',
    su.user_id,
    concat('email=', coalesce(su.email, 'NULL'), ', display_name=', coalesce(su.display_name, 'NULL'))
  FROM slack_users su
  LEFT JOIN principals p
    ON p.source_system = 'identity_seed'
   AND p.source_principal_id = su.user_id
   AND p.principal_kind = 'HI'
  WHERE p.principal_id IS NULL

  UNION ALL
  SELECT
    'source_human_display_mismatch',
    'WARN',
    h.source_id,
    concat('source_table=', h.source_table, ', source_display=', h.display_name, ', silver_display=', p.display_name)
  FROM all_source_humans h
  JOIN principals p
    ON p.source_system = 'identity_seed'
   AND p.source_principal_id = h.source_id
   AND p.principal_kind = 'HI'
  WHERE h.display_name IS NOT NULL
    AND trim(h.display_name) <> ''
    AND trim(h.display_name) <> trim(p.display_name)

  -- Credential semantics
  UNION ALL
  SELECT
    'credential_bound_principal_not_nhi',
    'FAIL',
    c.credential_id,
    concat('bound_principal_id=', c.bound_principal_id)
  FROM credentials c
  LEFT JOIN principals p
    ON c.bound_principal_id = p.principal_id
   AND p.principal_kind = 'NHI'
  WHERE p.principal_id IS NULL

  UNION ALL
  SELECT
    'credential_active_flag_mismatch',
    'FAIL',
    credential_id,
    concat('status=', status, ', expires_at=', coalesce(cast(expires_at AS string), 'NULL'), ', observed_at=', cast(observed_at AS string))
  FROM credentials
  WHERE is_active <> CASE
    WHEN status = 'active' AND (expires_at IS NULL OR expires_at > observed_at) THEN true
    ELSE false
  END

  UNION ALL
  SELECT
    'credential_active_but_expired',
    'FAIL',
    credential_id,
    concat('status=', status, ', expires_at=', cast(expires_at AS string), ', observed_at=', cast(observed_at AS string))
  FROM credentials
  WHERE is_active = true
    AND expires_at IS NOT NULL
    AND expires_at <= observed_at

  UNION ALL
  SELECT
    'credential_secret_like_display_name',
    'FAIL',
    credential_id,
    concat('display_name=', display_name)
  FROM credentials
  WHERE display_name IS NOT NULL
    AND (
      lower(display_name) LIKE '%secretvalue%'
      OR lower(display_name) LIKE '%privatekey%'
      OR lower(display_name) LIKE '%tokenvalue%'
      OR display_name RLIKE '^[A-Za-z0-9+/]{32,}={0,2}$'
    )

  UNION ALL
  SELECT
    'nhi_without_any_credential',
    'WARN',
    p.principal_id,
    concat('source_id=', p.source_principal_id, ', principal_type=', p.principal_type)
  FROM principals p
  LEFT JOIN credentials c
    ON p.principal_id = c.bound_principal_id
  WHERE p.principal_kind = 'NHI'
  GROUP BY p.principal_id, p.source_principal_id, p.principal_type
  HAVING COUNT(c.credential_id) = 0

  UNION ALL
  SELECT
    'active_nhi_without_active_credential',
    'WARN',
    p.principal_id,
    concat('source_id=', p.source_principal_id, ', principal_type=', p.principal_type)
  FROM principals p
  LEFT JOIN credentials c
    ON p.principal_id = c.bound_principal_id
   AND c.is_active = true
  WHERE p.principal_kind = 'NHI'
    AND p.status = 'active'
  GROUP BY p.principal_id, p.source_principal_id, p.principal_type
  HAVING COUNT(c.credential_id) = 0

  -- Asset semantics and display readiness
  UNION ALL
  SELECT
    'asset_display_name_missing_or_id_only',
    'FAIL',
    asset_id,
    concat('source_asset_id=', source_asset_id, ', display_name=', coalesce(display_name, 'NULL'))
  FROM assets
  WHERE display_name IS NULL
     OR trim(display_name) = ''
     OR lower(trim(display_name)) = lower(trim(source_asset_id))

  UNION ALL
  SELECT
    'asset_display_contains_hash_like_value',
    'WARN',
    asset_id,
    concat('display_name=', display_name)
  FROM assets
  WHERE display_name RLIKE '^[a-f0-9]{32,}$'
     OR display_name RLIKE '^sha256'

  UNION ALL
  SELECT
    'production_asset_unknown_or_low_sensitivity',
    'WARN',
    asset_id,
    concat('asset=', source_asset_id, ', environment=', environment, ', sensitivity=', sensitivity)
  FROM assets
  WHERE environment = 'production'
    AND sensitivity IN ('unknown', 'low')

  UNION ALL
  SELECT
    'sensitive_asset_unknown_environment',
    'WARN',
    asset_id,
    concat('asset=', source_asset_id, ', sensitivity=', sensitivity)
  FROM assets
  WHERE sensitivity IN ('critical', 'high', 'medium')
    AND environment = 'unknown'

  UNION ALL
  SELECT
    'asset_type_source_id_mismatch',
    'WARN',
    asset_id,
    concat('source_asset_id=', source_asset_id, ', asset_type=', asset_type)
  FROM assets
  WHERE (source_asset_id LIKE 'gh-%' AND asset_type <> 'repo')
     OR (source_asset_id LIKE 'gws-%' AND asset_type <> 'workspace')
     OR (source_asset_id LIKE 'slack-%' AND asset_type <> 'saas_app')
     OR (source_asset_id LIKE 'asset-%' AND asset_type <> 'cloud_resource')

  -- Edge and graph semantics
  UNION ALL
  SELECT
    'owner_edge_not_hi_to_nhi',
    'FAIL',
    edge_id,
    concat('owner=', coalesce(owner_source_principal_id, 'NULL'), ', owned=', coalesce(owned_source_principal_id, 'NULL'))
  FROM owner_edges
  WHERE owner_principal_id IS NULL
     OR owned_principal_id IS NULL
     OR owned_principal_kind <> 'NHI'

  UNION ALL
  SELECT
    'owner_edge_to_non_app_or_nhi_type',
    'WARN',
    edge_id,
    concat('owned_type=', coalesce(owned_principal_type, 'NULL'), ', owned=', coalesce(owned_source_principal_id, 'NULL'))
  FROM owner_edges
  WHERE owned_principal_type NOT IN ('app_registration', 'github_app', 'service_principal')

  UNION ALL
  SELECT
    'owner_edge_status_not_active',
    'FAIL',
    e.edge_id,
    concat('status=', e.status)
  FROM edges e
  WHERE e.relationship = 'owns_principal'
    AND e.status <> 'active'

  UNION ALL
  SELECT
    'access_edge_missing_endpoint',
    'FAIL',
    edge_id,
    concat('from_type=', from_type, ', to_type=', to_type, ', from_id=', from_id, ', to_id=', to_id)
  FROM access_edges
  WHERE (from_type = 'principal' AND from_principal_kind IS NULL)
     OR (from_type = 'credential' AND from_credential_type IS NULL)
     OR asset_type IS NULL

  UNION ALL
  SELECT
    'access_edge_missing_permission',
    'FAIL',
    edge_id,
    concat('source=', evidence_source, ', from=', from_source_principal_id, ', asset=', source_asset_id)
  FROM access_edges
  WHERE permission IS NULL OR trim(permission) = ''

  UNION ALL
  SELECT
    'access_edge_missing_last_used_at',
    'WARN',
    edge_id,
    concat('source=', evidence_source, ', from=', coalesce(from_source_principal_id, from_id), ', asset=', source_asset_id)
  FROM access_edges
  WHERE status = 'active'
    AND last_used_at IS NULL

  UNION ALL
  SELECT
    'access_edge_last_used_in_future',
    'FAIL',
    edge_id,
    concat('last_used_at=', cast(last_used_at AS string), ', observed_at=', cast(observed_at AS string))
  FROM access_edges
  WHERE last_used_at IS NOT NULL
    AND last_used_at > observed_at

  UNION ALL
  SELECT
    'non_access_edge_has_access_metadata',
    'FAIL',
    edge_id,
    concat('relationship=', relationship, ', permission=', coalesce(permission, 'NULL'), ', last_used_at=', coalesce(cast(last_used_at AS string), 'NULL'))
  FROM edges
  WHERE relationship <> 'accesses_asset'
    AND (
      (permission IS NOT NULL AND trim(permission) <> '')
      OR last_used_at IS NOT NULL
    )

  UNION ALL
  SELECT
    'credential_edge_bound_principal_mismatch',
    'FAIL',
    e.edge_id,
    concat('edge_from=', e.from_id, ', credential_bound=', c.bound_principal_id)
  FROM edges e
  JOIN credentials c
    ON e.to_type = 'credential'
   AND e.to_id = c.credential_id
  WHERE e.relationship IN ('owns_credential', 'manages_credential', 'accesses_credential')
    AND e.from_id <> c.bound_principal_id

  UNION ALL
  SELECT
    'active_access_from_inactive_nhi',
    'WARN',
    edge_id,
    concat('principal=', from_source_principal_id, ', status=', from_principal_status, ', asset=', source_asset_id)
  FROM access_edges
  WHERE from_type = 'principal'
    AND from_principal_kind = 'NHI'
    AND status = 'active'
    AND from_principal_status <> 'active'

  UNION ALL
  SELECT
    'active_access_from_inactive_credential',
    'WARN',
    edge_id,
    concat('credential_status=', from_credential_status, ', credential_active=', cast(from_credential_is_active AS string), ', asset=', source_asset_id)
  FROM access_edges
  WHERE from_type = 'credential'
    AND status = 'active'
    AND coalesce(from_credential_is_active, false) = false

  UNION ALL
  SELECT
    'duplicate_semantic_edge',
    'FAIL',
    concat(from_id, ':', relationship, ':', to_id),
    concat('edge_count=', cast(COUNT(*) AS string))
  FROM edges
  GROUP BY from_id, relationship, to_id
  HAVING COUNT(*) > 1

  -- Eval and residual-access semantic consistency
  UNION ALL
  SELECT
    'eval_case_subject_missing_silver',
    'FAIL',
    g.case_id,
    concat('subject_type=', g.subject_type, ', subject_id=', g.subject_id)
  FROM eval_cases g
  LEFT JOIN principals p
    ON g.subject_id = p.source_principal_id
   AND (
     (g.subject_type = 'nhi' AND p.principal_kind = 'NHI')
     OR (g.subject_type = 'hi' AND p.principal_kind = 'HI')
   )
  WHERE p.principal_id IS NULL

  UNION ALL
  SELECT
    'eval_case_asset_missing_silver',
    'FAIL',
    g.case_id,
    concat('asset_id=', g.asset_id)
  FROM eval_cases g
  LEFT JOIN assets a
    ON g.asset_id = a.source_asset_id
  WHERE a.asset_id IS NULL

  UNION ALL
  SELECT
    'eval_expected_severity_asset_mismatch',
    'FAIL',
    g.case_id,
    concat('expected=', coalesce(g.expected_severity, 'NULL'), ', silver_sensitivity=', coalesce(a.sensitivity, 'NULL'))
  FROM eval_cases g
  JOIN assets a
    ON g.asset_id = a.source_asset_id
  WHERE g.expected_severity IS NOT NULL
    AND upper(a.sensitivity) <> g.expected_severity

  UNION ALL
  SELECT
    'positive_eval_missing_terminated_owner',
    'FAIL',
    g.case_id,
    concat('subject_id=', g.subject_id, ', asset_id=', g.asset_id)
  FROM eval_cases g
  JOIN principals subject
    ON g.subject_id = subject.source_principal_id
   AND g.subject_type = 'nhi'
   AND subject.principal_kind = 'NHI'
  LEFT JOIN owner_edges oe
    ON oe.owned_principal_id = subject.principal_id
   AND oe.owner_status = 'terminated'
  WHERE g.is_planted_risk = true
    AND g.drift_type = 'nhi_residual_access'
    AND oe.edge_id IS NULL

  UNION ALL
  SELECT
    'positive_eval_missing_active_credential',
    'FAIL',
    g.case_id,
    concat('subject_id=', g.subject_id)
  FROM eval_cases g
  JOIN principals subject
    ON g.subject_id = subject.source_principal_id
   AND g.subject_type = 'nhi'
   AND subject.principal_kind = 'NHI'
  LEFT JOIN credentials c
    ON c.bound_principal_id = subject.principal_id
   AND c.is_active = true
  WHERE g.is_planted_risk = true
    AND g.drift_type = 'nhi_residual_access'
    AND c.credential_id IS NULL

  UNION ALL
  SELECT
    'positive_eval_missing_active_access_edge',
    'FAIL',
    g.case_id,
    concat('subject_id=', g.subject_id, ', asset_id=', g.asset_id)
  FROM eval_cases g
  JOIN principals subject
    ON g.subject_id = subject.source_principal_id
   AND g.subject_type = 'nhi'
   AND subject.principal_kind = 'NHI'
  JOIN assets asset
    ON g.asset_id = asset.source_asset_id
  LEFT JOIN edges e
    ON e.from_id = subject.principal_id
   AND e.to_id = asset.asset_id
   AND e.relationship = 'accesses_asset'
   AND e.status = 'active'
  WHERE g.is_planted_risk = true
    AND g.drift_type = 'nhi_residual_access'
    AND e.edge_id IS NULL

  UNION ALL
  SELECT
    'positive_eval_asset_not_sensitive',
    'FAIL',
    g.case_id,
    concat('asset_id=', g.asset_id, ', sensitivity=', coalesce(a.sensitivity, 'NULL'))
  FROM eval_cases g
  JOIN assets a
    ON g.asset_id = a.source_asset_id
  WHERE g.is_planted_risk = true
    AND g.drift_type = 'nhi_residual_access'
    AND a.sensitivity NOT IN ('critical', 'high', 'medium')

  UNION ALL
  SELECT
    'non_positive_eval_matches_full_positive_graph',
    'FAIL',
    g.case_id,
    concat('subject_id=', g.subject_id, ', asset_id=', g.asset_id)
  FROM eval_cases g
  JOIN positive_graph pg
    ON g.subject_id = pg.subject_id
   AND g.asset_id = pg.asset_id
  WHERE g.drift_type = 'nhi_residual_access'
    AND g.is_planted_risk = false

  UNION ALL
  SELECT
    'silver_positive_candidate_missing_eval_case',
    'WARN',
    concat(pg.subject_id, ':', pg.asset_id),
    concat('owner=', pg.owner_id, ', sensitivity=', pg.sensitivity)
  FROM positive_graph pg
  LEFT JOIN eval_cases g
    ON g.subject_id = pg.subject_id
   AND g.asset_id = pg.asset_id
   AND g.drift_type = 'nhi_residual_access'
  WHERE g.case_id IS NULL

  -- Risk Card / Access Path display readiness
  UNION ALL
  SELECT
    'access_path_owner_not_display_ready',
    'FAIL',
    edge_id,
    concat('owner=', coalesce(owner_source_principal_id, 'NULL'), ', display=', coalesce(owner_display_name, 'NULL'))
  FROM owner_edges
  WHERE owner_display_name IS NULL
     OR trim(owner_display_name) = ''
     OR owner_display_name LIKE '%@%.%'
     OR lower(trim(owner_display_name)) = lower(trim(owner_source_principal_id))

  UNION ALL
  SELECT
    'access_path_subject_not_display_ready',
    'FAIL',
    edge_id,
    concat('subject=', coalesce(owned_source_principal_id, 'NULL'), ', display=', coalesce(owned_display_name, 'NULL'))
  FROM owner_edges
  WHERE owned_display_name IS NULL
     OR trim(owned_display_name) = ''
     OR lower(trim(owned_display_name)) = lower(trim(owned_source_principal_id))

  UNION ALL
  SELECT
    'access_path_asset_not_display_ready',
    'FAIL',
    edge_id,
    concat('asset=', coalesce(source_asset_id, 'NULL'), ', display=', coalesce(asset_display_name, 'NULL'))
  FROM access_edges
  WHERE asset_display_name IS NULL
     OR trim(asset_display_name) = ''
     OR lower(trim(asset_display_name)) = lower(trim(source_asset_id))

  UNION ALL
  SELECT
    'access_path_active_access_missing_permission',
    'FAIL',
    edge_id,
    concat('subject=', coalesce(from_source_principal_id, from_id), ', asset=', coalesce(source_asset_id, to_id))
  FROM access_edges
  WHERE status = 'active'
    AND (permission IS NULL OR trim(permission) = '')
)
SELECT
  check_name,
  severity,
  COUNT(*) AS violation_count,
  concat_ws(' | ', slice(sort_array(collect_list(object_key)), 1, 10)) AS sample_keys
FROM violations
GROUP BY check_name, severity
ORDER BY
  CASE severity WHEN 'FAIL' THEN 0 ELSE 1 END,
  violation_count DESC,
  check_name;
