# Access Drift

퇴사, 부서 이동, 외주 계약 종료 이후에도 남아 있는 접근 권한이 고객 데이터, 코드 저장소, 클라우드 자산 같은 민감 자산에 닿는지 탐지하고, 보안 담당자가 조치할 수 있도록 Risk Card와 AI 기반 조치 지원을 제공하는 보안 운영 대시보드입니다.

- 발표자료: [docs/presentations/발표자료.pdf](docs/presentations/발표자료.pdf)
- 아키텍처 개요: [docs/architecture/arch-overview.md](docs/architecture/arch-overview.md)
- 대시보드 문서: [apps/dashboard/README.md](apps/dashboard/README.md)

---

## 1. 프로젝트 소개

### 배경

퇴사자 계정을 비활성화해도 모든 접근 경로가 사라지는 것은 아닙니다.

자동화 계정, 앱 등록, client secret, SaaS 권한, 클라우드 IAM 권한은 사람 계정과 별도로 남을 수 있습니다. 이 권한이 민감 자산에 닿으면 단순 관리 누락이 아니라 실제 보안 리스크가 됩니다.

### 목표

본 프로젝트는 HR, IAM, Cloud/SaaS, 자산, 접근 권한 데이터를 수집·정규화해 다음 정보를 제공합니다.

- 퇴사자·이동자와 연결된 잔존 접근 경로
- 자동화 계정과 credential 기반 NHI 리스크
- 민감 자산에 대한 접근 가능 여부
- 우선 검토가 필요한 Risk Case
- Risk Card 기반 접근 경로와 위험 요인
- AI Action Assistant 기반 조치 방향 제안
- 조치 상태 관리와 티켓 생성 흐름

---

## 2. 주요 기능

| 기능 | 설명 |
| --- | --- |
| Risk Overview | 전체 리스크 현황, severity 분포, 우선 검토 대상 확인 |
| Priority Review | Critical/High 중심의 우선 검토 목록 제공 |
| Risk Card | 개별 케이스의 owner, credential, asset, access path, risk factor 확인 |
| Access Path | HI -> NHI -> Credential -> Asset 접근 관계 확인 |
| AI Action Assistant | 정책/RAG 근거를 기반으로 조치 방향과 실행 단계를 제안 |
| Action State | Risk Case별 검토 상태와 조치 상태 관리 |
| Ticket Creation | 필요한 경우 조치 티켓 생성 흐름 제공 |
| SQL Dashboard | row count, validation 결과, severity, action state 등 운영 상태 확인 |
| 품질 검증 | DLT/SQL 기반 null key, orphan edge, enum, 관계 오류 검증 |
| 권한 경계 | Unity Catalog 기반 catalog/schema/table 접근 경계 관리 |

---

## 3. 데모 흐름

### 대시보드

보안 담당자는 전체 리스크 현황과 우선 검토 대상을 확인합니다.

### Risk Card

대표 케이스를 선택하면 다음 정보를 확인할 수 있습니다.

- 어떤 사람이 관련되어 있는지
- 어떤 자동화 계정이 남아 있는지
- 어떤 credential이 활성 상태인지
- 어떤 민감 자산에 접근 가능한지
- 어떤 위험 요인이 severity를 높였는지

### Access Path

예시 흐름:

```text
퇴사자(HI) -> 자동화 계정(NHI) -> 활성 Credential -> 고객 데이터 Storage
```

### AI Action Assistant

정책 문서와 Risk Card 근거를 기반으로 조치 방향을 제안합니다.

- owner 재확인
- credential rotation 또는 revoke
- 권한 제거
- 예외 승인 필요 여부 확인
- 조치 티켓 생성

---

## 4. 시스템 아키텍처

### 아키텍처 개요

```text
외부 데이터 소스
HR · IAM · Cloud/SaaS · 접근 권한
        |
        | 수집 / 파일 적재
        v
Azure / Databricks Data Platform
ADLS -> Bronze -> Silver -> Detection -> Gold
        |
        | 조회 / 조치
        v
Databricks Apps
리스크 현황 · 우선 검토 · Risk Card · Access Path · 조치 티켓 생성
```

### 데이터 흐름

1. HR, IAM, Cloud/SaaS, 접근 권한 데이터를 Landing에 적재합니다.
2. ADLS에 원본 파일을 보존합니다.
3. Bronze에서 source별 원천형 테이블로 적재합니다.
4. Silver에서 principal, credential, asset, edge 공통 모델로 정규화합니다.
5. Detection에서 Silver 관계를 조합해 Risk Case를 판단합니다.
6. Gold에서 대시보드가 소비할 Risk Card 결과를 생성합니다.
7. Databricks Apps가 Gold/App view를 조회해 화면을 제공합니다.
8. AI Action Assistant가 Vector Search와 Model Serving endpoint를 통해 조치 방향을 생성합니다.
9. SQL Dashboard가 row count와 validation 결과로 운영 상태를 확인합니다.

