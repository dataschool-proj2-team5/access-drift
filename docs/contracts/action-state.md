# Action State Contract

```text
version: 0.1.0
status: draft
updated_at: 2026-07-01
```

## 범위

이 문서는 Risk Card 화면에서 사용자가 변경한 현재 조치 상태를 저장하고 다시 조회하기 위한 `risk_action_state` 기준을 정의한다.

`risk_action_state`는 탐지 결과, 담당자 라우팅, 조치 이력, 감사 로그가 아니라 Risk Card에 붙는 현재 상태다. 따라서 Gold Core 본문에 직접 섞지 않고, app 조회 계층에서 별도로 조인한다.

상태 변경 이력은 `risk_action_state`에 누적하지 않는다. 사용자가 상태나 메모를 변경한 사실은 `risk_action_event`에 append-only event로 남긴다. Dashboard 기본 조회와 Gold/Core 스키마는 변경하지 않는다.

## 최소 필드

### risk_action_state

| 컬럼 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `risk_case_key` | string | yes | Gold Core와 조인할 Risk Card key |
| `status` | string | yes | 현재 조치 상태. `open`, `reviewing`, `resolved` |
| `reviewer_name` | string | no | 현재 검토자 이름 |
| `reviewer_team` | string | no | 현재 검토 팀 |
| `updated_by` | string | no | 마지막으로 상태를 변경한 사용자 |
| `updated_at` | timestamp | yes | 현재 상태가 마지막으로 변경된 시각 |
| `note` | string | no | 현재 상태에 대한 최신 메모 |

### risk_action_event

| 컬럼 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `event_id` | string | yes | action event 고유 id |
| `risk_case_key` | string | yes | Gold Core와 조인할 Risk Card key |
| `event_type` | string | yes | 이벤트 종류. `status_changed`, `note_updated` |
| `previous_status` | string | no | 변경 전 상태 |
| `new_status` | string | no | 변경 후 상태 |
| `actor_id` | string | no | 상태를 변경한 사용자 또는 app 사용자 id |
| `actor_name` | string | no | 상태를 변경한 사용자 표시 이름 |
| `event_at` | timestamp | yes | 이벤트 발생 시각 |
| `note` | string | no | 이벤트 시점의 메모 또는 변경 사유 |

## 상태값

| 저장값 | 화면 표시 | 의미 |
| --- | --- | --- |
| `open` | 미처리 | 아직 검토 또는 조치가 시작되지 않은 상태 |
| `reviewing` | 검토 중 | 담당자가 확인 또는 조치를 진행 중인 상태 |
| `resolved` | 처리 완료 | 조치가 완료되어 현재 Risk Card를 닫아도 되는 상태 |

## 이벤트 타입

| 저장값 | 의미 |
| --- | --- |
| `status_changed` | 사용자가 현재 조치 상태를 변경했다. |
| `note_updated` | 사용자가 현재 메모를 변경했다. |

## 조인 기준

`risk_action_state.risk_case_key`는 action state 기준 unique key로 관리한다. 같은 `risk_case_key`에 여러 현재 상태 row를 만들지 않는다.

`risk_action_event.risk_case_key`는 같은 Risk Card의 변경 이력을 연결하는 key다. 같은 `risk_case_key`에 여러 event row가 쌓일 수 있다.

Risk Card view에서는 Gold Core의 risk case key와 left join한다.

```text
risk_action_state.risk_case_key = gold_core.risk_case_key
```

state가 없는 Risk Card는 화면에서 `open`으로 처리한다.

이력 조회가 필요할 때만 `risk_action_event`를 `risk_case_key` 기준으로 조회한다.

## 저장 위치

Action State는 app 조회 계층의 사용자 상호작용 상태다.

```text
${catalog}.app.risk_action_state
${catalog}.app.risk_action_event
```

두 테이블은 pipeline seed 또는 Gold overwrite 대상이 아니다. Gold Core가 재생성되어도 사용자가 변경한 현재 상태와 이력은 별도 테이블에 유지한다.

상태 변경 처리는 다음 순서를 하나의 사용자 조작으로 본다.

```text
risk_action_state upsert
  + risk_action_event append
```

`risk_action_state`만 직접 수정하면 감사 로그가 남지 않으므로, 실제 구현 시 상태 변경 함수 또는 API에서 두 작업을 함께 수행해야 한다.

## 예시

### 현재 상태

```json
{
  "risk_case_key": "nhi:d8f4a5b6-7c8d-4e91-9f02-1a2b3c4d5e6f:asset-customer-export-storage-prod:nhi_residual_access",
  "status": "reviewing",
  "reviewer_name": "이다영",
  "reviewer_team": "CRM 데이터 운영팀",
  "updated_by": "app_user_001",
  "updated_at": "2026-06-30T10:00:00Z",
  "note": "CRM 데이터 운영팀에 소유자 확인 요청"
}
```

### 변경 이벤트

```json
{
  "event_id": "evt-20260701-000001",
  "risk_case_key": "nhi:d8f4a5b6-7c8d-4e91-9f02-1a2b3c4d5e6f:asset-customer-export-storage-prod:nhi_residual_access",
  "event_type": "status_changed",
  "previous_status": "open",
  "new_status": "reviewing",
  "actor_id": "app_user_001",
  "actor_name": "이다영",
  "event_at": "2026-07-01T10:00:00Z",
  "note": "CRM 데이터 운영팀에 소유자 확인 요청"
}
```

## 중복 선언하지 않는 필드

다음 값은 이미 Gold Core, Assignment Routing, Asset Context 경로에 있으므로 `risk_action_state`에서 다시 선언하지 않는다.

| 필드 | 기존 위치 |
| --- | --- |
| `finding_id` | `gold_core.finding_id` |
| `severity` | `gold_core.severity` |
| `recommended_action` | `gold_core.recommended_action` |
| `asset_display_name` | `gold_core.asset_display_name` |
| `data_scope_label` | `asset_context.data_scope_label` |
| `assignee_name` | `assignment_routing.assignee_name` |
| `assignee_team` | `assignment_routing.assignee_team` |

## 금지 사항

- Jira 티켓 번호, 티켓 상태, 권한 회수 실행 결과를 저장하지 않는다.
- 담당자/담당 팀 라우팅 필드를 중복 저장하지 않는다.
- Gold Core overwrite나 seed task에서 이 테이블들을 덮어쓰지 않는다.
- `risk_action_event`에 실제 고객 정보, secret value, token value, private key value를 저장하지 않는다.
