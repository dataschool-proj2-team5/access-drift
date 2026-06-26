## 작업 내용

Databricks Delta Live Tables(DLT)를 사용해 현재 Access Drift PoC의 Silver 테이블에 데이터 품질검증 레이어를 최소 변경으로 붙일 수 있는지 검토하고, 작은 범위로 실험했다.

이번 작업은 기존 Bronze/Silver notebook 기반 적재 흐름을 전면 DLT로 전환하는 것이 아니라, `silver_principals` 1개 테이블을 대상으로 DLT Expectations가 품질검증 자동화에 활용 가능한지 확인하는 Spike 성격의 작업이다.

실험은 기존 Bronze/Silver 테이블을 직접 수정하지 않고, 별도 DLT/Lakeflow pipeline을 구성해 진행했다.

---

## 목적

현재 PoC 파이프라인은 row count 중심 smoke test로 적재 성공 여부를 확인하고 있다.

하지만 아래와 같은 데이터 품질 조건은 자동화되어 있지 않다.

* 필수 ID null 여부
* enum 허용값 위반 여부
* status 값 정합성
* 품질 위반 row 감지 또는 차단 여부

이번 실험에서는 DLT Expectations를 사용해 Databricks 안에서 품질 조건을 선언하고, 정상 데이터 통과 여부와 위반 데이터 감지/drop 처리가 가능한지 확인했다.

---

## 실험 대상

실험 대상 테이블:

```sql
access_drift.silver.silver_principals
```

DLT pipeline target:

```text
Catalog: acdrift_dbx
Schema: default
```

생성된 DLT 테이블:

```sql
acdrift_dbx.default.dlt_silver_principals_quality_check
acdrift_dbx.default.dlt_silver_principals_quality_check_with_invalid
acdrift_dbx.default.dlt_silver_principals_gate_drop_test
```

실험 대상은 `silver_principals` 1개 테이블로 제한했다.

---

## 적용한 품질검증 조건

`silver_principals`의 실제 값 분포를 먼저 확인한 뒤, 아래 5개 expectation을 정의했다.

| Expectation                 | 조건                                               | 목적                     |
| --------------------------- | ------------------------------------------------ | ---------------------- |
| `valid_principal_id`        | `principal_id IS NOT NULL`                       | Silver 내부 조인 키 null 방지 |
| `valid_source_principal_id` | `source_principal_id IS NOT NULL`                | 원천 principal id 누락 방지  |
| `valid_principal_kind`      | `principal_kind IN ('HI', 'NHI')`                | principal kind enum 검증 |
| `valid_principal_type`      | `principal_type IN ('app_registration', 'user')` | principal type enum 검증 |
| `valid_status`              | `status IN ('active', 'inactive', 'terminated')` | status enum 검증         |

사전 확인 결과:

```text
principal_kind:
- HI: 10
- NHI: 10

principal_type:
- app_registration: 10
- user: 10

status:
- active: 17
- inactive: 1
- terminated: 2
```

---

## 구현 내용

DLT pipeline source file:

```text
spikes/dlt-poc/quality_check_silver_principals.py
```

구현은 3개 DLT 테이블로 나누어 진행했다.

### 1. 정상 데이터 품질검증 테이블

```python
@dlt.table(
    name="dlt_silver_principals_quality_check",
    comment="Spike #16 - silver_principals DLT expectation quality check"
)
@dlt.expect("valid_principal_id", "principal_id IS NOT NULL")
@dlt.expect("valid_source_principal_id", "source_principal_id IS NOT NULL")
@dlt.expect("valid_principal_kind", "principal_kind IN ('HI', 'NHI')")
@dlt.expect("valid_principal_type", "principal_type IN ('app_registration', 'user')")
@dlt.expect("valid_status", "status IN ('active', 'inactive', 'terminated')")
def dlt_silver_principals_quality_check():
    return spark.read.table("access_drift.silver.silver_principals")
```

목적:

* 기존 `silver_principals` 정상 데이터가 DLT expectation을 통과하는지 확인
* 위반 건수가 0인지 확인
* 기존 notebook 기반 Silver 테이블을 변경하지 않고 DLT quality check pipeline으로 사후 검증 가능한지 확인

---

### 2. 위반 데이터 감지 테스트

`@dlt.expect()` 동작 확인을 위해 정상 row 20건에 invalid row 5건을 추가했다.

위반 조건은 하나의 row에 몰아넣지 않고, 각 expectation별로 독립적인 invalid row를 생성했다.

```text
정상 row 20건
+ principal_id null row 1건
+ source_principal_id null row 1건
+ invalid principal_kind row 1건
+ invalid principal_type row 1건
+ invalid status row 1건
= 총 25건
```

목적:

* `@dlt.expect()`가 위반 row를 삭제하지 않고 유지하는지 확인
* 각 expectation violation metric이 1건씩 기록되는지 확인

