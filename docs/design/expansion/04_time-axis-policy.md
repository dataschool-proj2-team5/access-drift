# 04 · 시간축 처리 방침

> **목적**: 시간 파생 정보(잔존 기간·만료일·검토일 등)를 **어디까지 쓰고 어디서 배제**할지 고정한다.
> **근거**: PRD §8.3 (독립 점수 요소 제외 목록), 결정로그 [확정] "Risk Card 시간 데이터 추가".
>
> **범위 구분**: §1~5 (severity 점수에서 시간 제외 + Risk Card 맥락 표시) = **MVP 유효**(룰베이스).
> §6 IF feature allowlist = **post-MVP** (MVP는 ML 미도입).

---

## 1. 한 줄 방침

> **시간 파생값은 위험 점수(severity) 산정의 독립 요소로 쓰지 않는다.**
> 대신 **리스크 카드의 맥락(context) 필드**와 **스토리텔링**(수개월 방치)으로만 표시한다.

---

## 2. 두 종류의 시간 정보 구분

| 구분 | 예시 | 쓰임 |
|---|---|---|
| **사실(fact) 타임스탬프** | `created_at`, `offboarded_at`, `last_used_at`, `expires_at`, `granted_at` | Silver에 **원본 그대로 보관**. 그래프/맥락/표시에 사용 |
| **시간 파생 점수 피처** | 잔존 기간(일), 만료까지 남은 일수, 마지막 검토 후 경과, 갱신 지연 여부 | **점수 입력에서 제외**. Gold 카드에 "맥락"으로만 노출 |

> 즉 **타임스탬프 저장은 OK, 그것을 점수화하는 파생 피처는 금지**.

---

## 3. PRD §8.3 배제 목록 (점수 독립 요소로 사용 금지)

다음은 MVP에서 독립적인 점수 요소로 사용하지 않는 것 (맥락 정보로는 표시 가능):

- credential 발급 경과 기간 · 담당자 수 · 마지막 검토일 · 만료일/만료까지 잔여 · 갱신 지연 여부 · 대체 담당자 여부

→ 이들은 **`risk_card`의 context 블록**에만 들어가고, severity 계산식에는 들어가지 않는다.

---

## 4. 그래서 점수는 무엇으로?

severity는 [01 §5](01_label-taxonomy.md)대로 **최종 자산 민감도**가 주 근거다. 시간은 빠진다.
경로 활성 여부는 **점수 조정이 아니라 후보 자격**으로만 쓴다(활성 경로만 평가·severity 대상, 비활성=historical=범위 밖).

```
severity   = f(final_asset_sensitivity)   # 주 근거 (시간 무관)
후보 자격   = active path only             # 비활성/historical은 universe·severity 밖
정렬보조    : NHI 우선, 조치 가능성          # 등급 변경 아님
제외        : 모든 시간 파생값               # 본 방침
```

> 비활성 경로는 강등 대상이 아니라 **평가·severity 범위 밖**이다([01 §3](01_label-taxonomy.md)).

---

## 5. 리스크 카드에서의 시간 표시

스토리텔링("수개월 방치")을 위해 카드에 시간 **맥락**은 표시한다. 단, 점수가 아니라 **설명 텍스트/필드**다.

| 카드 필드 | 출처 | 성격 |
|---|---|---|
| `days_since_offboarding` | `now − offboarded_at` | 맥락. "퇴사 후 N일째 접근 가능" (잔존 기간) |
| `days_since_first_detection` | `now − intermediate.finding.first_seen_at` | 맥락. "시스템 최초 관측 후 N일째" (탐지 관측) |
| `last_used_at` | 사실 타임스탬프 | 맥락. 최근 활동 표시 |
| `expires_at` / 만료 임박 배지 | 사실 타임스탬프 | 맥락 배지 (점수 영향 없음) |
| `created_at` | 사실 타임스탬프 | NHI 발급 시점 표시 |

