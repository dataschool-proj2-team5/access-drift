# 대시보드 데이터 계약

이 문서는 Access Drift Streamlit 대시보드가 읽는 데이터 소스, 내부 컬럼 계약, fallback 방식, 화면 표시용 정규화 기준을 공유하기 위한 문서입니다.

대시보드 화면과 컴포넌트는 Databricks 원천 컬럼을 직접 읽지 않고, `src/data_loader.py`에서 정규화한 내부 컬럼만 사용합니다.

## 데이터 소스 우선순위

대시보드는 아래 순서로 데이터를 읽습니다.

1. Databricks app schema의 dashboard view
2. mock data

### 1. Databricks app view

로컬 Streamlit secrets에 Databricks 설정이 있으면 Databricks app schema의 view를 먼저 조회합니다.

사용하는 주요 view/table은 다음과 같습니다.

| 소스 | 용도 |
| --- | --- |
| `risk_case_list_view` | Overview, Asset List의 case 목록과 우선순위 정렬 |
| `risk_card_detail_view` | Risk Card header, summary, owner, reviewer, recommendation 정보 |
| `risk_access_path_view` | Risk Card Access Path 구성 정보 |
| `risk_action_state` | Review Status 표시용 상태 |

`gold_core`는 화면용 주 소스가 아니라 app view가 비어 있을 때 fallback 또는 검증용 원천으로만 사용합니다.

### 2. Mock data

Databricks를 사용할 수 없으면 `src/mock_data.py`에서 mock row를 생성합니다.

mock data를 사용하는 경우 대시보드 화면에 `Using mock data` 안내가 표시됩니다.

## 내부 schema 원칙

- 화면 코드(`pages/`, `components/`)는 내부 컬럼명만 읽습니다.
- Databricks와 mock data의 차이는 `src/data_loader.py`에서 흡수합니다.
- 새로운 원천 컬럼이 추가되면 먼저 `src/data_loader.py`에서 내부 컬럼으로 매핑합니다.
- 내부 컬럼이 추가되면 `src/schema.py`와 이 문서를 함께 갱신합니다.

## Case ID 정책

Databricks의 원본 `risk_case_key`는 내부 조회, join, navigation, session state 용도로 유지합니다.

화면에는 원본 key를 직접 표시하지 않고 `display_case_id`를 표시합니다.

`display_case_id` 생성 규칙:

1. `risk_case_key` 원본 문자열을 기준으로 SHA1 해시를 생성합니다.
2. SHA1 결과 앞 6자리를 대문자로 사용합니다.
3. 최종 형식은 `CASE-XXXXXX`입니다.

예:

```text
risk_case_key = b000dd29d54bf5a7753acaff3416de947c7d154bd903f4035458c19923e6e2b0
display_case_id = CASE-3C200A
```

## 화면 표시 정규화

실데이터 값은 화면에 바로 노출하지 않고, 필요한 경우 `src/data_loader.py`에서 표시용 값으로 정규화합니다.

예:

| 원천 값 | 화면 표시 |
| --- | --- |
| `app_registration` | `App Registration` |
| `client_secret` | `Client Secret` |
| `["고객 이름", "전화번호"]` | `고객 이름, 전화번호` |
| `customer-export-storage-prod` | `Export Storage` |

Access Path에서 `asset_name`은 요약 표시용으로 쓰고, 원본 asset 이름은 `asset_full_name`에 보존합니다.

## 내부 기대 컬럼

| 컬럼 | 설명 |
| --- | --- |
| `risk_case_key` | Databricks 조회와 join에 사용하는 안정적인 원천 risk key입니다. |
| `case_id` | 대시보드 navigation과 session state에 사용하는 내부 risk case 식별자입니다. |
| `display_case_id` | UI에 표시하는 짧은 결정적 case label입니다. |
| `risk_title` | Risk Card 제목입니다. |
| `risk_level` | Critical, High, Medium, Low 같은 표시용 위험도입니다. |
| `drift_type` | Access drift 유형입니다. |
| `identity_name` | 위험과 연결된 identity, principal, account 이름입니다. |
| `identity_type` | Identity 유형입니다. |
| `object_name` | Credential 또는 access object 이름입니다. |
| `object_type` | Access object 유형입니다. |
| `credential_type` | Credential 유형입니다. |
| `credential_expires_at` | Risk Card Access Path에 표시하는 credential 만료일입니다. |
| `credential_status` | Credential lifecycle 상태입니다. |
| `owner_status` | Owner lifecycle 상태입니다. |
| `owner_name` | Owner 표시 이름입니다. |
| `owner_team` | Owner 소속 팀 표시 이름입니다. |
| `related_person_status` | 연결된 사람 계정의 상태입니다. |
| `linked_owner_label` | Owner 연결 근거를 표시하기 위한 label입니다. |
| `asset_name` | 대시보드 표시용으로 정규화한 asset 이름입니다. |
| `asset_full_name` | Access Path 보조 텍스트에 사용하는 원천 asset 이름입니다. |
| `asset_type` | Asset 유형입니다. |
| `asset_sensitivity` | Asset 민감도 label입니다. |
| `data_scope` | Risk Card에 표시하는 data scope label입니다. |
| `data_categories` | Risk Card에 표시하는 민감 데이터 category 텍스트입니다. |
| `permission_level` | Permission 또는 role 수준입니다. |
| `last_accessed_at` | 마지막 접근 시각입니다. |
| `detected_at` | Finding 탐지 시각입니다. |
| `created_at` | Access object 또는 case 생성 시각입니다. |
| `rotation_status` | Credential rotation 상태입니다. |
| `risk_score` | 위험도 정렬에 사용하는 숫자 점수입니다. |
| `review_status` | Review workflow 상태입니다. |
| `reviewer` | 지정된 reviewer입니다. |
| `action_owner` | 조치 담당자 또는 담당 팀입니다. |
| `recommended_action` | 권장 조치 텍스트입니다. |
| `risk_summary` | 위험 분석 tab에 표시하는 risk summary입니다. |
| `risk_factors` | Risk factor checklist 항목입니다. |
| `action_plan` | 권장 실행 단계입니다. |
| `ai_agent_messages` | Mock AI Agent chat message입니다. |
| `overview_title` | Overview Priority Review에 사용하는 짧은 제목입니다. |
| `ai_summary` | AI/RAG summary placeholder 텍스트입니다. |
| `reference_docs` | 참조 policy, runbook, evidence link입니다. |

## 변경 시 확인 사항

데이터 소스나 내부 컬럼을 변경할 때는 아래를 함께 확인합니다.

- `src/schema.py`의 `EXPECTED_COLUMNS`
- `src/data_loader.py`의 source-to-internal mapping
- `pages/`와 `components/`에서 해당 컬럼을 표시, 집계, 필터, 정렬에 사용하는지 여부
- `apps/dashboard/README.md`의 실행/데이터 로딩 설명
- mock data fallback이 계속 동작하는지 여부

## 아직 구현하지 않은 항목

- `risk_action_state`에 대한 Databricks write-back
- `risk_action_event` insert
- 실제 RAG/AI Agent 연동
- 실제 Ticket API 연동
