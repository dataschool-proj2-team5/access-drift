# ADR-0004: Dev 재처리 멱등성과 Landing 원본 보존 범위

- **Status**: Accepted
- **Date**: 2026-07-02
- **Deciders**: DE

## Context

Access Drift 데모와 본개발 dev 파이프라인은 아직 대규모 증분 수집이나 실제 API connector 운영 단계가 아니다.
현재 데이터는 재현 가능한 dev seed를 기준으로 생성하고, Databricks task를 부분 실행해 Landing, Bronze, Silver, Eval, Context 산출물을 다시 만들 수 있어야 한다.

발표 전 범위에서는 실패 복구와 재실행 가능성을 보여주는 것이 중요하지만, 운영 수준의 run history, 자동 retry, 장기 retention, lifecycle policy까지 구현하는 것은 범위를 넘는다.

또한 Landing 원본은 향후 실제 API 수집으로 전환할 때 재처리 기준점이 되어야 한다. 다만 현재 dev seed 흐름에서는 `raw/dev` 고정 경로 overwrite를 허용하고 있으며, run_id별 Landing archive는 아직 사용하지 않는다.

## Decision

현재 dev/demo 파이프라인은 `MERGE INTO`나 증분 upsert가 아니라 overwrite 재생성을 기준으로 멱등성을 확보한다.

- 같은 seed parameter로 dev 데이터를 다시 생성하면 source id, eval key, context key가 유지되어야 한다.
- Bronze, Silver, Eval, Context 산출물은 같은 입력으로 재실행해도 append 중복이 생기지 않아야 한다.
- 실패 또는 변경이 발생하면 task 단위로 필요한 지점부터 재실행한다.
- 현재 범위에서는 run_id별 Landing 원본 보존, 장기 backfill, 자동 retry, alert, run history UI를 구현하지 않는다.
- 실제 API 수집 또는 운영 데이터 전환 시에는 Landing을 run_id 또는 수집일 기준으로 보존하고, 보존 기간과 ADLS lifecycle policy를 별도 운영 정책으로 결정한다.
- secret value, token value, private key value는 retention 대상이 아니라 저장 금지 대상이다. 저장 가능한 것은 credential id, key id, secret name, 상태, 만료일 같은 metadata로 제한한다.

실행 절차와 검증 방법은 [retry-idempotency-policy.md](../engineering/retry-idempotency-policy.md)를 따른다.

## Consequences

장점:

- 발표와 dev 검증에서 재실행 기준이 단순하다.
- 같은 seed 기준으로 row count, deterministic id, eval/context key 안정성을 확인하기 쉽다.
- partial write 복구나 증분 merge를 도입하지 않아도 현재 규모의 중복 방지 요구를 만족한다.
- Landing retention을 운영 전환 결정으로 분리해 현재 범위의 구현 부담을 줄인다.

단점:

- run_id별 Landing archive가 없으므로 과거 입력 snapshot을 장기적으로 복원하는 기능은 제공하지 않는다.
- 실제 API connector 도입 후에는 overwrite 기준만으로는 운영 backfill과 감사 요구를 충족하기 어렵다.
- source별 incremental 수집, partition overwrite, merge key 정책은 별도 결정이 필요하다.

후속 결정:

- 실제 API 수집 전환 시 Landing path partition 기준을 정한다.
- Landing 원본 보존 기간과 자동삭제 또는 ADLS lifecycle policy를 정한다.
- run_id, batch_id, checksum 기반 재처리 감사 기준을 확정한다.
- Bronze/Silver DLT 품질 게이트를 실제 운영 경로에 적용할지 결정한다.
