# Schema Consistency Review

## 목적

PoC 파이프라인의 계약 문서, DDL, notebook 변환 로직, seed 데이터가 서로 같은 필드와 ID 규칙을 쓰는지 확인한다.

## 검토 범위

- `docs/contracts/bronze-schema.md`
- `docs/contracts/silver-schema.md`
- `docs/contracts/eval-schema.md`
- `sql/databricks/migrations/001_create_bronze_tables.sql`
- `sql/databricks/migrations/002_create_silver_tables.sql`
- `sql/databricks/migrations/003_create_eval_tables.sql`
- `notebooks/02_ingest.py`
- `notebooks/03_silver.py`
- `notebooks/04_eval_seed.py`
- `data/poc/landing/raw/**`
- `data/poc/eval/ground_truth_case.jsonl`

## 검토 결과

| 영역 | 비교 대상 | 결과 | 메모 |
| --- | --- | --- | --- |
| Bronze | Bronze 계약, Bronze DDL, `data/poc/landing/raw/**`, `02_ingest.py` | PASS | PoC raw 샘플 필드명과 Bronze 적재 컬럼이 일치한다. |
| Silver | Silver 계약, Silver DDL, `03_silver.py` | PASS | `principal_id`, `source_principal_id`, `asset_id`, `source_asset_id`, `relationship` 값이 계약과 맞는다. |
| Eval | Eval 계약, Eval DDL, `ground_truth_case.jsonl`, `04_eval_seed.py` | PASS | eval key `(subject_type, subject_id, asset_id, drift_type)`와 적재 컬럼이 일치한다. |

## 항목별 대조

### Bronze 계약 vs `001_create_bronze_tables.sql`

| 계약 항목 | DDL 컬럼 또는 테이블 | 결과 | 확인 내용 |
| --- | --- | --- | --- |
| `bronze_azure_applications` | `bronze_azure_applications` | PASS | `app_id`, `display_name`, `created_at`가 DDL에 모두 존재한다. |
| `bronze_azure_application_owners` | `bronze_azure_application_owners` | PASS | `app_id`, `user_principal_name`가 DDL에 존재한다. |
| `bronze_azure_password_credentials` | `bronze_azure_password_credentials` | PASS | `app_id`, `key_id`, `display_name`, `end_date_time`, `status`가 DDL에 존재한다. |
| `bronze_identity_lifecycle_seed` | `bronze_identity_lifecycle_seed` | PASS | `user_principal_name`, `employment_status`, `termination_date`가 DDL에 존재한다. |
| `bronze_assets_seed` | `bronze_assets_seed` | PASS | `asset_id`, `name`, `environment`, `sensitivity`가 DDL에 존재한다. |
| `bronze_access_edges_seed` | `bronze_access_edges_seed` | PASS | `principal_id`, `asset_id`, `relationship`, `permission`, `status`가 DDL에 존재한다. |

### raw seed JSONL vs Bronze DDL

| Seed 파일 | JSONL 원본 필드 | Bronze 적재 컬럼 | 결과 | 확인 내용 |
| --- | --- | --- | --- | --- |
| `azure/applications.jsonl` | `appId`, `displayName`, `createdDateTime` | `app_id`, `display_name`, `created_at` | PASS | `02_ingest.py`가 camelCase 원본을 Bronze 컬럼으로 변환한다. |
| `azure/application_owners.jsonl` | `appId`, `userPrincipalName` | `app_id`, `user_principal_name` | PASS | 소유자 관계 원본이 그대로 적재 가능하다. |
| `azure/password_credentials.jsonl` | `appId`, `keyId`, `displayName`, `endDateTime`, `status` | `app_id`, `key_id`, `display_name`, `end_date_time`, `status` | PASS | secret value 없이 metadata만 적재한다. |
| `identity/lifecycle_seed.jsonl` | `userPrincipalName`, `employmentStatus`, `terminationDate` | `user_principal_name`, `employment_status`, `termination_date` | PASS | 퇴사/재직 상태 seed가 Bronze 컬럼과 맞는다. |
| `assets/assets_seed.jsonl` | `assetId`, `name`, `environment`, `sensitivity` | `asset_id`, `name`, `environment`, `sensitivity` | PASS | asset seed와 Bronze DDL의 명칭이 일치한다. |
| `access/access_edges_seed.jsonl` | `principalId`, `assetId`, `relationship`, `permission`, `status` | `principal_id`, `asset_id`, `relationship`, `permission`, `status` | PASS | access edge seed가 Bronze 관계 테이블에 그대로 들어간다. |

### Silver 계약 vs `002_create_silver_tables.sql`

