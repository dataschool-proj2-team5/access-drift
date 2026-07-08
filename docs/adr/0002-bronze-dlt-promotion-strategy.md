# ADR-0002: Bronze DLT 승격과 ingest 전환 전략

- **Status**: Proposed
- **Date**: 2026-06-30
- **Deciders**: DE team (PR review 예정)

## Context

현재 `access_drift_dev.bronze`의 6개 Bronze 테이블은
`sql/databricks/migrations/001_create_bronze_tables.sql`이 정의하고
`notebooks/02_ingest.ipynb`가 dev raw JSONL을 읽어 `overwrite`하는 Unity Catalog
managed Delta table이다. `access-drift-pipeline`의 `silver_task`는 이 notebook 기반
`ingest_task`가 끝난 뒤 실행된다.

PR #61은 동일한 6개 출력을 만드는 DLT expectation 코드를
`notebooks/08_bronze_dlt_expectations.py`에 추가했다. 이 코드는 격리된
`access_drift_dev.dlt_test`에서 valid, invalid, empty-source fixture를 검증했지만
정식 `bronze` schema에는 적용하지 않았다. 이 ADR은 이슈 #63의 범위에 따라
기존 Bronze를 변경하지 않고 승격 가능성, 전환 조건, rollback 기준을 정리한다.

### 현재 구현의 역할 차이

| 구분 | Migration | Notebook ingest | DLT pipeline |
| --- | --- | --- | --- |
| 파일 | `001_create_bronze_tables.sql` | `02_ingest.ipynb` | `08_bronze_dlt_expectations.py` |
| 역할 | 일반 Delta table과 `NOT NULL` 계약 생성 | raw를 읽어 6개 table을 overwrite | raw를 읽어 6개 materialized view를 refresh하고 expectation 기록 |
| orchestration | `migration_task` | `ingest_task` | 별도 `bronze-dlt-expectations` pipeline |
| 현재 target | `access_drift_dev.bronze` | `access_drift_dev.bronze` | `access_drift_dev.dlt_test` |
| 실패 정보 | DDL 실행 실패 | notebook assertion과 task log | update/flow 상태와 event log expectation metric |

Migration은 테이블이 없을 때 일반 Delta table을 만들고 notebook은 같은 이름의
테이블을 다시 쓴다. 반면 DLT는 dataset 정의와 lifecycle을 pipeline이 소유한다.
따라서 같은 이름과 schema를 설정하는 것만으로 기존 테이블을 안전하게 인계할 수
있다고 볼 수 없다.

### Databricks 확인 결과

2026-06-30에 다음을 확인했다.

- 기존 Bronze 6개는 `MANAGED` / `DELTA`이며 owner는
  `workspace-user@example.com`이다.
- `dlt_test`의 6개 출력은 `MATERIALIZED_VIEW`이며 owner는
  `pipeline-owner@example.com`, `pipelines.pipelineId`는
  `138f43e1-2028-4043-9a42-4c7822afb30a`다.
- `fixture_mode=false`와
  `abfss://lakehouse@acdriftadls.dfs.core.windows.net/raw/dev`를 사용한 격리
  full refresh가 update `739e826b-4f1c-4142-b9c9-c76153eaed11`로 성공했다.
- 6개 출력은 각각 20건이었다. 필수 metadata null, checksum 불일치,
  Silver 준비 key null, 관찰용 logical key 중복 group은 모두 0건이었다.
- source path는 6개 모두 `raw/dev` 아래 실제 입력 URI였으며 대표 business field,
  timestamp/date 변환 결과가 기존 Bronze 계약과 일치했다.
- 기존 Bronze 6개도 각각 20건이었다. DLT dev 출력과 같은 business key를 직접
  조회한 결과 source path와 아래 대표 값이 모두 일치했다.

  | 테이블 | 비교한 sample |
  | --- | --- |
  | applications | `d8f4a5b6-7c8d-4e91-9f02-1a2b3c4d5e6f`, `sp-crm-customer-export-prod`, `2026-03-15T09:00:00Z` |
  | application owners | `d8f4a5b6-7c8d-4e91-9f02-1a2b3c4d5e6f`, `kim.minsu@company.com` |
  | password credentials | `d8f4a5b6-7c8d-4e91-9f02-1a2b3c4d5e6f`, `c0ffee12-3456-7890-abcd-1234567890ab`, `2027-12-31T00:00:00Z`, `active` |
  | lifecycle | `kim.minsu@company.com`, `terminated`, `2026-06-10` |
  | assets | `asset-customer-export-storage-prod`, `production`, `critical` |
  | access edges | `d8f4a5b6-7c8d-4e91-9f02-1a2b3c4d5e6f`, `asset-customer-export-storage-prod`, `read/list`, `active`, `2026-06-27T09:00:00Z` |

  기존 Bronze count/sample 확인 SQL statement ID는
  `01f1746d-23d1-1d06-b924-2843049e8547`이다.
