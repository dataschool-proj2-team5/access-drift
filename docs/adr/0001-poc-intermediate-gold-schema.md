# ADR-0001: PoC Intermediate/Gold 최소 스키마

- **Status**: Proposed
- **Date**: 2026-06-24
- **Deciders**: DS/DE team

## Context

PoC의 완료 기준은 Azure App Registration 형태의 NHI residual access를 Silver 데이터에서 탐지하고, 팀 공용 Databricks에서 Risk Card용 Gold 결과를 조회하는 것이다.

Notion의 초기 DS 문서는 Pattern 1·2, holdout, Isolation Forest와 여러 평가 테이블을 함께 제안했지만, 현재 `docs/product/poc-scope.md`와 이슈 #10은 source 1개, drift pattern 1개, Gold 결과 최소 1건으로 범위를 축소한다.

현재 Silver 계약에서 owner 관계는 `silver_edges.relationship = 'owns_principal'`, credential 귀속은 `silver_credentials.bound_principal_id`, 자산 접근은 `silver_edges.relationship = 'accesses_asset'`으로 표현한다. Eval은 탐지 입력이 아니라 후속 검증 입력이다.

팀장 피드백에 따라 DS data-contract 전체를 개발 기준 문서로 먼저 병합하지 않고, 현재 구현 및 검증 가능한 Intermediate/Gold 계약과 DDL/노트북만 #10 범위에 포함한다. holdout, distractor, Isolation Forest, 확장 eval은 후속 구현 PR에서 계약으로 승격한다.

Notion 통합본의 Gold 설계 원칙에 따라 Gold Core는 LLM/RAG 실패와 무관하게 생성되어야 한다. 이 ADR의 `gold_core`는 deterministic Risk Card 최소 필드만 포함하고, `gold_enrichment`, `gold_policy_citation`, Action state는 #10 범위에서 제외한다.

## Decision

PoC에는 다음 두 테이블만 추가한다.

- `access_drift.intermediate.nhi_residual_access_findings`
- `access_drift.gold.gold_core`

탐지 후보는 아래 조건을 모두 만족할 때 생성한다.

1. owner principal은 `HI`, `terminated` 상태다.
2. owner에서 NHI로 향하는 `owns_principal` edge가 active다.
3. NHI는 `app_registration`, `active` 상태다.
4. NHI에 `bound_principal_id`로 연결된 credential이 active다.
5. NHI에서 asset으로 향하는 `accesses_asset` edge가 active다.

자산 민감도는 finding 생성 여부를 차단하지 않고 Gold의 severity로 전달한다. 현재 Eval seed의 HIGH와 MEDIUM positive를 모두 같은 구조적 residual access로 다루기 위해서다.

`risk_case_key`는 Eval key와 같은 의미를 갖는 `(subject_type, subject_source_principal_id, asset_source_id, drift_type)`으로 결정적으로 생성한다. `finding_id`도 `risk_case_key`에서 결정적으로 생성한다. 두 테이블은 매 실행마다 `overwrite`하여 동일 입력 재실행 시 행이 누적되지 않게 한다.

Eval 테이블은 Intermediate와 Gold 생성 노트북에서 읽지 않는다.

Notion 통합본에서 제안한 `created_principal` 관계는 Pattern 2 정밀화를 위한 후속 Silver 계약 변경 후보로 둔다. #10에서는 이미 적재된 DE Silver 모델을 기준으로 `owns_principal` 관계를 사용한다.

## Consequences

- Silver 사실과 탐지 결과, 사용자 표시 결과의 책임이 분리된다.
- Gold에서 Silver owner edge, access edge, credential까지 역추적할 수 있다.
- 현재 seed에서는 위험 후보 2건과 Gold 2건이 생성되고, active owner 정상 케이스는 제외된다.
- 다중 credential 또는 다중 접근 경로를 하나의 Risk Card로 집계하는 일반화는 PoC 이후 별도 결정이 필요하다.
- 운영 이력 누적 대신 현재 스냅샷을 유지하므로 장기 추세 분석에는 적합하지 않다.
