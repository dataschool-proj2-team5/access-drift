# 아키텍처 발표자료 초안

> PPT로 옮기기 위한 발표용 요약 문서입니다. 기준 문서는 `docs/architecture/arch-overview.md`를 따르며, 이 문서는 기준 문서를 대체하지 않습니다.

---

## Architecture Overview

PO 문제를 시스템 구조로 연결하는 전체 흐름

- 외부 데이터 소스
- Azure / Databricks Data Platform
- 메달리온 기반 데이터 파이프라인
- Databricks Apps 조회 / 조치
- AI 지원과 운영·거버넌스

발표 위치:

- PO 문제 제기 이후
- DE / DS 상세 설명 이전
- 목표 설명 시간 3~5분

발표 대본 초안:

아키텍처 파트에서는 PO에서 제기한 문제를 실제 시스템 구조로 어떻게 풀었는지 설명합니다. 이 프로젝트의 핵심은 단순히 위험 목록을 보여주는 것이 아니라, HR, IdP/IAM, Cloud/SaaS, 접근 권한 데이터를 한 흐름으로 연결해서 “누가, 어떤 자동화 계정을 통해, 어떤 자산에 접근 가능한지”를 볼 수 있게 만드는 것입니다.

그래서 전체 구조는 세 덩어리로 나눠 설명할 수 있습니다. 먼저 외부 데이터 소스가 있고, 그 다음 Azure / Databricks Data Platform 안에서 데이터를 보존·정규화·탐지·서빙하는 파이프라인이 있습니다. 마지막으로 Databricks Apps에서 리스크 현황, 우선 검토 목록, Risk Card, Access Path, 조치 티켓 생성을 지원합니다.

이 장에서는 개별 테이블이나 파이프라인 구현보다 시스템 경계와 책임을 먼저 보여줍니다. 이후 DE 파트에서 각 레이어의 데이터 계약과 품질 검증을 설명하고, DS 파트에서 Detection과 eval 검증으로 이어지는 흐름입니다.

---

## System Overview

흩어진 identity, cloud/SaaS, 접근 권한 데이터를 Databricks에서 정규화하고 Risk Card로 연결

발표용 구성:

```text
외부 데이터 소스
HR · IdP/IAM · Cloud/SaaS · 접근 권한
        |
        | 수집 / 파일 적재
        v
Azure / Databricks Data Platform
ADLS → Bronze → Silver → Detection → Gold
        |
        | 조회 / 조치
        v
Databricks Apps
리스크 현황 · 우선 검토 · 리스크 카드 · 접근 경로 · 조치 티켓 생성
```

설명 포인트:

- 외부 데이터 소스: HR, IdP/IAM, Cloud/SaaS, 접근 권한
- 데이터 플랫폼: ADLS 보존, Databricks 정규화·탐지·서빙
- Databricks Apps: 리스크 현황, 우선 검토, Risk Card, 접근 경로, 조치 티켓 생성
- AI: Vector Search + Foundation Model APIs 기반 조치 지원
- 운영·거버넌스: Unity Catalog, DLT, SQL Dashboard

이 장에서 제외:

- 개별 table 이름, notebook 이름, task 세부 구현은 DE 발표에서 다룬다.
- UC 권한 상세, DLT expectation 상세, SQL Dashboard query 목록은 이 장에서 길게 설명하지 않는다.

발표 대본 초안:

전체 흐름은 왼쪽의 외부 데이터 소스에서 시작합니다. HR은 재직·퇴사·이동 상태를 제공하고, IdP/IAM은 사용자와 자동화 계정, credential, owner 정보를 제공합니다. Cloud/SaaS와 접근 권한 데이터는 실제 접근 대상 자산과 권한 관계를 제공합니다.

이 데이터는 Azure / Databricks Data Platform으로 들어옵니다. ADLS는 원본을 보존하는 역할을 하고, Databricks 안에서 Bronze, Silver, Detection, Gold 흐름으로 데이터가 처리됩니다. 여기서 Bronze와 Silver는 DE 파트에서 자세히 설명하고, Detection과 eval은 DS 파트에서 이어서 설명합니다.

