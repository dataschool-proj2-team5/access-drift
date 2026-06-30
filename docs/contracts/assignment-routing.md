# Assignment Routing Contract

```text
version: 0.1.0
status: draft
updated_at: 2026-06-30
```

## 범위

이 문서는 Risk Card 화면에서 특정 리스크를 어떤 담당자 또는 담당 팀에게 확인 요청할지 표시하기 위한 `assignment_routing` 기준을 정의한다.

`assignment_routing`은 조치 상태 이력이나 Jira 티켓이 아니라 Risk Card에 붙는 담당자/팀 배정 context다. 따라서 Gold Core 본문에 직접 섞지 않고, Risk Card view 또는 app 조회 계층에서 별도로 조인한다.

## 최소 필드

| 컬럼 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `subject_type` | string | yes | routing 대상 주체 유형. 예: `nhi` |
| `subject_id` | string | yes | source principal id. Gold Core의 `subject_source_principal_id`와 비교 |
| `asset_id` | string | yes | source asset id. Gold Core의 `asset_source_id`와 비교 |
| `drift_type` | string | yes | routing 대상 drift type |
| `assignee_name` | string | yes | 화면에 표시할 조치 담당자 이름 |
| `assignee_team` | string | yes | 화면에 표시할 조치 담당 팀 |
| `routing_reason` | string | no | 해당 담당자/팀으로 배정한 이유. 없으면 화면에 표시하지 않는다. |

## 조인 기준

`assignment_routing`은 Gold Core에서 계산되는 `risk_case_key`를 직접 입력으로 요구하지 않는다. 합성 데이터와 eval에서 사용하는 source-key 조합을 기준으로 관리한다.

다음 조합은 context 기준 unique key로 관리한다. 같은 조합에 여러 routing row를 만들지 않는다.

```text
subject_type + subject_id + asset_id + drift_type
```

Risk Card view에서는 Gold Core의 동일 source-key 조합과 left join한다.

```text
assignment_routing.subject_type = gold_core.subject_type
assignment_routing.subject_id = gold_core.subject_source_principal_id
assignment_routing.asset_id = gold_core.asset_source_id
assignment_routing.drift_type = gold_core.drift_type
```

context가 없는 Risk Card는 담당자를 빈 값 또는 `unassigned`로 처리한다.

`assignment_routing`은 Gold Core의 `risk_case_key`, `finding_id`, `owner_principal_id`, `asset_id`를 직접 관리하지 않는다.

## 대표 데모 라우팅

아래 값은 대표 데모 케이스의 routing 예시다. `subject_id`와 `asset_id`는 source id 기준이다.

```json
{
  "subject_type": "nhi",
  "subject_id": "d8f4a5b6-7c8d-4e91-9f02-1a2b3c4d5e6f",
  "asset_id": "asset-customer-export-storage-prod",
  "drift_type": "nhi_residual_access",
  "assignee_name": "이다영",
  "assignee_team": "CRM 데이터 운영팀",
  "routing_reason": "sp-crm-customer-export-prod와 crm-customer-export-prod 운영 책임 팀"
}
```

## 중복 선언하지 않는 필드

다음 값은 이미 Gold Core 또는 Action State 경로에 있으므로 `assignment_routing`에서 다시 선언하지 않는다.

| 필드 | 기존 위치 |
| --- | --- |
| `risk_case_key` | `gold_core.risk_case_key` |
| `finding_id` | `gold_core.finding_id` |
| `subject_principal_id` | `gold_core.subject_principal_id` |
| `owner_principal_id` | `gold_core.owner_principal_id` |
| 내부 `asset_id` | `gold_core.asset_id` |
| `severity` | `gold_core.severity` |
| `action_status` | Action State |
| `action_updated_at` | Action State |

## 금지 사항

- `assignment_routing`에 현재 조치 상태나 상태 변경 이력을 저장하지 않는다.
- Jira 티켓 번호, 티켓 상태, 발행 이력은 저장하지 않는다.
- 실제 조치 승인 여부를 routing context로 표현하지 않는다.
- 담당자/팀 배정을 `asset_context`에 중복 저장하지 않는다.
