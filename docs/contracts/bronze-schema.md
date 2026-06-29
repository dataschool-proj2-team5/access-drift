# Bronze Schema Contract

## 버전

```text
version: 0.1.0
status: draft
updated_at: 2026-06-24
```

## 변경이력

| 버전 | 날짜 | 변경 내용 |
| --- | --- | --- |
| 0.1.0 | 2026-06-24 | source 단위 landing JSONL 기준 Bronze 계약 초안 추가 |

## 목적

Bronze는 Landing에 도착한 source 입력을 원본 데이터로 보존하는 레이어다.

Bronze에서는 source별 구조를 허용한다. 이 단계에서는 위험 점수, severity, finding, 권장 조치, 화면 표시용 문구를 만들지 않는다.

## Landing 입력

Landing 입력은 source/API/export 응답 형태에 가깝게 분리된 JSONL 파일이다.

```text
data/{poc|dev}/landing/raw/azure/applications.jsonl
data/{poc|dev}/landing/raw/azure/application_owners.jsonl
data/{poc|dev}/landing/raw/azure/password_credentials.jsonl
data/{poc|dev}/landing/raw/identity/lifecycle_seed.jsonl
data/{poc|dev}/landing/raw/assets/assets_seed.jsonl
data/{poc|dev}/landing/raw/access/access_edges_seed.jsonl
```

## 공통 컬럼

모든 Bronze 테이블은 원본 추적을 위해 아래 컬럼을 가진다.

| 컬럼 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `_src_system` | string | yes | source system 이름 |
| `_src_object` | string | yes | source object 종류 |
| `_src_file_path` | string | no | landing 파일 경로 |
| `_ingestion_ts` | timestamp | yes | Bronze 적재 시각 |
| `_run_id` | string | no | pipeline run id |
| `_batch_id` | string | no | batch id |
| `_checksum` | string | no | raw payload checksum |
| `_raw_payload` | string | yes | 원본 JSON payload |
| `_schema_version` | string | yes | Bronze schema version |

## bronze_azure_applications

Azure application 또는 App Registration 원본을 보존한다.

| 컬럼 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `app_id` | string | no | source application id |
| `display_name` | string | no | application 표시 이름 |
| `created_at` | timestamp | no | application 생성 시각 |

예시:

```json
{
  "_src_system": "azure",
  "_src_object": "applications",
  "_raw_payload": "{\"appId\":\"a1b2c3d4-1234-5678-abcd-ef0123456789\",\"displayName\":\"payment-service-prod\",\"createdDateTime\":\"2022-03-10T09:00:00Z\"}",
  "_schema_version": "bronze_azure_applications_v1",
  "app_id": "a1b2c3d4-1234-5678-abcd-ef0123456789",
  "display_name": "payment-service-prod",
  "created_at": "2022-03-10T09:00:00Z"
}
```

## bronze_azure_application_owners

Application과 owner 관계 원본을 보존한다.

| 컬럼 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `app_id` | string | no | source application id |
| `user_principal_name` | string | no | owner UPN 또는 email |

## bronze_azure_password_credentials

Application에 연결된 credential metadata 원본을 보존한다.

Secret value, token value, private key value는 저장하지 않는다.

| 컬럼 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `app_id` | string | no | source application id |
| `key_id` | string | no | source credential id |
| `display_name` | string | no | credential 표시 이름 |
| `end_date_time` | timestamp | no | credential 만료 시각 |
| `status` | string | no | source credential 상태 |

## bronze_identity_lifecycle_seed

사용자 lifecycle seed 원본을 보존한다.

| 컬럼 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `user_principal_name` | string | no | 사용자 UPN 또는 email |
| `employment_status` | string | no | 고용 또는 offboarding 상태 |
| `termination_date` | date | no | 퇴사일 |

## bronze_assets_seed

Asset seed 원본을 보존한다.

| 컬럼 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `asset_id` | string | no | source asset id |
| `name` | string | no | asset 이름 |
| `environment` | string | no | asset 환경 |
| `sensitivity` | string | no | asset 민감도 |

## bronze_access_edges_seed

Access edge seed 원본을 보존한다.

| 컬럼 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `principal_id` | string | no | source principal id |
| `asset_id` | string | no | source asset id |
| `relationship` | string | no | 관계 유형 |
| `permission` | string | no | permission 또는 role |
| `status` | string | no | 관계 상태 |
| `last_used_at` | timestamp | no | 접근 관계의 마지막 사용 시각. 합성 입력에서는 source-like 보강 필드로 둘 수 있다. |

## Bronze에 두지 않는 것

아래 항목은 Bronze에서 생성하지 않는다.

```text
risk_score
severity
finding_id
recommended_action
why_risky
dashboard label
is_planted_risk
is_distractor
expected_severity
truth_class
secret value
token value
private key value
```

## DDL

Databricks Bronze DDL은 아래 파일에 둔다.

```text
sql/databricks/migrations/001_create_bronze_tables.sql
```
