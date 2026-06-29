# 01 · 레이블 분류 체계 — IS_PLANTED_RISK 정답 기준 (확장)

> **확장 대상**: main의 [`eval-schema.md`](../../contracts/eval-schema.md)는 단일 `drift_type = nhi_residual_access`만
> 정의한다. 이 문서는 그것을 **5종(A-S1~B-S2)으로 확장**할 때의 정답 판정 기준을 고정한다.
> **base 스키마**(`eval.ground_truth_case` 컬럼·eval key·라벨 해석)는 eval-schema.md를 그대로 따르며, 여기서 재정의하지 않는다.

---

## 1. 레이블 단위 (granularity)

레이블은 행이 아니라 **"리스크 케이스(risk case)" 단위**로 붙는다.

> **리스크 케이스 = `(subject, final_asset, drift_type)`**
> 예: `(account=kim@slack, asset=고객DB, A-S2)` = 하나의 케이스.

- 한 주체가 여러 자산에 잔존 권한 → **자산 수만큼 별도 케이스**.
- 평가 조인 키는 eval-schema.md와 동일: **`(subject_type, subject_id, asset_id, drift_type)`**.
- `case_id`는 사람이 읽는 핸들이며, 기계 조인은 eval key로 한다.

---

## 2. drift_type 분류 체계 (PoC `nhi_residual_access` → 5종)

PoC의 `nhi_residual_access`는 아래 **B-S2**에 해당한다. 확장 시 사람(Pattern 1)·NHI(Pattern 2)를 다음으로 세분한다.
**MVP 범위는 A-S1·A-S2·B-S2**이고 A-S3·B-S1은 **향후 고려**다 (PRD §8.1, 6/26 MVP 미팅).

| drift_type | 패턴 | MVP 여부 | 한 줄 정의 |
|---|---|---|---|
| `A-S1` | P1 사람 | **MVP** | 퇴사/역할변경인데 SaaS **계정**이 활성 잔존 |
| `A-S2` | P1 사람 | **MVP** | 퇴사/역할변경인데 앱 내부 **권한·멤버십**이 잔존 |
| `A-S3` | P1 사람 | Future | 퇴사인데 소유한 **객체(자동화 규칙 등)**가 활성 잔존 |
| `B-S1` | P2 NHI | Future | NHI **소유자 불명확**(unassigned/퇴사 owner) + 활성 |
| `B-S2` | P2 NHI | **MVP** | NHI **생성자 퇴사** 후 미폐기 (= 현 PoC `nhi_residual_access`) |

> 데이터 생성기는 아래 **구조적 조건**대로 노드/엣지를 배치한다. 모든 positive는 §3 공통 게이트를 만족한다.
> 아래 조건은 **확장 데이터 모델 기준 서술**이다. 현재 main Silver(`silver_principals`/`silver_credentials`/`silver_assets`/`silver_edges`)로의 매핑(특히 Pattern 1)은 후속 태스크에서 정리한다.

### Pattern 1 — 사람 계정

**A-S1 · 계정 잔존**
1. `identity.employment_status ∈ {offboarded, role_changed}` 또는 `idp_status=disabled`
2. 연결된 `account.account_status=active`
3. 그 account의 활성 엣지가 민감 자산 도달
4. 원인: `scim_managed=false` 또는 `scim_sync_state ∈ {stale, failed}`

**A-S2 · 앱 내부 권한·멤버십 잔존**
1. 사람 offboarded/role_changed
2. `edge.relation ∈ {project_role, group_membership, space_permission}` 활성 엣지가 별도 존재
3. 그 엣지가 민감 자산 도달
4. (게스트 변형) `account.invited_via=personal_email`

**A-S3 · 소유권·객체 잔존**
1. 사람 offboarded (account는 비활성일 수 있음)
2. `edge: (identity|account) --owns--> object` 존재 + `object.is_active=true`
3. `object.owner_type='identity'` 이고 `owner_id` = 그 퇴사자 (후임 인계 안 됨)
4. `edge: object --grants_access--> asset(민감)` 활성
> 핵심: account가 비활성이어도 **object가 활성 + 소유권 미이전**이면 positive. 후임 이전 시 정상([02](02_distractor-catalog.md) D-P1-05).

### Pattern 2 — NHI

**B-S1 · 소유자 불명확 NHI**
1. `nhi.owner_type='unassigned'` **또는** `owner_type='identity'`인데 owner가 offboarded/role_changed
2. `nhi.lifecycle_status='active'`
3. NHI 활성 엣지가 민감 자산 도달
4. **grace-period 예외 아님** (§4)

**B-S2 · 퇴사·역할변경자 연결 NHI 미폐기** (현 PoC 패턴)
1. `nhi.created_by_identity` 또는 `last_accessed_by_id`가 offboarded
2. 해당 사람 account는 오프보딩 완료 (사람 경로 끊김)
3. `nhi.lifecycle_status='active'` + 활성 credential로 민감 자산 도달 (사람과 독립 경로)

---

## 3. 공통 게이트 & 활성/비활성

- **모든 planted positive는 "활성 경로가 민감(HIGH/MEDIUM) 자산에 도달"** 을 만족한다 → positive는 정의상 활성.
- 비활성 경로 잔존은 **positive로 심지 않는다.** 탐지기가 surface하면 `intermediate.finding.finding_state='historical'`로 표기하고, **평가 universe(활성 경로만) 밖**이므로 TP/FP/FN에서 **제외**한다(`normal`로 채점하지 않음). 평가 모집단·채점 설계는 rule vs IF 비교 문서(후속 태스크)로 분리한다.
- 따라서 severity 식에 **활성/비활성 강등 항을 두지 않는다.** 활성 여부는 후보 자격 필터로만 쓴다.

