# Dev 합성 데이터 기준

`data/dev`는 본개발용 합성 데이터의 기준 위치다. PoC 재현용 `data/poc`와 분리하며, Databricks dev target은 `access_drift_dev` catalog와 `raw/dev` 경로를 사용한다.

생성기는 `data/dev/generator/`에 둔다. 생성된 JSONL은 로컬 검증과 Databricks 적재 입력으로만 사용하고 Git에는 커밋하지 않는다.

## 경로

| 경로 | 역할 |
| --- | --- |
| `data/dev/generator/` | dev Landing/Eval JSONL 생성 및 검증 코드 |
| `data/dev/landing/raw/` | dev용 Landing 입력 JSONL 생성 위치 |
| `data/dev/eval/ground_truth_case.jsonl` | dev용 eval 정답지 생성 위치 |
| `data/dev/context/` | Risk Card context 입력 JSONL 생성 위치 |

생성기는 Landing 입력, eval 정답지, Risk Card context를 함께 만들지만, 생성 파일 자체는 Git에 올리지 않는다.

## Source 확장 기준

기본 dev 데이터는 Microsoft Entra ID 기반 NHI residual access 케이스를 중심으로 생성한다. GitHub와 Google Workspace는 후속 확장 가능성을 확인하기 위한 소량 source-like 예시로 함께 생성한다.

| source | 목적 | ID namespace | eval 처리 |
| --- | --- | --- | --- |
| Microsoft Entra ID / HR / asset / access seed | S1 대표 NHI residual access 케이스 생성 | 기존 `appId`, `asset-...` | `ground_truth_case.jsonl`에 포함 |
| GitHub | 퇴사 owner가 남긴 GitHub App / credential / private repo 접근 예시 5건 | `gh-...` | 기존 eval 뒤에 append |
| Google Workspace | 퇴사·정지 사용자 / shared drive 또는 문서 접근 예시 5건 | `gws-...` | 기존 eval 뒤에 append |
| Slack | 퇴사·비활성 사용자 / private channel 접근 예시 5건 | `slack-...` | 기존 eval 뒤에 append |

GitHub/Google Workspace/Slack 예시는 기존 Entra ID 기반 source id, eval key, context key, `case_id`를 변경하지 않는다. eval/context에서는 사람이 검토하는 첫 20개 NHI 케이스 뒤에 GitHub 5건, Google Workspace 5건, Slack 5건을 append하고, `--size`가 20보다 크면 나머지 NHI 케이스를 그 뒤에 이어 붙인다. 따라서 `--size 20`의 eval/context는 `--size 100` 결과의 prefix로 유지된다.

## SaaS 확장 대표 케이스

GitHub, Google Workspace, Slack 케이스도 기존 20건 샘플처럼 "왜 residual access인지"를 source-like 입력에서 추적할 수 있어야 한다.

GitHub NHI 케이스:

| case_id | subject | residual 근거 | credential | edge | asset | 권한/민감도 |
| --- | --- | --- | --- | --- | --- | --- |
| `eval-github-nhi-001` | `gh-app-prod-deploy-bot` | owner `kim.minsu@company.com` terminated | active deploy key | active | `gh-repo-payment-service-prod` | admin / high |
| `eval-github-nhi-002` | `gh-app-security-audit-bot` | owner `jung.woojin@company.com` terminated | active PAT metadata | active | `gh-repo-infra-secrets-prod` | read / high |
| `eval-github-nhi-003` | `gh-app-data-export-bot` | owner `lee.dayoung@company.com` terminated | active deploy key | active | `gh-repo-customer-export-prod` | write / high |
| `eval-github-nhi-004` | `gh-app-finance-ci-bot` | owner `park.seojun@company.com` terminated | active PAT metadata | active | `gh-repo-finance-ledger-prod` | write / high |
| `eval-github-nhi-005` | `gh-app-support-automation-bot` | owner `kim.hana@company.com` terminated | active deploy key | active | `gh-repo-support-tools-prod` | admin / medium |

Google Workspace HI 케이스:

| case_id | subject | residual 근거 | edge | asset | 권한/민감도 |
| --- | --- | --- | --- | --- | --- |
| `eval-gws-hi-001` | `gws-user-lee.hana` | user suspended, employment terminated | active | `gws-drive-customer-support-shared` | editor / high |
| `eval-gws-hi-002` | `gws-user-park.jun` | user suspended, employment terminated | active | `gws-doc-finance-close-playbook` | viewer / medium |
| `eval-gws-hi-003` | `gws-user-choi.seo` | user suspended, employment terminated | active | `gws-sheet-vip-customer-list` | editor / critical |
| `eval-gws-hi-004` | `gws-user-jung.woo` | user suspended, employment terminated | active | `gws-drive-seller-settlement` | viewer / critical |
| `eval-gws-hi-005` | `gws-user-oh.sehun` | user suspended, employment terminated | active | `gws-doc-marketing-segment-plan` | editor / medium |

Slack HI 케이스:

