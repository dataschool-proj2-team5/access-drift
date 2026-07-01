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
- `notebooks/02_ingest.ipynb`
- `notebooks/03_silver.ipynb`
- `notebooks/04_eval_seed.ipynb`
- `data/poc/landing/raw/**`
- `data/poc/eval/ground_truth_case.jsonl`

## 검토 결과

| 영역 | 비교 대상 | 결과 | 메모 |
| --- | --- | --- | --- |
| Bronze | Bronze 계약, Bronze DDL, `data/poc/landing/raw/**`, `02_ingest.ipynb` | PASS | raw 필드명과 Bronze 적재 컬럼이 일치한다. |
| Silver | Silver 계약, Silver DDL, `03_silver.ipynb` | PASS | `principal_id`, `source_principal_id`, `asset_id`, `source_asset_id`, `relationship` 값이 계약과 맞는다. |
| Silver key 품질 | Bronze nullable key, Silver required key, `03_silver.ipynb` | REVIEW REQUIRED | Bronze business key는 nullable이므로 Silver 변환 전후 null key 품질검증이 필요하다. |
| Eval | Eval 계약, Eval DDL, `ground_truth_case.jsonl`, `04_eval_seed.ipynb` | PASS | eval key `(subject_type, subject_id, asset_id, drift_type)`와 적재 컬럼이 일치한다. |

## 항목별 대조

### Bronze 계약 vs `001_create_bronze_tables.sql`

| 계약 항목 | DDL 컬럼 또는 테이블 | 결과 | 확인 내용 |
| --- | --- | --- | --- |
| `bronze_azure_applications` | `bronze_azure_applications` | PASS | `app_id`, `display_name`, `created_at`가 DDL에 모두 존재한다. |
| `bronze_azure_application_owners` | `bronze_azure_application_owners` | PASS | `app_id`, `user_principal_name`가 DDL에 존재한다. |
| `bronze_azure_password_credentials` | `bronze_azure_password_credentials` | PASS | `app_id`, `key_id`, `display_name`, `end_date_time`, `status`가 DDL에 존재한다. |
| `bronze_identity_lifecycle_seed` | `bronze_identity_lifecycle_seed` | PASS | `user_principal_name`, `display_name`, `employment_status`, `termination_date`가 DDL에 존재한다. |
| `bronze_assets_seed` | `bronze_assets_seed` | PASS | `asset_id`, `name`, `environment`, `sensitivity`가 DDL에 존재한다. |
| `bronze_access_edges_seed` | `bronze_access_edges_seed` | PASS | `principal_id`, `asset_id`, `relationship`, `permission`, `status`, `last_used_at`가 DDL에 존재한다. |

### raw seed JSONL vs Bronze DDL

| Seed 파일 | JSONL 원본 필드 | Bronze 적재 컬럼 | 결과 | 확인 내용 |
| --- | --- | --- | --- | --- |
| `azure/applications.jsonl` | `appId`, `displayName`, `createdDateTime` | `app_id`, `display_name`, `created_at` | PASS | `02_ingest.ipynb`가 camelCase 원본을 Bronze 컬럼으로 변환한다. |
| `azure/application_owners.jsonl` | `appId`, `userPrincipalName` | `app_id`, `user_principal_name` | PASS | 소유자 관계 원본이 그대로 적재 가능하다. |
| `azure/password_credentials.jsonl` | `appId`, `keyId`, `displayName`, `endDateTime`, `status` | `app_id`, `key_id`, `display_name`, `end_date_time`, `status` | PASS | secret value 없이 metadata만 적재한다. |
| `identity/lifecycle_seed.jsonl` | `userPrincipalName`, `displayName`, `employmentStatus`, `terminationDate` | `user_principal_name`, `display_name`, `employment_status`, `termination_date` | PASS | 사용자 식별자, 표시 이름, 퇴사/재직 상태 seed가 Bronze 컬럼과 맞는다. |
| `assets/assets_seed.jsonl` | `assetId`, `name`, `environment`, `sensitivity` | `asset_id`, `name`, `environment`, `sensitivity` | PASS | asset seed와 Bronze DDL의 명칭이 일치한다. |
| `access/access_edges_seed.jsonl` | `principalId`, `assetId`, `relationship`, `permission`, `status`, optional `lastUsedDateTime` / `last_used_at` | `principal_id`, `asset_id`, `relationship`, `permission`, `status`, `last_used_at` | PASS | access edge seed가 Bronze 관계 테이블에 들어간다. 마지막 사용 시각은 있으면 보존하고 없으면 null로 둔다. |

