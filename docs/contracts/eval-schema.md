# Eval Schema Contract

## 버전

```text
version: 0.1.0
status: draft
updated_at: 2026-06-24
```

## 변경이력

| 버전 | 날짜 | 변경 내용 |
| --- | --- | --- |
| 0.1.0 | 2026-06-24 | DS 초안 기준 PoC 최소 eval 정답 테이블 계약 추가 |

## 목적

Eval은 탐지 품질을 확인하기 위한 정답/평가용 격리 레이어다.

운영 탐지 파이프라인은 Eval을 입력으로 사용하지 않는다. Eval은 Intermediate 또는 Gold 결과가 생성된 뒤, 탐지 결과가 의도한 정답과 맞는지 채점하거나 룰 변경 전후 회귀 검증을 수행할 때만 사용한다.

## 원칙

- Eval은 탐지 로직이 읽지 않는다.
- Eval은 Intermediate/Gold 결과 채점과 회귀 검증에만 사용한다.
- Landing raw, Bronze, Silver에는 정답 라벨과 planted risk 정보를 넣지 않는다.
- Secret value, token value, private key value는 저장하지 않는다.
- PoC에서는 최소 정답 테이블 1개로 시작한다.

## ground_truth_case

PoC 합성 데이터에 심어 둔 정답 케이스를 저장한다.

탐지 결과와 평가 결과는 아래 eval key로 조인한다.

```text
(subject_type, subject_id, asset_id, drift_type)
```

`case_id`는 테이블 PK와 사람이 읽기 쉬운 케이스 핸들을 위한 surrogate id다. 평가 조인에는 `case_id`가 아니라 eval key를 사용한다.

`subject_id`와 `asset_id`는 Bronze row id가 아니라 source id 기준이다. Silver와 비교할 때는 각각 `silver_principals.source_principal_id`, `silver_assets.source_asset_id`와 매칭한다.

| 컬럼 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `case_id` | string | yes | PK. 사람이 읽는 케이스 핸들 |
| `scenario_id` | string | no | holdout 분리 단위 |
| `scenario_family` | string | no | 위험 케이스와 대응 distractor 묶음 |
| `subject_type` | string | yes | 정답의 주체 유형. PoC에서는 `nhi` |
| `subject_id` | string | yes | 정답 주체 id. PoC에서는 App Registration `app_id` |
| `asset_id` | string | yes | 접근 가능한 asset id |
| `drift_type` | string | yes | drift 유형. 예: `nhi_residual_access`. distractor는 가장 가까운 유형을 사용 |
| `is_planted_risk` | boolean | yes | 정답. `true`면 탐지되어야 할 실제 drift |
| `is_distractor` | boolean | yes | 함정 케이스 여부 |
| `pattern` | string | no | 탐지 패턴. 예: `P1`, `P2` |
| `expected_severity` | string | no | 기대 severity. 예: `HIGH`, `MEDIUM`, `LOW` |
| `seed_finding_type` | string | no | 합성 데이터 생성 의도를 설명하는 대표 화면 라벨. Gold/대시보드 결과가 반드시 동일해야 하는 hard assertion은 아님 |
| `label_reason` | string | no | 정답으로 분류한 이유 |
| `created_at` | timestamp | yes | eval case 생성 시각 |

## 라벨 해석

| 컬럼 조합 | 의미 |
| --- | --- |
| `is_planted_risk = true`, `is_distractor = false` | 탐지되어야 하는 실제 drift |
| `is_planted_risk = false`, `is_distractor = true` | 위험해 보이지만 정답 risk는 아닌 방해 케이스 |
| `is_planted_risk = false`, `is_distractor = false` | 탐지되지 않아야 하는 정상 케이스 |

`seed_finding_type`은 합성 데이터가 어떤 대표 화면 라벨을 재현하려는지 기록하는 선택 필드다. 탐지 품질 검증의 조인 key나 정답 판정 기준으로 사용하지 않는다.

현재 허용 후보:

```text
NHI Access Drift
NHI Credential Drift
NHI Permission Drift
HI Access Drift
HI Permission Drift
HI Stale Access
```

## Eval에 두지 않는 것

아래 항목은 Eval에 저장하지 않는다.

```text
secret value
token value
private key value
raw API payload
rendered dashboard copy
operator action state
```

## DDL

Databricks Eval DDL은 아래 파일에 둔다.

```text
sql/databricks/migrations/003_create_eval_tables.sql
```