사용자 입장에서는 Databricks Apps를 통해 결과를 봅니다. 보안 담당자는 리스크 현황과 우선 검토 대상을 보고, Risk Card에서 특정 케이스의 접근 경로를 확인합니다. 필요한 경우 조치 티켓 생성까지 연결됩니다. AI 지원은 이 과정에서 정책 문서와 Risk Card 근거를 바탕으로 조치 방향을 제안하는 역할입니다.

운영·거버넌스는 별도 시스템이 아니라 플랫폼 전체에 걸쳐 있는 공통 축입니다. Unity Catalog는 권한과 lineage, DLT는 품질 게이트, SQL Dashboard는 운영 상태 확인에 사용합니다. 다만 이 장에서는 전체 구조만 보여주고, 각 항목의 세부 구현은 뒤쪽 DE 설명으로 넘깁니다.

---

## 메달리온 아키텍처 설계

데이터의 신뢰 수준과 책임 분리

설계 원칙:

- 메달리온 적용: source, 탐지 로직, 앱 요구사항 변화 영향 분리
- 파이프라인 순서: `Landing(원본) → Bronze(원천형) → Silver(공통 모델) → Detection(탐지) → Gold(서빙)`
- Detection 단계 분리: Silver 공통 모델과 Gold 서빙 결과 사이에서 핵심 탐지 룰 적용
- 보조 데이터 분리: 탐지 로직 검증, 대시보드 보조, 조치 이력, AI 근거

발표 시 언급:

- 메달리온의 핵심은 레이어별 데이터 책임 분리
- 지원 서비스 확장, 탐지 로직 고도화, 대시보드 요구사항 확장을 전제로 한 구조
- 파이프라인 순서는 짧게만 언급
- Detection은 데이터 변환 파이프라인에 포함되지만 Silver의 공통 모델 정규화와 Gold의 대시보드 소비 결과 사이에 둔 핵심 처리 단계
- 파이프라인에 포함되지는 않지만, 보조용 데이터는 별도 레이어로 분리해 둠

추가 질문 대응:

- 메달리온을 Bronze/Silver/Gold 세 단계 고정 구조가 아니라 데이터 신뢰 수준과 책임을 단계별로 나누는 패턴으로 해석
- 이 프로젝트에서는 Silver와 Gold 사이에 Detection을 명시해 공통 모델, 탐지 룰, 앱 서빙 결과를 분리

발표 대본 초안:

메달리온 구조를 선택한 이유는 데이터의 신뢰 수준과 책임을 단계별로 분리하기 위해서입니다. 이 프로젝트는 source가 계속 늘어날 수 있고, 탐지 로직도 바뀔 수 있고, 대시보드에서 보여줘야 하는 요구사항도 바뀔 수 있습니다. 이 변화가 서로 직접 흔들리지 않게 하려면 레이어별 책임을 분리하는 것이 중요합니다.

흐름은 Landing에서 원본을 보존하고, Bronze에서 source 형태를 유지한 채 적재하고, Silver에서 공통 접근 모델로 정규화하는 구조입니다. 그 다음 Detection에서 핵심 탐지 룰을 적용하고, Gold에서 앱이 바로 소비할 수 있는 결과로 제공합니다.

여기서 중요한 결정은 Detection을 Silver와 Gold 사이에 별도로 둔 것입니다. Silver는 공통 모델을 만드는 레이어이고, Gold는 앱이 소비하는 결과입니다. 탐지 룰은 둘 중 어느 한쪽에 섞기보다 별도 단계로 두는 것이 책임이 명확합니다. 이렇게 하면 나중에 탐지 로직이 바뀌어도 Silver 모델 전체를 흔들지 않고, 앱 출력 요구가 바뀌어도 Detection의 의미를 유지할 수 있습니다.

또한 Eval, Context, Knowledge/RAG 같은 데이터는 변환 파이프라인의 핵심 레이어는 아니지만, 탐지 검증, 화면 보강, AI 근거 제공에 필요합니다. 그래서 메달리온 본 흐름과 구분해서 보조 데이터로 분리했습니다.

