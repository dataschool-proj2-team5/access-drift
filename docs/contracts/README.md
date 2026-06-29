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
| [Sensitive Asset Taxonomy](./sensitive-asset-taxonomy.md) | 합성 데이터와 Gold severity 매핑에 참고할 민감 자산 예시 기준 |
| [Schema Consistency Review](./schema-consistency-review.md) | Bronze/Silver/Eval 계약, DDL, notebook, seed 정합성 검토 결과 |

## Landing 계약

현재 Landing 입력 규칙은 [Bronze Schema Contract](./bronze-schema.md)의 `Landing 입력` 섹션에서 함께 관리한다.

Landing raw 입력에는 eval 라벨, planted risk 여부, expected severity 같은 정답 정보를 포함하지 않는다.

향후 source가 늘어나거나 API 응답, export 파일, seed 파일의 원본 shape을 별도로 검증해야 하면 Landing 계약을 독립 문서로 분리한다.

```text
docs/contracts/landing-contract.md
```

## 공통 원칙

- Landing과 Bronze는 source 형태와 원본 payload를 보존한다.
- Silver는 source 차이를 공통 모델로 정규화한다.
- 탐지 결과, risk score, severity, 권장 조치, 화면 표시용 문구는 Silver에 두지 않는다.
- 정답 라벨과 planted risk 정보는 Eval에만 둔다.
- Secret value, token value, private key value는 어떤 레이어에도 저장하지 않는다.
- 계약 변경 시 각 계약 문서의 버전과 변경이력을 함께 갱신한다.
