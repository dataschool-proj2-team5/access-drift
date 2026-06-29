# Access Drift — PoC 이후 확장 설계 (Expansion Design)

> **성격**: 설계 레퍼런스 (binding contract 아님, 코드·DDL 없음).
> **상태**: PoC 완료(2026-06-25) 이후의 **확장 범위** 설계. 실제 DDL·파이프라인·검증 코드는
> 각 구현 태스크 PR에서 함께 제출한다.
> **작성**: DS팀

---

## 포지션

PoC 이후 확장 아이디어를 보존하되, **main 병합 대상은 구현을 강제하지 않는 설계 레퍼런스 문서로 제한**한다.
리뷰 가능한 단위를 작게 유지하기 위해 이 PR에는 DDL·파이프라인·검증 코드를 포함하지 않는다.
MVP 필수 계약(Intermediate/Gold 정식 계약 등)은 후속 태스크 PR에서 코드·DDL·검증과 함께 올린다.

---

## 현재 구현 상태 (오해 방지)

- PoC는 **완료**됐고 산출물이 존재한다: `intermediate.nhi_residual_access_findings` 2건, `gold.gold_core` 2건
  (2026-06-25 공용 Databricks 검증 — [poc-scope.md](../../product/poc-scope.md)).
- 레이어 DDL은 [`sql/databricks/migrations/`](../../../sql/databricks/migrations/)에 001 Bronze ~ 005 Gold까지 있으나,
  **004/005는 schema 생성 수준**이다.
- 이 문서가 다루는 **확장 범위의 Intermediate/Gold 정식 계약·DDL은 아직 미정**이며, 후속 DS 구현 PR에서 추가한다.
  즉, PoC 산출은 존재하지만 이 확장 설계의 정식 계약은 아직 후속 범위다.

---

## MVP 범위와의 관계 (2026-06-26 MVP 확정 미팅 기준)

- MVP는 **ML 미도입** — NHI residual access **룰베이스 + Gold 검증 구조**를 유지한다.
- 따라서 이 문서의 **Isolation Forest / IF 피처 allowlist / rule vs IF 비교**는 MVP 확정 구현이 아니라
  **post-MVP 검증 실험 후보**다 (DS 스프린트 Post-MVP Backlog 기준).
- **MVP drift type = A-S1, A-S2, B-S2.** A-S3·B-S1은 **향후 고려** (PRD §8.1).
- PoC 대표 패턴 `nhi_residual_access` = 본 문서의 **B-S2**.

---

## 이 PR에 포함 (설계만, 코드·DDL 없음)

| 문서 | 내용 | MVP 관련성 |
|---|---|---|
| [01_label-taxonomy.md](01_label-taxonomy.md) | drift 유형 A-S1~B-S2 (MVP/Future 구분), grace-period, 민감도, 규모, 누수 방지 | MVP(A-S1/A-S2/B-S2) + Future |
| [02_distractor-catalog.md](02_distractor-catalog.md) | 위험해 보이지만 정상인 함정 12종 — **룰 검증·합성 데이터 구성 스펙용** | 합성 구성 스펙(룰 검증) / IF 비교는 post-MVP |
| [04_time-axis-policy.md](04_time-axis-policy.md) | 시간 파생값을 severity에서 제외 + Risk Card 맥락 표시 | §1~5 MVP / §6 IF allowlist는 post-MVP |

> 번호 `03`(holdout 정책)·`05`(rule vs IF 비교)는 **이 PR에 없다.** 후속 구현 태스크 PR에서 코드와 함께 추가한다.

---

## main에 이미 있는 것 (여기서 재정의하지 않음)

| 이미 있는 것 (main) | 위치 |
|---|---|
| Bronze / Silver / Eval 스키마 계약 | [`docs/contracts/`](../../contracts/) |
| 레이어 DDL (001 Bronze ~ 005 Gold) | [`sql/databricks/migrations/`](../../../sql/databricks/migrations/) |
| PoC E2E 파이프라인 노트북 (00~07) | [`notebooks/`](../../../notebooks/) |
| PoC 범위·완료 결과 | [`docs/product/poc-scope.md`](../../product/poc-scope.md) |
| `eval.ground_truth_case` (PoC 최소 정답) | [`docs/contracts/eval-schema.md`](../../contracts/eval-schema.md) |
| Silver 공통 모델 (`silver_principals`/`silver_credentials`/`silver_assets`/`silver_edges`) | [`docs/contracts/silver-schema.md`](../../contracts/silver-schema.md) |