---

## Key Architecture Decisions

구현 편의보다 데이터 신뢰성, 접근 경계, 검증 가능성을 우선

| 선택 SELECTED | 대안 ALTERNATIVES |
| --- | --- |
| **Azure / Databricks Data Platform**<br>보안 데이터 수집·검증·서빙·권한 관리를 한 플랫폼에서 처리 | **Snowflake / Airflow 또는 ADF + Spark 조합**<br>구성 가능하지만 운영 경계가 분산 |
| **ADLS Gen2**<br>원본 보존 · 재처리 · 계층형 데이터 관리 | **일반 Blob Storage / S3 / GCS**<br>레이어 권한 분리 또는 Azure 경계 이슈 |
| **Batch Processing**<br>기준 시점 정합성 · 재현 가능한 판단 | **Real-time Streaming**<br>초 단위 SLA보다 상태 정합성 우선 |
| **Databricks Apps + Streamlit**<br>보안 조치용 콘솔을 가볍게 제공 | **Power BI / Grafana / React 별도 앱**<br>BI 중심이거나 별도 앱 운영 부담 |
| **Databricks AI Search + Foundation Model APIs**<br>AI 검색·모델 선택을 Databricks 경계에서 처리 | **Azure AI Search + Azure OpenAI**<br>검색·LLM·앱 경계가 분산 |

발표 시 언급:

- 이 장에서는 전체 SIEM이나 무승인 자동 Revoke 같은 제품 범위 결정보다는, 그 범위를 만족시키기 위한 기술 선택을 설명
- 대안들도 각각 강점은 있지만, 이번 프로젝트에서는 보안 데이터 경계, 권한 관리, 재현 가능한 판단, 운영 단순성을 더 우선
- 데이터 수집, 품질 검증, 앱 서빙, AI 검색이 서로 다른 운영 경계로 쪼개지는 것을 피하고자 Databricks 중심으로 설계
- Azure / Databricks를 선택한 핵심 이유는 Lakehouse, Workflows, DLT, Unity Catalog를 한 플랫폼 경계에서 운영할 수 있기 때문
- 보안 프로젝트이므로 처리 성능뿐 아니라 Unity Catalog 기반 권한 경계와 lineage 관리도 중요한 선택 기준
- 앱과 AI도 같은 플랫폼 경계 안에서 붙여, 조회·검색·조치 지원의 운영 경계를 단순화
- Access Drift는 단일 이벤트 처리보다 HR, IdP/IAM, credential, access, asset 상태를 조합하는 판단에 가까움
- 여러 source를 같은 기준 시점으로 맞춰 보는 것이 중요하므로, 초 단위 SLA보다 상태 정합성과 재현 가능한 판단을 우선해 배치 처리를 선택
- 스트리밍도 가능하지만 지연 도착, 이벤트 순서, 상태 저장, replay 설계가 필요해 현재 범위에서는 복잡도 대비 이득이 낮음
- 대시보드는 단순 리포팅이 아니라 Risk Card 확인, Access Path 검토, 조치 티켓 생성 같은 운영 앱에 가까움
- Power BI나 Grafana는 시각화에는 좋지만 운영 액션 중심 화면에는 한계가 있고, React 별도 앱은 API 서버, 인증, 배포, 권한 연동을 따로 관리해야 해 MVP에는 무거움
- 그래서 Databricks Apps + Streamlit으로 Gold 데이터를 바로 조회하는 가벼운 운영 앱 구조를 선택
- Azure AI Search + Azure OpenAI 조합도 Azure 네이티브 대안으로 가능하지만, 검색 인덱스, LLM 호출, Gold 데이터, 앱 운영 경계가 분리됨
- Databricks AI Search를 쓰면 RAG 검색을 Gold/Risk Card 데이터와 같은 플랫폼 경계에서 설명하기 쉬움
- Foundation Model APIs는 모델 선택지가 넓어 Claude 같은 모델도 사용할 수 있고, 보안 조치 지원처럼 정책·권한 구조·코드성 문맥을 함께 봐야 하는 경우 유리하다고 판단

