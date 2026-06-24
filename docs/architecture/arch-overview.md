**버전:** v0.1

**기준:** 2026년 6월 18일

---

## 1. 문제 정의

IdP/SCIM에서 퇴사·팀이동·외주 종료를 처리해도, SCIM 밖의 SaaS 계정과 NHI(Non-Human Identity)는 별도로 남아 있을 수 있다.

> **핵심 Pain:** "IdP에서 계정을 껐는데도 실제 접근경로가 다 끊겼는지 확신이 없다"
> 

탐지 대상은 두 가지다.

- **비SCIM 계정**: SCIM 미지원 SaaS 로컬 계정, SSO 미강제 앱, Google Drive 외부공유 등
- **NHI**: Azure App Registration / Service Principal, Key Vault secret, CI/CD secret, Deploy key, 외부 API key 등

---

## 2. 시스템 컨텍스트

!image.png

```
┌──────────────────────────────────────────────────────────────────┐
│                          Evidence Sources                         │
│  HR/IdP CSV · GitHub API · Azure Resource Graph                  │
│  Azure App Reg / SP / Key Vault metadata · SaaS/Legacy CSV       │
│                                                                   │
│  * MVP: 실제 API 응답 스키마 기반 합성 데이터 사용               │
│  * api_pull_task는 스키마 검증 및 확장용                         │
└─────────────────────────────┬─────────────────────────────────────┘
                        │ 수집 (API Pull / CSV Drop)
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              Databricks Lakehouse (ADLS Gen2)               │
│                                                             │
│  Landing → Bronze → Silver → Graph + Risk Scoring → Gold   │
│                                                             │
│  Unity Catalog: 전 레이어 거버넌스 / RBAC / Column Masking   │
└──────────────────────┬──────────────────────────────────────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
   AI Runbook 생성  Streamlit     Databricks SQL Dashboard
   (LLMOps)        (Security     (파이프라인/Ops 모니터링)
                    Ops Console)
          │            │
          └─────┬───────┘
                ▼
   Jira / GitHub Issue 생성 · SaaS 권한 해제
```

---

## 3. 파이프라인 레이어

| 레이어 | 역할 | 핵심 특성 |
| --- | --- | --- |
| **Landing Zone** | 원본 파일 불변 보존 | raw JSON/CSV, Dead Letter 분리 |
| **Bronze** | 원본 적재 | append-only, 메타데이터 태깅 |
| **Silver** | 정규화 + 품질 보증 | DLT expectations, identity/NHI/asset/edge 모델 |
| **Graph** | 잔존 접근 경로 탐지 | NetworkX(MVP) → GraphFrames(확장), residual path 계산 |
| **Risk Scoring** | 위험도 산출 | Rule-based (운영) + Isolation Forest (baseline 비교) |
| **Gold** | 조치용 마트 | Risk Card, SLA status, 티켓 페이로드, Audit report |
| **AI Runbook** | 조치 초안 생성 | RAG(정책 문서 참조) + PII 마스킹 후 Azure AI Foundry LLM 호출, fallback template |
| **Streamlit** | Security Ops Console | Risk Card 검토 · Jira 티켓 · SaaS 권한 해제 · 조치 완료 버튼 |
| **SQL Dashboard** | 파이프라인/Ops 모니터링 | Delta ops 테이블 기반 — 사용자 제품 화면 아님 |
| **SQL Alerts** | 운영 알림 | 파이프라인 실패 · 품질 이상 · source stale 감지 |

---

## 4. Workflow DAG

!ChatGPT Image 2026년 6월 23일 오전 10_32_43.png

```
synthetic_data_task          api_pull_task
(실제 스키마 기반 합성)       (스키마 검증 · 확장용)
         │                          │
         └────────────┬─────────────┘
                      ▼
ingest_task
(Auto Loader → Bronze)
      │
      ▼
dlt_silver_task
(정규화 + 품질 체크)
      │
      ▼
graph_task
(residual path)
      │
      ▼
risk_scoring_task
(risk score)
      │
      ▼
dlt_gold_task
(Risk Card + SLA)
      │
      ▼
ai_runbook_task               ops_log_task
(LLM 조치 초안)    ────────▶  (Delta ops 테이블 write)
      │                              │
      ▼                              ▼
export_task              SQL Dashboard / SQL Alerts
(Jira 자동 티켓 — High Risk)
```

---

## 5. 거버넌스 원칙

**Review-first** — 시스템은 판단하지 않는다. 탐지 → 설명 → 사람 승인 → 조치 순서를 강제한다.

- AI는 조치 보조자. "침해됨" 단정 대신 "접근 가능한 경로가 남아 있음"으로 표현
- 권한 revoke는 반드시 사람 승인 후
- 자동 티켓(export_task)은 알림이지 권한 제거가 아님
- LLM에 PII / secret 값 비전송. 패턴 정보만 전달

**Unity Catalog 권한 계층**

| 스키마 | 접근 권한 | Column Masking |
| --- | --- | --- |
| Bronze | DE write / SecOps read | — |
| Silver | DE write / SecOps read | principal_email, secret_name |
| Gold | DE write / SecOps read | principal_email, secret_name (SecOps만 full 노출) |

---

## 6. ADR (Architecture Decision Record)

