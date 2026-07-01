# Bronze DLT expectation fixture

이 디렉터리는 이슈 #54의 Bronze DLT expectation 검증 전용 fixture다. 공식 dev 합성 데이터인 `data/dev/landing/raw/`와 분리하며, `access_drift_dev.dlt_test` 이외의 schema에 자동 적용하지 않는다.

## 구성

- `valid/landing/raw/`: Bronze 6개 source별 정상 row 1건
- `invalid/landing/raw/`: expectation별 null, 원본 매핑 불일치, 파싱 오류, 금지 필드 예시
- `empty-source/landing/raw/`: `applications.jsonl`만 0건이고 나머지 source는 정상인 입력 부재 예시

정적 fixture 기준 valid는 총 6건, invalid는 총 35건이다. invalid 중 eval label과 secret/token/private-key field가 있는 7건은 drop되고 나머지 28건은 결과에 남으면서 계약 또는 readiness failed count를 기록하는 것이 기대 결과다. 실제 건수는 pipeline event log와 결과 테이블에서 다시 확인한다.

`bronze-dlt-fixture-setup` job은 fixture를 ADLS `raw/dlt-test/{valid|invalid|empty-source}/`에 복사한다. 이 경로는 공식 dev raw인 `raw/dev/`와 분리된다.

invalid fixture의 `_test_case`와 `_test_overrides`는 `bronze.fixture_mode=true`일 때만 테스트 adapter가 읽는다. 두 필드는 Bronze 구조화 컬럼에는 포함되지 않으며, `dlt_test`에서 실패 입력을 추적할 수 있도록 fixture `_raw_payload`에는 남긴다. 실제 dev raw 실행에서는 `bronze.fixture_mode=false`로 설정해 adapter를 비활성화한다.

`check_dlt_expectation_result.py` notebook/job은 새 expectation 기준을 정의하지 않는다. 기존 `08_bronze_dlt_expectations.py`가 생성한 결과 테이블과 event log를 `update_id` 기준으로 조회해 pass/fail/drop 결과만 자동 판정한다.

## 검증 분류

| 분류 | DLT action | 예시 |
| --- | --- | --- |
| Bronze 계약 위반 | `expect_all` | 필수 metadata, source/table 불일치, checksum, raw JSON, timestamp/date 파싱, 원본 매핑 |
| 유입 차단 | `expect_all_or_drop` | eval label, secret/token/private-key top-level field |
| Silver 변환 준비 | `expect_all` | `app_id`, `key_id`, `user_principal_name`, `asset_id`, access edge key null 또는 빈 문자열 |

Bronze 원본 보존을 위해 일반 계약 위반과 nullable business key 위반 row는 drop하지 않는다. eval label과 민감값 field처럼 Bronze에 저장하면 안 되는 row만 차단한다.

## invalid fixture 관점

- 공통 metadata: source system/object, 입력 경로, ingestion timestamp, checksum, raw payload, schema version
- 금지 필드: eval label과 top-level secret/token/private-key 계열 필드명
- source 보존: ID, 표시 이름, 상태, 관계, permission 등 원본과 Bronze 값 불일치
- 파싱: `createdDateTime`, `endDateTime`, `terminationDate`, `lastUsedDateTime`
- Silver 준비 key: 각 source별 ID와 access relationship 누락
- source 입력: 6개 JSONL 중 하나라도 비어 있으면 `bronze_source_input_audit`의 `source_not_empty` expectation으로 pipeline을 실패시킴

## 현재 미구현 기준

- 일반 컬럼에 섞인 secret/token/private-key의 실제 값을 판별할 기준이 없어 값 자체 탐지는 구현하지 않았다.
- 금지 필드 검사는 flat JSON source의 top-level key를 대상으로 한다. nested key와 마스킹 판정 범위는 계약에서 `확인 필요`다.
- `_run_id`, `_batch_id`는 optional이며 DLT 구현에서는 null로 둔다. 실행/batch 단위 포맷과 일관성 정책은 아직 확정되지 않았다.
- source enum, snapshot/run 단위 중복, timezone과 미래 시각 허용 범위, 경로 정규화는 계약에서 `확인 필요`이므로 expectation으로 고정하지 않았다.

## Databricks 검증 결과

2026-06-30에 `access_drift_dev.dlt_test`에서 확인했다.

| 실행 | Update ID | 결과 |
| --- | --- | --- |
| valid | `ea1f8f8e-d2c4-4832-b2f5-8568e66b7d51` | 6개 테이블 각 1건, dropped/warned 0, `source_not_empty` 6건 통과 |
| invalid 최종 | `50ff7e90-ddc6-41d4-89e0-623f326c9997` | 입력 35건 중 금지 필드 7건 drop, 나머지 28건 유지 및 계약/readiness failed count 기록 |
| empty source | `ac166d8c-6223-4e3f-b0f9-28f4026a432c` | `applications.jsonl`의 `source_row_count=0`으로 `source_not_empty` expectation 실패 |
| valid 복구 | `ddcc933b-1986-43c8-a7e5-dcd3d7477fd0` | 성공, 최종 `dlt_test` 결과를 valid 상태로 복구 |

invalid 최종 실행의 테이블별 결과는 다음과 같다.

| 테이블 | output | dropped | warned |
| --- | ---: | ---: | ---: |
| `bronze_azure_applications` | 11 | 7 | 11 |
| `bronze_azure_application_owners` | 3 | 0 | 3 |
| `bronze_azure_password_credentials` | 4 | 0 | 4 |
| `bronze_identity_lifecycle_seed` | 3 | 0 | 3 |
| `bronze_assets_seed` | 2 | 0 | 2 |
| `bronze_access_edges_seed` | 5 | 0 | 5 |

기존 `access_drift_dev.bronze` 6개 테이블은 실행 전후 모두 각각 20건이었고 `information_schema.tables.last_altered` 값도 동일했다. 실제 `bronze` target deploy/run은 수행하지 않았다.
