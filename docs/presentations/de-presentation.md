# DE 발표자료 초안

> PPT로 옮기기 위한 발표용 요약 문서입니다. 기준 문서는 `docs/engineering/`, `docs/contracts/`, `docs/adr/`를 따릅니다.

---

## DE Overview

신뢰 가능한 리스크 탐지를 위한 데이터 기반 구축

- 탐지 근거 데이터
- Landing/Bronze 원천 보존
- Silver 공통 접근 경로 모델 정규화
- 데이터 계약과 자동화된 품질검증
- 운영 안정성과 권한 통제

---

## Data Scope - 근거 데이터 정의

리스크 탐지에 필요한 근거 데이터

| 데이터 영역 | Source 예시 | 설명 |
| --- | --- | --- |
| Identity / HR | HR export | 재직/퇴사/이동 |
| IdP / NHI | Microsoft Entra ID, Azure | App Registration, owner, credential |
| Asset | Azure, GitHub, Slack | 민감 자산, 환경, 민감도 |
| Access | Azure, GitHub, Slack | 권한 주체 → 자산 접근 경로 |
| Eval | internal eval seed | 탐지 결과 검증용 정답 케이스 |

합성 데이터 사용 이유:

- HR, Asset, Access 데이터는 회사마다 수집 시스템과 정책이 다름
- IdP/NHI는 대표 API 응답 구조를 참고해 실제 export와 유사하게 구성
- 구현 기준은 Microsoft Entra ID / Azure를 대표 케이스로 사용
- seed 기반으로 동일 데이터 재생성 및 규모 확장 가능

---

## Landing & Bronze

원본 파일 보존 및 원천 시스템별 테이블 적재

| 구분 | Landing | Bronze |
| --- | --- | --- |
| 목적 | 원본 파일 보존 | 원천 시스템별 테이블 적재 |
| 형태 | Raw JSONL | 테이블 내 레코드 |
| 구조 | API/export 형태 | Landing 데이터 기반 스키마 |
| 보존 | 원본 payload | 원천 ID, 인사 이벤트 발생 시각, 적재 시각 |
| 하지 않음 | 정답 위험도, 시크릿 값 저장 | 원본 의미 수정, 시스템 간 병합 |
| 다음 단계 | Bronze 적재 입력 | Silver 정규화 입력 |

예시 흐름: `landing/raw/azure/...jsonl` → `bronze_azure_*`

---

## Silver

여러 원천 데이터를 위험 탐지가 가능한 공통 접근 경로 모델로 정규화

| 모델 요소 | 의미 |
| --- | --- |
| Principal | HI/NHI 주체 |
| Credential | NHI 인증 수단 |
| Asset | 접근 대상 자산 |
| Edge | Principal 소유 / Credential 보유 / Asset 접근 권한 |

대표 접근 경로:
퇴사자(HI) --소유--> Azure App(NHI)
Azure App --활성 Client Secret 보유--> 인증 가능
Azure App --조회 권한--> 고객 데이터 Storage

이후 Detection 레이어에서 Risk 판단
---

## 신뢰성 보장 - 데이터 계약, 자동화된 품질 검증

데이터 계약을 자동 검증해 탐지 로직이 신뢰할 수 있는 입력을 보장

| 구분 | 역할 | 잡을 수 있는 오류 예시 |
| --- | --- | --- |
| 스키마 계약 | required, enum, ID, 관계 규칙 문서화 | 컬럼/관계 기준 누락 |
| CI | PR 단계에서 계약/구현 불일치 조기 탐지 | 스키마 계약 문서와 DDL/DLT 불일치 |
| DLT Expectations | 변환 로직 중 도메인 규칙 검증 | 잘못된 edge 방향, credential active 판정 오류 |
| SQL 검증 | 적재 데이터가 계약을 만족하는지 확인 | null key, 중복 ID, orphan edge |

---

## 운영 안정성

실패 감지, 재처리, 권한 통제로 파이프라인 운영 안정성 확보

왼쪽:

- DLT/SQL 검증으로 실패 감지
- DLT task 실패 시 downstream 실행 차단
- 같은 입력 재처리 시 중복 행 누적 방지
- Unity Catalog로 민감 데이터 접근/수정 권한 통제
- SQL Dashboard로 row count / validation 결과 확인

오른쪽:

- SQL Dashboard 캡처
