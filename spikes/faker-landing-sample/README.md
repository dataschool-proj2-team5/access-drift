# Faker Landing Sample Spike

## 목적

이 spike는 이슈 #41에서 요구한 작은 Landing JSONL 샘플을 같은 seed로 재생성하고 관계 정합성을 확인한다.

- 고정된 시나리오 skeleton이 ID와 관계를 결정한다.
- Faker는 UPN, 표시명, 생성일, 마지막 사용일 같은 세부값만 채운다.
- 위험도와 eval label은 Landing 파일에 저장하지 않는다.
- client secret은 값이 아닌 metadata만 생성한다.

Landing lifecycle 계약에는 사람 이름 필드가 없으므로 이름을 임의 필드로 추가하지 않는다. 사람 관련 Faker 값은 계약에 존재하는 UPN에만 사용한다.

## 독립 실행 환경

저장소 공용 Python 환경은 변경하지 않는다. Python 3.11 이상에서 이 디렉터리 전용 venv를 만든다.

```powershell
cd spikes/faker-landing-sample
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

`.venv/`는 저장소의 `.gitignore`에 포함되어 있다.

## 생성과 검증

기본 seed는 `41`이며, 결과는 `data/dev/landing/raw/` 아래에 생성된다.
생성된 JSONL은 로컬 검증용 산출물이므로 Git에 커밋하지 않으며 `.gitignore`에 포함되어 있다.

```powershell
python generate.py
python verify.py
```

다른 출력 위치에서 생성 동작만 확인하려면 다음처럼 실행한다.

```powershell
python generate.py --seed 41 --output-root ./tmp-output
```

`verify.py`는 다음 항목을 확인한다.

- 동일 seed로 두 번 생성한 6개 파일의 byte와 SHA-256이 같은지
- 파일별 필드, UUID, 날짜/timestamp 포맷이 계약과 맞는지
- owner, lifecycle, application, credential, access edge, asset 참조가 이어지는지
- ID, UPN이 중복되지 않는지
- active/expired credential, active/terminated owner가 포함되는지
- critical/high/medium/low sensitivity asset이 포함되는지
- eval label과 secret value 필드가 없는지

## 출력 구조와 필드 매핑

| Landing 파일 | 생성 필드 |
| --- | --- |
| `azure/applications.jsonl` | `appId`, `displayName`, `createdDateTime` |
| `azure/application_owners.jsonl` | `appId`, `userPrincipalName` |
| `azure/password_credentials.jsonl` | `appId`, `keyId`, `displayName`, `endDateTime`, `status` |
| `identity/lifecycle_seed.jsonl` | `userPrincipalName`, `employmentStatus`, `terminationDate` |
| `assets/assets_seed.jsonl` | `assetId`, `name`, `environment`, `sensitivity` |
| `access/access_edges_seed.jsonl` | `principalId`, `assetId`, `relationship`, `permission`, `status`, `lastUsedDateTime` |

각 파일은 핵심 케이스 4건과 배경 케이스 4건으로 총 8행이다. JSONL은 UTF-8과 LF로 기록하고 시나리오 순서를 고정한다.

## 핵심 시나리오

아래 `case` 값은 생성기 내부 skeleton과 이 문서에서만 사용한다. Landing row에는 넣지 않는다.

| case | owner | credential | asset | 설명 |
| --- | --- | --- | --- | --- |
| Critical | terminated | active | critical, production | 퇴사자가 owner였던 `sp-crm-customer-export-prod`의 active credential이 `crm-customer-export-prod`에 접근한다. |
| High | active | active | high, production | 재직자 소유의 별도 app과 high asset을 사용해 Critical 경로와 구분한다. |
| Medium | active | expired | medium, staging | 만료 credential과 medium asset 조합이라 active 잔존 credential 경로가 아니다. |
| Normal | active | active | low, development | 재직자, 유효 credential, 낮은 민감도 자산으로 위험 후보가 아닌 기준 조합을 제공한다. |

배경 케이스는 active/expired credential, active/terminated owner, low/medium/high asset 조합을 추가해 한 가지 대표 케이스만으로 검증하는 문제를 줄인다.

## 계약 기준

- `docs/contracts/landing-source-assumptions.md`
- `docs/contracts/bronze-schema.md`
- `docs/product/demo.md`
