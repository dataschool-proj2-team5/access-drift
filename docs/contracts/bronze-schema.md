# Bronze Schema Contract

## 버전

```text
version: 0.1.1
status: draft
updated_at: 2026-06-30
```

## 변경이력

| 버전 | 날짜 | 변경 내용 |
| --- | --- | --- |
| 0.1.1 | 2026-06-30 | 컬럼별 품질검증 기준과 미확정 정책 표시 추가 |
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

Bronze의 source business 컬럼은 원본 보존을 위해 nullable로 둔다. 따라서 optional 컬럼의 null 자체는 계약 위반이 아니다. 다만 Silver required key로 쓰이는 값이 null이면 Bronze 컬럼 계약과 별개로 변환 준비 실패로 분류한다.

Bronze row는 재수집과 재실행으로 같은 source record가 여러 번 나타날 수 있으므로, 아래에서 별도로 명시하지 않은 컬럼에는 전역 unique를 요구하지 않는다. snapshot 또는 run 안에서의 중복 허용 기준은 아직 확정되지 않았으므로 `확인 필요`다.

| 컬럼 | 타입 | 필수 | 설명 | Validation |
| --- | --- | --- | --- | --- |
| `_src_system` | string | yes | source system 이름 | null 또는 빈 문자열이면 실패. 현재 테이블별 값은 `entra_id`, `identity_seed`, `assets_seed`, `access_seed` 중 하나이며 `_src_object`와 일치해야 한다. |
| `_src_object` | string | yes | source object 종류 | null 또는 빈 문자열이면 실패. 현재 값은 `applications`, `application_owners`, `password_credentials`, `lifecycle_seed`, `assets_seed`, `access_edges_seed` 중 하나이며 대상 Bronze 테이블과 일치해야 한다. |
| `_src_file_path` | string | no | landing 파일 경로 | 값이 있으면 ingest의 `raw_base`로부터 실제 읽은 입력 URI를 그대로 보존해야 한다. repo seed 경로와 `abfss://.../raw/{poc\|dev}/...` 경로를 임의로 상호 변환하지 않는다. 경로 정규화 방식은 `확인 필요`. |
| `_ingestion_ts` | timestamp | yes | Bronze 적재 시각 | null이면 실패. Databricks `timestamp`로 저장되어야 한다. 허용 timezone과 미래 시각 허용 범위는 `확인 필요`. |
| `_run_id` | string | no | pipeline run id | 값이 있으면 같은 실행에서 일관되어야 한다. 포맷과 unique 범위는 `확인 필요`. |
| `_batch_id` | string | no | batch id | 값이 있으면 같은 batch에서 일관되어야 한다. 포맷과 unique 범위는 `확인 필요`. |
| `_checksum` | string | no | raw payload checksum | 값이 있으면 `md5(_raw_payload)`로 다시 계산한 값과 일치해야 한다. 같은 payload는 같은 checksum이어야 하며 checksum 자체는 unique가 아니다. |
| `_raw_payload` | string | yes | 파싱된 source 필드의 JSON payload | null 또는 빈 문자열이면 실패. JSON object로 파싱 가능하고 Spark가 읽은 source 필드와 값이 보존되어야 한다. 원본 파일의 byte-level 문자열 동일성은 보장하지 않는다. |
| `_schema_version` | string | yes | Bronze row schema version | null 또는 빈 문자열이면 실패. 현재 ingest가 기록하는 `0.1.0`이어야 한다. 이 값은 문서 상단의 계약 문서 버전과 별개이며, 향후 허용 version 목록과 전환 기준은 `확인 필요`. |

## bronze_azure_applications

Azure application 또는 App Registration 원본을 보존한다.

| 컬럼 | 타입 | 필수 | 설명 | Validation |
| --- | --- | --- | --- | --- |
| `app_id` | string | no | source application id | 값이 있으면 Landing `appId`와 동일해야 한다. 전역 unique는 요구하지 않으며 snapshot/run 단위 중복 허용 기준은 `확인 필요`. |
| `display_name` | string | no | application 표시 이름 | 값이 있으면 Landing `displayName`을 의미 변경 없이 보존해야 한다. |
| `created_at` | timestamp | no | application 생성 시각 | Landing `createdDateTime`이 있으면 timestamp 변환에 성공하고 같은 시점을 나타내야 한다. 파싱 실패로 null이 된 row는 실패다. |

예시:

```json
{
  "_src_system": "entra_id",
  "_src_object": "applications",
  "_ingestion_ts": "2026-06-23T00:00:00Z",
  "_raw_payload": "{\"appId\":\"a1b2c3d4-1234-5678-abcd-ef0123456789\",\"displayName\":\"payment-service-prod\",\"createdDateTime\":\"2022-03-10T09:00:00Z\"}",
  "_schema_version": "0.1.0",
  "app_id": "a1b2c3d4-1234-5678-abcd-ef0123456789",
  "display_name": "payment-service-prod",
  "created_at": "2022-03-10T09:00:00Z"
}
```

## bronze_azure_application_owners

Application과 owner 관계 원본을 보존한다.