---

### 3. 품질 gate drop 테스트

`@dlt.expect_or_drop()`을 사용해 품질 위반 row가 결과 테이블에 유입되지 않도록 처리 가능한지 확인했다.

```text
정상 row 20건 + invalid row 5건
↓
DLT expect_or_drop 적용
↓
결과 테이블에는 정상 row 20건만 유지
```

목적:

* DLT를 Bronze → Silver 변환 흐름 내부에 적용할 경우, 품질 위반 row를 drop하는 gate로 사용할 수 있는지 확인
* 단순 사후 검증이 아니라 품질 조건 기반 차단 가능성을 검토

---

## 검증 결과

### 1. 정상 데이터 검증

검증 쿼리:

```sql
SELECT
  COUNT(*) AS total_rows
FROM acdrift_dbx.default.dlt_silver_principals_quality_check;
```

결과:

```text
total_rows = 20
```

확인 결과:

| 항목                               | 결과 |
| -------------------------------- | -- |
| 원본 `silver_principals` row count | 20 |
| DLT 결과 table row count           | 20 |
| expectation violation            | 0건 |


---

### 2. 위반 데이터 감지 테스트

검증 쿼리:

```sql
SELECT
  COUNT(*) AS total_rows
FROM acdrift_dbx.default.dlt_silver_principals_quality_check_with_invalid;
```

결과:

```text
total_rows = 25
```

DLT UI에서 expectation violation이 각 조건별로 기록되는 것을 확인했다.

예상/확인 결과:

| Expectation                 | 위반 건수 |
| --------------------------- | ----: |
| `valid_principal_id`        |     1 |
| `valid_source_principal_id` |     1 |
| `valid_principal_kind`      |     1 |
| `valid_principal_type`      |     1 |
| `valid_status`              |     1 |

`@dlt.expect()`는 위반 row를 삭제하지 않고 결과 테이블에 유지하면서 violation metric을 기록하는 방식임을 확인했다.

<img width="407" height="501" alt="warn" src="https://github.com/user-attachments/assets/eff84423-ed83-4d3d-b3f1-cd78e20db834" />


---

### 3. expect_or_drop gate 테스트

검증 쿼리:

```sql
SELECT
  COUNT(*) AS total_rows
FROM acdrift_dbx.default.dlt_silver_principals_gate_drop_test;
```

결과:

```text
total_rows = 20
```

invalid row 유입 여부 확인:

```sql
SELECT
  COUNT(*) AS invalid_rows
FROM acdrift_dbx.default.dlt_silver_principals_gate_drop_test
WHERE principal_id IS NULL
   OR source_principal_id IS NULL
   OR principal_kind NOT IN ('HI', 'NHI')
   OR principal_type NOT IN ('app_registration', 'user')
   OR status NOT IN ('active', 'inactive', 'terminated');
```

결과:

```text
invalid_rows = 0
```

확인 결과:

| 항목                 |                  결과 |
| ------------------ | ------------------: |
| 입력 데이터             | 정상 20건 + invalid 5건 |
| 결과 table row count |                  20 |
| invalid row 유입 여부  |                  0건 |

이를 통해 `expect_or_drop`을 사용하면 품질 조건을 위반한 row를 결과 테이블에서 제거할 수 있음을 확인했다.

<img width="362" height="492" alt="drop" src="https://github.com/user-attachments/assets/bd7bf9cf-b391-4fbd-b54c-f30fbae669e4" />


---

## 기존 smoke test 대비 비교

| 항목        | 기존 notebook smoke test  | DLT Expectations                    |
| --------- | ----------------------- | ----------------------------------- |
| 주요 목적     | 적재 성공 여부 확인             | row-level 데이터 품질 조건 검증              |
| 대표 검증     | row count, 테이블 생성 여부    | null, enum, status, 조건 위반           |
| 위반 row 처리 | 별도 SQL/로직 필요            | warn/drop/fail 방식 선택 가능             |
| 결과 확인     | notebook output, SQL 결과 | DLT Pipeline UI, expectation metric |
| 자동화 수준    | 직접 쿼리 작성 필요             | pipeline 실행 과정에 통합 가능               |
| 라인리지/UI   | 제한적                     | Databricks Pipeline UI에서 확인 가능      |
| 도입 부담     | 낮음                      | DLT pipeline 구성 필요                  |
| 기존 구조 영향  | 거의 없음                   | 별도 pipeline이면 영향 작음, 전환 시 영향 큼      |

기존 smoke test는 주로 “테이블이 생성되었는지”, “row가 존재하는지”를 확인하는 수준이다.
이번 DLT 실험은 여기서 한 단계 더 나아가 필수 키 null, enum 값, status 값 같은 row-level 품질 조건을 pipeline 내부에서 자동 검증할 수 있는지 확인했다.

