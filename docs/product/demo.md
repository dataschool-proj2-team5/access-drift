# MVP Demo Scenario

**버전:** v0.1  
**기준:** 2026년 6월 26일  
**상태:** 초안

이 문서는 Access Drift MVP 데모에서 사용할 대표 시나리오와 보안 전제를 정리한다. PRD와 Sprint 1 Scope의 기준에 맞춰, S1에서는 하나의 대표 리스크 케이스를 중심으로 Risk Card 흐름을 검증한다.

이 문서의 인물, 팀, 자산명은 모두 데모를 위한 가상 데이터다.

---

## 1. 타겟 기업 프로필

- **기업 유형:** 대형 이커머스 플랫폼
- **비즈니스 규모:** 대규모 고객 기반과 주문·배송·CS·마케팅 운영을 가진 커머스 기업
- **인프라 환경:** Azure 기반 데이터·서비스 환경을 운영하며, GitHub 등 외부 SaaS를 개발 협업 도구로 사용한다.
- **보안 현황:** Entra ID와 IAM 체계를 기반으로 사용자 계정과 주요 시스템 접근 권한을 중앙 관리하지만, SaaS 내부 권한과 NHI(Service Principal, API token, integration credential)는 각 시스템별로 분산 관리되어 통합적으로 확인하기 어렵다.

---

## 2. 데모 시나리오 주요 개념

이 시나리오는 Azure 기반 자동 배치와 NHI client secret이 남아 있는 상황을 다룬다.

- **Service Principal:** 자동 배치나 외부 연동이 사람 계정 대신 Azure 리소스에 접근할 때 사용하는 NHI다.
- **Client secret:** Service Principal이 Entra ID에서 access token을 발급받을 때 사용하는 인증 수단이다. Secret 값 자체는 Access Drift에 저장하지 않는다.
- **Export Storage:** CRM, CS, 데이터 분석을 위해 고객 데이터를 추출해 저장하는 Azure Storage/ADLS 영역이다. 운영 DB를 외부 도구나 업무팀에 직접 노출하지 않고, 필요한 데이터만 파일 형태로 분리해 후속 업무에서 재사용하기 위해 사용한다.
- **Public network access:** Storage endpoint가 외부 네트워크에서 접근 가능한 설정이다. 실제 접근 가능 여부는 Storage 권한, 네트워크 정책, client secret 상태가 함께 결정한다.