| 컬럼 | 타입 | 필수 | 설명 | Validation |
| --- | --- | --- | --- | --- |
| `app_id` | string | no | source application id | 값이 있으면 Landing `appId`와 동일해야 한다. 단일 컬럼 unique는 요구하지 않는다. |
| `user_principal_name` | string | no | owner UPN 또는 email | 값이 있으면 Landing `userPrincipalName`과 동일해야 한다. `(app_id, user_principal_name)` 중복 허용 기준은 `확인 필요`. |

## bronze_azure_password_credentials

Application에 연결된 credential metadata 원본을 보존한다.

Secret value, token value, private key value는 저장하지 않는다.

| 컬럼 | 타입 | 필수 | 설명 | Validation |
| --- | --- | --- | --- | --- |
| `app_id` | string | no | source application id | 값이 있으면 Landing `appId`와 동일해야 한다. 단일 컬럼 unique는 요구하지 않는다. |
| `key_id` | string | no | source credential id | 값이 있으면 Landing `keyId`와 동일해야 한다. `(app_id, key_id)`의 snapshot/run 단위 중복 허용 기준은 `확인 필요`. |
| `display_name` | string | no | credential 표시 이름 | 값이 있으면 Landing `displayName`을 의미 변경 없이 보존해야 한다. |
| `end_date_time` | timestamp | no | credential 만료 시각 | Landing `endDateTime`이 있으면 timestamp 변환에 성공하고 같은 시점을 나타내야 한다. 파싱 실패로 null이 된 row는 실패다. |
| `status` | string | no | source credential 상태 | source 값을 보존해야 한다. Bronze에서 허용할 source enum은 `확인 필요`이며 Silver enum을 Bronze에 강제하지 않는다. |

## bronze_identity_lifecycle_seed

사용자 lifecycle seed 원본을 보존한다.

| 컬럼 | 타입 | 필수 | 설명 | Validation |
| --- | --- | --- | --- | --- |
| `user_principal_name` | string | no | 사용자 UPN 또는 email | 값이 있으면 Landing `userPrincipalName`과 동일해야 한다. snapshot/run 단위 unique 기준은 `확인 필요`. |
| `display_name` | string | no | 사용자 표시 이름 | 값이 있으면 Landing `displayName`을 의미 변경 없이 보존해야 한다. |
| `employment_status` | string | no | 고용 또는 offboarding 상태 | Landing `employmentStatus`를 보존해야 한다. Bronze에서 허용할 source enum은 `확인 필요`. |
| `termination_date` | date | no | 퇴사일 | Landing `terminationDate`가 있으면 date 변환에 성공하고 같은 날짜를 나타내야 한다. 파싱 실패로 null이 된 row는 실패다. |

## bronze_assets_seed

Asset seed 원본을 보존한다.

| 컬럼 | 타입 | 필수 | 설명 | Validation |
| --- | --- | --- | --- | --- |
| `asset_id` | string | no | source asset id | 값이 있으면 Landing `assetId`와 동일해야 한다. snapshot/run 단위 unique 기준은 `확인 필요`. |
| `name` | string | no | asset 이름 | 값이 있으면 Landing `name`을 의미 변경 없이 보존해야 한다. |
| `environment` | string | no | asset 환경 | source 값을 보존해야 한다. Bronze에서 허용할 source enum은 `확인 필요`이며 Silver enum을 Bronze에 강제하지 않는다. |
| `sensitivity` | string | no | asset 민감도 | source 값을 보존해야 한다. Bronze에서 허용할 source enum은 `확인 필요`이며 Silver enum을 Bronze에 강제하지 않는다. |

## bronze_access_edges_seed

Access edge seed 원본을 보존한다.

| 컬럼 | 타입 | 필수 | 설명 | Validation |
| --- | --- | --- | --- | --- |
| `principal_id` | string | no | source principal id | 값이 있으면 Landing `principalId`와 동일해야 한다. 단일 컬럼 unique는 요구하지 않는다. |
| `asset_id` | string | no | source asset id | 값이 있으면 Landing `assetId`와 동일해야 한다. 단일 컬럼 unique는 요구하지 않는다. |
| `relationship` | string | no | 관계 유형 | source 값을 보존해야 한다. Silver 변환이 지원하는 값인지 별도로 검증하며 Bronze 허용 enum은 `확인 필요`. |
| `permission` | string | no | permission 또는 role | 값이 있으면 Landing 값을 의미 변경 없이 보존해야 한다. |
| `status` | string | no | 관계 상태 | source 값을 보존해야 한다. Bronze에서 허용할 source enum은 `확인 필요`. |
| `last_used_at` | timestamp | no | 접근 관계의 마지막 사용 시각. 합성 입력에서는 source-like 보강 필드로 둘 수 있다. | Landing `lastUsedDateTime` 또는 `last_used_at`이 있으면 timestamp 변환에 성공하고 같은 시점을 나타내야 한다. 입력에 없을 때만 null을 허용한다. |

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

검증 시 구조화 컬럼뿐 아니라 `_raw_payload`에도 위 정답 라벨과 secret, token, private key의 실제 값이 포함되지 않았는지 확인한다. 필드명 탐지 범위와 마스킹 판정 방식은 `확인 필요`다.

## DDL

Databricks Bronze DDL은 아래 파일에 둔다.

```text
sql/databricks/migrations/001_create_bronze_tables.sql
```
