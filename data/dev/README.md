# Dev Landing Fixtures

이 디렉터리는 이슈 #40용 대표 데모 Landing fixture를 둔다. 목적은 랜덤/대량 생성이 아니라, 사람이 한 눈에 따라갈 수 있는 단일 흐름을 만드는 것이다.

## 구성

```text
data/dev/landing/raw/azure/applications.jsonl
data/dev/landing/raw/azure/application_owners.jsonl
data/dev/landing/raw/azure/password_credentials.jsonl
data/dev/landing/raw/identity/lifecycle_seed.jsonl
data/dev/landing/raw/assets/assets_seed.jsonl
data/dev/landing/raw/access/access_edges_seed.jsonl
```

## 대표 흐름

```text
김민수(terminated, 2026-06-10)
  -> sp-crm-customer-export-prod
  -> active credential metadata
  -> crm-customer-export-prod storage
```

## 파일 역할

| 파일 | 역할 |
| --- | --- |
| `azure/applications.jsonl` | App Registration 원본 메타데이터 |
| `azure/application_owners.jsonl` | application과 owner 관계 |
| `azure/password_credentials.jsonl` | active credential metadata |
| `identity/lifecycle_seed.jsonl` | 사용자 재직/퇴사 상태 |
| `assets/assets_seed.jsonl` | 접근 대상 asset 메타데이터 |
| `access/access_edges_seed.jsonl` | principal -> asset 접근 관계 |

## 주요 ID와 키

| 항목 | 값 |
| --- | --- |
| owner userPrincipalName | `kim.minsu@company.com` |
| application appId | `d8f4a5b6-7c8d-4e91-9f02-1a2b3c4d5e6f` |
| credential keyId | `c0ffee12-3456-7890-abcd-1234567890ab` |
| assetId | `asset-customer-export-storage-prod` |

## 추적 순서

1. `application_owners.jsonl`에서 owner UPN과 application `appId`를 확인한다.
2. `applications.jsonl`에서 해당 `appId`의 App Registration을 확인한다.
3. `password_credentials.jsonl`에서 같은 `appId`의 credential metadata를 확인한다.
4. `identity/lifecycle_seed.jsonl`에서 owner의 employment status와 termination date를 확인한다.
5. `access_edges_seed.jsonl`에서 `principalId`와 `assetId`가 각각 application과 asset으로 해석되는지 확인한다.
6. `assets_seed.jsonl`에서 asset 이름과 민감도(`critical`)를 확인한다.

## 수동 확인

- 각 JSONL은 한 줄에 하나의 JSON 객체만 둔다.
- `appId`, `userPrincipalName`, `keyId`, `assetId`가 서로 연결되는지 확인한다.
- access edge는 `read/list` 권한만 표현한다.
- `is_planted_risk`, `is_distractor`, `expected_severity`, `truth_class`는 넣지 않는다.
- secret value, token value, private key value는 저장하지 않는다.