---

## 5. 데이터 레이어

| 레이어 | 역할 |
| --- | --- |
| Landing | source별 raw 파일 보존 |
| Bronze | 원천 시스템 구조에 가까운 적재 |
| Silver | principal, credential, asset, edge 공통 모델 정규화 |
| Detection | 접근 관계를 조합해 Risk Case 판단 |
| Gold | Risk Card와 대시보드 소비용 결과 생성 |
| Eval | 탐지 결과 검증용 정답 케이스 |
| Context | Risk Card 표시와 조치 상태 보강 |
| RAG / Knowledge | AI Action Assistant 근거 문서 제공 |

---

## 6. 기술 스택

| 영역 | 기술 |
| --- | --- |
| Data Platform | Azure Databricks, Delta Lake, Databricks Workflows |
| Storage | ADLS Gen2 |
| Data Quality | DLT Expectations, SQL Validation, Schema Contract |
| Governance | Unity Catalog |
| Dashboard | Databricks Apps, Streamlit |
| AI / RAG | Databricks Vector Search, Model Serving endpoint, Foundation Model API endpoint |
| Infrastructure | Azure, Databricks Asset Bundle |
| CI/CD | GitHub Actions |
| Collaboration | GitHub Issues, Pull Requests, ADR |

---

## 7. 프로젝트 구조

```text
.
├── apps/
│   └── dashboard/              # Streamlit 기반 Databricks Apps 대시보드
├── data/
│   ├── dev/                    # dev/demo용 합성 데이터와 seed
│   ├── dlt-test/               # DLT smoke/validation 테스트 입력
│   └── poc/                    # PoC fixture seed
├── docs/
│   ├── adr/                    # 주요 기술·운영 의사결정
│   ├── architecture/           # 시스템 아키텍처와 데이터 흐름
│   ├── contracts/              # 스키마 계약, 데이터 계약
│   ├── engineering/            # DE 운영 기준과 runbook
│   ├── presentations/          # 발표자료와 발표 대본 초안
│   └── product/                # PRD, 데모 시나리오
├── infra/
│   ├── azure/                  # Azure 리소스 정의
│   └── databricks/             # Databricks bootstrap 및 설정
├── notebooks/                  # Databricks pipeline notebook
├── pipelines/                  # DLT pipeline source
├── sql/
│   └── databricks/
│       ├── migrations/         # DDL migration
│       └── queries/            # 검증 및 운영 SQL
├── tests/                      # 자동화 검증
├── tools/                      # 개발/검증 보조 도구
└── databricks.yml              # Databricks Asset Bundle 설정
```

---

## 8. 실행 방법

### 대시보드 로컬 실행

```bash
cd apps/dashboard
pip install -r requirements.txt
streamlit run app.py
```

Databricks 연결 정보가 없으면 mock data로 fallback합니다.

### Databricks Bundle 검증

```bash
databricks bundle validate -t dev
```

### Databricks Apps 배포

```bash
cd apps/dashboard
databricks bundle validate -t dev
databricks apps deploy -t dev --auto-approve --skip-validation
```

### 데이터 로딩 우선순위

대시보드는 다음 순서로 데이터를 읽습니다.

1. Databricks app schema view
2. Gold schema fallback
3. mock data fallback

주요 view:

- `risk_case_list_view`
- `risk_card_detail_view`
- `risk_access_path_view`
- `risk_action_state`

---

## 9. 검증 결과

| 항목 | 확인 내용 |
| --- | --- |
| 합성 데이터 생성 | HR, IAM/NHI, asset, access, eval seed 생성 |
| Landing/Bronze | 원본 보존과 source별 적재 흐름 구성 |
| Silver | principal, credential, asset, edge 공통 모델 정규화 |
| Detection/Gold | Risk Case와 Risk Card 결과 생성 |
| 품질 검증 | DLT/SQL 기반 key, enum, orphan, 관계 오류 확인 |
| CI 검증 | 스키마 계약과 구현 불일치 조기 탐지 |
| 대시보드 | Overview -> Priority Review -> Risk Card -> Access Path 흐름 확인 |
| AI Assistant | Vector Search 근거 검색 + LLM 응답/fallback 흐름 구성 |
| 운영 모니터링 | SQL Dashboard 기반 row count, validation, action state 확인 |
| 권한 통제 | Unity Catalog 기반 접근 경계 설계 및 적용 |

