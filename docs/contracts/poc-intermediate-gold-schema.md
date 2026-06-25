# PoC Intermediate/Gold Schema Contract

```text
version: 0.1.0
status: draft
updated_at: 2026-06-24
```

## 범위

이 계약은 Azure App Registration / NHI residual access 한 가지 PoC 패턴만 다룬다.

```text
terminated HI
  --owns_principal-->
active App Registration
  --bound_principal_id-->
active credential

active App Registration
  --accesses_asset-->
asset
```

Eval은 탐지 입력으로 사용하지 않는다.

이번 PoC는 현재 구현되어 검증 가능한 DE Silver 모델
`silver_principals`, `silver_credentials`, `silver_assets`, `silver_edges`를 입력으로 사용한다.
DS data-contract의 holdout, distractor, Isolation Forest, 확장 eval 설계는 후속 구현 범위로 남기고
이 계약에는 Intermediate/Gold 실행 산출물에 필요한 최소 필드만 둔다.

Gold Core는 LLM/RAG 실패와 무관하게 생성되어야 한다. 따라서 이 계약의 `gold_core`에는
deterministic pipeline에서 만든 최소 Risk Card 필드만 저장하고, LLM 요약이나 정책 citation은
후속 `gold_enrichment`, `gold_policy_citation` 범위로 분리한다.

## Silver 입력 컬럼

Intermediate는 다음 Silver 컬럼만 입력으로 사용한다.

| Silver 테이블 | 사용 컬럼 | 용도 |
| --- | --- | --- |
| `silver_principals` | `principal_id`, `source_principal_id`, `principal_kind`, `principal_type`, `display_name`, `status` | 퇴사 HI owner와 active NHI App Registration 식별 |
| `silver_credentials` | `credential_id`, `bound_principal_id`, `status`, `is_active` | NHI에 남아 있는 active credential 확인 |
| `silver_assets` | `asset_id`, `source_asset_id`, `display_name`, `environment`, `sensitivity` | 최종 접근 자산과 Gold severity 근거 |
| `silver_edges` | `edge_id`, `from_id`, `from_type`, `to_id`, `to_type`, `relationship`, `permission`, `status` | owner -> NHI, NHI -> asset 근거 경로 |

현재 Silver에서는 퇴사자와 NHI의 관계를 `owns_principal`로 표현한다. Notion 통합본의
`created_principal` 관계는 Pattern 2 정밀화를 위한 후속 Silver 계약 변경 후보이며, #10에서는
이미 적재된 Silver 구조에 맞춰 `owns_principal`을 사용한다.

## intermediate.nhi_residual_access_findings

Silver 사실을 조인해 만든 탐지 후보와 근거 식별자를 저장한다.

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `finding_id` | string | `risk_case_key` 기반 deterministic finding id |
| `risk_case_key` | string | source subject, source asset, drift type 기반 키 |
| `drift_type` | string | PoC에서는 `nhi_residual_access` |
| `subject_type` | string | PoC에서는 `nhi` |
| `owner_principal_id` | string | 퇴사 owner의 Silver id |
| `owner_source_principal_id` | string | 퇴사 owner의 source id |
| `subject_principal_id` | string | NHI의 Silver id |
| `subject_source_principal_id` | string | App Registration source id |
| `credential_id` | string | active credential의 Silver id |
| `asset_id` | string | 자산의 Silver id |
| `asset_source_id` | string | 자산 source id |
| `owner_edge_id` | string | owner → NHI 근거 edge |
| `access_edge_id` | string | NHI → asset 근거 edge |
| `permission` | string | asset 접근 permission |
| `owner_status` | string | 탐지 시점 owner 상태 |
| `credential_is_active` | boolean | 탐지 시점 credential 활성 여부 |
| `asset_environment` | string | 자산 환경 |
| `asset_sensitivity` | string | 자산 민감도 |
| `detected_at` | timestamp | 탐지 시각 |
| `run_id` | string | 파이프라인 실행 식별자 |

## gold.gold_core

Risk Card가 복잡한 Silver 조인 없이 읽을 수 있는 최소 결과를 저장한다.

주요 필드는 다음 질문에 답해야 한다.

- 어떤 NHI가 남아 있는가?
- 어떤 자산에 닿는가?
- 왜 finding인가?
- 다음 조치는 무엇인가?

Gold의 `subject_type`, `subject_source_principal_id`, `asset_source_id`, `drift_type`은 후속 Eval 검증에서 각각 Eval key의 `subject_type`, `subject_id`, `asset_id`, `drift_type`과 비교한다.

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| `risk_case_key` | string | `(subject_type, subject_source_principal_id, asset_source_id, drift_type)` 기반 안정 키 |
| `finding_id` | string | Intermediate finding id |
| `drift_type` | string | PoC에서는 `nhi_residual_access` |
| `subject_type` | string | PoC에서는 `nhi` |
| `subject_principal_id` | string | NHI Silver id |
| `subject_source_principal_id` | string | NHI source id. Eval `subject_id`와 비교할 값 |
| `subject_display_name` | string | Risk Card에 표시할 NHI 이름 |
| `owner_principal_id` | string | 퇴사 owner Silver id |
| `owner_display_name` | string | Risk Card에 표시할 owner 이름 |
| `asset_id` | string | 자산 Silver id |
| `asset_source_id` | string | 자산 source id. Eval `asset_id`와 비교할 값 |
| `asset_display_name` | string | Risk Card에 표시할 자산 이름 |
| `asset_environment` | string | 자산 환경 |
| `asset_sensitivity` | string | 자산 민감도 |
| `severity` | string | PoC에서는 `asset_sensitivity`를 대문자로 전달 |
| `evidence_summary` | string | Silver 근거를 사람이 읽을 수 있게 요약한 deterministic 문구 |
| `recommended_action` | string | LLM이 아닌 고정 템플릿 기반 최소 조치 문구 |
| `owner_edge_id` | string | owner -> NHI 근거 edge |
| `access_edge_id` | string | NHI -> asset 근거 edge |
| `credential_id` | string | active credential 근거 |
| `detected_at` | timestamp | Intermediate 탐지 시각 |
| `run_id` | string | Gold 적재 실행 식별자 |

## 적재 방식

Intermediate와 Gold는 현재 PoC 스냅샷을 `overwrite`한다. 결정적 `risk_case_key`와 `finding_id`를 사용하므로 동일 입력 재실행 시 행이 중복 누적되지 않는다.
