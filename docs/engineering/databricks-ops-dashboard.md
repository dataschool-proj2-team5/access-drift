# Databricks SQL Ops Dashboard

이 문서는 이슈 #85 범위의 Databricks SQL 운영/검증용 dashboard 기준을 정리한다.
대상은 제품 UI가 아니라 DE/운영/데모 검증용 Databricks SQL dashboard다.

## 우선순위

- P0: Gold row count 0, Silver orphan/unmatched > 0, positive eval unmatched > 0
- P1: Risk Card context/assignment coverage 누락, stale action state
- P2: severity/status 분포와 row count 추세 관찰

## 원격 스키마 확인 결과

Intermediate/Gold 쿼리 작성 전 `access_drift_dev`의 실제 스키마를 확인했다.

- `access_drift_dev.intermediate.nhi_residual_access_findings`
  - 로컬 DDL 공통 컬럼 외에 `principal_kind`, `source_system`, `principal_type`, `finding_type_label`, `risk_factors`가 추가돼 있다.
  - `credential_id`, `owner_edge_id`, `credential_is_active`는 실제 테이블에서 nullable이다.
- `access_drift_dev.gold.gold_core`
  - 로컬 DDL 공통 컬럼 외에 `principal_kind`, `source_system`, `principal_type`, `finding_type_label`, `risk_factors`가 추가돼 있다.
  - `owner_edge_id`, `credential_id`는 실제 테이블에서 nullable이다.
- `access_drift_dev.app.risk_action_state`
  - 실제 컬럼은 `risk_case_key`, `status`, `reviewer_name`, `reviewer_team`, `updated_by`, `updated_at`, `note`
- `access_drift_dev.app.risk_action_event`
  - 실제 컬럼은 `event_id`, `risk_case_key`, `event_type`, `previous_status`, `new_status`, `actor_id`, `actor_name`, `event_at`, `note`

ops dashboard 쿼리는 nullable 여부와 추가 컬럼 차이 때문에 실제 공통 컬럼만 사용한다.

## Dashboard Query 목록

저장 위치: `sql/databricks/queries/ops_dashboard/`

- `01_pipeline_row_count.sql`
  - Bronze/Silver/Intermediate/Gold/Eval/Context/App 최소 row count
- `02_silver_orphan_unmatched_summary.sql`
  - Silver join/reference orphan 요약
- `03_gold_severity_status_summary.sql`
  - Gold severity 분포와 action status 분포
- `04_eval_positive_unmatched.sql`
  - planted positive eval의 Silver/Gold 매칭 누락
  - `case_id` 기준으로 집계해 조인 중복 때문에 mismatch 수가 부풀지 않게 한다.
- `05_context_assignment_coverage.sql`
  - Gold 기준 asset context / assignment routing coverage
- `06_action_state_event_summary.sql`
  - action status / event type / stale state 요약

## Dashboard Metric

- Pipeline row count
- Silver orphan/unmatched summary
- Gold severity summary
- Gold action status summary
- Eval positive unmatched summary
- Context coverage
- Assignment coverage
- Action state status summary
- Action event type summary
- Stale action state count

## Alert Candidate

Dashboard metric과 Alert candidate는 분리한다. 실제 Alert 생성은 이 이슈 범위가 아니다.

- P0
  - `gold.gold_core` row count = 0
  - `02_silver_orphan_unmatched_summary.sql` 결과 중 하나라도 `issue_count > 0`
  - `04_eval_positive_unmatched.sql`의 `positive_eval_without_silver_match > 0`
  - `04_eval_positive_unmatched.sql`의 `positive_eval_without_gold_match > 0`
- P1
  - `05_context_assignment_coverage.sql`의 `asset_context` `missing_count > 0`
  - `05_context_assignment_coverage.sql`의 `assignment_routing` `missing_count > 0`
  - `06_action_state_event_summary.sql`의 `stale_risk_action_state` `row_count > 0`