발표 대본 초안:

이 장은 “무엇을 썼는가”보다 “왜 이 조합을 선택했는가”를 설명하는 페이지입니다. 기준은 네 가지였습니다. 보안 데이터 경계, 권한 관리, 재현 가능한 판단, 운영 단순성입니다.

첫 번째로 Azure / Databricks를 선택한 이유는 보안 데이터 수집, 검증, 서빙, 권한 관리를 한 플랫폼 경계 안에서 처리하기 위해서입니다. Snowflake나 Airflow, ADF와 Spark 조합도 가능하지만, 파이프라인, 권한, 앱, 검증의 운영 경계가 여러 군데로 나뉩니다. 이 프로젝트는 identity, credential, 접근 권한처럼 민감한 데이터를 다루기 때문에 경계를 단순하게 유지하는 것이 더 중요하다고 판단했습니다. 특히 보안 프로젝트에서는 처리 성능만큼 접근 경계와 lineage가 중요하기 때문에, Unity Catalog를 같은 플랫폼 안에서 사용할 수 있다는 점도 Databricks 선택 이유에 포함됩니다.

두 번째로 ADLS Gen2는 원본 보존과 재처리 기준점으로 사용했습니다. Landing 데이터를 남겨야 나중에 변환 결과가 이상할 때 원본으로 돌아가 확인할 수 있고, 같은 입력으로 다시 처리할 수 있습니다. 또한 레이어별 데이터 관리와 권한 분리에도 적합합니다.

세 번째로 처리 방식은 실시간 스트리밍보다 배치를 선택했습니다. 퇴사나 권한 변경은 빠르게 대응해야 하지만, 초 단위 이벤트 처리보다 여러 source 상태를 같은 기준 시점으로 맞춰 판단하는 것이 더 중요합니다. HR, IdP/IAM, credential, asset, access 데이터를 조합해야 하므로, 현재 범위에서는 배치가 더 재현 가능하고 운영이 단순합니다.

네 번째로 대시보드는 BI 리포트가 아니라 보안 조치용 콘솔에 가깝습니다. Risk Card를 보고, 접근 경로를 확인하고, 조치 티켓을 생성해야 합니다. 그래서 Power BI나 Grafana보다 Databricks Apps + Streamlit이 더 적합했고, React 별도 앱은 인증, API 서버, 배포, 권한 연동을 별도로 관리해야 해서 MVP에는 무겁다고 판단했습니다.

마지막으로 AI 쪽은 Databricks AI Search와 Foundation Model APIs를 선택했습니다. RAG 검색과 모델 호출을 Gold/Risk Card 데이터와 같은 플랫폼 경계에서 설명할 수 있고, Foundation Model APIs를 통해 모델 선택지도 가져갈 수 있습니다. 보안 조치 지원은 정책 문서, 권한 구조, 코드성 문맥을 함께 봐야 하므로 이런 유연성이 필요하다고 판단했습니다.

---

## 발표 연결 멘트

PO 문제 제기에서 DE / DS 상세 설명으로 넘어가는 연결 문장

- PO → Architecture: “사람, 앱, credential, 자산, 접근 권한 데이터를 한 경로로 연결해야 합니다.”
- Architecture → DE: “이 구조를 신뢰 가능한 데이터 제품으로 만들기 위해 각 레이어의 계약과 검증을 설명하겠습니다.”
- Architecture → DS: “Gold 이전까지 만들어진 접근 경로와 탐지 후보를 바탕으로 리스크 판단과 추천 로직을 설명하겠습니다.”

---

## 확인 체크리스트

- [ ] `docs/architecture/arch-overview.md`의 용어와 충돌하지 않는다.
- [ ] 발표자가 이 문서만 보고 3~5분 안에 아키텍처 파트를 설명할 수 있다.
- [ ] UC/Governance 상세 설명이 아키텍처 파트를 과도하게 차지하지 않는다.
- [ ] 현재 구현 범위와 후속 확장 후보가 구분되어 있다.
- [ ] DE 상세 구현으로 넘어가는 연결 멘트가 자연스럽다.