> 두 잔존 필드(`days_since_offboarding` vs `days_since_first_detection`)는 의미가 다르므로 한 필드에 섞지 않는다.
> 카드 UI에는 "맥락(Context)" 섹션으로 묶어 severity와 분리됨을 명시한다.

---

## 6. IF feature allowlist (원본 timestamp 유입 차단) — ⚪ post-MVP

> **MVP는 ML(Isolation Forest)을 도입하지 않는다.** 이 절은 IF를 **post-MVP 실험**으로 도입할 때 적용할 피처 계약이다.
> 단 "시간 파생값을 severity 점수에 넣지 않는다"(§4)는 원칙은 **MVP 룰베이스에도 그대로 유효**하다.

Silver에는 사실 타임스탬프를 저장하지만(맥락·그래프용), IF 도입 시 **피처에는 명시적 allowlist만** 투입한다.
파생값뿐 아니라 **원본 timestamp·ID·시나리오/평가 메타 전체를 제외**한다.

### ✅ 허용 (구조·상태 피처만)
- 사람: `employment_status`, `idp_status`, `scim_managed`, `scim_sync_state`
- 계정: `account_status`, `sso_enforced`, `scim_linked`, `invited_via`
- NHI: `nhi_type`, `owner_type`, `ownership_registration_status`, `lifecycle_status`
- 객체: `object_type`, `is_active`, `owner_type`
- 자산: `asset_type`, `sensitivity`, `environment`
- 엣지: `relation`, `permission`, `is_active`
- 그래프 구조 파생(시간 무관): degree, 민감 자산까지 경로 길이, 도달 가능 민감 자산 수, 경로 활성 비율

### ⛔ 제외 (학습/스코어 입력 금지)
- **모든 timestamp**: `created_at`, `expires_at`, `last_used_at`, `offboarded_at`, `granted_at`, `last_active_at`, `_ingested_at` + Intermediate 관측 시각 `detected_at`/`first_seen_at`/`last_seen_at`
- **모든 ID**: `*_id` (누수·과적합 위험)
- **모든 시간 파생 수치**: 잔존 일수, 만료 잔여, 마지막 검토 후 경과 등 (§3 목록)
- **시나리오/평가 메타**: `scenario_id`, `split`, `case_id`, `truth_class`, `is_planted_risk`, `is_distractor`

### 구현 계약
- 피처 빌더는 **allowlist 화이트리스트 방식**으로만 컬럼을 선택한다(블랙리스트 금지 — 신규 컬럼이 실수로 새는 것 방지).
- **IF**: 위 allowlist **구조·상태 피처만** 입력. timestamp 일절 미투입.
- **rule-based**: allowlist 피처 + **명시적 정책 게이트는 timestamp 사용 허용**. 예: grace-period 판정의 `created_at` 비교([01 §4](01_label-taxonomy.md))는 *정책 규칙*이지 학습 피처가 아니다. 이것이 rule의 설계상 강점(정책 인지)이며, 시간에 *눈먼* IF가 D-P2-05/B-S1를 혼동하는 지점이다.
- **공정 비교의 기준은 "동일 입력"이 아니라 "동일 holdout · 동일 universe · 동일 eval key · 동일 정답지"**다. severity 점수 자체에는 어느 방식도 시간 파생값을 넣지 않는다(§4).
- allowlist는 코드 상수로 고정하고 변경 시 본 문서 갱신.

---

## 7. 체크 (구현 시 확인)

**MVP (룰베이스)**
- [ ] severity 계산 코드에 시간 파생 변수가 입력으로 들어가지 않음 (코드 리뷰)
- [ ] Silver/Graph 피처셋에 "잔존 일수/만료 잔여" 등 파생 컬럼 부재 (사실 타임스탬프만)
- [ ] Gold `risk_card`의 시간 필드는 context 블록에만 위치

**post-MVP (IF 도입 시)**
- [ ] IF 피처 빌더가 §6 allowlist 화이트리스트만 사용 (timestamp/ID/메타 0개)
- [ ] positive/distractor 시간 분포 동일성 검증 통과 (KS-test)
