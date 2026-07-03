# DE 발표자료 초안

> PPT로 옮기기 위한 발표용 요약 문서입니다. 기준 문서는 `docs/engineering/`, `docs/contracts/`, `docs/adr/`를 따릅니다.

---

## DE Overview

신뢰 가능한 Risk 탐지를 위한 데이터 기반

- 원천 근거 보존
- 공통 Silver 모델 정규화
- 스키마 계약과 품질검증
- 재실행 안전성
- 권한과 운영 관측성

---

## DE Data Scope

Access Drift 탐지를 위해 필요한 근거 데이터

| 데이터 영역 | Source 예시 | 설명 |
| --- | --- | --- |
| Identity / HR | HR export | 재직/퇴사/이동 상태로 owner 유효성 판단 |
| IdP / NHI | Microsoft Entra ID, Azure | App Registration, owner, credential 상태 확인 |
| Asset | Azure, GitHub, Slack | 민감 자산, 환경, 민감도 확인 |
| Access | Azure, GitHub, Slack | 권한 주체 → 자산 접근 경로 표현 |
| Eval | internal eval seed | 검증용 정답 케이스로 탐지 결과 확인 |

합성 데이터 사용 이유:

- HR, Asset, Access 데이터는 회사마다 수집 시스템과 정책이 다름
- IdP/NHI는 대표 API 응답 구조를 참고해 실제 export와 유사하게 구성
- 구현 기준은 Microsoft Entra ID / Azure를 대표 케이스로 사용
- seed 기반으로 동일 데이터 재생성 및 규모 확장 가능

---

## Landing & Bronze

원천 근거를 보존하고, Silver 정규화를 준비하는 구간

| 구분 | Landing | Bronze |
| --- | --- | --- |
| 목적 | 원본 파일 보존 | 원천 시스템별 테이블 적재 |
| 형태 | Raw JSONL | 테이블 내 레코드 |
| 구조 | API/export 형태 | Landing 데이터 기반 스키마 |
| 보존 | 원본 payload | 원천 ID, 주요 날짜, 적재 시각 |
| 하지 않음 | 정답 위험도, 시크릿 값 저장 | 리스크 판단, 소스 통합 join |
| 다음 단계 | Bronze 적재 입력 | Silver 정규화 입력 |

검증: 입력 누락 없음 · 필수 key 존재 · 금지 필드 없음 · raw payload 보존

---

## Silver

source별 데이터를 Risk 탐지에 사용할 공통 모델로 정규화

| 테이블 | 역할 |
| --- | --- |
| `silver_principals` | HI/NHI 주체 정규화 |
| `silver_credentials` | NHI credential metadata |
| `silver_assets` | 민감 자산 정규화 |
| `silver_edges` | owner/access 관계 표현 |

핵심:

- deterministic ID로 재실행 시 같은 입력은 같은 key 생성
- HI → NHI → Credential → Asset 접근 경로 표현
- severity, finding, eval label은 Silver 책임이 아님

---

## Schema Contract & Quality Gates

계약을 정의하고, 적재 데이터와 파이프라인 실행을 검증

| 구분 | 역할 |
| --- | --- |
| Schema Contract | required column, enum, ID, relationship 규칙 정의 |
| SQL Validation | 현재 적재 데이터가 계약을 만족하는지 확인 |
| DLT Expectations | 파이프라인 실행 중 품질 gate 역할 |
| CI | PR 단계에서 계약/구현 불일치 조기 탐지 |

핵심 메시지:

> 문서 계약 → SQL 확인 → DLT gate → CI 자동화로 데이터 신뢰성을 보강했습니다.

---

## Operations & Expansion

재실행, 권한, 운영 관측성, 후속 확장

| 영역 | 현재 | 후속 |
| --- | --- | --- |
| Re-run Safety | deterministic ID, full refresh | `MERGE INTO`, partition overwrite |
| Governance | Unity Catalog catalog/schema 권한 | lineage / audit 고도화 |
| Monitoring | SQL validation, DLT event log | SQL Dashboard / Alerts |
| Ingestion | 재현 가능한 합성 데이터 | 실제 API connector, Auto Loader |

핵심:

- 같은 입력을 다시 처리해도 같은 ID 생성
- Gold/Eval/App 접근 경계 분리
- 품질검증 결과를 운영 모니터링으로 확장 가능
