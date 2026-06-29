# 02 · 디스트랙터(함정) 케이스 카탈로그

> **목적**: `IS_PLANTED_RISK = false` 이지만 위험해 *보이는* 정상 케이스를 카탈로그화한다.
> 용도는 두 가지다 — (1) **룰 검증·합성 데이터 구성 스펙**(단일 신호 룰이 trivial하게 풀리지 않게), (2) post-MVP **Isolation Forest 비교**(결정로그 0621 [확정]).
> MVP는 ML 미도입이므로 IF 비교는 **post-MVP 실험**으로 둔다.
> main `eval.ground_truth_case`에 `is_distractor` 컬럼은 있으나, **distractor 생성 로직과 카탈로그는 아직 미구현**이다 — 이 문서가 그 설계다.

---

## 설계 원칙

> **디스트랙터 = positive와 신호 1~2개를 공유하되, 결정적 조건 1개가 빠진 케이스.**

좋은 디스트랙터의 조건:
1. **표면 신호 공유**: 오프보딩됨 / NHI active / 권한 잔존처럼 1차 필터에 걸릴 신호를 가진다.
2. **결정적 조건 결여**: positive 게이트([01 §2](01_label-taxonomy.md)) 중 *정확히 하나*가 빠진다 → 정답은 false.
3. **시간·메타 분포 동일**: positive와 같은 범위의 `created_at`/`expires_at`/`last_used_at`을 갖는다 (시간만으로 가르지 못하게).
4. **오탐 후보**: 잘 만든 rule은 통과시키지만, 순진한 임계값 규칙(또는 post-MVP IF)은 틀리도록 유도.

목표 효과: rule-based가 디스트랙터를 정상 처리(낮은 오탐) → "설명 가능한 규칙"의 견고함을 보여준다. (post-MVP에서 IF를 비교하면 IF가 디스트랙터에서 오탐을 내며 baseline 한계를 드러낸다.)

---

## 카탈로그

각 디스트랙터는 닮은 positive 유형, **공유 신호**, **빠진 결정 조건**으로 정의한다.

### Pattern 1 닮은꼴 (사람)

| id | 이름 | 닮은 유형 | 공유 신호 | 빠진 결정 조건 (→ 정상인 이유) |
|---|---|---|---|---|
| `D-P1-01` | 오프보딩됐지만 비민감 자산만 | A-S1/A-S2 | 사람 offboarded + SaaS account active | 도달 자산이 전부 `sensitivity=LOW` (사내 위키). **민감 자산 미도달** |
| `D-P1-02` | 정상 재직자 광범위 권한 | A-S2 | 민감 자산에 닿는 활성 권한 다수 | `employment_status=active` + SCIM 정상. **잔존이 아님(정당한 현직 권한)** |
| `D-P1-03` | 게스트지만 만료/회수 완료 | A-S2(게스트 변형) | `invited_via=personal_email` 외부 협력자 | account `status=suspended` + 엣지 비활성. **활성 경로 없음** |
| `D-P1-04` | 역할 변경 후 권한 정상 회수 | A-S2 | `role_changed` 상태 | 이전 역할 엣지가 모두 회수됨, 신규 역할 권한만 활성. **잔존 권한 없음** |
| `D-P1-05` | 오프보딩 + 객체 인계 완료 | A-S3 | 과거 소유 자동화 규칙 존재 | 자동화 규칙 `owner`가 후임자로 이전됨. **소유권 잔존 아님** |
| `D-P1-06` | SCIM stale이지만 실제 차단됨 | A-S1 | `scim_sync_state=stale` | SSO 강제 + account가 실제 disabled. **로그인 경로 없음** |

### Pattern 2 닮은꼴 (NHI)