데모의 Export Storage `crm-customer-export-prod`는 고객 이름, 전화번호, 배송지, 주문내역을 포함하므로 PRD의 민감 자산 분류 기준상 Critical로 본다. 상세 기준은 [PRD 8.4 민감 자산 영향 기준 위험 설명 및 우선순위](./prd.md#84-민감-자산-영향-기준-위험-설명-및-우선순위)를 따른다.

이 케이스에서 탐지 소스는 Service Principal/App Registration, client secret metadata, Storage 권한 metadata다. `crm-customer-export-prod`는 탐지 소스가 아니라 접근 경로의 최종 민감 자산이다.

---

## 3. S1 대표 리스크 케이스

### 고객 데이터 Export Storage 접근 NHI 잔존

#### 상황

김민수는 CRM 데이터 운영팀의 Senior Data Engineer로, 재직 중 마케팅, CS, 데이터 분석을 위해 고객 분석 테이블에서 필요한 고객 데이터를 정기적으로 추출하는 Azure 자동 배치 작업을 운영했다.

운영 DB를 외부 도구나 업무팀에 직접 노출하지 않기 위해, 이 배치는 필요한 데이터만 추출해 Export Storage `crm-customer-export-prod`에 저장한다. CRM, CS, 데이터 분석 도구는 이 Storage의 파일을 기준으로 후속 업무를 수행한다.

이 배치는 Service Principal `sp-crm-customer-export-prod`로 인증해 `crm-customer-export-prod`에 접근한다. `crm-customer-export-prod`에는 CRM 캠페인, CS 응대, 데이터 분석을 위해 추출된 고객 이름, 전화번호, 배송지, 주문내역 파일이 저장된다.

Access Drift는 `sp-crm-customer-export-prod`와 client secret metadata, Storage 권한 관계를 이용해 이 NHI가 `crm-customer-export-prod`에 닿는지 확인한다.

#### 정상 접근 주체와 권한

`crm-customer-export-prod`는 업무별로 제한된 경로 권한을 부여받아 사용한다.

| 주체 | 업무 목적 | 정상 권한 |
| --- | --- | --- |
| CRM/마케팅팀 | 휴면 고객 리텐션, VIP 쿠폰, 장바구니 이탈 캠페인 대상자 추출 | `crm-segments/` 경로 `read/list` |
| CS 운영팀 | 고객 문의 대응을 위한 주문·배송 관련 export 파일 조회 | `cs-lookup/` 경로 `read` |
| 데이터 분석팀 | 캠페인 성과와 고객군별 주문 패턴 분석 | `analytics-export/` 경로 `read/list` |
| `sp-crm-customer-export-prod` | 고객 분석 테이블에서 데이터를 추출해 `crm-customer-export-prod`에 적재 | export 경로 `write`, 재처리·검증용 `read/list` |

이번 리스크는 정상 업무팀 권한이 아니라, 퇴사자와 연결된 자동화 Service Principal의 client secret과 Storage 권한이 함께 남아 있는 경우다.

#### 보안 전제

이 시나리오는 다음 전제가 성립하는 경우를 다룬다.

- 김민수는 2026년 6월 10일 퇴사했고 HR/IdP 계정은 비활성화됐다.
- 김민수가 owner로 등록되어 있던 Service Principal `sp-crm-customer-export-prod`는 별도 비활성화되지 않았다.
- `sp-crm-customer-export-prod`의 client secret은 active 상태로 남아 있다.
- `sp-crm-customer-export-prod`는 `crm-customer-export-prod`에 `read/list` 권한을 가지고 있다.
- 신규 Storage는 private endpoint와 IP 제한을 적용하지만, 과거 CRM/CS 연동용 `crm-customer-export-prod`는 외부 연동을 위해 public network access가 허용된 상태로 남아 있다.
- 네트워크 통제와 권한 구성이 맞물려, 해당 client secret은 Storage API 인증에 사용할 수 있고 export 파일 조회가 가능한 접근 경로를 만든다.
- Access Drift는 secret 값을 저장하거나 노출하지 않고, client secret metadata와 권한 관계만 사용한다.

#### 문제

김민수의 사람 계정은 비활성화됐지만, 김민수가 owner로 남아 있던 `sp-crm-customer-export-prod`와 해당 client secret은 계속 active 상태다.

`sp-crm-customer-export-prod`는 `crm-customer-export-prod`에 접근할 수 있으므로, 퇴사자와 연결된 NHI가 Critical 고객 데이터에 닿는 잔존 접근 경로로 판단된다.

#### 접근 경로

```text
김민수 / 전 CRM 데이터 운영팀
  -> Service Principal `sp-crm-customer-export-prod`
  -> active client secret
  -> Storage read/list 권한
  -> Export Storage `crm-customer-export-prod`
  -> 고객 이름/전화번호/배송지/주문내역
```

#### 기대 Risk Card

- **드리프트 유형:** NHI Access Drift
- **권한 주체:** Service Principal `sp-crm-customer-export-prod`
- **연결 인물:** 김민수, 전 CRM 데이터 운영팀
- **활성 client secret:** active client secret metadata
- **민감 자산:** Export Storage `crm-customer-export-prod`
- **심각도:** Critical
- **왜 위험한가:** 퇴사자와 연결된 NHI client secret이 active 상태로 남아 있으며, 고객 식별 정보와 주문내역이 포함된 export storage에 접근 가능하다.
- **검토 담당자:** 박지연, SecOps
- **조치 담당 후보:** 이다영, CRM 데이터 운영팀 Lead
- **권장 조치:** client secret rotation, Service Principal owner 재지정, Storage 권한 재검토, legacy public access 정책 점검

---

## 4. S1 데모 흐름

1. 보안 담당자가 Risk Overview에서 Critical 리스크를 확인한다.
2. High-Priority list에서 `crm-customer-export-prod` 접근 리스크를 선택한다.
3. Risk Card 상세에서 다음 정보를 확인한다.
   - 어떤 NHI client secret이 남아 있는지
   - 해당 client secret이 어떤 사람 owner와 연결되는지
   - 어떤 권한을 통해 어떤 민감 자산에 닿는지
   - 왜 Critical 리스크인지
4. 접근 경로를 확인한다.
5. AI 조치 권고안을 확인한다.
6. 보안 담당자는 수동 조치 후보를 확인한다.

S1에서는 Jira 실제 발행, 자동 권한 회수, 조치 이력 추적은 포함하지 않는다.

---

## 5. 아카이브된 후보 시나리오

다음 시나리오는 초기 후보였으나 S1 대표 케이스에서는 제외한다. 후속 스프린트 또는 확장 데모에서 다시 검토할 수 있다.

### 후보 A. Azure Key Vault 내 PG 마스터 키

- 결제 인프라 담당자가 퇴사한 뒤 Azure Key Vault의 PG 마스터 키가 active 상태로 남아 있는 시나리오
- 결제 승인/취소 영향이 강하지만, 실제 환경에서는 PG사 방화벽, IP allowlist, 승인 정책 등 추가 통제가 있는 경우가 많아 S1 대표 케이스에서는 제외한다.

### 후보 B. GitHub Repository 권한 잔존

- 퇴사한 개발자의 GitHub repository write 권한이 수동으로 제거되지 않아 소스코드 접근 권한이 남아 있는 시나리오
- SaaS Access Drift를 설명하기 좋은 케이스이나, S1에서는 NHI 대표 케이스를 우선 구현하고 GitHub 케이스는 확장 후보로 둔다.
