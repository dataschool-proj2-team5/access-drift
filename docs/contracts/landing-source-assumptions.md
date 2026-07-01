# Landing Source Assumptions

## 목적

이 문서는 Landing 합성 데이터 필드가 실제 source/API/export 응답에 존재하는 형태를 따른 값인지, 데모와 탐지를 위해 별도로 보강한 값인지 구분한다. 이 데이터는 실제 API 호출 결과가 아니라 합성 데이터다.

Bronze/Silver 컬럼 계약은 각 schema contract에서 관리한다. 이 문서는 컬럼 타입이나 테이블 구조가 아니라 입력 데이터의 source shape 가정만 다룬다.

## 분류 기준

| 분류 | 의미 |
| --- | --- |
| source 원본형 | 실제 source API 또는 export 응답에 존재하는 형태를 따르는 합성 필드 |
| source-like 보강 | 운영 source, CMDB, HR export, tagging 정책 등에서 올 수 있으나 합성 seed에서는 합성 생성기가 보강하는 필드 |
| eval 전용 | 정답지 또는 평가용 필드. Landing/Bronze/Silver 입력에 포함하지 않는다. |
| 저장 금지 | secret value, token value, private key value처럼 어떤 레이어에도 저장하지 않는 값 |

## Landing 합성 입력 가정