- P2
  - severity/status 분포 급변은 우선 dashboard 관찰 대상으로만 둔다.

## Databricks SQL Dashboard 수동 구성 절차

1. Databricks SQL Editor에서 `sql/databricks/queries/ops_dashboard/`의 6개 SQL을 각각 새 Query로 저장한다.
2. Query 이름은 `ops_01_pipeline_row_count`부터 `ops_06_action_state_event_summary`까지 순서대로 맞춘다.
3. Warehouse는 `Starter Warehouse` (`8baac3b353ebbda4`)를 사용한다.
4. 새 Dashboard를 만들고 이름은 `DE P2 Ops Dashboard`로 맞춘다.
5. 각 Query를 widget으로 추가한다.
6. 권장 배치:
   - 1행: pipeline row count
   - 2행: silver orphan/unmatched, eval positive unmatched
   - 3행: gold severity/status
   - 4행: context/assignment coverage
   - 5행: action state/event summary
7. 실제 dashboard 링크를 이 문서와 PR 본문에 기록한다.
8. dashboard 스크린샷을 남기고 경로를 이 문서와 PR 본문에 기록한다.

## 실행 검증 스냅샷

- Warehouse: `Starter Warehouse` (`8baac3b353ebbda4`)
- 검증 일시: 2026-07-02
- 실행 방식: Databricks SQL Statement API
- 실행 결과: `01` ~ `06` 전부 `SUCCEEDED`

아래 값은 2026-07-02 시점의 검증 스냅샷이다. 데이터가 바뀌면 row count와 예외 건수도 함께 달라질 수 있다.

핵심 row count:

- `gold.gold_core`: 22
- `intermediate.nhi_residual_access_findings`: 22
- `eval.ground_truth_case`: 35
- `context.asset_context`: 35
- `context.assignment_routing`: 35
- `app.risk_action_state`: 3
- `app.risk_action_event`: 7
- `silver_assets`: 35
- `silver_credentials`: 25
- `silver_edges`: 65
- `silver_principals`: 59

예외/관측 결과:

- `02_silver_orphan_unmatched_summary.sql`
  - `credentials_without_bound_principal`: 0
  - `credential_edges_without_credential`: 0
  - `access_edges_without_principal_or_asset`: 0
  - `owner_edges_without_hi_or_nhi`: 0
- `03_gold_severity_status_summary.sql`
  - severity: `CRITICAL 7`, `HIGH 7`, `MEDIUM 5`, `LOW 3`
  - action status: `open 20`, `resolved 1`, `reviewing 1`
- `04_eval_positive_unmatched.sql`
  - `positive_eval_total`: 19
  - `positive_eval_without_gold_match`: 0
  - `positive_eval_without_silver_match`: 0
  - `case_id` 기준 집계로 조인 중복 영향을 제거한 뒤 Gold/Silver 모두 planted positive eval mismatch 없음
- `05_context_assignment_coverage.sql`
  - `asset_context`: covered 22 / missing 0 / 100.0%
  - `assignment_routing`: covered 22 / missing 0 / 100.0%
- `06_action_state_event_summary.sql`
  - `risk_action_state_total`: 3
  - `risk_action_event_total`: 7
  - `risk_action_state_status`: `resolved 1`, `reviewing 2`
  - `stale_risk_action_state.missing_gold_match`: 3

## 실제 Dashboard 기록

- Dashboard link: `https://adb-7405615323116390.10.azuredatabricks.net/sql/dashboardsv3/01f175b50a4110c8b2ca863d24736d9f?o=7405615323116390`
- Screenshot path: 대화 첨부 스크린샷 기준 확인
- 검증 메모:
  - Lakeview widget 제목과 연결을 맞춘 뒤 재확인했다.
  - `silver orphan/unmatched`, `eval positive unmatched`, `context/assignment coverage`는 기대값과 일치했다.
  - `action state/event` 관련 값은 최초 Statement API 검증 시점보다 후속 사용자 상태 변경이 반영된 최신 값으로 관측됐다.