- event log에서 6개 flow가 `COMPLETED`였고 모든 expectation의
  `failed_records`가 0이었다.
- 컬럼명, 순서, Spark type은 기존 Bronze와 같았다. 다만 계약상 `NOT NULL`인
  `_src_system`, `_src_object`, `_ingestion_ts`, `_raw_payload`,
  `_schema_version`이 DLT materialized view metadata에서는 nullable로 등록됐다.
- 기존 Bronze 6개는 검증 직전 별도 writer 실행으로 version 10이 됐으며 최신
  Delta history timestamp는 `09:55:46Z`~`09:56:06Z`였다. DLT update는
  `09:56:43Z` 이후 시작했으므로 이번 DLT 검증이 기존 Bronze를 변경하지 않았다.
- 검증 후 기본 valid fixture 설정으로 복구했고 update
  `21854b99-4aee-4d8e-9c41-be29cb9fd978`에서 6개 출력이 각각 1건,
  expectation 실패가 0건임을 확인했다.
- dev raw 정합성, expectation, schema 비교, 복구 결과의 SQL statement ID는 각각
  `01f1746a-483a-1084-bab4-749d36e64541`,
  `01f1746a-7ad5-13d3-bc0a-b4afaef918bd`,
  `01f1746a-a4c9-13a3-b7ef-0cc2c30d363a`,
  `01f1746b-17ca-1a8d-9a91-134f4fb6bd57`이다.
- `databricks bundle validate -t dlt-test`는 성공했다. 다만
  `/Workspace/Shared/access-drift-dlt-test`가 모든 workspace 사용자에게 writable인
  기존 경고는 남아 있다.

Databricks의 table 이동 절차는 pipeline이 관리하는 materialized view 또는
streaming table을 다른 pipeline으로 옮기는 경우를 대상으로 한다. 일반 managed
Delta table을 pipeline dataset으로 직접 채택하는 절차는 확인하지 못했다. 또한
pipeline update는 pipeline owner identity로 실행되므로 현재의 서로 다른 owner를
그대로 둔 승격은 운영 주체와 권한이 불명확하다.

참고:

- [Move tables between pipelines - Azure Databricks](https://learn.microsoft.com/en-us/azure/databricks/ldp/move-table)
- [Manage identities, permissions, and privileges for pipelines - Azure Databricks](https://learn.microsoft.com/en-us/azure/databricks/ldp/privileges)
- [Use Unity Catalog with pipelines - Azure Databricks](https://learn.microsoft.com/en-us/azure/databricks/ldp/unity-catalog)

## Decision

현재 DLT 코드를 정식 `access_drift_dev.bronze` pipeline으로 승격하지 않는다.
기존 `02_ingest.ipynb`와 `ingest_task`를 정식 Bronze 적재 경로로 유지하고,
`bronze-dlt-expectations`는 `dlt_test`의 격리 검증 경로로 유지한다.

이 결정은 DLT를 포기하는 것이 아니라 다음 blocker가 해소될 때까지 실제 cutover를
보류하는 결정이다.

1. DLT output metadata의 required column nullable 차이를 계약과 일치시키거나,
   expectation 보장만으로 충분하다는 계약 변경을 승인한다.
2. 일반 managed Delta table과 같은 이름의 materialized view가 충돌하는 조건을
   비파괴적인 별도 검증 환경에서 재현하고, 지원되는 migration 절차를 확정한다.
3. 기존 Bronze data와 grants를 보존할 backup 위치, 보존 기간, 복구 명령을
   승인한다.
4. 개인 사용자가 아닌 service principal 등 pipeline owner와 필요한 UC 권한을
   확정한다.
5. full refresh 비용과 실패 시 재실행 범위를 확인한다.
6. notebook writer와 DLT writer가 동시에 실행되지 않도록 단일 writer cutover
   순서와 승인자를 정한다.

### 파일 위치 제안

현재 이슈에서는 파일을 이동하지 않는다. 실제 승격 PR에서는 notebook 이름을 유지한
채 경로만 바꾸는 대신 `pipelines/bronze_dlt.py`로 옮겨 pipeline source임을 분명히
한다. 현재 저장소에는 `pipelines/` 디렉터리가 없으므로 이 경로는 승격이 승인된 PR에서
Bundle sync 설정과 함께 추가한다. fixture 준비 코드는 검증 전용이므로 현재 위치에
남긴다.

### Bundle 구조 제안

승격 전에는 현재 구조를 유지한다.

```text
access-drift-pipeline
  migration_task -> generate_dev_seed_task -> synthetic_data_task
                  -> ingest_task -> silver_task

bronze-dlt-expectations (dlt-test target only)
  dlt_test materialized views + dlt_test event log
```

승격이 승인되면 기존 job 안에서 `ingest_task`를 `pipeline_task` 기반
`bronze_dlt_task`로 교체하고 `silver_task`가 이 task에 의존하도록 한다. notebook과
DLT를 같은 Bronze table의 병행 writer로 두지 않는다. pipeline resource, event log,
raw path, fixture mode를 명시적으로 분리하고 dev target에서 먼저 적용한다.

```text
access-drift-pipeline (dev)
  migration_task -> generate_dev_seed_task -> synthetic_data_task
                  -> bronze_dlt_task -> silver_task
                                    |
                                    +-> bronze event log
```

`migration_task`가 일반 Bronze table을 먼저 만드는 현재 DDL도 함께 조정해야 한다.
DLT가 소유할 dataset을 migration이 선점하지 않도록 table lifecycle의 단일 owner를
정하되, 구체적인 DDL 변경은 migration과 rollback 방식이 승인된 승격 PR에서 다룬다.

### 판단 기준

선택지는 아래 기준을 순서대로 적용해 비교한다. 편의성이나 코드 중복 감소보다 데이터
안전성과 복구 가능성을 우선한다.

1. 기존 Bronze를 삭제, rename, overwrite하지 않고 검증할 수 있어야 한다.
2. 정식 Bronze table에는 한 시점에 하나의 writer만 있어야 한다.
3. row 값뿐 아니라 column type, nullability, table type, owner와 grants가 계약에
   맞아야 한다.
4. Bronze 성공 또는 실패가 `silver_task` 실행 여부에 명확히 반영돼야 한다.
5. 전환 전에 backup과 restore를 실제로 rehearsal할 수 있어야 한다.
6. 운영 경로와 검증 경로를 이름, target, event log에서 구분할 수 있어야 한다.

### ingest 전환 선택지 비교

| 선택지 | 정식 Bronze writer | DLT의 위치 | 장점 | 주요 위험과 비용 | 판단 |
| --- | --- | --- | --- | --- | --- |
| **유지** | `02_ingest.ipynb` | `dlt_test`의 격리 검증 도구 | 현재 Delta table 계약과 `ingest_task -> silver_task` DAG를 바꾸지 않는다. 기존 Bronze에 대한 migration이나 rollback 작업 없이 DLT 결과를 계속 비교할 수 있다. | 정식 ingest에는 expectation이 적용되지 않는다. notebook과 DLT 변환 로직이 중복되고, DLT 검증을 실행할 때 추가 비용이 든다. | **현재 선택.** 정식 경로는 유지하되 DLT 검증 자산은 버리지 않는다. |
| **병행** | Notebook과 DLT 모두 사용 | 같은 `bronze` 또는 별도 production target | 두 구현 결과를 장기간 비교하고 전환 시점을 늦출 수 있다. | 같은 target이면 일반 Delta table과 materialized view가 충돌하고 두 writer가 경쟁한다. target을 나누면 공식 Bronze가 둘이 되어 Silver 입력, grants, 장애 대응과 재실행 기준이 모호해진다. | 채택하지 않음. 비교는 `dlt_test`에서 하되 두 경로를 모두 정식 writer로 운영하지 않는다. |
| **대체** | DLT만 사용 | `access_drift_dev.bronze` | expectation과 event log가 정식 ingest gate가 된다. writer와 변환 구현이 하나로 줄고, Bronze 실패가 Silver 실행을 차단하도록 DAG를 연결할 수 있다. | table type, nullability, owner, DDL migration, backup과 restore가 모두 확정돼야 한다. 기존 table lifecycle을 바꾸므로 준비 없이 진행하면 원복을 보장하기 어렵다. | 현재 보류, **향후 목표**. 승격 조건을 모두 충족한 별도 PR에서 단계적으로 전환한다. |

### 유지 선택 근거

현재는 **유지**를 선택한다. 여기서 유지는 DLT 코드를 폐기한다는 뜻이 아니다.
`02_ingest.ipynb`와 `ingest_task`를 정식 Bronze writer로 유지하고, DLT는
`dlt_test`에서 contract와 expectation을 확인하는 shadow 검증 도구로 둔다는 뜻이다.

첫째, DLT의 기능 가능성은 충분히 확인했다. `fixture_mode=false`와 dev raw 실행에서
6개 출력이 각각 20건 생성됐고, 기존 Bronze와 동일 business key의 source path와 대표
값이 일치했다. expectation 실패도 0건이었다. 따라서 유지를 선택하는 이유는 DLT가
데이터를 만들지 못해서가 아니다.

둘째, 정식 target 전환 조건은 아직 충족되지 않았다. 기존 Bronze는 `MANAGED DELTA`,
DLT 출력은 `MATERIALIZED_VIEW`이고, 계약상 `NOT NULL`인 공통 5개 컬럼이 DLT metadata에서는
nullable이다. 기존 table owner와 DLT output owner도 다르다. 데이터 값이 같다는 사실만으로
table lifecycle과 권한까지 같은 것으로 볼 수 없다.

셋째, 유지는 현재 시점에서 rollback 위험이 가장 작다. 정식 writer를 바꾸지 않으므로
기존 Bronze table을 삭제, rename, overwrite하거나 backup에서 복구할 상황을 만들지 않는다.
동시에 PR #61의 valid/invalid/empty-source expectation과 이번 dev raw 결과를 향후 승격의
비교 기준으로 계속 사용할 수 있다.

### 병행을 선택하지 않는 이유

병행은 두 가지 방식이 있지만 둘 다 정식 운영안으로 적합하지 않다.

- 같은 `bronze` table을 notebook과 DLT가 함께 쓰면 notebook의 overwrite와 DLT의
  materialized view lifecycle이 경쟁한다. 어느 실행이 최종 상태를 만들었는지 보장하기
  어렵고, object type 자체도 다르므로 안전한 비교 방법이 아니다.
- target을 나눠 notebook Bronze와 DLT Bronze를 둘 다 정식 운영하면 writer 충돌은
  피할 수 있지만 공식 Bronze가 두 개가 된다. `silver_task`가 어느 쪽을 읽을지,
  두 결과가 다를 때 무엇을 정답으로 볼지, 어느 경로부터 재실행할지 별도 정책이
  필요하다. 비용과 권한, event log, 모니터링도 이중으로 관리해야 한다.

따라서 병행은 정식 경로를 둘로 운영하는 방식으로 사용하지 않는다. 현재의
`bronze`와 `dlt_test` 동시 존재는 운영 병행이 아니라, notebook만 정식 writer인 상태에서
DLT 결과를 비교하는 제한된 shadow 검증이다.

### 대체를 지금 선택하지 않는 이유와 향후 조건

대체는 장기적으로 가장 단순한 운영 구조다. DLT만 Bronze를 쓰고 기존 job의
`ingest_task`를 `bronze_dlt_task`로 바꾸면 writer, expectation, event log와 downstream
의존성을 한 경로에 둘 수 있다. 하지만 지금 즉시 대체하면 기능 검증보다 table migration
위험이 더 크다.

다음 조건을 모두 충족하면 유지 결정을 다시 검토하고 **대체**로 전환한다.

1. required column nullability를 기존 계약과 일치시키거나 계약 변경을 승인한다.
2. 일반 managed Delta table과 같은 이름의 materialized view 전환 절차를 별도 환경에서
   비파괴적으로 검증한다.
3. 기존 data, table grants와 owner를 보존하는 backup/restore rehearsal을 완료한다.
4. service principal 등 정식 pipeline owner와 UC 권한을 확정한다.
5. `bronze_dlt_task -> silver_task` 실패 전파와 부분 재실행 기준을 검증한다.
6. 리뷰어가 기존 writer 중지와 DLT writer 시작 시점을 승인한다.

대체 시에도 notebook과 DLT를 일정 기간 같은 table의 writer로 두지 않는다. candidate
target 검증을 마친 뒤 승인된 시점에 writer를 한 번 전환하고, 문제가 생기면 사전에
rehearsal한 backup과 notebook 경로로 복구한다.

### Bundle orchestration 선택지 비교

| Bundle 구성 | 장점 | 단점 | 판단 |
| --- | --- | --- | --- |
| DLT pipeline을 기존 job과 독립 실행 | 현재 `dlt-test`처럼 기존 DAG를 바꾸지 않고 검증할 수 있다. | 운영에 사용하면 pipeline 성공과 `silver_task` 시작 사이의 순서와 실패 전파가 자동 보장되지 않는다. | 검증 단계에만 사용한다. |
| 기존 job의 `ingest_task`를 `pipeline_task`로 교체 | `synthetic_data_task -> bronze_dlt_task -> silver_task` 의존성이 한 DAG에 남고 Bronze 실패 시 Silver가 시작되지 않는다. | 기존 DDL과 table lifecycle을 함께 바꿔야 하며 dev/poc target별 resource 구성이 필요하다. | 실제 승격 시 선호한다. |
| 별도 DLT job이 기존 downstream job을 호출 | pipeline과 downstream 배포를 분리할 수 있다. | job 간 run ID와 재실행 지점이 나뉘고, 현재 규모에서는 권한과 모니터링 복잡도만 늘어난다. | 현재 요구에는 과도하므로 채택하지 않는다. |

즉, 현재의 독립 pipeline은 검증 격리를 위한 구조이지 최종 운영 구조가 아니다. 실제
승격에서는 기존 job 안의 `pipeline_task`로 연결해 Bronze 품질 실패 시 `silver_task`
실행이 차단되도록 하는 안을 우선한다.

### 최소 cutover 및 rollback 기준

향후 승격 PR은 다음 순서로 진행한다.

1. notebook과 DLT schedule을 중지하고 진행 중인 실행이 없는지 확인한다.
2. 기존 6개 table의 ID, type, owner, grants, schema, Delta version, row count와
   대표 sample을 기록한다.
3. 승인된 backup 위치에 기존 table data와 grants를 보존하고 실제 restore를
   rehearsal한다.
4. 별도 candidate target에서 dev raw, `fixture_mode=false` full refresh를 실행해
   schema, row count, sample, null, duplicate, type/format, expectation을 비교한다.
5. 리뷰어 승인 후 한 번에 하나의 writer만 남기고 DLT dataset lifecycle로
   전환한다.
6. `bronze_dlt_task -> silver_task` 전체 경로를 실행해 Bronze/Silver 정합성을
   확인한다.

아래 중 하나가 발생하면 downstream 실행을 중단하고 notebook 경로와 backup을
이용해 기존 Delta version으로 복구한다.

- dataset 생성 또는 ownership 전환 실패
- 계약 column/type/nullability 불일치
- source row 누락, 의도하지 않은 drop 또는 checksum/field mapping 불일치
- Silver required key 또는 참조 정합성 악화
- pipeline 실패 후 재실행 기준이 불명확한 상태

## Consequences

### 장점

- 기존 Bronze와 downstream Silver를 손상시키지 않고 PR #61 코드를 dev raw로
  검증했다.
- table type, nullability, ownership이라는 실제 전환 blocker를 명시했다.
- notebook과 DLT를 동시에 정식 writer로 두지 않는 기준이 생겼다.
- 승격 PR이 갖춰야 할 데이터 검증, 승인, rollback 조건을 재사용할 수 있다.

### 단점

- 당분간 정식 Bronze ingest에는 DLT expectation이 적용되지 않는다.
- `02_ingest.ipynb`와 DLT 코드의 변환 로직이 중복된 상태가 유지된다.
- full refresh 비용, service principal ownership, 실제 migration/restore rehearsal은
  후속 작업으로 남는다.

### 확인하지 못한 항목

- 일반 managed Delta table을 동일 이름의 pipeline materialized view로 바꾸는
  Databricks 지원 절차와 실제 오류 payload
- DLT required column을 UC metadata에서도 `NOT NULL`로 유지할 수 있는 방식
- approved backup schema/location과 보존 기간
- service principal run-as 및 grants
- 증분 refresh와 장기 운영 비용

이 항목들은 기존 Bronze를 삭제, rename, overwrite하지 않는 이슈 #63의 범위에서는
안전하게 검증할 수 없으므로 승격 전 후속 이슈에서 다룬다.