### Silver 계약 vs `002_create_silver_tables.sql`

| 계약 항목 | DDL 컬럼 | 결과 | 확인 내용 |
| --- | --- | --- | --- |
| `silver_principals` | `principal_id`, `source_system`, `source_principal_id`, `principal_kind`, `principal_type`, `display_name`, `email`, `status`, `termination_date`, `observed_at` | PASS | 계약 컬럼과 동일하다. |
| `silver_credentials` | `credential_id`, `source_system`, `source_credential_id`, `bound_principal_id`, `credential_type`, `display_name`, `status`, `expires_at`, `is_active`, `observed_at` | PASS | 계약 컬럼과 동일하다. |
| `silver_assets` | `asset_id`, `source_system`, `source_asset_id`, `asset_type`, `display_name`, `environment`, `sensitivity`, `observed_at` | PASS | 계약 컬럼과 동일하다. |
| `silver_edges` | `edge_id`, `source_system`, `from_id`, `from_type`, `to_id`, `to_type`, `relationship`, `permission`, `status`, `evidence_source`, `observed_at` | PASS | 계약 컬럼과 동일하다. |

### `03_silver.ipynb` vs Silver 계약

| notebook 동작 | 계약 항목 | 결과 | 확인 내용 |
| --- | --- | --- | --- |
| `silver_id(F.lit("entra_id"), F.col("app_id"), F.lit("app_registration"))` | `principal_id`, `source_principal_id`, `principal_type` | PASS | source id와 principal type을 이용해 deterministic id를 만든다. |
| `principal_kind = "NHI"` / `"HI"` | `principal_kind` | PASS | App Registration은 `NHI`, lifecycle seed user는 `HI`로 생성한다. |
| `source_system`은 `entra_id`, `identity_seed`, `assets_seed`, `access_seed` 사용 | `source_system` | PASS | 계약의 허용 source system 값과 일치한다. |
| `source_principal_id = app_id` 또는 `user_principal_name` | `source_principal_id` | PASS | Bronze 원본 id를 Silver source id로 유지한다. |
| `credential_id`와 `bound_principal_id` 생성 | `credential_id`, `bound_principal_id` | PASS | credential은 동일 principal 기준으로 묶인다. |
| `asset_id = silver_id(..., asset_id, "cloud_resource")` | `asset_id`, `asset_type` | PASS | asset은 `cloud_resource`로 정규화된다. |
| `relationship = "accesses_asset"` / `"owns_principal"` | `relationship` | PASS | 계약의 허용 관계 값과 일치한다. |
| `from_type`, `to_type`를 `principal`/`asset`으로 지정 | `from_type`, `to_type` | PASS | 관계 방향이 계약의 매트릭스와 일치한다. |

### Silver required key 품질검증 필요 항목

Bronze는 source 원본 보존을 위해 business key를 nullable로 허용한다. Silver는 조인과 추적에 필요한 key를 required로 사용하므로, 변환 전후에 아래 품질검증을 수행해야 한다.

| 검증 대상 | 예시 조건 | 필요 이유 |
| --- | --- | --- |
| principal 원본 key | `app_id IS NOT NULL`, `user_principal_name IS NOT NULL` | null source key가 deterministic id 충돌이나 잘못된 principal 생성으로 이어질 수 있다. |
| credential 원본 key | `key_id IS NOT NULL`, `app_id IS NOT NULL` | credential id와 `bound_principal_id` 생성에 필요하다. |
| asset 원본 key | `asset_id IS NOT NULL` | asset id 생성과 access edge 조인에 필요하다. |
| access edge 원본 key | `principal_id IS NOT NULL`, `asset_id IS NOT NULL`, `relationship IS NOT NULL` | edge id와 경로 탐지에 필요하다. |

### Bronze → Silver Transform validation

컬럼 계약 검증과 변환 검증은 아래처럼 구분한다.

| 구분 | 확인 대상 | 실패 의미 |
| --- | --- | --- |
| 컬럼 계약 검증 | 한 테이블 안에서 null, logical unique, enum, 타입/포맷, 금지 필드 조건을 만족하는지 | 해당 Bronze 또는 Silver 테이블의 schema contract 위반 |
| 변환 검증 | 계약을 만족하거나 변환에 필요한 key를 가진 Bronze row가 의도한 Silver row와 관계로 만들어지는지 | Bronze 입력 준비 또는 Bronze → Silver 변환 로직 문제 |

