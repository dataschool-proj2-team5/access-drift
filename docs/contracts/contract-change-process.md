# Data Contract Change Process

## 버전

```text
version: 0.1.0
status: draft
updated_at: 2026-06-26
```

## 변경이력

| 버전 | 날짜 | 변경 내용 |
| --- | --- | --- |
| 0.1.0 | 2026-06-26 | 데이터 계약 변경 공통 절차, PR 체크리스트, 최소 schema validation 방식 추가 |

## 목적

이 문서는 Access Drift PoC에서 데이터 계약이 변경될 때 공통으로 따라야 할 절차를 정리한다.

이번 범위는 dbt contract 같은 강제 도구 도입이 아니라, 현재 저장소의 Databricks/Delta 기반 구조에서 문서, DDL, notebook, seed, 검증 SQL이 따로 움직이지 않도록 최소 운영 규칙을 정하는 것이다.

## 적용 대상

아래 변경은 모두 데이터 계약 변경으로 본다.

- 컬럼 추가, 삭제, 이름 변경
- 타입 변경
- nullable 여부 또는 필수 여부 변경
- 컬럼 의미 변경
- 허용값, enum, 상태값 변경
- id 생성 규칙 변경
- 테이블 추가, 삭제, 이름 변경
- 레이어 간 키 매핑 방식 변경

## 계약 관련 파일과 역할

| 영역 | 현재 위치 | 역할 |
| --- | --- | --- |
| 계약 진입점 | `docs/contracts/README.md` | 레이어별 계약 문서와 관련 문서의 시작점 |
| Bronze 계약 | `docs/contracts/bronze-schema.md` | Landing raw 입력과 Bronze 보존 컬럼 기준 |
| Silver 계약 | `docs/contracts/silver-schema.md` | 공통 모델, deterministic id, 관계 규칙 기준 |
| Eval 계약 | `docs/contracts/eval-schema.md` | 정답/평가용 격리 스키마 기준 |
| Intermediate/Gold 계약 | `docs/contracts/poc-intermediate-gold-schema.md` | 탐지 결과와 Risk Card 최소 산출물 기준 |
| 정합성 검토 | `docs/contracts/schema-consistency-review.md` | 계약 문서, DDL, notebook, seed 간 정적 대조 결과 |
| 검증 가이드 | `docs/contracts/poc-verification.md` | Intermediate/Gold 및 eval 검증 기준 |
| Bronze DDL | `sql/databricks/migrations/001_create_bronze_tables.sql` | Bronze 테이블 정의 |
| Silver DDL | `sql/databricks/migrations/002_create_silver_tables.sql` | Silver 테이블 정의 |
| Eval DDL | `sql/databricks/migrations/003_create_eval_tables.sql` | Eval 테이블 정의 |
| Intermediate DDL | `sql/databricks/migrations/004_create_intermediate_tables.sql` | Intermediate 테이블 정의 |
| Gold DDL | `sql/databricks/migrations/005_create_gold_tables.sql` | Gold 테이블 정의 |
| Ingest notebook | `notebooks/02_ingest.ipynb` | Landing raw를 Bronze로 적재하는 변환 로직 |
| Silver notebook | `notebooks/03_silver.ipynb` | Bronze를 Silver 공통 모델로 정규화하는 로직 |
| Eval seed notebook | `notebooks/04_eval_seed.ipynb` | eval seed 적재 로직 |
| Intermediate notebook | `notebooks/05_intermediate.ipynb` | Silver 조인 기반 탐지 후보 생성 로직 |
| Gold notebook | `notebooks/06_gold.ipynb` | Gold 최소 결과 생성 로직 |
| 검증 notebook | `notebooks/07_verify_gold_core_pipeline.ipynb` | Gold 검증 실행 흐름 |
| Landing seed | `data/poc/landing/raw/**` | Bronze 입력이 되는 raw JSONL 샘플 |
| Eval seed | `data/poc/eval/ground_truth_case.jsonl` | Eval 정답 seed |
| 검증 SQL | `sql/databricks/queries/*.sql` | 계약/탐지 결과 확인 SQL |

