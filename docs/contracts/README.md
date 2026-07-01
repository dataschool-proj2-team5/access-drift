# Access Drift Contracts

이 문서는 Access Drift 데이터 계약의 진입점이다.

세부 스키마와 처리 기준은 레이어별 계약 문서에서 관리한다. 구현자는 계약 문서의 컬럼명, 타입, 의미, id 생성 규칙을 임의로 바꾸지 않는다.

## 계약 문서

| 문서 | 역할 |
| --- | --- |
| [Bronze Schema Contract](./bronze-schema.md) | source 입력을 원본 데이터로 보존하는 Bronze 테이블 계약 |
| [Silver Schema Contract](./silver-schema.md) | 원본 데이터를 공통 모델로 정규화한 Silver 테이블 계약 |
| [Eval Schema Contract](./eval-schema.md) | DS 초안 기준 PoC 정답/평가용 라벨을 격리하는 Eval 테이블 계약 |
| [PoC Intermediate/Gold Schema Contract](./poc-intermediate-gold-schema.md) | NHI residual access 탐지 후보와 Risk Card용 Gold 최소 계약 |
| [Asset Context Contract](./asset-context.md) | Risk Card / Access Path 화면에서 자산 설명과 데이터 범위를 붙이는 context 기준 |
| [Assignment Routing Contract](./assignment-routing.md) | Risk Card 화면에서 조치 담당자와 담당 팀을 붙이는 context 기준 |
| [Action State Contract](./action-state.md) | Risk Card 화면에서 사용자가 변경한 현재 조치 상태를 저장/조회하는 기준 |
| [RAG Evidence Contract](./rag-evidence.md) | RAG / AI Runbook이 참조할 Risk Case evidence document와 chunk 기준 |
| [Sensitive Asset Taxonomy](./sensitive-asset-taxonomy.md) | 합성 데이터와 Gold severity 매핑에 참고할 민감 자산 예시 기준 |
| [Landing Source Assumptions](./landing-source-assumptions.md) | Landing 합성 입력이 source 원본형 필드인지 합성 보강값인지 구분하는 기준 |
| [Data Contract Change Process](./contract-change-process.md) | 데이터 계약 변경 시 공통 절차, PR 체크리스트, 최소 schema validation 기준 |
| [Schema Consistency Review](./schema-consistency-review.md) | Bronze/Silver/Eval 계약, DDL, notebook, seed 정합성 검토 결과 |

## Landing 계약

Landing 합성 입력의 source 원본형 필드와 합성 보강값 구분은 [Landing Source Assumptions](./landing-source-assumptions.md)에서 관리한다.

Bronze 테이블 적재 컬럼은 [Bronze Schema Contract](./bronze-schema.md)에서 관리한다.

Landing raw 입력에는 eval 라벨, planted risk 여부, expected severity 같은 정답 정보를 포함하지 않는다.

## 공통 원칙

- Landing과 Bronze는 source 형태와 원본 payload를 보존한다.
- Silver는 source 차이를 공통 모델로 정규화한다.
- 탐지 결과, risk score, severity, 권장 조치, 화면 표시용 문구는 Silver에 두지 않는다.
- 화면 표시용 자산 설명과 데이터 범위는 Asset Context로 분리한다.
- 조치 담당자와 담당 팀 배정은 Assignment Routing으로 분리한다.
- 사용자가 변경한 현재 조치 상태는 Action State로 분리한다.
- 정답 라벨과 planted risk 정보는 Eval에만 둔다.
- Secret value, token value, private key value는 어떤 레이어에도 저장하지 않는다.
- 계약 변경 시 각 계약 문서의 버전과 변경이력을 함께 갱신한다.
