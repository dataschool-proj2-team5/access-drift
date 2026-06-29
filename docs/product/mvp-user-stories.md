# MVP User Stories

**버전:** v0.1  
**기준:** 2026년 6월 26일  
**상태:** 초안

이 문서는 Access Drift MVP의 사용자 요구사항을 Epic / Feature / User Story 단위로 정리한다. 제품 범위와 원칙은 [PRD](./prd.md)를 기준으로 하며, 스프린트별 상세 완료 기준과 검증 방법은 별도 sprint scope 문서에서 다룬다.

## 1. Epic / Feature 요약

| **Epic** | ID | **Feature** | Priority | Target Sprint |
| --- | --- | --- | --- | --- |
| Epic 1. 통합 모니터링 | F1.1 | 전체 현황 (Risk Overview) | P0 | S1 |
|  | F1.2 | 최우선 검토 대상 목록 (High-Priority list) | P0 | S1 |
| Epic 2. 위험 탐지 및 분석 | F2.1 | 잔존 권한 목록 | P0 | S1 |
|  | F2.2 | 접근 경로 | P0 | S1 |
|  | F2.3 | 아이덴티티 기준 자산 매핑 (Identity-Centric Asset Mapping) | P2 | Backlog |
| Epic 3. 조치 워크플로우 | F3.1 | AI 조치 권고안 조회 (AI Recommendation Review) | P0 | S1 |
|  | F3.2 | Jira 티켓 초안 자동 생성 (Jira Ticket Auto-Generation) | P1 | S2 |
|  | F3.3 | 권장 조치 내용 수정 (Draft Customization) | P1 | S2 |
|  | F3.4 | 최종 승인 및 티켓 발행 (Approval & Ticket Issuance) | P1 | S2 |
| Epic 4. 거버넌스 및 감사 | F4.1 | 조치 이력 및 진행 상태 추적 (Remediation Tracking) | P2 | Backlog |
|  | F4.2 | 보안 감사 로그 조회/관리 (Audit Log Management) | P3 | Backlog |

Priority 기준: P0 필수 / P1 중요 / P2 보통 / P3 낮음  
Target Sprint 기준: P0는 S1, P1은 S2, P2/P3는 Backlog로 둔다. 단, 팀 합의에 따라 조정할 수 있다.

## 2. 상세 기능 요구사항

### Epic 1. 통합 모니터링

#### **F1.1. 전체 현황 (Risk Overview)**

- **User Story:** 보안 담당자로서 업무 파악을 위해 조치가 필요한 권한을 한눈에 확인하고 싶다.
- **Acceptance Criteria**
    - 대시보드 상단에 전체 권한의 조치 현황(미처리/처리 중/처리 완료)이 표시되어야 한다.
    - 각 권한에 대한 위험 등급 분포가 표시되어야 한다.
- 참고: S1에서는 조치 상태 표시를 우선 적용하고, S2에서는 조치 방법 기록을 확장한다.

#### **F1.2. 최우선 검토 대상 목록 (High-Priority list)**

- **User Story:** 보안 담당자로서 검토 및 조치가 시급한 위험 권한을 알고 싶다.
- **Acceptance Criteria**
    - 위험도가 높은 Top N개가 표시되어야 한다.
    - 권한에 대한 최소 요약 정보(권한 주체/위험 등급/조치 상태)가 표시되어야 한다.
    - 각 항목에는 우선 검토 대상으로 선정된 핵심 사유가 한 줄로 표시되어야 한다.
    - 각 항목을 선택하면 상세 분석 화면으로 이동할 수 있어야 한다.

### Epic 2. 위험 탐지 및 분석

#### **F2.1. 잔존 권한 목록**

- **User Story:** 보안 담당자로서 남아있는 권한의 전체 목록을 알고 싶다.
- **Acceptance Criteria**
    - 각 권한에 위험 점수 또는 등급이 표시되어야 한다.
    - 각 권한에는 SaaS Access Drift 또는 NHI Access Drift 등 드리프트 유형이 표시되어야 한다.
    - 각 권한은 Critical/High/Medium 등급으로 분류되어야 한다.
        - Low 등급은 탐지는 하나, 대시보드에선 제외한다.
    - 가능한 경우 잔존 접근 기간 또는 산정 기준일이 표시되어야 한다.
    - 각 권한을 선택하면 상세 분석 화면으로 이동할 수 있어야 한다.

#### **F2.2. 접근 경로**