## 공통 변경 절차

데이터 계약 변경은 아래 순서를 기본 절차로 사용한다.

1. 변경 대상과 영향 범위를 먼저 적는다.
2. 계약 문서를 먼저 고친다.
3. 대응하는 DDL을 수정한다.
4. notebook 변환 로직을 수정한다.
5. seed 또는 샘플 입력이 계약과 맞는지 확인하고 필요 시 같이 수정한다.
6. 검증 SQL 또는 확인 방법을 갱신한다.
7. PR 본문에 어떤 계약이 바뀌었는지와 실제 확인 근거를 적는다.

## 변경 시 공통 체크리스트

아래 항목은 어떤 레이어든 공통으로 확인한다.

| 확인 항목 | 질문 |
| --- | --- |
| 계약 문서 | 컬럼명, 타입, 의미, 허용값, id 규칙이 문서에 반영되었는가 |
| DDL | 계약 문서와 같은 컬럼이 실제 테이블 정의에 반영되었는가 |
| notebook 로직 | notebook이 새 컬럼을 채우거나 삭제된 컬럼을 더 이상 참조하지 않는가 |
| seed/raw 샘플 | 샘플 입력 또는 eval seed 필드가 계약과 맞는가 |
| 키 정합성 | source id, Silver id, eval key, risk_case_key 연결 규칙이 유지되는가 |
| 검증 SQL | 변경된 컬럼과 규칙을 확인할 수 있는 쿼리가 있는가 |
| PR 설명 | 어떤 계약이 왜 바뀌었는지, 어떤 파일을 같이 바꿨는지 드러나는가 |

## 레이어별 추가 확인 포인트

### Bronze

- raw 입력 shape와 Bronze 컬럼명이 대응되는지 확인한다.
- `_raw_payload`, `_src_*`, `_schema_version` 같은 추적 컬럼이 유지되는지 확인한다.
- secret value, token value, private key value가 새로 저장되지 않는지 확인한다.

### Silver

- `source_*` 컬럼과 deterministic id 생성 규칙이 문서와 구현에서 같은지 확인한다.
- `principal_kind`, `principal_type`, `relationship`, `status` 같은 허용값이 계약 범위를 벗어나지 않는지 확인한다.
- Silver에 위험 점수, severity, finding 설명 같은 후속 레이어 책임이 섞이지 않았는지 확인한다.

### Eval

- eval이 탐지 입력이 아니라 검증 전용이라는 원칙이 유지되는지 확인한다.
- `(subject_type, subject_id, asset_id, drift_type)` 조인 키가 Intermediate/Gold 비교 방식과 맞는지 확인한다.
- planted risk, distractor, severity 라벨이 raw/Bronze/Silver로 섞이지 않는지 확인한다.

### Intermediate

- 탐지 후보를 만드는 조인 조건과 근거 edge/key가 계약 문서와 같은지 확인한다.
- `risk_case_key`, `finding_id`, `run_id` 생성 규칙이 재실행 시에도 안정적인지 확인한다.
- Silver에서 오지 않은 파생 필드가 있다면 그 규칙이 문서에 드러나는지 확인한다.

### Gold

- Risk Card용 필드가 Intermediate 근거와 같은 의미를 유지하는지 확인한다.
- `subject_source_principal_id`, `asset_source_id`, `drift_type`가 eval 비교 기준과 맞는지 확인한다.
- `severity`, `recommended_action`, `evidence_summary`가 deterministic 규칙인지 확인한다.

## PR 작성 기준

데이터 계약 변경 PR은 구현 변경만 나열하지 말고, 계약 변경 사실과 영향 범위를 리뷰어가 바로 볼 수 있어야 한다.

PR 본문에는 최소한 아래 내용을 적는다.

- 어떤 계약이 바뀌었는가
- 바뀐 레이어와 테이블은 무엇인가
- 같이 수정한 계약 문서, DDL, notebook, seed, 검증 SQL은 무엇인가
- 기존 데이터 또는 downstream 해석에 어떤 영향이 있는가
- 실제로 어떤 쿼리, 샘플 데이터, 결과로 확인했는가