| Source 영역 | Entity | Field | 분류 | 비고 |
| --- | --- | --- | --- | --- |
| Microsoft Entra ID | application | `appId` | source 원본형 | App Registration 식별자 |
| Microsoft Entra ID | application | `displayName` | source 원본형 | App Registration 표시 이름 |
| Microsoft Entra ID | application | `createdDateTime` | source 원본형 | App Registration 생성 시각 |
| Microsoft Entra ID | application owner | `appId` | source 원본형 | owner 관계의 대상 application |
| Microsoft Entra ID | application owner | `userPrincipalName` | source 원본형 | owner principal 식별자 |
| Microsoft Entra ID | password credential | `appId` | source 원본형 | credential이 연결된 application |
| Microsoft Entra ID | password credential | `keyId` | source 원본형 | credential 식별자 |
| Microsoft Entra ID | password credential | `displayName` | source 원본형 | credential 표시 이름 |
| Microsoft Entra ID | password credential | `endDateTime` | source 원본형 | credential 만료 시각 |
| Microsoft Entra ID | password credential | `status` | source-like 보강 | 합성 seed에서는 `active`/`expired`를 명시한다. 운영에서는 만료 시각, 회수 상태, 수집 시점 기준으로 계산될 수 있다. |
| HR/IdP export | identity lifecycle | `userPrincipalName` | source 원본형 | 사용자 식별자 |
| HR/IdP export | identity lifecycle | `displayName` | source 원본형 | 사용자 표시 이름. 대시보드 표시용 이름이며 식별/조인은 `userPrincipalName`을 기준으로 한다. |
| HR/IdP export | identity lifecycle | `employmentStatus` | source-like 보강 | 실제 source마다 명칭이 다를 수 있어 공통 seed 필드로 둔다. |
| HR/IdP export | identity lifecycle | `terminationDate` | source-like 보강 | HR/IdP에서 제공 가능한 퇴사일 또는 비활성 기준일로 가정한다. |
| Asset inventory | asset | `assetId` | source-like 보강 | CMDB, cloud inventory, tagging export에서 오는 자산 식별자로 가정한다. |
| Asset inventory | asset | `name` | source-like 보강 | 자산 표시 이름 |
| Asset inventory | asset | `environment` | source-like 보강 | 운영/스테이징/개발 환경 구분 |
| Asset inventory | asset | `sensitivity` | source-like 보강 | CMDB, data classification, tag 정책에서 오는 민감도 구분으로 가정한다. |
| Access export | access edge | `principalId` | source-like 보강 | 접근 주체 식별자 |
| Access export | access edge | `assetId` | source-like 보강 | 접근 대상 자산 식별자 |
| Access export | access edge | `relationship` | source-like 보강 | source별 권한 관계를 공통 관계명으로 맞춘 값 |
| Access export | access edge | `permission` | source-like 보강 | IAM/RBAC/export에서 올 수 있는 권한명 |
| Access export | access edge | `status` | source-like 보강 | 접근 관계의 활성 상태 |
| Access export | access edge | `lastUsedDateTime` 또는 `last_used_at` | source-like 보강 | 합성 입력에서는 접근 관계의 마지막 사용 시각으로 둘 수 있다. 실제 운영에서는 Entra application/passwordCredential API 원본 필드가 아니라 sign-in/audit log에서 계산될 수 있는 값으로 본다. |
| GitHub | app | `appId`, `slug`, `displayName`, `status`, `ownerEmail`, `ownerEmploymentStatus`, `ownerTerminationDate` | source-like 보강 | GitHub App 또는 bot principal metadata와 퇴사 owner 근거를 source-like 형태로 둔다. 실제 API connector는 범위 밖이다. |
| GitHub | credential | `appId`, `credentialId`, `credentialType`, `displayName`, `status`, `expiresAt` | source-like 보강 | deploy key/PAT metadata만 저장한다. credential value는 저장하지 않는다. |
| GitHub | repo | `repoId`, `name`, `visibility`, `environment`, `sensitivity` | source-like 보강 | private repo 또는 production repo asset 예시다. |
| GitHub | access edge | `principalId`, `assetId`, `relationship`, `permission`, `status` | source-like 보강 | GitHub App 또는 bot이 repo에 갖는 접근 관계 예시다. |
| Google Workspace | user | `userId`, `email`, `displayName`, `status`, `employmentStatus`, `terminationDate` | source-like 보강 | SaaS HI principal과 퇴사/정지 상태 근거 예시다. |
| Google Workspace | asset | `assetId`, `name`, `assetType`, `environment`, `sensitivity` | source-like 보강 | shared drive 또는 민감 문서 asset 예시다. |
| Google Workspace | access edge | `principalId`, `assetId`, `relationship`, `permission`, `status` | source-like 보강 | user가 shared drive 또는 문서에 갖는 권한 관계 예시다. |
| Slack | user | `userId`, `email`, `displayName`, `status`, `employmentStatus`, `terminationDate` | source-like 보강 | SaaS HI principal과 퇴사/비활성 상태 근거 예시다. |
| Slack | channel | `channelId`, `name`, `channelType`, `environment`, `sensitivity` | source-like 보강 | private channel 또는 민감 운영 channel asset 예시다. |
| Slack | access edge | `principalId`, `assetId`, `relationship`, `permission`, `status` | source-like 보강 | user가 Slack channel에 갖는 접근 관계 예시다. |

## Landing에 포함하지 않는 값

| 값 | 분류 | 처리 |
| --- | --- | --- |
| `is_planted_risk` | eval 전용 | Eval 입력에만 둔다. |
| `is_distractor` | eval 전용 | Eval 입력에만 둔다. |
| `expected_severity` | eval 전용 | Eval 입력에만 둔다. |
| `truth_class` | eval 전용 | Eval 입력에만 둔다. |
| client secret value | 저장 금지 | 저장하지 않는다. |
| token value | 저장 금지 | 저장하지 않는다. |
| private key value | 저장 금지 | 저장하지 않는다. |

GitHub, Google Workspace, Slack 확장 예시는 기존 Entra ID 기반 eval key를 변경하지 않고 뒤에 append한다. eval label, planted risk 여부, expected severity는 기존과 동일하게 Eval 입력에만 둔다.

## 작성 기준

- source 원본형 필드는 가능하면 실제 source 응답 명칭을 유지한다.
- source-like 보강 필드는 실제 운영 source에서 올 수 있는 업무 사실이어야 한다.
- 평가 정답이나 탐지 기대값은 Landing 원본에 섞지 않는다.
- source-like 보강 필드가 늘어나면 어떤 source에서 올 수 있는지 이 문서에 먼저 기록한다.