- **User Story:** 보안 담당자로서 위험 권한의 업무 영향 판단을 위해, 이 자산이 어디까지 접근 가능한지 알고 싶다.
- **Acceptance Criteria**
    - 선택한 위험 권한의 접근 경로가 시각화되어야 한다.
    - 접근 가능한 시스템과 데이터 유형이 표시되어야 한다.
    - 민감 자산 접근 여부가 표시되어야 한다.
    - 접근 이벤트/로그가 있는 경우, 탐지 판정 기준이 아닌 상세 분석 참고 정보로 표시할 수 있어야 한다. 단, 이 항목은 S2에서 고려한다.

#### **F2.3. 아이덴티티 기준 자산 매핑 (Identity-Centric Asset Mapping)**

- **User Story:** 보안 담당자로서 특정 인사 변동자가 어떤 SaaS 계정들을 가지고 있고, 그 계정들이 어떤 자산들과 연결되어 있는지 인물 중심으로 묶어서 확인하고 싶다.
- **Acceptance Criteria**
    - 특정 인사 변동자를 선택하면 해당 인물이 보유한 모든 서드파티 SaaS 계정 리스트가 노출되어야 한다.

### Epic 3. 조치 워크플로우

#### F3.1. AI 조치 권고안 조회 (AI Recommendation Review)

- **User Story:** 보안 담당자로서 위험 권한에 대한 권장 조치를 확인하고 싶다.
- **Acceptance Criteria**
    - 시스템은 위험 요인을 분석한 바탕으로 권장 조치를 생성해야 한다.
    - 권장 조치 유형은 Secret Rotation, 권한 회수, Owner 재지정, 접근 권한 축소, 담당자 확인 요청 등을 포함해야 한다.
    - 권고안은 수동 권한 회수 절차를 포함할 수 있어야 한다.
    - AI 권고안은 탐지 근거에 없는 사실을 생성하지 않아야 한다.
    - AI 권고안은 secret 값을 출력하지 않아야 하며, 침해 사실을 단정하지 않아야 한다.
    - AI가 생성한 권고안임이 표시되어야 한다.

#### F3.2. Jira 티켓 초안 자동 생성 (Jira Ticket Auto-Generation)

- **User Story:** 보안 담당자로서 각 시스템 담당자가 실제 조치를 수행할 수 있도록 Jira 티켓을 발급하고 싶다.
- **Acceptance Criteria**
    - 위험 권한 정보와 AI 권고안을 기반으로 Jira 티켓 초안이 생성되어야 한다.
    - Jira 티켓에는 다음 정보가 포함되어야 한다.
    - 정보: 제목, 담당자, 대상 권한, 위험 등급, 위험 요소, 접근 가능 자산, 권장 조치, 조치 기한
    - 초안 상태에서는 Jira 티켓이 실제 발행되지 않아야 한다.
    - 보안 담당자는 생성된 티켓 초안을 확인할 수 있어야 한다.

#### F3.3. 권장 조치 내용 수정 (Draft Customization)

- **User Story:** 보안 담당자로서 조직 상황에 맞게 AI가 생성한 권장 조치와 Jira 티켓 초안을 수정하고 싶다.
- **Acceptance Criteria**
    - 보안 담당자는 권장 조치 내용을 수정할 수 있어야 한다.
    - 승인되지 않은 조치안은 Jira 티켓으로 생성되지 않아야 한다.

#### F3.4. 최종 승인 및 티켓 발행 (Approval & Ticket Issuance)

- **User Story:** 보안 담당자로서 검토가 완료된 조치안을 최종 승인하여 Jira 티켓으로 자동 발행하고 싶다.
- **Acceptance Criteria**
    - Jira 티켓 생성 전 승인 단계가 반드시 있어야 한다.
    - 승인된 조치안만 Jira 티켓으로 생성되어야 한다.
    - Jira 티켓 생성 성공/실패 상태가 사용자에게 표시되어야 한다.
    - Jira 티켓 생성에 성공한 경우 티켓 번호와 링크가 표시되어야 한다.

### Epic 4. 거버넌스 및 감사

#### F4.1. 조치 이력 및 진행 상태 추적 (Remediation Tracking)

- **User Story:** 보안 담당자는 발급된 Jira 티켓의 진행 상태를 확인하고 싶다.
- **Acceptance Criteria**
    - 각 자산별 Jira 티켓 상태가 표시되어야 한다.
    - 조치 상태는 미처리, 처리 중, 처리 완료로 구분되어야 한다.

#### F4.2. 보안 감사 로그 조회/관리 (Audit Log Management)

- **User Story:** 보안 담당자로서 컴플라이언스 감사 자료 대응을 위해 위험 탐지부터 조치 승인 및 티켓 발행까지의 활동 이력을 확인하고 싶다.
- **Acceptance Criteria**
    - 감사 로그를 기간별, 조치 상태별, 담당자별로 조건 검색 및 필터링하여 조회할 수 있어야 한다.