PR 작성자가 사용할 체크리스트:

- [ ] 변경한 계약 문서를 갱신했다.
- [ ] 대응하는 DDL migration을 갱신했다.
- [ ] 대응하는 notebook 변환 로직을 갱신했다.
- [ ] 관련 seed 또는 샘플 입력을 확인했고 필요 시 갱신했다.
- [ ] 관련 검증 SQL 또는 확인 방법을 갱신했다.
- [ ] PR 본문에 변경된 컬럼, 타입, id 규칙 또는 허용값을 적었다.
- [ ] PR 본문에 영향 범위와 미확인 항목을 적었다.

## 최소 schema validation 방식

dbt 없이도 아래 수준의 schema validation은 수행할 수 있다.

### 1. 테이블 컬럼 존재 여부 확인

`DESCRIBE TABLE` 또는 `information_schema.columns`로 계약 문서의 컬럼이 실제 테이블에 모두 있는지 확인한다.

예시:

```sql
SELECT column_name, data_type
FROM access_drift.information_schema.columns
WHERE table_schema = 'silver'
  AND table_name = 'silver_credentials'
ORDER BY ordinal_position;
```

### 2. 필수 컬럼 null 여부 확인

notebook이 채워야 하는 핵심 컬럼이 null로 남지 않는지 확인한다.

예시:

```sql
SELECT
  SUM(CASE WHEN credential_id IS NULL THEN 1 ELSE 0 END) AS missing_credential_id,
  SUM(CASE WHEN bound_principal_id IS NULL THEN 1 ELSE 0 END) AS missing_bound_principal_id
FROM access_drift.silver.silver_credentials;
```

### 3. 허용값 범위 확인

status, relationship, principal_kind 같은 enum 성격 컬럼이 계약의 허용값만 가지는지 확인한다.

예시:

```sql
SELECT status, COUNT(*) AS cnt
FROM access_drift.silver.silver_credentials
GROUP BY status
ORDER BY status;
```

### 4. 레이어 간 키 연결 확인

source id, Silver id, eval key, finding key가 계약대로 연결되는지 확인한다.

예시 확인 대상:

- `silver_principals.source_principal_id`
- `silver_assets.source_asset_id`
- `eval.ground_truth_case.subject_id`
- `gold.gold_core.subject_source_principal_id`

### 5. seed와 DDL 정적 대조

raw JSONL 또는 eval seed의 필드명이 계약 문서와 DDL에 없는 필드를 새로 요구하지 않는지 확인한다.

현재 저장소에서는 [schema-consistency-review.md](./schema-consistency-review.md)가 이 역할의 기준 문서다.

## PR 리뷰 확인 포인트

리뷰어는 아래 질문으로 계약 변경 PR을 본다.

- 문서, DDL, notebook, seed, 검증 SQL이 함께 바뀌었는가
- 컬럼 의미 변경이 단순 rename처럼 숨겨지지 않았는가
- id 생성 규칙 또는 조인 키 변경이 downstream에 미치는 영향이 설명되었는가
- Eval 전용 필드가 Bronze/Silver/Intermediate에 섞이지 않았는가
- secret value 같은 금지 데이터가 새로 저장되지 않는가

## 후속 자동화 후보

- 계약 문서의 컬럼 표와 DDL 컬럼 diff를 비교하는 정적 검사
- `information_schema.columns` 기반 schema validation SQL 묶음 추가
- `data/poc/landing/raw/**`와 Bronze 계약 필드 매핑 검사를 스크립트화
- Eval seed와 Eval DDL 정합성 검사를 스크립트화
- PR 템플릿에 데이터 계약 변경 체크 섹션을 추가
- Databricks job에 validation query 실행 단계를 추가

## 이번 문서의 한계

- dbt의 `contract: enforced` 같은 compile-time enforcement는 포함하지 않는다.
- Databricks workspace에서 실제 런타임 검증을 자동화하지는 않는다.
- 레이어별 상세 운영 매뉴얼까지 확장하지 않고, 공통 절차와 확인 포인트만 정의한다.
