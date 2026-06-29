# Databricks Environment Policy

**버전:** v0.1  
**기준:** 2026년 6월 29일  
**상태:** Sprint 1 실행 기준  
**관련 문서:** [Sprint 1 DE Scope](./sprint1-de-scope.md), [Demo Scenario](../product/demo.md), [Infra README](../../infra/README.md)

---

## 1. 목적

이 문서는 Access Drift의 Databricks 실행 환경, Unity Catalog catalog, ADLS raw 경로를 어떻게 나눌지 정리한다.

제품 데모 시나리오와 Databricks 실행 target을 혼동하지 않는 것이 핵심이다. `demo.md`의 데모는 사용자가 보게 될 대표 리스크 케이스이며, 별도 Databricks 실행 환경을 뜻하지 않는다.

---

## 2. 기본 원칙

1. PoC 재현과 본개발 실행은 catalog와 raw 경로로 분리한다.
2. 데이터 레이어는 catalog가 아니라 schema로 분리한다.
3. Sprint 1 대표 데모 케이스는 dev 데이터 안의 고정 시나리오로 관리한다.
4. Databricks workspace 배포 경로는 코드 배포 위치이며, 데이터 분리 기준은 catalog와 raw 경로다.

---

## 3. Catalog와 Target 기준

| 구분 | Databricks target | Catalog | ADLS raw 경로 | 용도 |
| --- | --- | --- | --- | --- |
| PoC 재현 | `poc` | `access_drift` | `lakehouse/raw/poc/` | PoC 완료 기준 재확인 |
| 본개발 | `dev` | `access_drift_dev` | `lakehouse/raw/dev/` | S1 개발, 탐색, 대표 데모 케이스 검증 |

`poc` target은 과거 PoC 결과를 다시 확인할 때 사용한다. S1 구현과 데모 준비는 `dev` target을 기준으로 한다.

다른 catalog는 임의로 사용하지 않는다. 예를 들어 `acdrift_dbx` 같은 개인/실험 catalog에 테이블을 만들고 결과를 공유하지 않는다. 기존 실험 결과가 남아 있다면 PR이나 검증 근거에서는 공식 catalog 기준 결과와 구분해서 설명한다.

---

## 4. Schema 기준

각 catalog 안에서는 동일한 레이어 schema를 사용한다.

| Schema | 역할 |
| --- | --- |
| `bronze` | 원본 구조에 가까운 적재 |
| `silver` | source 종속성을 낮춘 공통 모델 |
| `intermediate` | 탐지 후보와 근거 조합 |
| `gold` | Risk Card와 App 조회용 결과 |
| `eval` | 정답지와 검증 전용 데이터 |

레이어를 나누기 위해 `access_drift_bronze`, `access_drift_silver` 같은 별도 catalog를 만들지 않는다.

공식 schema 밖에 임의 테이블을 만들지 않는다. 필요한 테이블은 데이터 계약, migration, Databricks job/notebook 변경과 함께 PR에 포함한다. 임시 확인용 테이블이 필요하면 작업자 개인 scratch 영역에서만 사용하고, S1 산출물이나 검증 결과로 참조하지 않는다.

---

## 5. Demo Scenario 데이터 기준

`demo.md`의 대표 데모 케이스는 별도 `demo` target이나 별도 catalog로 관리하지 않는다.

S1에서는 대표 리스크 케이스를 `access_drift_dev`의 개발용 합성 데이터 안에 포함한다. 데이터 생성 시에는 다음과 같은 식별 기준을 둘 수 있다.

- `scenario_id`
- `case_id`
- `is_demo_case`
- `risk_case_key`

이 식별자는 대표 케이스를 화면, eval, 검증 SQL에서 찾기 쉽게 하기 위한 것이며, 데이터 레이어 분리 기준은 아니다.

---

## 6. DLT 적용 기준

DLT를 본도입하더라도 별도 catalog를 만들지 않는다.

- 실험 단계: `access_drift_dev` 안의 임시 schema 또는 제한된 테이블에서 검증한다.
- 본도입 단계: 최종 산출물은 공식 레이어 schema에 저장한다.
- Sprint 1 우선 범위: Bronze/Silver 품질검증과 재실행 안정성 확인이다.

예시:

```text
access_drift_dev.bronze
access_drift_dev.silver
access_drift_dev.intermediate
access_drift_dev.gold
access_drift_dev.eval
```

---

## 7. 실행 문서와 역할

이 문서는 정책 기준만 정의한다. 실제 명령과 bootstrap 절차는 [Infra README](../../infra/README.md)를 따른다.

| 문서 | 역할 |
| --- | --- |
| `docs/engineering/databricks-environment-policy.md` | catalog, target, raw 경로, demo case 관리 원칙 |
| `infra/README.md` | Databricks Bundle 실행 명령, Unity Catalog bootstrap, grant 절차 |
| `databricks.yml` | 실제 bundle target과 job parameter 정의 |

---

## 8. 후속 작업

### 8.1 dev seed 경로 변수화

bundle에는 `data/dev`가 sync path로 추가되어 있고, seed 입력 경로는 `databricks.yml`의 `seed_data_path` 변수로 제어한다.

기본값:

```yaml
variables:
  seed_data_path:
    description: Repo-relative seed data path deployed with the bundle
    default: data/dev/landing/raw
  eval_seed_path:
    description: Repo-relative eval seed JSONL path deployed with the bundle
    default: data/dev/eval/ground_truth_case.jsonl

targets:
  poc:
    variables:
      seed_data_path: data/poc/landing/raw
      eval_seed_path: data/poc/eval/ground_truth_case.jsonl
  dev:
    default: true
```

`01_synthetic_data.ipynb`는 `seed_data_path`와 `raw_base_path`를 함께 받아 다음을 수행한다.

1. bundle에 배포된 seed 파일을 읽는다.
2. target별 ADLS raw 경로로 복사한다.
3. 이후 `02_ingest.ipynb`가 같은 raw 경로를 읽어 Bronze로 적재한다.

### 8.2 대표 데모 케이스 식별자 확정

S1 합성 데이터 생성 시 대표 케이스를 안정적으로 찾을 수 있도록 `scenario_id`, `case_id`, `risk_case_key` 중 어떤 값을 공식 식별자로 쓸지 정한다.

이 결정은 Gold/Risk Card, eval 검증, App 조회 조건과 연결된다.
