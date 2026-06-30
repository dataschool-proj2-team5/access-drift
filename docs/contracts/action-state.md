# Action State Contract

```text
version: 0.1.0
status: draft
updated_at: 2026-06-30
```

## 범위

이 문서는 Risk Card 화면에서 사용자가 변경한 현재 조치 상태를 저장하고 다시 조회하기 위한 `risk_action_state` 기준을 정의한다.

`risk_action_state`는 탐지 결과, 담당자 라우팅, 조치 이력, 감사 로그가 아니라 Risk Card에 붙는 현재 상태다. 따라서 Gold Core 본문에 직접 섞지 않고, app 조회 계층에서 별도로 조인한다.

## 최소 필드

| 컬럼 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `risk_case_key` | string | yes | Gold Core와 조인할 Risk Card key |
| `status` | string | yes | 현재 조치 상태. `open`, `reviewing`, `resolved` |
| `reviewer_name` | string | no | 현재 검토자 이름 |
| `reviewer_team` | string | no | 현재 검토 팀 |
| `updated_by` | string | no | 마지막으로 상태를 변경한 사용자 |
| `updated_at` | timestamp | yes | 현재 상태가 마지막으로 변경된 시각 |
| `note` | string | no | 현재 상태에 대한 최신 메모 |

## 상태값

| 저장값 | 화면 표시 | 의미 |
| --- | --- | --- |
| `open` | 미처리 | 아직 검토 또는 조치가 시작되지 않은 상태 |
| `reviewing` | 검토 중 | 담당자가 확인 또는 조치를 진행 중인 상태 |
| `resolved` | 처리 완료 | 조치가 완료되어 현재 Risk Card를 닫아도 되는 상태 |

## 조인 기준

`risk_action_state.risk_case_key`는 action state 기준 unique key로 관리한다. 같은 `risk_case_key`에 여러 현재 상태 row를 만들지 않는다.

Risk Card view에서는 Gold Core의 risk case key와 left join한다.

```text
risk_action_state.risk_case_key = gold_core.risk_case_key
```

state가 없는 Risk Card는 화면에서 `open`으로 처리한다.

## 저장 위치

Action State는 app 조회 계층의 사용자 상호작용 상태다.

```text
${catalog}.app.risk_action_state
```

이 테이블은 pipeline seed 또는 Gold overwrite 대상이 아니다. Gold Core가 재생성되어도 사용자가 변경한 현재 상태는 별도 테이블에 유지한다.

## 예시

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

- 상태 변경 이력을 저장하지 않는다.
- 감사 로그를 저장하지 않는다.
- Jira 티켓 번호, 티켓 상태, 권한 회수 실행 결과를 저장하지 않는다.
- 담당자/담당 팀 라우팅 필드를 중복 저장하지 않는다.
- Gold Core overwrite나 seed task에서 이 테이블을 덮어쓰지 않는다.
