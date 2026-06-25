# PoC Scope

## 문서 목적

이 문서는 Access Drift PoC에서 어디까지 구현하면 완료로 볼지 정의한다.

PoC의 목표는 완성형 제품 데모가 아니라, 데이터 파이프라인이 입력 데이터에서 Gold 테이블까지 정상 동작하는지 확인하는 것이다.

## PoC 목표

합성 입력 데이터를 사용해 다음 흐름이 end-to-end로 동작하는지 검증한다.

```text
Landing -> Bronze -> Silver -> Intermediate -> Gold
```

PoC 완료 시점에는 팀 공용 Databricks workspace에서 Gold 테이블의 Risk Card용 최소 결과를 조회할 수 있어야 한다.

## 대표 케이스

PoC 대표 케이스는 Azure App Registration 형태의 NHI residual access로 한다.

```text
퇴사자 owner
  -> App Registration / NHI
  -> active credential
  -> high sensitivity asset
```

## 입력 Evidence

PoC 입력 데이터는 다음 evidence를 포함한다.

- NHI: App Registration 또는 service principal 역할의 주체
- Credential metadata: client secret의 key id, 이름, 만료일, 활성 여부
- Owner context: owner 계정과 퇴사 또는 비활성 상태
- Asset context: 접근 가능한 자산과 민감도

실제 secret 값은 포함하지 않는다.

## 완료 기준

PoC는 다음 조건을 만족하면 완료로 본다.

- 합성 source 입력이 Landing 또는 Bronze에 적재된다.
- Bronze 데이터가 Silver 공통 모델로 정규화된다.
- Silver 데이터를 기반으로 Intermediate에서 finding 후보가 생성된다.
- Intermediate 결과가 Gold 테이블로 적재된다.
- Gold 테이블에 최소 1건 이상의 Risk Card용 레코드가 존재한다.
- 위 결과를 팀 공용 Databricks workspace에서 조회할 수 있다.
- Gold 레코드에서 다음 정보를 확인할 수 있다.
  - 어떤 주체 또는 권한이 남아 있는지
  - 어떤 자산에 닿는지
  - 왜 finding으로 판단됐는지
  - 다음 조치가 무엇인지

## 포함 범위

- 합성 데이터 기반 입력
- source 1개
- drift pattern 1개
- Landing/Bronze/Silver/Intermediate/Gold 최소 파이프라인
- 팀 공용 Databricks workspace 내 Gold 테이블 적재 확인
- Gold 결과 조회용 검증 SQL 또는 노트북

## 제외 범위

- 완성형 Streamlit UI
- 실제 SaaS 또는 클라우드 API 연동
- 자동 권한 회수
- Jira/GitHub Issue 자동 생성
- 정교한 ML 기반 위험 점수화
- 전체 권한 정책 구현
- 전체 source 확장
- 운영용 모니터링과 알림

## 확인 방법

PoC 검증은 단순히 잡이 성공했는지만 보지 않는다.

다음 항목을 함께 확인한다.

- 각 레이어에 데이터가 적재됐는지
- 공용 Databricks workspace에서 Gold 결과를 조회할 수 있는지
- 레이어 간 주요 키가 유지되는지
- Gold 레코드가 입력 데이터의 어떤 증거에서 나왔는지 추적 가능한지
- Gold 결과가 Risk Card로 표시 가능한 최소 필드를 갖는지
- 동일 입력을 재실행해도 Gold 결과가 중복 증가하지 않는지

## 완료 기준 대비 현재 결과

2026-06-25 기준 공용 Databricks workspace에서 다음 결과가 확인됐다.

| 완료 기준 | 확인 결과 | 상태 |
| --- | --- | --- |
| Landing/Bronze 적재 | PoC seed 기반 Bronze 적재 완료 | 충족 |
| Bronze -> Silver 정규화 | Silver 4테이블 생성 및 기존 검증 완료 | 충족 |
| Silver -> Intermediate finding 생성 | `intermediate.nhi_residual_access_findings` 2건 생성 | 충족 |
| Intermediate -> Gold 적재 | `gold.gold_core` 2건 생성 | 충족 |
| Gold Risk Card 최소 결과 존재 | HIGH 1건, MEDIUM 1건 Gold 샘플 출력 확인 | 충족 |
| 공용 Databricks workspace 조회 | `07_verify_gold_core_pipeline` read-only 검증 노트북 실행 완료 | 충족 |
| 의도한 리스크 탐지 | eval positive 2건이 Gold 2건과 모두 매칭 | 충족 |
| 정상 케이스 제외 | eval normal 1건은 Gold에 생성되지 않음 | 충족 |
| severity 정합성 | `HIGH`, `MEDIUM`이 eval `expected_severity`와 일치 | 충족 |
| 중복 방지 | `risk_case_key` 중복 0건 | 충족 |
| 필수 필드 | Risk Card 필수 필드 null 0건 | 충족 |

따라서 현재 PoC seed와 공용 Databricks workspace 기준으로는 `Landing/Bronze -> Silver -> Intermediate -> Gold` 파이프라인이 정상 동작했고, Gold 테이블에 Risk Card용 최소 결과가 생성된 것으로 판단한다.

단, 이 결과는 PoC 합성 데이터와 최소 eval seed 기준의 검증이다. 실제 source 연동, 대량 데이터, DLT 기반 품질검증, 운영용 재처리, UI/Databricks Apps, RAG, 조치 흐름은 본개발 또는 후속 범위에서 다룬다.