---

## 적용 전/후 비교 및 Tradeoff

| 관점                    | 적용 전                  | DLT 적용 후                                    |
| --------------------- | --------------------- | ------------------------------------------- |
| 구현 복잡도                | 단순 SQL smoke test 중심  | DLT pipeline 구성 필요                          |
| 재실행/장애 대응             | notebook/job 로그 중심 확인 | Pipeline 실행 상태 및 expectation metric 확인 가능   |
| 품질검증 자동화 수준           | 수동 쿼리 중심              | expectation 선언 기반 자동 검증                     |
| Databricks UI/라인리지    | 제한적                   | Pipeline graph, table, expectation 결과 확인 가능 |
| 비용/compute 부담         | 기존 job compute 사용     | 별도 DLT/Lakeflow pipeline compute 비용 발생 가능   |
| 기존 notebook/job 변경 범위 | 없음                    | 별도 quality pipeline이면 작음, 전면 전환 시 큼         |
| 품질 위반 처리              | 직접 구현 필요              | warn/drop/fail 정책 선택 가능                     |

---



```text
스키마가 맞지 않는 데이터
→ Spark/Delta 단계에서 오류

스키마는 맞지만 값이 품질 조건을 위반하는 데이터
→ DLT Expectation이 violation으로 감지하거나 drop 처리
```

---

## 확인 관점별 결과

### 정상 케이스

* DLT pipeline에서 expectation 결과 확인 가능
* 정상 데이터는 expectation violation 없이 통과
* 조건 위반 데이터는 `@dlt.expect()`에서 violation metric으로 기록됨
* 조건 위반 데이터는 `@dlt.expect_or_drop()`에서 결과 테이블에서 제거됨
* 기존 Bronze/Silver 원본 테이블을 직접 변경하지 않고 실험 가능

---

## 확인한 대상

* DLT pipeline 실행 상태
* DLT 결과 테이블 row count
* expectation 위반 건수
* `expect_or_drop` 적용 후 invalid row 제거 여부
* Databricks pipeline 실행 로그 및 UI
* target schema 권한 문제


<img width="1050" height="632" alt="DLT1" src="https://github.com/user-attachments/assets/eefab748-803d-4c66-84f9-9acbd6c8d03d" />

---

## 완료 기준 체크리스트

* [x] DLT Expectations로 검증 가능한 품질 조건을 2~3개 이상 정리했다.
* [x] Silver 테이블 중 `silver_principals` 1개를 대상으로 실험했다.
* [x] 실험 코드와 재현 절차를 PR에 기록했다.
* [x] 기존 notebook smoke test 대비 장점과 제약을 정리했다.
* [x] DLT 적용 전/후 비교와 tradeoff를 정리했다.
* [x] 현재 PoC에 바로 적용할지, 후속으로 둘지 추천안을 남겼다.
* [x] 확인하지 못한 항목과 제약을 기록했다.

---

## 추천안

현재 PoC에서는 Bronze/Silver 전체를 DLT로 전면 전환하지 않는 것을 추천한다.

추천 방향은 다음과 같다.

1. 기존 notebook 기반 Bronze/Silver pipeline은 유지한다.
2. DLT는 우선 별도 quality check pipeline으로 운영해 사후 품질검증 metric을 수집한다.
3. 품질 조건이 안정되면 `silver_credentials`, `silver_edges`로 검증 범위를 확장한다.
4. Bronze → Silver 단계에서 실제 차단이 필요한 조건은 후속 작업에서 DLT 내부 변환 흐름으로 일부 분리하고 `expect_or_drop` 또는 `expect_or_fail` 적용을 검토한다.
5. 현재 단계에서는 `expect_or_drop` 기반 gate 적용 가능성까지 확인했으므로, 운영 반영 전에는 권한, compute 비용, 기존 job 구조 변경 범위를 추가 검토해야 한다.

---

## 결론

DLT Expectations는 Access Drift PoC의 데이터 품질검증 자동화 후보로 적용 가능성이 있다.

이번 실험을 통해 다음을 확인했다.

* Silver 테이블 기준 사후 품질검증 가능
* expectation violation metric 확인 가능
* `expect_or_drop` 기반 품질 gate 적용 가능
* 기존 Bronze/Silver 원본 테이블을 크게 변경하지 않고 작은 범위로 실험 가능

다만 현재 Bronze/Silver pipeline은 notebook 기반으로 동작 중이므로, DLT를 즉시 전면 도입하는 것은 변경 범위가 크다.
따라서 이번 PoC에서는 별도 DLT quality check pipeline 또는 후속 작업으로 두고, 핵심 테이블과 필수 품질 조건부터 점진적으로 확대하는 방식이 적절하다.

---

## 관련 이슈

Closes #16