| # | 결정 항목 | 선택 | 대안 | 선택 이유 |
| --- | --- | --- | --- | --- |
| 1 | 데이터 플랫폼 | Databricks / Lakehouse | 별도 앱 DB + 백엔드 | 대기업 타겟 규모 대응 · 스냅샷/이력 누적 · 고객사 데이터 경계 내 처리 |
| 2 | 오케스트레이터 | Databricks Workflows | ADF, Airflow | 모든 작업이 Databricks 내부 — 외부 오케스트레이터 불필요 |
| 3 | Silver/Gold 변환 | DLT | dbt | 복잡한 조인 없음, expectations/멱등성 자동 처리, 팀 학습 비용 절감 |
| 4 | 그래프 분석 MVP | NetworkX | GraphFrames | identity < 10,000 규모, 단일 노드로 충분 |
| 5 | 그래프 분석 확장 | GraphFrames | — | identity ≥ 10,000 시 SP2 실측 후 전환 |
| 6 | 거버넌스 | Unity Catalog | 없음 | Column masking · RBAC · Lineage — 보안 도메인에 필수 |
| 7 | Security Ops Console | Streamlit + Databricks Apps | React/Next.js, Power BI, Gradio | 티켓 생성·revoke·AI chat은 BI 도구가 아닌 운영 콘솔 기능 · Gold Delta 직접 읽기 · UC 권한 상속 |
| 8 | Ops 모니터링 | Databricks SQL Dashboard | 별도 모니터링 웹앱, App Insights | ops 테이블이 이미 Delta에 있어 SQL Dashboard가 자연스러움 · 별도 인프라 불필요 |
| 9 | 운영 알림 | Databricks SQL Alerts | App Insights, 외부 모니터링 | 파이프라인 실패·품질 이상을 SQL로 감지 가능 · Databricks 안에서 닫을 수 있음 |
| 10 | App Insights 제외 | — | App Insights | 별도 Azure 앱 실행 계층 없음 · Databricks 로그 + ops 테이블로 대체 |
| 11 | LLM 플랫폼 | Azure AI Foundry (모델 프로바이더) | OpenAI API 직접 호출 | Azure 스택 통일 · 엔터프라이즈 보안 요건 충족. Private Endpoint는 엔터프라이즈 확장 시 옵션 |
| 11-1 | Prompt 최적화 | promptfoo | LangSmith 등 | 코드 기반 관리, CI 연동 용이, Hub 구조 없이 경량 |
| 11-2 | RAG 목적 | 회사 정책/런북 문서 참조 기반 조치 초안 생성 | Fine-tuning | 퇴사자 정리 정책·Secret rotation 정책 등 참고 · fine-tuning 대비 데이터 요구량 낮음 |
| 11-3 | RAG 구현 스택 | Databricks Vector Search | Azure AI Search | 별도 인프라 확장 없음 · UC 거버넌스 일관성 유지 · Databricks 안에서 완결 |
| 12 | Risk Scoring 방식 | Rule-based (운영) + Isolation Forest (baseline 비교) | ML 지도학습 | 운영 점수는 Rule-based로 설명 가능성 확보. IF는 "rule-based vs ML" 성능 비교용 baseline — baseline 결과에 따라 운영 점수 편입 확장 가능 (SP2 실측 후 판단) |
| 13 | 수집 방식 | 배치 (이벤트 트리거) | 실시간 스트리밍 | 퇴사 이벤트 트리거 배치로 충분, 실시간 불필요 |
| 13-1 | 데이터 출처 | 실제 API 응답 스키마 기반 합성 데이터 | 실제 기업 데이터 | 실제 기업 데이터 수집 불가 · IS_PLANTED_RISK 레이블 포함 · api_pull_task는 스키마 검증 및 확장용 |
| 14 | LLM 외부 전송 범위 | PII/secret 마스킹 후 패턴만 전송 | 전체 전송 | 엔터프라이즈 보안 요건, AI 윤리 원칙 |
| 15 | IaC | Databricks Bundle + Bicep | Terraform | Databricks 네이티브 번들 + Azure 네이티브 Bicep으로 도구 통일 |
| 16 | SLA 기준 | 7일 breach / 3일 at_risk | — | 퇴사 후 잔존 접근 비즈니스 허용 기준 (ISO27001 참조) |
| 17 | 티켓 생성 트리거 | 자동(export_task) + 수동(Streamlit 버튼) | 자동만 | High Risk 자동 알림 + 보안팀 수동 검토 후 트리거 분리 |
| 18 | 자산 메타데이터 역할 | 컨텍스트 고지만 | 리스크 판단 반영 | 자산관리 시스템이 아님. 판단 근거는 접근 경로에 한정 |
| 19 | SaaS 권한 해제 | 관리자 버튼 기반 해제 지원 | 자동 해제 | 버튼 클릭을 사람 승인으로 간주 — Review-first 원칙 유지 |
| 20 | 배포 모델 | Customer-managed 우선 | 멀티테넌트 SaaS | 고객사 데이터·인증을 고객사 환경에 유지 · 대기업 데이터 반출 우려 해소 · MVP에서 멀티테넌트 격리 부담 제거 |
| 21 | 멀티테넌트 SaaS | 상용화 확장 옵션 | MVP 기본 구조 | 테넌트 격리·SSO 연동·DPA·보관 정책이 필요 — MVP 핵심 검증 이후 단계 |

---

## 7. 마일스톤

| 단계 | 목표 |
| --- | --- |
| **PoC** | Walking Skeleton — 소스 1개 end-to-end, Risk Card 1건 렌더링 |
| **Sprint 1** | 소스 확장 (GitHub + HR CSV), Silver 모델 완성, LLMOps 초안 |
| **Sprint 2** | Risk Scoring 고도화, Streamlit UI 완성, CI/CD, 발표 준비 |

---

*구현 세부 스펙(컬럼 정의, DLT 코드, 스키마)은 별도 문서(arch-spec) 작성 예정*