---

## 후속 태스크 PR로 분리 (이 PR 범위 밖)

이 PR은 **설계만** 담는다. 아래는 해당 태스크를 진행할 때 **문서 + 코드/DDL/검증을 같은 PR**로 올린다.

| 후속 산출물 | 내용 |
|---|---|
| `docs/contracts/intermediate-schema.md` + 004 확장 DDL | finding 정식 계약: `finding_id`, `risk_case_key`, `drift_type`, `subject_principal_id`, `asset_id`, `severity`, `finding_state`, evidence refs, `detected_at`, `run_id` |
| `docs/contracts/gold-schema.md` + 005 확장 DDL | Risk Card 정식 계약: `risk_case_key`, Risk Card 표시 필드, `recommended_action`, context, **lineage keys**, `status`, `updated_at` |
| **Gold lineage keys (UC 우선)** | Gold가 최소 `finding_id`·`credential_id`·`owner_edge_id`·`access_edge_id`·`subject_principal_id`·`asset_id`를 보존 → Risk Card 근거 추적 (UC 활용 논의 기준, P1) |
| `03_holdout-policy.md` + DDL + split 코드 | connected-component holdout — `eval.scenario_membership`/`component_split` + 산출 코드 |
| `05_detection-comparison.md` + 코드 (**post-MVP**) | eval 정밀 검증(Precision/Recall/FPR, `eval.eval_universe`) · Isolation Forest 비교 · IF 피처 빌더 |
| Pattern 1 SaaS/GitHub Silver 매핑 | A-S1/A-S2를 현재 Silver 모델(`silver_principals`/`silver_edges`)로 표현하는 매핑 |
| Action State / Audit / Ticket 저장 계약 | finding 상태와 분리된 운영 상태·감사·티켓 이력 |
| RAG chunk/citation 계약 | 조치 보조(LLM) 근거 문서 chunk·citation metadata |

---

## eval 격리 (현재 상태)

- 현재 eval 계약은 **PoC 최소 ground truth**(`eval.ground_truth_case`)다 ([eval-schema.md](../../contracts/eval-schema.md)).
- **holdout은 후속 구현 PR에서 `scenario_id`/`scenario_family` 기반으로 확장**한다 (`03_holdout-policy.md`는 후속 구현 PR에서 추가).
- 탐지 잡·앱은 eval을 읽지 않는다(격리). 이 원칙은 MVP에서도 유지한다.

---

## 미합의 / 열린 결정

| 항목 | 현재 제안 | 근거 |
|---|---|---|
| 합성 규모 (MVP 상한) | **identity ≤ 1,000 / positive ≤ 40** | 6/26 MVP 미팅 — 01 §6 |
| distractor 배치 | positive 조건을 하나씩 깨는 방식으로 균형 | 6/26 MVP 미팅 — 02 |
| `grace_period_days` | 7일 (제안) | 01 §4 |
| **asset sensitivity ↔ risk severity 매핑표** | **PO 민감 자산 분류표 확정 후 asset sensitivity 매핑 태스크에서 확정** | 01 §5 |
| (post-MVP) `split_seed`·holdout 비율·IF allowlist | 해당 태스크에서 확정 | 03·04 |

---

## 배경 (왜 이 설계를 보존하는가)

결정 로그(0621) [확정] 원칙.

> **Isolation Forest = baseline 비교 역할 (post-MVP).**
> 합성 데이터에 정답 레이블이 새어 들어가면 비교가 trivial해지므로,
> 함정(distractor) + holdout 분리로 공정한 비교 구조를 만든다.

MVP는 룰베이스만 쓰지만, 이 원칙은 **합성 데이터를 "단일 신호로 trivial하게 풀리지 않게, 정답이 새지 않게" 설계**하라는 요구로 MVP의 룰 검증에도 그대로 유효하다. IF 비교 자체는 post-MVP 실험으로 둔다.
