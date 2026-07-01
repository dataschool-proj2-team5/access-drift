# 실패/재처리 및 멱등성 기준

이 문서는 dev seed 기준 데이터 파이프라인을 다시 실행할 때 중복과 누락을 피하기 위한 최소 기준을 정리한다.

## 기본 판단

#55는 "어느 task부터 다시 실행할 것인가"를 정리한다. 이 문서는 "그 task를 다시 실행해도 데이터가 중복되거나 깨지지 않는가"를 다룬다.

현재 dev 파이프라인은 대규모 증분 처리가 아니라 20건 dev seed를 기준으로 한 재현 가능한 개발/검증 흐름이다. 따라서 Bronze, Silver, Eval, Context는 `MERGE INTO`가 아니라 overwrite 재생성을 기준으로 멱등성을 확보한다.

## Task별 처리 기준

| Task | 입력 | 출력 | 현재 처리 기준 | 재실행 판단 |
| --- | --- | --- | --- | --- |
| `generate_dev_seed_task` | generator 코드, seed, size, reference date | workspace files의 `data/dev` JSONL | 같은 파라미터로 deterministic 재생성 | 같은 입력이면 source id, eval key, context key가 유지돼야 한다. |
| `synthetic_data_task` | workspace files의 Landing seed | ADLS `raw/dev` JSONL | 같은 경로 overwrite/copy | raw/dev는 현재 dev 기준 입력 위치이며 run_id별 보존은 하지 않는다. |
| `ingest_task` | ADLS `raw/dev` | Bronze 6개 Delta table | table overwrite | 같은 raw 입력이면 Bronze row count가 유지돼야 한다. |
| `silver_task` | Bronze 6개 table | Silver 4개 table | table overwrite | 같은 Bronze 입력이면 deterministic id와 row count가 유지돼야 한다. |
| `eval_seed_task` | eval JSONL | `eval.ground_truth_case` | table overwrite | 재실행해도 eval row가 append 누적되지 않아야 한다. |
| `context_seed_task` | context JSONL | `context.asset_context`, `context.assignment_routing` | table overwrite | 재실행해도 context row가 append 누적되지 않아야 한다. |

## 재실행 기준

| 변경 또는 실패 지점 | 재실행 시작점 | 함께 확인할 항목 |
| --- | --- | --- |
| dev seed 생성 규칙 변경 | `generate_dev_seed_task` | 대표 source id, eval key, context key 유지 여부 |
| raw 배치 실패 | `synthetic_data_task` | ADLS `raw/dev` 6개 JSONL 존재 여부 |
| Bronze 적재 실패 | `ingest_task` | Bronze 6개 table row count |
| Silver 변환 실패 | `silver_task` | Silver row count, distinct key count, orphan reference |
| eval 적재 실패 | `eval_seed_task` | eval row count, Silver 매칭 누락 |
| context 적재 실패 | `context_seed_task` | context row count, Silver/Eval 매칭 누락 |

upstream 입력이 바뀐 경우 downstream은 다시 실행한다. 예를 들어 raw/dev가 바뀌면 `ingest_task`와 `silver_task`를 다시 실행하고, eval/context의 source key 매칭 결과도 다시 확인한다.

## 현재 보장하는 범위

- 같은 `dev_seed_size`, `dev_seed`, `dev_reference_date`로 seed를 재생성하면 대표 source id와 key가 유지된다.
- Bronze/Silver/Eval/Context는 overwrite 기준이므로 같은 입력 재실행에서 append 중복이 생기지 않는다.
- Silver deterministic id는 source id 기반으로 재생성되므로 같은 Bronze 입력에서 key가 유지된다.
- eval/context는 source key 기준으로 Silver와 매칭되며, 재적재 시 row count가 늘어나지 않아야 한다.

## 현재 보장하지 않는 범위

- run_id별 Landing 원본 보존
- 대규모 증분 처리용 `MERGE INTO` 또는 partition overwrite
- partial write를 인위적으로 만든 뒤 자동 복구하는 운영 테스트
- 자동 retry, alert, run history 기반 복구 UI
- 실제 API connector 기준 장기 backfill
- DLT expectation을 실제 Bronze/Silver 운영 경로에 적용한 품질 게이트

위 항목은 품질검증 고도화 또는 재처리/멱등성 고도화 백로그로 둔다.

## 검증 방법

재실행 검증은 `sql/databricks/queries/de_retry_idempotency_validation.sql`을 사용한다. 이 SQL은 job task가 아니라 read-only 검산 아티팩트다.

검증 순서는 다음을 기준으로 한다.

1. dev seed 생성부터 context 적재까지 1차 실행한다.
2. 검증 SQL 결과를 snapshot으로 기록한다.
3. `ingest_task,silver_task`만 다시 실행하고 snapshot과 비교한다.
4. `eval_seed_task,context_seed_task`만 다시 실행하고 snapshot과 비교한다.
5. 같은 seed 파라미터로 end-to-end 재실행한 뒤 대표 key와 unmatched count를 다시 확인한다.