| case_id | subject | residual 근거 | edge | asset | 권한/민감도 |
| --- | --- | --- | --- | --- | --- |
| `eval-slack-hi-001` | `slack-user-kang.yuna` | user deactivated, employment terminated | active | `slack-channel-customer-support-private` | member / critical |
| `eval-slack-hi-002` | `slack-user-lim.taehyun` | user deactivated, employment terminated | active | `slack-channel-security-incident` | member / high |
| `eval-slack-hi-003` | `slack-user-han.jimin` | user deactivated, employment terminated | active | `slack-channel-finance-settlement` | member / critical |
| `eval-slack-hi-004` | `slack-user-seo.minji` | user deactivated, employment terminated | active | `slack-channel-vip-customer-ops` | member / critical |
| `eval-slack-hi-005` | `slack-user-moon.jae` | user deactivated, employment terminated | active | `slack-channel-ops-runbook` | member / medium |

GitHub의 residual 근거는 `github/apps.jsonl`의 owner 상태 필드에서, Google Workspace의 residual 근거는 `google_workspace/users.jsonl`의 user 상태 필드에서, Slack의 residual 근거는 `slack/users.jsonl`의 user 상태 필드에서 확인한다.


## 대시보드 라벨 재현 기준

`seed_finding_type`은 합성 데이터 생성 의도를 설명하는 eval 전용 필드다. 탐지 결과가 반드시 이 값을 맞춰야 하는 hard assertion은 아니며, 대시보드 대표 라벨 샘플을 재현하기 위한 기준으로만 사용한다.

| seed_finding_type | 대표 케이스 | 근거 축 |
| --- | --- | --- |
| `NHI Access Drift` | `eval-nhi-001`, `eval-github-nhi-001` | NHI가 민감 자산에 접근 가능한 경로 |
| `NHI Credential Drift` | `eval-nhi-002`, `eval-github-nhi-002` | active credential/key/PAT metadata가 남은 경로 |
| `NHI Permission Drift` | `eval-nhi-003`, `eval-github-nhi-003` | admin/write/read 같은 권한이 남은 경로 |
| `HI Access Drift` | `eval-gws-hi-001`, `eval-slack-hi-001` | 퇴사/비활성 HI가 민감 자산에 접근 가능한 경로 |
| `HI Permission Drift` | `eval-gws-hi-002`, `eval-slack-hi-003` | viewer/editor/member 권한이 남은 경로 |
| `HI Stale Access` | `eval-gws-hi-005`, `eval-slack-hi-002` | 퇴사/비활성 계정 또는 멤버십이 stale 상태로 남은 경로 |


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
| owner displayName | `김민수` |
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

Risk Card context:

| 파일 | 역할 |
| --- | --- |
| `context/asset_context.jsonl` | `assetId` 기준 자산 설명과 데이터 범위 표시 |
| `context/assignment_routing.jsonl` | `subject_type + subject_id + asset_id + drift_type` 기준 조치 담당자/팀 표시 |

대표 데모 케이스의 context 값:

| context | 항목 | 값 |
| --- | --- | --- |
| `asset_context` | `source_asset_id` | `asset-customer-export-storage-prod` |
| `asset_context` | `data_scope_label` | `고객 DB` |
| `asset_context` | `sensitive_data_examples` | `고객 이름`, `전화번호`, `배송지`, `주문내역` |
| `asset_context` | `sensitivity_reason` | `고객 식별 정보와 배송지/주문내역을 포함하는 export storage` |
| `assignment_routing` | `subject_type` | `nhi` |
| `assignment_routing` | `subject_id` | `d8f4a5b6-7c8d-4e91-9f02-1a2b3c4d5e6f` |
| `assignment_routing` | `asset_id` | `asset-customer-export-storage-prod` |
| `assignment_routing` | `drift_type` | `nhi_residual_access` |
| `assignment_routing` | `assignee_name` | `이다영` |
| `assignment_routing` | `assignee_team` | `CRM 데이터 운영팀` |
| `assignment_routing` | `routing_reason` | `sp-crm-customer-export-prod와 customer-export-storage-prod의 운영 책임 팀` |

`asset_context`의 민감 데이터 예시는 실제 고객 데이터 값이 아니라 화면 설명용 문구다.

## 민감 자산 taxonomy 정합성

20건 샘플의 자산 민감도는 [Sensitive Asset Taxonomy](../../docs/contracts/sensitive-asset-taxonomy.md)를 참고해 해석한다.

| generator sensitivity | 샘플 자산 | taxonomy 해석 | context 표시 방향 |
| --- | --- | --- | --- |
| `critical` | `customer-export-storage-prod`, `customer-profile-export-prod`, `seller-settlement-export-prod` | 고객 식별 정보, 배송지/주문내역, 정산 정보처럼 보호 의무가 강한 데이터 | 고객/정산 데이터 범위와 민감 근거 표시 |
| `high` | `finance-reporting-prod`, `order-events-prod` | 매출, 주문 이벤트, 운영상 타격이 큰 핵심 비즈니스 데이터 | 핵심 비즈니스 데이터 범위 표시 |
| `medium` | `operations-dashboard-staging` | 비식별 통계, 개발로그, 스테이징 정보 같은 내부 운영 자산 | 내부 운영 데이터 범위 표시 |
| `low` | `team-notification-dev`, `catalog-preview-dev`, `qa-dashboard-dev` | 민감 자산으로 분류하지 않는 개발/테스트/비핵심 자산 | Dashboard 비교군과 normal/distractor용 비민감 개발 데이터로 표시 |

`low`는 주요 탐지 우선순위의 민감 자산은 아니지만 Dashboard에서 정상/비민감 비교군과 필터 표시를 위해 포함한다. `expected_severity`는 eval 검증용으로 asset sensitivity를 대문자로 매핑한다.

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
