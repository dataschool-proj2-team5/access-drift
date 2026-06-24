# Schema Consistency Review

## 목적

PoC 파이프라인의 계약 문서, DDL, notebook 변환 로직, seed 데이터가 서로 같은 필드와 ID 규칙을 쓰는지 확인한다.

## 검토 범위

- `docs/contracts/bronze-schema.md`
- `docs/contracts/silver-schema.md`
- `docs/contracts/eval-schema.md`
- `sql/databricks/migrations/001_create_bronze_tables.sql`
- `sql/databricks/migrations/002_create_silver_tables.sql`
- `sql/databricks/migrations/003_create_eval_tables.sql`
- `notebooks/02_ingest.py`
- `notebooks/03_silver.py`
- `notebooks/04_eval_seed.py`
- `data/poc/landing/raw/**`
- `data/poc/eval/ground_truth_case.jsonl`

## 검토 결과

| 영역 | 비교 대상 | 결과 | 메모 |
| --- | --- | --- | --- |
| Bronze | Bronze 계약, Bronze DDL, `data/poc/landing/raw/**`, `02_ingest.py` | PASS | raw 필드명과 Bronze 적재 컬럼이 일치한다. |
| Silver | Silver 계약, Silver DDL, `03_silver.py` | PASS | `principal_id`, `source_principal_id`, `asset_id`, `source_asset_id`, `relationship` 값이 계약과 맞는다. |
| Eval | Eval 계약, Eval DDL, `ground_truth_case.jsonl`, `04_eval_seed.py` | PASS | eval key `(subject_type, subject_id, asset_id, drift_type)`와 적재 컬럼이 일치한다. |

## 확인한 정정 사항

- Bronze 계약의 Landing 경로를 실제 PoC 경로인 `data/poc/landing/raw/...`로 맞췄다.
- Silver 예시의 `evidence_source` 값을 실제 브론즈 테이블명 `bronze_azure_applications`로 맞췄다.

## 참고

- `03_silver.py`는 `principal_kind`, `principal_type`, `relationship` 값을 계약 문서에 정의된 범위 안에서 생성한다.
- `04_eval_seed.py`는 `ground_truth_case.jsonl`을 `access_drift.eval.ground_truth_case`에 적재하고, `subject_id`를 Silver의 `source_principal_id`와 매칭 가능하게 유지한다.

## 확인하지 못한 점

- Databricks 런타임에서 notebook을 실제 실행한 검증은 수행하지 않았다.
- 이번 검토는 정적 대조를 기준으로 했고, 런타임 전처리/권한/배포 설정은 별도 확인이 필요하다.