---

## 4. grace-period 예외 규칙 (B-S1 변별)

"소유자 미등록"이 **신규 발급 직후 등록 대기**라면 정상으로 본다 (정당한 운영).

> B-S1은 다음 중 하나라도 참이면 **positive에서 제외**(정상/디스트랙터):
> - `ownership_registration_status='pending'` **AND** `created_at`이 grace_period 내 **AND** `created_by`가 active, 또는
> - `owner_type='team'` 이고 `owner_id`가 유효 (소유권 이전 완료 → [02](02_distractor-catalog.md) D-P2-06)

- `grace_period_days` 기본 제안 **7일** (DE/DS 합의 필요 — [README §미합의](README.md)).
- 이 규칙은 데이터 생성·rule 탐지 **양쪽에 동일 적용**(정답지와 rule이 같은 게이트를 봐야 함).
- **경계 케이스**: `pending`인데 `created_at`이 grace를 **초과**하면 → 등록이 끝내 안 된 것이므로 **B-S1 positive**. 같은 'pending'이라도 시간 경과로 정답이 갈린다. 시간 정책을 인지하는 rule은 이를 맞힌다. (post-MVP에서 IF를 비교하면, 시간에 눈먼 IF가 grace 내 함정과 grace 초과 positive를 혼동하는 baseline 한계 시연 포인트가 된다.)

---

## 5. 자산 민감도 분류 & severity 매핑

**주 근거 = 최종 자산 민감도.** 시간 파생값 미사용 → [04](04_time-axis-policy.md).

### 자산 민감도 (데모 시나리오 기준 — 확정: Critical / High / Medium)

| 등급 | 기준 | 예시 (커머스) |
|---|---|---|
| **Critical** | 법적으로 보호 의무가 강제되는 정보 | 고객 식별정보·주소/배송지·주문/결제·환불 내역, 카드/계좌, 판매자 정산·계약 |
| **High** | 유출 시 운영상 타격이 큰 핵심 자산 | DB 암호화 키, 핵심 소스코드, 운영 루트 권한, 운영 SSL/TLS 개인키·Secret, 매출 데이터, 권한목록·보안감사로그·운영 런북 |
| **Medium** | 사내 공유가 필요한 내부 자산 | 비식별 통계, 실시간 재고, 개발로그·스테이징, 사내 매뉴얼, 셀러 현황 |

> 고객 개인정보·결제정보 접근으로 이어지는 High 자산은 **Critical로 승격**한다.

### expected_severity 매핑 (후속 태스크에서 확정)

`expected_severity`는 위 자산 민감도에서 유도한다. **정확한 asset sensitivity ↔ risk severity 매핑표는 PO 민감 자산 분류표 확정 후 asset sensitivity 매핑 태스크에서 확정**한다(후속 PR).

> ⚠️ 정합 주의: 현재 main `silver_assets.sensitivity` enum은 `high`/`medium`/`low`/`unknown`(source 레벨)이다.
> 데모 민감도(Critical/High/Medium)와 Silver enum, risk severity 등급 사이의 매핑이 매핑표에서 확정돼야 한다.

정렬 보조(등급 변경 아님): NHI 우선, 조치 가능성.

---

## 6. 합성 규모 (MVP 상한 — 6/26 MVP 미팅)

> 합성 데이터 요청은 단순 총량이 아니라 **positive / distractor / holdout 구성 스펙**으로 DE에 전달한다 (ML 학습 표본이 아님).

**MVP 상한 (확정 초안):**

| 항목 | MVP 상한 |
|---|---|
| identity | **≤ 1,000** (active 대부분 / offboarded·role_changed 소수) |
| **positive 케이스** | **≤ 40** (MVP drift type A-S1·A-S2·B-S2 중심) |
| distractor | positive 조건을 하나씩 깨는 방식으로 균형 배치 ([02](02_distractor-catalog.md)) |

- dev/holdout은 **시나리오 단위로 분리**해 같은 케이스가 양쪽에 섞이지 않게 한다 ([03] 후속 태스크).
- account/nhi/asset/edge 세부 규모와 **확장 실험용 대규모 합성**은 별도 합의(post-MVP).
- NetworkX 단일 노드 한계(identity < 10,000) 내.

---

## 7. 누수 방지 불변식 (data generator invariants)

1. 정답/시나리오/split 컬럼은 **Silver 본문에 절대 미포함**. `eval.*`에만 둔다.
   - 생성기는 Silver에 직접 쓰지 않는다. source 형태 raw → Landing/Bronze 원본 보존 → Silver 정규화. 정답 레이블은 raw에 넣지 않고 생성 메타로 `eval.*`에 분리.
2. positive와 distractor는 **전역(marginal) 시간 분포가 동일**해야 한다 — 단일 전역 임계값("오래됨=위험")으로 정답이 갈리면 비교가 trivial.
   - 단, **정책 조건부 시간 게이트는 허용·의도**된다(예: `pending` 부분집합 안에서 grace 경계로 정답이 갈리는 것). 이는 *정책*이지 전역 시간 누수가 아니다.
3. 모든 positive는 §2 구조적 조건으로만 생성 — rule이 채점 가능해야 한다.
4. positive를 식별하는 단일 "마법 컬럼" 금지. 항상 **신원/owner 상태 × 엣지 활성 × 자산 민감도** 조합으로만 성립.
5. (post-MVP) IF 도입 시 **구조·상태 피처만** 사용 → [04 §6 IF allowlist](04_time-axis-policy.md). MVP는 ML 미도입(룰베이스).