| id | 이름 | 닮은 유형 | 공유 신호 | 빠진 결정 조건 (→ 정상인 이유) |
|---|---|---|---|---|
| `D-P2-01` | 활성 prod SP, 소유자 명확 | B-S1 | `lifecycle=active` + 민감 자산(prod) 접근 | `owner_type='identity'` + 현직 + 실사용 |
| `D-P2-02` | 소유자 퇴사했으나 폐기 완료 | B-S2 | `created_by` offboarded | `lifecycle_status='revoked'`(이미 폐기). **활성 경로 없음** |
| `D-P2-03` | 소유자 불명확이나 비민감 자산만 | B-S1 | `owner_type='unassigned'` + active | 도달 자산 `sensitivity=LOW`(dev/test). **민감 자산 미도달** |
| `D-P2-04` | 만료 임박 token, 소유자 명확·실사용 | B-S1 | `expires_at` 임박(시간 신호) | `owner_type='identity'`+현직+실사용. **시간 신호만으로 위험 아님**(시간축 함정) |
| `D-P2-05` | 신규 발급 SP, owner 등록 대기 | B-S1 | `owner_type='unassigned'` + `active` + 민감 자산 도달 | **grace-period 예외**: `pending` + `created_at` grace 내 + `created_by` active → [01 §4](01_label-taxonomy.md) |
| `D-P2-06` | 퇴사자 생성 NHI, 소유권 팀 이전 | B-S2 | `created_by` offboarded + active | `owner_type='team'` + 유효 `owner_id`(팀 계정). **소유권 이전 완료 → 고아 아님** |

> **D-P2-05 = 가장 어려운 디스트랙터.** B-S1의 표면 신호(unassigned + active + 민감 자산 도달)를 **전부 공유**하고, 구분되는 유일한 근거가 **grace-period 정책 예외**다. 데이터 생성기와 rule 탐지기는 *반드시 같은* grace 규칙([01 §4](01_label-taxonomy.md))을 적용해야 한다(한쪽만 적용하면 정답지와 탐지 기준이 어긋남). "정책을 모르는" IF가 오탐하기 쉬운 지점.

---

## 디스트랙터 ↔ positive 신호 매트릭스

순진한 규칙이 왜 디스트랙터에 걸려 넘어지는지 한눈에 보기 위한 표. `✓` = 신호 보유, `—` = 미보유.

| 신호 | A-S1/2 positive | D-P1-01 | D-P1-02 | D-P2-01 | D-P2-04 |
|---|---|---|---|---|---|
| 신원 offboarded/role_changed | ✓ | ✓ | — | (NHI) | (NHI) |
| 권한/엔티티 active | ✓ | ✓ | ✓ | ✓ | ✓ |
| **민감 자산 도달** | ✓ | **—** | ✓ | ✓ | ✓ |
| SCIM 미관리/stale | ✓ | ✓ | — | — | — |
| owner 명확 + 실사용 | — | — | ✓ | **✓** | **✓** |
| 시간 신호(오래됨/만료임박) | 분포 동일 | 분포 동일 | 분포 동일 | 분포 동일 | ✓(함정) |

> 굵게 표시한 칸이 **정답을 가르는 결정 조건**이다. 시간 신호는 어느 쪽도 결정하지 못하도록(분포 동일) 설계 — [04](04_time-axis-policy.md).

---

## 규모·배치 규칙

- **positive ≤ 40 기준, distractor는 positive 대비 약 1:2 범위에서 균형 배치한다** ([01 §6](01_label-taxonomy.md) MVP 상한).
- 각 positive drift_type마다 **최소 1개 이상의 대응 디스트랙터 유형**을 포함한다 (위 카탈로그가 전 유형 커버).
- 디스트랙터도 `scenario_id`로 묶고, **대응 positive와 같은 scenario_family에 일부 배치**한다 (같은 회사 스토리 안에 위험/정상이 섞여 있어야 현실적이고, holdout 시 함께 이동 — holdout 정책은 후속 태스크 문서로 분리).
- 시간/메타 필드는 positive 그룹과 **동일한 난수 분포**에서 추출 ([01 §7](01_label-taxonomy.md) 불변식).

---

## 검증 기준 (데이터 생성 후 DS가 확인)

- [ ] 모든 positive drift_type에 대응 디스트랙터 ≥ 1 존재
- [ ] positive와 distractor의 시간 필드 분포가 통계적으로 구분 불가 (KS-test p > 0.05 권장)
- [ ] "오프보딩 = 무조건 위험" 같은 단일 신호 규칙의 정밀도가 1.0 미만 (디스트랙터가 실제로 함정 역할)
- [ ] `eval.ground_truth_case`에서 `is_distractor=true` 행이 모두 `is_planted_risk=false`
