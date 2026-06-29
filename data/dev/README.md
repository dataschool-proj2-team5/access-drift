# Dev 데이터 저장 및 라벨 분리 기준

이 문서는 본개발/dev 합성 데이터의 저장 위치, 대표 데모 케이스 고정 방식, Landing 입력과 Eval 라벨 분리 기준을 정의한다.

`data/dev`는 PoC 재현용 `data/poc`와 분리한다. 실제 데이터 생성 로직은 별도 작업에서 구현하고, 이 문서는 생성 결과가 따라야 할 기준만 다룬다.

## 경로 기준

| 경로 | 역할 |
| --- | --- |
| `data/dev/landing/raw/` | dev용 Landing 입력 JSONL |
| `data/dev/eval/` | dev용 eval 정답/검증 JSONL |
| `data/dev/README.md` | dev 데이터 구성, 대표 케이스 key, 검증 방법 |

Databricks dev target은 `access_drift_dev` catalog와 `raw/dev` 경로를 사용한다. PoC target의 `access_drift` catalog, `raw/poc` 경로와 섞지 않는다.

## Landing 입력 원칙

Landing 입력은 source/API/export 응답에 가까운 사실 데이터만 담는다.

포함:

- App Registration / Service Principal metadata
- application owner 관계
- credential metadata
- identity lifecycle context
- asset metadata
- access edge

제외:

- `case_id`
- `scenario_id`
- `scenario_family`
- `is_planted_risk`
- `is_distractor`
- `expected_severity`
- `truth_class`
- secret value, token value, private key value

정답 라벨과 평가용 필드는 `data/dev/eval/`에만 둔다.

## Eval 기준

Eval은 탐지 결과 검증용 정답지다. 탐지 파이프라인은 eval을 입력으로 읽지 않는다.

평가 조인 key:

```text
(subject_type, subject_id, asset_id, drift_type)
```

`subject_id`와 `asset_id`는 source id 기준이다. Silver와 비교할 때는 각각 `silver_principals.source_principal_id`, `silver_assets.source_asset_id`와 매칭한다.

`case_id`는 사람이 읽는 eval 전용 핸들이다. Landing/Bronze/Silver에는 저장하지 않는다.

예:

```text
case_id: nhi_ra_owner_offboarding_pos_001
drift_type: nhi_residual_access
scenario_family: owner_offboarding
```

## 대표 데모 케이스

대표 데모 케이스는 dev 데이터에 고정 포함한다.

대표 케이스는 별도 라벨을 Landing에 넣지 않고, README와 eval에서 주요 key를 추적한다.

README에는 최소한 아래 내용을 기록한다.

- 대표 케이스의 `case_id`
- App Registration / Service Principal source id
- owner UPN
- credential metadata key
- asset source id
- access edge 관계
- 파일 간 ID 추적 순서

파일 간 추적 순서 예:

```text
identity/lifecycle_seed.jsonl
  -> 퇴사자 UPN 확인
azure/application_owners.jsonl
  -> 퇴사자 UPN이 owner로 남은 appId 확인
azure/applications.jsonl
  -> appId가 어떤 App Registration인지 확인
azure/password_credentials.jsonl
  -> 같은 appId의 active client secret metadata 확인
access/access_edges_seed.jsonl
  -> appId/principalId가 접근하는 assetId 확인
assets/assets_seed.jsonl
  -> assetId의 sensitivity 확인
```

Demo Scenario가 변경되면 아래 항목을 함께 확인한다.

- `docs/product/demo.md`의 대표 케이스 설명
- `data/dev/README.md`의 대표 케이스 key와 추적 순서
- `data/dev/landing/raw/...`의 source-like 입력 파일
- `data/dev/eval/...`의 eval case

### 대표 Landing fixture

이슈 #40에서는 대표 데모 케이스를 사람이 한 눈에 따라갈 수 있는 단일 Landing 흐름으로 둔다.

```text
김민수(terminated, 2026-06-10)
  -> sp-crm-customer-export-prod
  -> active credential metadata
  -> crm-customer-export-prod storage
```

구성 파일:

```text
data/dev/landing/raw/azure/applications.jsonl
data/dev/landing/raw/azure/application_owners.jsonl
data/dev/landing/raw/azure/password_credentials.jsonl
data/dev/landing/raw/identity/lifecycle_seed.jsonl
data/dev/landing/raw/assets/assets_seed.jsonl
data/dev/landing/raw/access/access_edges_seed.jsonl
```

주요 ID와 키:

| 항목 | 값 |
| --- | --- |
| case_id | `eval-nhi-demo-001` |
| owner userPrincipalName | `kim.minsu@company.com` |
| application appId | `d8f4a5b6-7c8d-4e91-9f02-1a2b3c4d5e6f` |
| credential keyId | `c0ffee12-3456-7890-abcd-1234567890ab` |
| assetId | `asset-customer-export-storage-prod` |

수동 확인:

- 각 JSONL은 한 줄에 하나의 JSON 객체만 둔다.
- `appId`, `userPrincipalName`, `keyId`, `assetId`가 서로 연결되는지 확인한다.
- access edge는 `read/list` 권한만 표현한다.
- `is_planted_risk`, `is_distractor`, `expected_severity`, `truth_class`는 넣지 않는다.
- secret value, token value, private key value는 저장하지 않는다.

## 케이스 구성 기준

### Positive

`nhi_residual_access` positive는 아래 조건이 모두 성립하는 케이스다.

- owner가 퇴사자다.
- App Registration / Service Principal이 존재하며 활성으로 간주된다.
- client secret metadata가 active 상태다.
- 민감 자산에 대한 active access edge가 있다.

### Distractor

Distractor는 positive와 유사하지만 positive 조건 중 일부가 깨진 케이스다.

DS가 별도 distractor/eval 규칙을 제공하면 그 기준을 우선한다. 별도 기준이 없으면 아래 축을 우선 사용한다.

- owner는 퇴사했지만 credential은 expired
- credential은 active지만 owner는 재직
- access는 있지만 asset sensitivity가 낮음
- app/credential은 active지만 access edge가 inactive
- owner 관계가 없음

### Normal

Normal은 탐지되지 않아야 하는 정상 케이스다.

예:

- 재직자 owner가 관리하는 App Registration
- credential이 정상 관리되는 상태
- 낮거나 중간 민감도의 asset 접근

## 규모 기준

dev 데이터는 ML 학습용이 아니라 룰 검증과 데모용이다.

권장 상한:

- identity 최대 1,000건
- positive 최대 40건
- 나머지는 normal과 distractor로 구성

precision/recall 평가용 holdout은 후순위로 보류한다.

## 시간 필드 기준

시간 필드는 서로 모순되지 않아야 한다.

- `termination_date`: owner 퇴사 또는 비활성 기준일
- `createdDateTime`: App Registration 생성 시각
- `endDateTime`: credential 만료 시각
- `lastUsedDateTime` 또는 `last_used_at`: 접근 관계의 마지막 사용 시각

예:

- active credential은 `endDateTime`이 미래이거나 null이다.
- expired credential은 `endDateTime`이 과거다.
- 퇴사자 positive는 `termination_date`가 기준일보다 과거다.
