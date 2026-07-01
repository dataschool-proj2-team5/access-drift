# Architecture Overview

**버전:** v0.2  
**기준:** 2026년 6월 27일  
**상태:** Sprint 1 아키텍처 기준  
**기준 문서:** [PRD](../product/prd.md), [Sprint 1 Scope](../product/sprint1-scope.md), [Sprint 1 DE Scope](../engineering/sprint1-de-scope.md)

---

## 1. Overview

이 문서는 Sprint 1 기준 Access Drift의 시스템 구성, 데이터 흐름, 주요 데이터 레이어를 설명한다.
제품 문제 정의와 기능 요구사항은 PRD와 Sprint 1 Scope에서 다룬다.

---

## 2. Architecture Flow

```text
[External Sources]
- IdP / HR: 재직, 퇴사, 이동 상태
- Microsoft Entra ID: 앱 등록, 소유자, credential 메타데이터
- Cloud / SaaS 자산 목록: 민감 자산과 접근 관계
- 위 소스 구조를 기준으로 만든 합성 데이터 사용

        |
        | 수집 / seed 복사
        v

[Databricks Data Platform]
- Data Layers: Landing -> Bronze -> Silver -> Intermediate -> Gold
- Eval: 검증 전용 데이터
- Risk Card Context: 자산 설명, 현재 조치 상태, 조치 담당자/담당 팀
- AI 권고안: Gold 생성 시 탐지 근거 기반으로 생성
- RAG Evidence: Gold와 Risk Card Context 기반 근거 document / chunk

Unity Catalog: Gold-only App 접근, Eval 격리

        |
        | Risk Card 조회 / 현재 조치 상태 조회·변경
        v

[App / Dashboard]
- 전체 리스크 현황
- 최우선 검토 대상 목록
- 리스크 카드
- 접근 경로
- AI 조치 권고안
- 현재 조치 상태
```

---

## 3. System Components

| 컴포넌트 | 역할 | 주 오너 |
|----------|------|---------|
| **External Sources** | 탐지에 필요한 외부 근거 데이터를 제공 | DE |
| **Databricks Data Platform** | 데이터 레이어와 검증/상태 데이터를 저장·처리 | DE / DS |
| **App / Dashboard** | 보안 담당자가 리스크를 조회하고 현재 조치 상태를 변경하는 화면 제공 | PO |
| **Azure AI Foundry / Azure OpenAI** | Gold 생성 과정에서 탐지 근거 기반 조치 권고안 생성 | DS |
| **RAG Evidence / Vector Search** | Risk Case 단위 근거 document/chunk와 검색 index 기반 제공 | DE / DS |
| **Unity Catalog** | App 접근 경계와 Eval 격리 기준 제공 | DE |

---

## 4. Data Layers and Risk Card Context

| 레이어 | 역할 | 비고 | 주 오너 |
|--------|------|------|---------|
| **Landing** | 원본 입력 보존 | 합성 데이터 원본을 재현 가능하게 보존 | DE |
| **Bronze** | 원본 구조에 가까운 적재 | 소스별 입력과 공통 적재 메타데이터 보존 | DE |
| **Silver** | 정규화된 공통 모델 | source 종속성을 낮춘 principal, credential, asset, edge 관점 | DE |
| **Intermediate** | 탐지 후보 생성 | Silver 입력을 조합해 대표 리스크 후보 생성 | DS |
| **Gold** | Risk Card용 결과 | App / Dashboard가 직접 조회하는 조치 판단용 결과 | DS |
| **Eval** | 정답지와 검증 | pipeline에서 읽지 않고 검증 단계에서만 사용 | DS |
| **Risk Card Context** | Risk Card 표시와 운영 상태 보강 | Gold와 분리 | DE / PO |

---

## 5. Pipeline Flow

```
Schema / Migration
       │
       ▼
Synthetic Data Generation
       │
       ▼
Landing / Bronze
       │
       ▼
Silver
       │
       ▼
Intermediate
       │
       ▼
Gold
       │
       ├─ Azure AI Foundry / Azure OpenAI
       │  - 탐지 근거 기반 AI 조치 권고안 생성
       │
       ├─ Read-only Verification
       │  - Eval 데이터로 결과 검증
       │
       ├─ Risk Card Context
       │  - Asset Context: 자산 설명 / 데이터 범위
       │  - Action State: 현재 조치 상태
       │  - Assignment Routing: 조치 담당자 / 담당 팀
       │
       ├─ RAG Evidence / Vector Search
       │  - Risk Case 단위 근거 document / chunk
       │  - DS/AI 답변 생성을 위한 citation metadata
       │
       └─ App / Dashboard
          - Risk Card 조회
          - Action State 조회·변경
          - AI 조치 권고안 조회
```
