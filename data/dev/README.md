# Dev 합성 데이터 기준

`data/dev`는 본개발용 합성 데이터의 기준 위치다. PoC 재현용 `data/poc`와 분리하며, Databricks dev target은 `access_drift_dev` catalog와 `raw/dev` 경로를 사용한다.

생성기는 `data/dev/generator/`에 둔다. 생성된 JSONL은 로컬 검증과 Databricks 적재 입력으로만 사용하고 Git에는 커밋하지 않는다.

## 경로

| 경로 | 역할 |
| --- | --- |
| `data/dev/generator/` | dev Landing/Eval JSONL 생성 및 검증 코드 |
| `data/dev/landing/raw/` | dev용 Landing 입력 JSONL 생성 위치 |
| `data/dev/eval/ground_truth_case.jsonl` | dev용 eval 정답지 생성 위치 |

생성기는 Landing 입력과 eval 정답지를 함께 만들지만, 생성 파일 자체는 Git에 올리지 않는다.

## 20건 샘플 구성

20건은 사람이 빠르게 검토할 수 있는 최소 dev 샘플이다.

| 구분 | 건수 | 의미 |
| --- | ---: | --- |
| positive | 4 | B-S2/NHI residual access 조건을 모두 만족 |
| distractor | 12 | positive와 유사하지만 조건 하나만 깨짐 |
| normal | 4 | positive 조건 조합을 만족하지 않는 정상 샘플 |

20건 샘플 상세:

| case_id | 구분 | app | owner | credential | edge | asset | 깨진 조건 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `eval-nhi-001` | positive | `sp-crm-customer-export-prod` | terminated | active | active | critical / production | - |
| `eval-nhi-002` | positive | `customer-profile-export-prod` | terminated | active | active | critical / production | - |
| `eval-nhi-003` | positive | `finance-reporting-prod` | terminated | active | active | high / production | - |
| `eval-nhi-004` | positive | `operations-dashboard-staging` | terminated | active | active | medium / staging | - |
| `eval-nhi-005` | distractor | `customer-profile-export-prod` | active | active | active | critical / production | owner가 퇴사자가 아님 |
| `eval-nhi-006` | distractor | `refund-report-export-prod` | terminated | expired | active | critical / production | credential이 active가 아님 |
| `eval-nhi-007` | distractor | `marketing-segment-export-prod` | terminated | active | inactive | critical / production | active access edge가 아님 |
| `eval-nhi-008` | distractor | `team-notification-dev` | terminated | active | active | low / development | 민감 자산 도달 조건을 만족하지 않음 |
| `eval-nhi-009` | distractor | `customer-order-export-prod` | active | active | active | critical / production | owner가 퇴사자가 아님 |
| `eval-nhi-010` | distractor | `seller-settlement-export-prod` | terminated | expired | active | critical / production | credential이 active가 아님 |
| `eval-nhi-011` | distractor | `support-case-export-prod` | terminated | active | inactive | critical / production | active access edge가 아님 |
| `eval-nhi-012` | distractor | `catalog-preview-dev` | terminated | active | active | low / development | 민감 자산 도달 조건을 만족하지 않음 |
| `eval-nhi-013` | distractor | `loyalty-segment-export-prod` | active | active | active | critical / production | owner가 퇴사자가 아님 |
| `eval-nhi-014` | distractor | `finance-ledger-export-prod` | terminated | expired | active | critical / production | credential이 active가 아님 |
| `eval-nhi-015` | distractor | `crm-audience-export-prod` | terminated | active | inactive | critical / production | active access edge가 아님 |
| `eval-nhi-016` | distractor | `qa-dashboard-dev` | terminated | active | active | low / development | 민감 자산 도달 조건을 만족하지 않음 |
| `eval-nhi-017` | normal | `operations-dashboard-staging` | active | expired | active | medium / staging | owner가 퇴사자가 아니고 credential도 active가 아님 |
| `eval-nhi-018` | normal | `order-events-prod` | active | expired | active | high / production | owner가 퇴사자가 아니고 credential도 active가 아님 |
| `eval-nhi-019` | normal | `catalog-preview-dev` | active | active | active | low / development | owner가 퇴사자가 아니고 민감 자산 도달 조건도 만족하지 않음 |
| `eval-nhi-020` | normal | `team-notification-dev` | active | active | active | low / development | owner가 퇴사자가 아니고 민감 자산 도달 조건도 만족하지 않음 |

## 대표 데모 케이스

첫 번째 positive는 대표 데모 케이스로 고정한다.

| 항목 | 값 |
| --- | --- |
| case_id | `eval-nhi-001` |
| owner userPrincipalName | `kim.minsu@company.com` |
| application appId | `d8f4a5b6-7c8d-4e91-9f02-1a2b3c4d5e6f` |
| application displayName | `sp-crm-customer-export-prod` |
| application createdDateTime | `2026-03-15T09:00:00Z` |
| credential keyId | `c0ffee12-3456-7890-abcd-1234567890ab` |
| assetId | `asset-customer-export-storage-prod` |
| asset name | `customer-export-storage-prod` |
| asset sensitivity | `critical` |

파일 간 추적 순서:

```text
identity/lifecycle_seed.jsonl
  -> owner UPN과 퇴사 상태 확인
azure/application_owners.jsonl
  -> owner UPN이 owner로 남은 appId 확인
azure/applications.jsonl
  -> appId가 어떤 App Registration인지 확인
azure/password_credentials.jsonl
  -> 같은 appId의 active client secret metadata 확인
access/access_edges_seed.jsonl
  -> appId/principalId가 접근하는 assetId 확인
assets/assets_seed.jsonl
  -> assetId의 sensitivity 확인
```

## 설계 문서 대비 구현 범위

현재 generator는 `docs/design/expansion/`의 전체 distractor catalog를 구현하지 않는다. B-S2/NHI residual access 검증에 필요한 최소 범위만 구현한다.

구현됨:

- B-S2/NHI 중심 positive 생성
- `is_distractor=true` 행은 `is_planted_risk=false`
- positive 조건 중 하나만 깨는 최소 distractor
  - `owner_active`: owner가 퇴사자가 아님
  - `credential_expired`: credential이 active가 아님
  - `access_inactive`: active access edge가 아님
  - `asset_low_dev`: 민감 자산 도달 조건을 만족하지 않음
- 대표 데모 케이스 1건 고정 key 포함

아직 미구현:

- Pattern 1(A-S1/A-S2) SaaS/사람 계정 distractor
- NHI 자체 `revoked` lifecycle
- 소유권 팀 이전 완료 케이스
- grace-period 예외 케이스
- 만료 임박 credential 시간축 함정
- holdout split
- positive/distractor 시간 분포 통계 검증

## 규모 기준

dev 데이터는 ML 학습용이 아니라 룰 검증과 데모용이다.

- `20`: 사람이 검토하기 위한 최소 샘플
- `100`: 분포와 edge 연결을 보기 위한 중간 샘플
- `1000`: Databricks dev catalog 적재 검증용 확장 샘플

Databricks 적재는 사용자 허가 후 실행한다.
