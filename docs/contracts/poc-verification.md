# PoC 검증 가이드 (#11 키·근거추적·재실행 / #12 secret·eval)

> **범위**: #10에서 생성한 Intermediate/Gold 결과의 **검증**. 계약(스키마) 정의는
> [poc-intermediate-gold-schema.md](./poc-intermediate-gold-schema.md)(#10) 참조 — 본 문서는 중복하지 않고 검증만 다룬다.
> **대상**: `access_drift.intermediate.nhi_residual_access_findings`, `access_drift.gold.gold_core`, `access_drift.eval.ground_truth_case`
> **검증 SQL**: `sql/databricks/queries/11_ds_key_lineage_rerun.sql`, `sql/databricks/queries/12_ds_secret_eval_min.sql`
> **관련 이슈**: #11(V3·V4·V6), #12(V7·V8)

## 선행조건
#10 파이프라인(00→06 노트북)이 공용 Databricks workspace에 적재 완료되어, 위 테이블에 데이터가 존재해야 한다.
빠른 확인: `SELECT count(*) FROM access_drift.gold.gold_core;` → 1건 이상.

## 검증 항목

| ID | 검증 | 쿼리(파일) | PASS 조건 |
|---|---|---|---|
| **V3** | 레이어 간 키 유지 | 11 §V3 | `gold→finding` 연결 끊김 0 (`key_chain='OK'`), source 키 일관성 `OK` |
| **V4** | 근거 추적 | 11 §V4 | edge 역추적이 **존재+관계+방향(from→to)+status=active 일치** → `lineage='VALID'` 전 행, ORPHAN/WRONG_* 0 |
| **V6** | 재실행 중복 방지 | 11 §V6 | `rows = distinct risk_case_key`(중복 0) **AND** 파이프라인 2회 실행 전후 row count 동일 |
| **V7** | secret 미저장 | 12 §V7 | 결과 스키마에 secret 원문 컬럼 0행, gold 텍스트 secret 패턴 0행 |
| **V8** | 최소 eval | 12 §V8 | eval은 검증 입력만(탐지 입력 아님). planted positive 전부 TP, FP 0 → `poc_eval_verdict='PASS'` |

## 실행 방법 (요약)
- **SQL Editor**(권장) 또는 노트북 `%sql` 셀에 각 쿼리 블록(`-- ───` 단위)을 붙여 실행.
- 쿼리는 모두 완전 수식 이름(`access_drift.…`)을 사용 → 카탈로그 선택 불필요.
- **V6 2회 실행**: 11 §V6 실행(1st 기록) → 05/06 노트북 재실행 → 11 §V6 재실행(2nd 기록) → 1st=2nd & no_dup=PASS면 통과.

## 결과 기록 위치
검증 **결과(row count·verdict·TP/FN/FP/TN)**는 각 이슈의 **PR 본문**에 표로 남긴다(#11/#12 완료기준 "검증 결과를 PR에 정리").
- 본 문서는 *방법·기준*만 고정하고, *실측 결과*는 PR 본문에 둔다(재실행마다 값이 달라지므로).

## 원칙 (재확인)
- eval(`ground_truth_case`)은 **탐지 입력으로 사용 금지** — 검증에서만 조인.
- secret value 원문은 샘플이라도 어떤 결과 테이블에도 저장하지 않는다.
- 중복 방지 방식: #10이 `overwrite` + 결정적 `risk_case_key` → 재실행 누적 없음.