---

## 10. 주요 의사결정

### Databricks 중심 플랫폼 선택

보안 데이터 수집, 정규화, 검증, 서빙, 권한 관리를 한 플랫폼 경계 안에서 처리하기 위해 Azure Databricks를 중심으로 구성했습니다.

### ADLS Gen2 기반 원본 보존

Landing 데이터를 원본 형태로 보존해 재처리와 추적 가능성을 확보했습니다. ADLS Gen2는 계층형 네임스페이스를 제공해 레이어별 경로 관리에 적합합니다.

### Batch Processing 선택

Access Drift 판단은 단일 이벤트보다 HR, IAM, credential, asset, access 상태를 같은 기준 시점으로 조합하는 것이 중요합니다. 따라서 초 단위 스트리밍보다 재현 가능한 배치 처리를 우선했습니다.

### 메달리온 기반 데이터 파이프라인

Landing -> Bronze -> Silver -> Detection -> Gold 흐름으로 데이터의 신뢰 수준과 책임을 분리했습니다. Detection을 Silver와 Gold 사이에 두어 공통 모델, 탐지 룰, 앱 소비 결과를 분리했습니다.

### Silver 공통 접근 모델

여러 source의 데이터를 principal, credential, asset, edge 모델로 정규화했습니다. Silver는 Risk를 판단하지 않고, Detection이 조합할 수 있는 관계 데이터를 제공합니다.

### DLT/SQL 기반 품질 검증

DLT는 변환 중 품질 게이트로 사용하고, SQL 검증은 적재 이후 row count, orphan, enum, key 오류를 확인하는 운영 검증으로 사용했습니다.

### Unity Catalog 기반 거버넌스

보안 프로젝트 특성상 데이터 처리 성능뿐 아니라 접근 경계와 lineage가 중요합니다. Unity Catalog를 통해 catalog/schema/table 단위의 권한 경계를 관리합니다.

### AI Action Assistant

AI는 최종 조치를 자동 확정하지 않고, 정책 문서와 Risk Card 근거를 바탕으로 조치 방향을 보조합니다. LLM 실패 시 deterministic fallback을 사용해 대시보드 기본 흐름은 유지합니다.

---

## 11. 현재 범위와 제외 범위

### 현재 범위

- 잔존 접근권한 탐지 흐름
- NHI credential 기반 접근 경로 탐지
- Risk Card와 Access Path 제공
- AI 기반 조치 방향 보조
- SQL Dashboard 기반 운영 관측
- Unity Catalog 기반 권한 경계
- GitHub Actions 기반 일부 CI/CD 자동화

### 제외 범위

- 회사 전체 SIEM 대체
- 모든 보안 이상행위 탐지
- 사람 승인 없는 자동 revoke
- 실시간 스트리밍 탐지
- 실제 고객사 전체 데이터 규모 검증
- 완전한 cross-table atomic publish

---

## 12. 향후 개선 방향

| 영역 | 개선 방향 |
| --- | --- |
| Product | 승인 기반 조치 자동화, 외부 업무 시스템 연동 확대 |
| DE | 실제 source connector 도입, Landing -> Bronze 적재 자동화 |
| DE | published_run 기반 atomic publish 강화 |
| DE | 대규모 데이터 기준 성능/비용 검증 |
| DS | scoring 로직 고도화, ML 기반 행동 패턴 비교 |
| AI | RAG 평가 고도화, citation 품질 개선 |
| Ops | 비용 모니터링, SQL Warehouse/App/Vector Search 비용 최적화 |

---

## 13. 협업 방식

- GitHub Issues로 작업 단위를 관리합니다.
- 기능 작업은 브랜치를 분리해 Pull Request로 병합합니다.
- 중요한 기술·운영 결정은 ADR로 남깁니다.
- 데이터 계약과 스키마 변경은 문서와 구현을 함께 갱신합니다.
- CI와 SQL 검증으로 변경 영향도를 확인합니다.

---

## 14. 관련 문서

- 제품 요구사항: [docs/product/prd.md](docs/product/prd.md)
- 데모 시나리오: [docs/product/demo.md](docs/product/demo.md)
- 아키텍처 개요: [docs/architecture/arch-overview.md](docs/architecture/arch-overview.md)
- 스키마 계약: [docs/contracts/](docs/contracts/)
- 주요 의사결정: [docs/adr/](docs/adr/)
- 대시보드 문서: [apps/dashboard/README.md](apps/dashboard/README.md)
