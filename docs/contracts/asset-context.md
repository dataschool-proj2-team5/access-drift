# Asset Context Contract

```text
version: 0.1.0
status: draft
updated_at: 2026-06-30
```

## 범위

이 문서는 Risk Card / Access Path 화면에서 최종 자산이 어떤 비즈니스 데이터 범위를 포함하는지 표시하기 위한 `asset_context` 기준을 정의한다.

`asset_context`는 접근 사실이나 탐지 결과가 아니라 자산에 붙는 설명용 context다. 따라서 Landing/Bronze/Silver 원천 모델이나 Gold Core 본문에 직접 섞지 않고, Risk Card view 또는 app 조회 계층에서 별도로 조인한다.

## 위치

```text
gold_core
  + asset_context       -- 자산 설명 / 데이터 범위
  + action_state        -- 현재 조치 상태
  + assignment_routing  -- 조치 담당자 / 담당 팀
  = risk_card_view      -- 화면/API 조회용 Risk Card
```

`asset_context`는 자산 설명만 담당한다. 조치 담당자나 담당 팀 배정은 `assignment_routing` 후보로 분리한다.

## 조인 기준

Risk Card view에서는 Gold Core의 source asset id와 조인한다.

```text
asset_context.source_asset_id = gold_core.asset_source_id
```

Silver 기준으로 확인할 때는 Silver asset의 source id와 조인한다.

```text
asset_context.source_asset_id = silver_assets.source_asset_id
```

`asset_context`는 Silver 내부 hash id인 `asset_id`를 직접 관리하지 않는다.

## 최소 필드

| 컬럼 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `source_asset_id` | string | yes | Gold/Silver와 조인할 source asset id |
| `data_scope_label` | string | yes | 화면에 표시할 데이터 범위 이름 |
| `sensitive_data_examples` | array<string> | yes | 자산에 포함되는 민감 데이터 예시 |
| `sensitivity_reason` | string | yes | 해당 자산을 민감하게 보는 이유 |

## 대표 데모 자산

아래 값은 dev 합성 데이터의 source asset id 기준 context 예시다. 화면 표시명은 `gold_core.asset_display_name` 또는 `silver_assets.display_name`에서 가져오며, `asset_context`에 중복 저장하지 않는다.

```json
{
  "source_asset_id": "asset-customer-export-storage-prod",
  "data_scope_label": "고객 DB",
  "sensitive_data_examples": [
    "고객 이름",
    "전화번호",
    "배송지",
    "주문내역"
  ],
  "sensitivity_reason": "고객 식별 정보와 배송지/주문내역을 포함하는 export storage"
}
```

## 중복 선언하지 않는 필드

다음 값은 이미 Silver 또는 Gold 경로에 있으므로 `asset_context`에서 다시 선언하지 않는다.

| 필드 | 기존 위치 |
| --- | --- |
| `asset_id` | `silver_assets.asset_id`, `gold_core.asset_id` |
| `source_system` | `silver_assets.source_system` |
| `asset_display_name` | `silver_assets.display_name`, `gold_core.asset_display_name` |
| `sensitivity` | `silver_assets.sensitivity`, `gold_core.asset_sensitivity` |
| `asset_type` | `silver_assets.asset_type` |
| `environment` | `silver_assets.environment`, `gold_core.asset_environment` |

## 금지 사항

- 실제 고객 데이터 값을 저장하지 않는다.
- Secret value, token value, private key value를 저장하지 않는다.
- `data_scope_label`이나 `sensitive_data_examples`를 실제 graph edge처럼 모델링하지 않는다.
- `asset_context`에 `steward_team`, `assignee`, `team` 같은 조치 담당자/담당 팀 라우팅 필드를 직접 추가하지 않는다.
