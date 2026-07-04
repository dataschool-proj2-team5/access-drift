# Architecture Overview

**버전:** v0.2
**기준:** 2026년 7월 2일
**상태:** 현재 아키텍처 개요
**기준 문서:** [PRD](../product/prd.md), [Sprint Scope](../product/sprint1-scope.md), [DE Scope](../engineering/sprint1-de-scope.md)

---

## 1. Overview

이 문서는 Access Drift의 시스템 구성, 데이터 흐름, 주요 데이터 레이어를 설명한다.
제품 문제 정의와 기능 요구사항은 제품 범위 문서에서 다룬다.

용어: 이 문서의 Detection Layer는 구현상 `intermediate` schema와 pipeline step을 의미한다.

---

## 2. Architecture Flow

```text
[External Data Sources]
- HR: 재직, 퇴사, 이동 상태
- IdP / IAM: 사용자, 앱, credential, 권한 주체
- Cloud / SaaS Platforms: 클라우드/SaaS 계정, 앱, 자산, 접근 정보
- Asset / Access Records: 시스템 export, CSV, 수동 관리 파일의 자산 목록과 접근 관계

        |
        | 수집 / 파일 적재
        v

[ADLS Raw / Landing Zone]
- source별 raw 파일 보존
- dev/demo 입력 데이터 재현 가능성 유지

        |
        | Databricks Workflows
        v

[Access Drift Platform Boundary]
- Data Flow: ADLS Raw / Landing Zone -> Bronze -> Silver -> Detection Processing -> Gold
- Supporting Data: Eval, Risk Card Context, Knowledge / RAG Layer
- Serving / Assistance: Risk Card Outputs, AI Action Assistant, Foundation Model APIs

Cross-cutting Controls:
- Unity Catalog · 품질 게이트(DLT) · 실행 모니터링 · 재처리/복구

        |
        | Risk Card 조회 / 상태 변경 / 티켓 생성 / AI 질의
        v

[App / Dashboard]
- 전체 리스크 현황
- 최우선 검토 대상 목록
- 리스크 카드
- 접근 경로
- 조치 상태 조회·변경
- Jira 티켓 발급
- AI Action Assistant
```

### 발표용 다이어그램 초안

```text
┌────────────────────────────┐                            ┌──────────────────────────────────────────────────────────────────────┐                      ┌────────────────────────────┐
│ 외부 데이터 소스           │                            │ Azure / Databricks Data Platform                                     │                      │ Databricks Apps            │
│                            │                            │                                                                      │                      │                            │
│ HR                         │                            │                         [오케스트레이션]                             │                      │ 리스크 현황                │
│ IdP/IAM                    │                            │                        Databricks Workflows                          │                      │ 우선 검토                  │
│ Cloud/SaaS                 │      수집 / 파일 적재      │                                                                      │      조회 / 조치      │ 리스크 카드                │
│ 접근 권한                  │ ────────────────────────▶ │ [데이터 파이프라인]                                                   │ ───────────────────▶ │ 접근 경로                  │
│                            │                            │ ADLS ─▶ Bronze ─▶ Silver ─▶ Detection ─▶ Gold                        │                      │ 조치 티켓 생성             │
│                            │                            │                                                                      │                      │                            │
│                            │                            │ [AI] Vector Search · Foundation Model APIs                           │                      │                            │
│                            │                            │ [보조 데이터] Eval · Context · Knowledge/RAG                         │                      │                            │
│                            │                            │ [운영·거버넌스] Unity Catalog · DLT · SQL Dashboard                  │                      │                            │
└────────────────────────────┘                            └──────────────────────────────────────────────────────────────────────┘                      └────────────────────────────┘
```

---

## 3. System Components

| 컴포넌트 | 역할 | 주 오너 |
|----------|------|---------|
| **External Data Sources** | 탐지에 필요한 외부 입력 데이터를 제공 | DE |
| **ADLS Raw / Landing Zone** | source별 raw 입력 파일을 보존하고 Databricks 적재 입력을 제공 | DE |
| **Databricks Data Platform** | 데이터 레이어와 검증/상태 데이터를 저장·처리 | DE / DS |
| **App / Dashboard** | 보안 담당자가 리스크를 조회하고 현재 조치 상태를 변경하는 화면 제공 | PO |
| **Databricks Vector Search** | RAG 근거 chunk 검색 index 제공 | DS |
| **Databricks Foundation Model APIs** | AI Action Assistant의 근거 기반 응답 생성 | DS |
| **Knowledge / RAG Layer** | 정책/playbook/source guide chunk, 검색 index, citation/fallback 기준 제공 | DE / DS |
| **Unity Catalog** | App 접근 경계, RAG/Eval 격리, catalog/schema governance 제공 | DE |

---

## 4. Data Layers and Risk Card Context

| 레이어 | 역할 | 비고 | 주 오너 |
|--------|------|------|---------|
| **ADLS Raw / Landing Zone** | 원본 입력 보존 | source별 raw 파일과 합성 데이터 원본을 재현 가능하게 보존 | DE |
| **Bronze** | 원본 구조에 가까운 적재 | 소스별 입력과 공통 적재 메타데이터 보존 | DE |
| **Silver** | 정규화된 공통 모델 | source 종속성을 낮춘 principal, credential, asset, edge 관점 | DE |
| **Detection Processing** | 탐지 후보 생성 | Silver 입력을 조합해 대표 리스크 후보 생성. 구현상 `intermediate` schema를 사용 | DS |
| **Gold** | Risk Card용 결과 | App / Dashboard가 직접 조회하는 조치 판단용 결과 | DS |
| **Eval** | 정답지와 검증 | pipeline에서 읽지 않고 검증 단계에서만 사용 | DS |
| **Risk Card Context** | Risk Card 표시와 운영 상태 보강 | Gold와 분리 | DE / PO |
| **Knowledge / RAG Layer** | AI Action Assistant 근거 제공 | `rag.doc_chunks`, Vector Search index, RAG answer/eval 결과 | DE / DS |

---

## 5. Pipeline Flow

```
Schema / Migration
       │
       ▼
Synthetic Data Generation
       │
       ▼
ADLS Raw / Landing
       │
       ▼
Bronze
       │
       ▼
Silver
       │
       ▼
Detection Processing
       │
       ▼
Gold
       │
       ├─ Risk Card Outputs
       │  - Dashboard 조회용 risk case 결과
       │
       ├─ Knowledge / RAG Layer
       │  - 정책/playbook/source guide 기반 rag.doc_chunks
       │  - Databricks Vector Search index
       │  - RAG recommended action / eval result / citation
       │
       ├─ Databricks Foundation Model APIs
       │  - AI Action Assistant 응답 생성
       │  - 실패 시 deterministic fallback
       │
       ├─ Read-only Verification
       │  - Eval 데이터로 결과 검증
       │
       ├─ Risk Card Context
       │  - Asset Context: 자산 설명 / 데이터 범위
       │  - Action State: 현재 조치 상태
       │  - Assignment Routing: 조치 담당자 / 담당 팀
       │
       └─ App / Dashboard
          - Risk Card 조회
          - Action State 조회·변경
          - Jira ticket 생성
          - AI Action Assistant 조회
```