아래 기준은 특정 구현 도구에 종속되지 않는 불변조건이다. 후속 DDL 제약, DLT expectation, notebook smoke test, 수동 SQL 검증, PR 체크리스트는 같은 조건을 사용한다.

#### Source table → Silver table 매핑

변환에 필요한 key가 있는 각 Bronze row는 아래 대상 Silver 테이블에서 추적 가능해야 한다.

| Bronze 입력 | Silver 결과 | 검증 불변조건 | 실패 시 우선 확인 |
| --- | --- | --- | --- |
| `bronze_azure_applications` | `silver_principals` | `app_id`가 `source_principal_id`로 보존된 `principal_kind = 'NHI'`, `principal_type = 'app_registration'` row가 존재한다. | Bronze `app_id` null 여부 → principal 변환 로직 |
| `bronze_identity_lifecycle_seed` | `silver_principals` | `user_principal_name`이 `source_principal_id`로 보존된 `principal_kind = 'HI'`, `principal_type = 'user'` row가 존재하고, `display_name`은 Bronze 표시 이름을 우선 사용한다. | Bronze `user_principal_name` / `display_name` null 여부 → principal 변환 로직 |
| `bronze_azure_password_credentials` | `silver_credentials` | `key_id`가 `source_credential_id`로 보존되고 `app_id`로 만든 principal에 연결된 row가 존재한다. | Bronze `key_id`/`app_id` null 여부 → credential 변환 로직 |
| `bronze_assets_seed` | `silver_assets` | Bronze `asset_id`가 `source_asset_id`로 보존된 row가 존재한다. | Bronze `asset_id` null 여부 → asset 변환 로직 |
| `bronze_azure_application_owners` | `silver_edges` | human principal에서 NHI principal로 향하는 `owns_principal` edge가 존재한다. | Bronze owner key null 여부 → owner edge 변환 로직 |
| `bronze_access_edges_seed` | `silver_edges` | NHI principal에서 asset으로 향하는 `accesses_asset` edge가 존재한다. | Bronze edge key/relationship 여부 → access edge 변환 로직 |

#### 변환별 검증 기준

| 검증 항목 | 입력과 기대 결과 | 검증 불변조건 | 실패 분류와 우선 확인 레이어 |
| --- | --- | --- | --- |
| source ID 보존 | Bronze `app_id`, `user_principal_name`, `key_id`, `asset_id` → 각 Silver `source_*` | Silver `source_*` 값이 대응 Bronze source ID와 동일하며 내부 deterministic ID로 치환되지 않는다. | 값이 Bronze에서 이미 다르면 Bronze 컬럼 계약, Bronze가 정상인데 Silver가 다르면 변환 로직 |
| deterministic ID 재현성 | 같은 source system, source ID, type 또는 정규화된 관계 조합 → 같은 Silver ID | ID 생성 규칙으로 재계산한 값과 저장 ID가 같고, 같은 입력을 재실행해도 값이 바뀌지 않으며 테이블의 primary ID는 logical unique다. access edge의 `edge_id`는 Silver 정규화 후 relationship 기준으로 재계산한다. | 입력 조합이 null이면 Bronze 변환 준비, 재계산 값이 다르면 변환 로직, 중복 ID row는 Silver 컬럼 계약 |
| owner edge 방향 | application owner + application → `silver_edges` | `from_id`는 `identity_seed` human principal, `from_type = 'principal'`, `to_id`는 `entra_id` NHI principal, `to_type = 'principal'`, `relationship = 'owns_principal'`이다. | endpoint가 없으면 principal 선행 변환, 방향/relationship이 다르면 owner edge 변환 로직 |
| access edge 방향 | Bronze principal + asset access → `silver_edges` | `from_id`는 NHI principal, `from_type = 'principal'`, `to_id`는 asset, `to_type = 'asset'`, `relationship = 'accesses_asset'`이며 두 endpoint가 Silver에 존재한다. | endpoint source key가 null이면 Bronze 변환 준비, endpoint가 없으면 principal/asset 변환, 방향이 다르면 access edge 변환 로직 |
| credential 연결 | Bronze password credential의 `app_id` → `bound_principal_id` | `bound_principal_id`가 같은 `app_id`로 만든 `silver_principals.principal_id`와 같고 실제 principal row가 존재한다. | principal이 없으면 principal 선행 변환, ID가 다르면 credential 변환 로직, dangling reference는 Silver 컬럼 계약 |
| active/expired 판정 | Bronze `status`, `end_date_time`, `_ingestion_ts` → Silver `status`, `expires_at`, `observed_at`, `is_active` | `observed_at = _ingestion_ts`, `expires_at = end_date_time`이며 `is_active = (status == 'active') AND (expires_at IS NULL OR expires_at > observed_at)`이다. | Bronze 시간 파싱이 잘못되면 Bronze 컬럼 계약, 입력이 정상인데 계산 결과가 다르면 credential 변환 로직 |
| eval key 매칭 | Eval `subject_id`, `asset_id` → Silver source ID | Eval `subject_id`는 `silver_principals.source_principal_id`, Eval `asset_id`는 `silver_assets.source_asset_id`와 매칭되며 내부 ID와 직접 비교하지 않는다. | Silver source ID가 유실됐으면 변환 로직, source ID가 정상인데 매칭되지 않으면 eval seed/계약 |

