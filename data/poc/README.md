# PoC 데이터 구성

이 문서는 PoC 파이프라인에서 사용하는 seed 데이터의 목적과 구성을 설명한다.

## 목적

PoC 데이터는 Access Drift 탐지 흐름을 재현하기 위한 작은 샘플 데이터다.

핵심 확인 대상은 다음 조합이다.

```text
퇴사자
  -> NHI 또는 application
  -> active credential
  -> 민감 자산 접근
```

이 조합이 Bronze, Silver, Intermediate, Gold 흐름에서 위험 후보로 이어지는지 확인하는 데 사용한다.

## 데이터 위치

현재 데이터는 두 형태로 분리한다.

```text
data/poc/landing/raw/
data/poc/eval/
```

`data/poc/landing/raw/`는 source/API/export 응답에 가깝게 분리한 입력 데이터다. Bronze 적재 기준은 이 형태를 우선으로 본다.

`data/poc/eval/`은 탐지 결과 검증을 위한 정답 데이터다. 정답 라벨과 planted risk 정보는 raw 입력에 넣지 않고 eval에만 둔다.

## 기준 데이터 규모

PoC 기준 데이터 규모는 아래 건수를 기준으로 한다.

| 데이터 | 기준 건수 |
| --- | ---: |
| App Registration / NHI | 10건 |
| Application owner 관계 | 10건 |
| Credential metadata | 10건 |
| User lifecycle | 10건 |
| Asset | 10건 |
| Access edge | 10건 |
| Eval ground truth | 3건 |

Eval ground truth 3건은 다음 구성을 기준으로 한다.

| truth 유형 | 기준 건수 |
| --- | ---: |
| planted risk positive | 2건 |
| normal | 1건 |
| distractor | 0건 |

이 규모는 Databricks 파이프라인 동작과 대표 탐지 경로 확인을 위한 최소 샘플이다. 성능 검증이나 통계적 평가 목적의 데이터 규모는 아니다.

## Landing raw 구성

```text
data/poc/landing/raw/azure/applications.jsonl
data/poc/landing/raw/azure/application_owners.jsonl
data/poc/landing/raw/azure/password_credentials.jsonl
data/poc/landing/raw/identity/lifecycle_seed.jsonl
data/poc/landing/raw/assets/assets_seed.jsonl
data/poc/landing/raw/access/access_edges_seed.jsonl
```

각 파일의 역할은 다음과 같다.

| 파일 | 기준 건수 | 의미 |
| --- | ---: | --- |
| `azure/applications.jsonl` | 10건 | Azure App Registration / NHI metadata |
| `azure/application_owners.jsonl` | 10건 | App Registration과 owner 관계 |
| `azure/password_credentials.jsonl` | 10건 | App Registration client secret metadata |
| `identity/lifecycle_seed.jsonl` | 10건 | 사용자 재직/퇴사/이동 상태 seed |
| `assets/assets_seed.jsonl` | 10건 | 접근 대상 asset 정보 |
| `access/access_edges_seed.jsonl` | 10건 | NHI에서 asset으로 이어지는 접근 관계 |

`identity/lifecycle_seed.jsonl`은 실제 IdP API 응답이 아니라 PoC용 lifecycle seed다. Azure owner 정보와 조인해 owner가 퇴사자, 이동자, 재직자인지 판단하는 데 사용한다.

## Eval 구성

```text
data/poc/eval/ground_truth_case.jsonl
```

이 파일은 `access_drift.eval.ground_truth_case`에 적재할 정답 데이터다.

정답 케이스의 평가 조인 키는 아래 조합이다.

```text
(subject_type, subject_id, asset_id, drift_type)
```

`case_id`는 사람이 읽기 쉬운 케이스 핸들이며, 실제 탐지 결과와의 조인은 eval key를 기준으로 한다.

Eval 데이터는 raw 입력이 아니다. Bronze/Silver 적재 대상이 아니라 탐지 결과 검증용 정답지로만 사용한다.

## 대표 위험 시나리오

대표 케이스는 아래 흐름이다.

```text
kim.minsu@company.com
  -> payment-service-prod
  -> prod-secret
  -> payment-api
```

의미는 다음과 같다.

- `kim.minsu@company.com`은 퇴사자로 설정한다.
- `payment-service-prod`는 운영 application이다.
- `prod-secret`은 아직 active 상태인 credential이다.
- `payment-api`는 민감도가 높은 production asset이다.

이 데이터는 탐지 로직이 “퇴사자와 연결된 live credential이 민감 자산 접근으로 이어지는지”를 확인하기 위한 기준 케이스다.

## 주의사항

- secret value, token value, private key value는 저장하지 않는다.
- credential은 값이 아니라 metadata만 사용한다.
- raw 입력에는 `is_planted_risk`, `is_distractor`, `expected_severity` 같은 eval 라벨을 넣지 않는다.
- `identity/lifecycle_seed.jsonl`은 PoC용 HR/IdP lifecycle context이며 실제 identity source 연동을 의미하지 않는다.
- asset sensitivity와 access edge는 실제 source가 붙기 전까지 seed 데이터로 표현한다.
- 계약 문서는 `docs/contracts/`에 두고, PoC 데이터 설명은 이 문서에서만 다룬다.