| 계약 항목 | DDL 컬럼 | 결과 | 확인 내용 |
| --- | --- | --- | --- |
| `silver_principals` | `principal_id`, `source_system`, `source_principal_id`, `principal_kind`, `principal_type`, `display_name`, `email`, `status`, `termination_date`, `observed_at` | PASS | 계약 컬럼과 동일하다. |
| `silver_credentials` | `credential_id`, `source_system`, `source_credential_id`, `bound_principal_id`, `credential_type`, `display_name`, `status`, `expires_at`, `is_active`, `observed_at` | PASS | 계약 컬럼과 동일하다. |
| `silver_assets` | `asset_id`, `source_system`, `source_asset_id`, `asset_type`, `display_name`, `environment`, `sensitivity`, `observed_at` | PASS | 계약 컬럼과 동일하다. |
| `silver_edges` | `edge_id`, `source_system`, `from_id`, `from_type`, `to_id`, `to_type`, `relationship`, `permission`, `status`, `evidence_source`, `observed_at` | PASS | 계약 컬럼과 동일하다. |

### `03_silver.py` vs Silver 계약

| notebook 동작 | 계약 항목 | 결과 | 확인 내용 |
| --- | --- | --- | --- |
| `silver_id(F.lit("azure_ad"), F.col("app_id"), F.lit("app_registration"))` | `principal_id`, `source_principal_id`, `principal_type` | PASS | source id와 principal type을 이용해 deterministic id를 만든다. |
| `principal_kind = "NHI"` / `"HI"` | `principal_kind` | PASS | App Registration은 `NHI`, lifecycle seed user는 `HI`로 생성한다. |
| `source_principal_id = app_id` 또는 `user_principal_name` | `source_principal_id` | PASS | Bronze 원본 id를 Silver source id로 유지한다. |
| `credential_id`와 `bound_principal_id` 생성 | `credential_id`, `bound_principal_id` | PASS | credential은 동일 principal 기준으로 묶인다. |
| `asset_id = silver_id(..., asset_id, "cloud_resource")` | `asset_id`, `asset_type` | PASS | asset은 `cloud_resource`로 정규화된다. |
| `relationship = "accesses_asset"` / `"owns_principal"` | `relationship` | PASS | 계약의 허용 관계 값과 일치한다. |
| `from_type`, `to_type`를 `principal`/`asset`으로 지정 | `from_type`, `to_type` | PASS | 관계 방향이 계약의 매트릭스와 일치한다. |

### Eval 계약 vs `003_create_eval_tables.sql`

| 계약 항목 | DDL 컬럼 | 결과 | 확인 내용 |
| --- | --- | --- | --- |
| `ground_truth_case` PK | `case_id` | PASS | surrogate id를 PK로 둔다. |
| eval key 구성 | `subject_type`, `subject_id`, `asset_id`, `drift_type` | PASS | 문서의 조인 키와 DDL 컬럼이 일치한다. |
| 라벨 컬럼 | `is_planted_risk`, `is_distractor`, `pattern`, `expected_severity`, `label_reason` | PASS | 정답/평가용 필드가 문서와 일치한다. |
| 시간 컬럼 | `created_at` | PASS | eval 생성 시각 컬럼이 존재한다. |

### `ground_truth_case.jsonl` vs `04_eval_seed.py`

| seed 필드 | notebook 적재 컬럼 | 결과 | 확인 내용 |
| --- | --- | --- | --- |
| `case_id` | `case_id` | PASS | surrogate key를 그대로 적재한다. |
| `scenario_id`, `scenario_family` | `scenario_id`, `scenario_family` | PASS | holdout/패밀리 분리용 필드를 유지한다. |
| `subject_type`, `subject_id`, `asset_id`, `drift_type` | `subject_type`, `subject_id`, `asset_id`, `drift_type` | PASS | eval key가 그대로 유지된다. |
| `is_planted_risk`, `is_distractor` | `is_planted_risk`, `is_distractor` | PASS | 정답 라벨이 raw/Bronze/Silver로 섞이지 않는다. |
| `pattern`, `expected_severity`, `label_reason`, `created_at` | `pattern`, `expected_severity`, `label_reason`, `created_at` | PASS | 부가 라벨과 생성 시각이 일치한다. |

## 확인한 정정 사항

- Bronze 계약의 논리 Landing 경로와 현재 저장소의 PoC 샘플 경로를 구분해 해석해야 한다.
- Silver 예시의 `evidence_source` 값을 실제 브론즈 테이블명 `bronze_azure_applications`로 맞췄다.

## 참고

- `03_silver.py`는 `principal_kind`, `principal_type`, `relationship` 값을 계약 문서에 정의된 범위 안에서 생성한다.
- `04_eval_seed.py`는 `ground_truth_case.jsonl`을 `access_drift.eval.ground_truth_case`에 적재하고, `subject_id`를 Silver의 `source_principal_id`와 매칭 가능하게 유지한다.

## 확인하지 못한 점

- Databricks 런타임에서 notebook을 실제 실행한 검증은 수행하지 않았다.
- 이번 검토는 정적 대조를 기준으로 했고, 런타임 전처리/권한/배포 설정은 별도 확인이 필요하다.