Bronze business key가 null인 것은 현재 Bronze schema contract 위반이 아닐 수 있다. 그러나 그 key가 Silver required 컬럼 또는 deterministic ID에 필요하면 해당 row는 변환 준비 실패다. 이 경우 Bronze 계약을 임의로 강화하지 않고 null row의 처리 정책을 `확인 필요`로 기록한다.

### Eval 계약 vs `003_create_eval_tables.sql`

| 계약 항목 | DDL 컬럼 | 결과 | 확인 내용 |
| --- | --- | --- | --- |
| `ground_truth_case` PK | `case_id` | PASS | surrogate id를 PK로 둔다. |
| eval key 구성 | `subject_type`, `subject_id`, `asset_id`, `drift_type` | PASS | 문서의 조인 키와 DDL 컬럼이 일치한다. |
| 라벨 컬럼 | `is_planted_risk`, `is_distractor`, `pattern`, `expected_severity`, `seed_finding_type`, `label_reason` | PASS | 정답/평가용 필드와 합성 데이터 생성 의도 라벨이 문서와 일치한다. |
| 시간 컬럼 | `created_at` | PASS | eval 생성 시각 컬럼이 존재한다. |

### `ground_truth_case.jsonl` vs `04_eval_seed.ipynb`

| seed 필드 | notebook 적재 컬럼 | 결과 | 확인 내용 |
| --- | --- | --- | --- |
| `case_id` | `case_id` | PASS | surrogate key를 그대로 적재한다. |
| `scenario_id`, `scenario_family` | `scenario_id`, `scenario_family` | PASS | holdout/패밀리 분리용 필드를 유지한다. |
| `subject_type`, `subject_id`, `asset_id`, `drift_type` | `subject_type`, `subject_id`, `asset_id`, `drift_type` | PASS | eval key가 그대로 유지된다. |
| `is_planted_risk`, `is_distractor` | `is_planted_risk`, `is_distractor` | PASS | 정답 라벨이 raw/Bronze/Silver로 섞이지 않는다. |
| `pattern`, `expected_severity`, `seed_finding_type`, `label_reason`, `created_at` | `pattern`, `expected_severity`, `seed_finding_type`, `label_reason`, `created_at` | PASS | 부가 라벨, 생성 의도 라벨, 생성 시각이 일치한다. |

## 확인한 정정 사항

- Bronze 계약의 Landing 경로를 `data/{poc|dev}/landing/raw/...` 기준으로 맞췄다.
- Silver 예시의 `evidence_source` 값을 실제 브론즈 테이블명 `bronze_azure_applications`로 맞췄다.

## 참고

- `03_silver.ipynb`는 `principal_kind`, `principal_type`, `relationship` 값을 계약 문서에 정의된 범위 안에서 생성한다.
- `04_eval_seed.ipynb`는 `ground_truth_case.jsonl`을 `access_drift.eval.ground_truth_case`에 적재하고, `subject_id`를 Silver의 `source_principal_id`와 매칭 가능하게 유지한다.

## 확인하지 못한 점

- Databricks 런타임에서 notebook을 실제 실행한 검증은 수행하지 않았다.
- 이번 검토는 정적 대조를 기준으로 했고, 런타임 전처리/권한/배포 설정은 별도 확인이 필요하다.
