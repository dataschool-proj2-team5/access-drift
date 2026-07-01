# RAG Doc Chunks Contract

```text
version: 0.1.0
status: draft
updated_at: 2026-07-01
```

## 범위

이 문서는 RAG / AI Runbook이 참조할 근거 문서 chunk 기준을 정의한다.

RAG chunk는 탐지 결과 자체가 아니라 AI 답변의 근거로 쓰는 조회용 데이터다. 따라서 Gold Core 본문에 직접 섞지 않고, `rag` schema의 `doc_chunks` 테이블에서 별도 관리한다.

Risk Card 현재값은 DS/AI가 질의 생성 시 `gold_core`, `asset_context`, `assignment_routing`, `risk_action_state`에서 읽는다. `rag.doc_chunks`에는 정책, playbook, source guide, API reference처럼 검색 대상이 되는 corpus만 저장한다.

## 요구사항 매핑

RAG corpus는 Risk Card의 권장 조치 설명을 보강하기 위한 근거다. `rag.doc_chunks`는 아래 요구사항을 최소 필드로 만족해야 한다.

| 요구사항 | 필요한 필드 | 설명 |
| --- | --- | --- |
| 보안 정책 문서 검색 | `doc_type`, `drift_type`, `principal_kind` | NHI/HI별 정책 근거를 drift 유형에 맞춰 찾는다. |
| Remediation playbook 검색 | `doc_type`, `action_type`, `drift_type` | owner 재지정, credential 회전/삭제, 권한 검토/회수 같은 조치 절차를 찾는다. |
| 과거 Risk Case sample 검색 | `doc_type`, `drift_type`, `source_system`, `principal_kind` | 유사한 검증용 sample case를 참고 근거로 찾는다. |
| source별 운영 가이드 검색 | `source_system`, `source_area`, `action_type` | Azure, GitHub, Google Workspace 등 source별 조치 근거를 찾는다. |
| citation 표시 | `chunk_id`, `source_title`, `source_uri` | AI 답변이 어떤 근거 chunk와 문서를 참조했는지 표시한다. |
| corpus 재현성 | `doc_id`, `chunk_order`, `effective_date`, `chunk_hash`, `run_id` | 같은 문서의 chunk 순서, 기준일, 적재 run을 추적한다. |

현재 seed에는 검증용 내부 정책/playbook/case가 포함된다. 검증용 여부는 `doc_type`, `source_uri`, 계약 문서로 구분하고, `chunk_text`에는 검색에 필요한 근거 문장만 둔다.

## rag.doc_chunks

v1에서는 사람이 큐레이션한 짧은 chunk를 저장한다. chunk size/overlap 조정은 DS/AI가 RAG 품질을 보며 후속 조정한다.

| 컬럼 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `chunk_id` | string | yes | chunk unique key |
| `doc_id` | string | yes | 원본 문서 단위 id |
| `source_system` | string | yes | `azure`, `github`, `google_workspace`, `internal` 같은 source 구분 |
| `source_area` | string | yes | `entra_id`, `microsoft_graph`, `github_apps`, `security_policy` 같은 세부 영역 |
| `doc_type` | string | yes | 문서 유형. 예: `internal_policy`, `internal_playbook`, `synthetic_case_history`, `source_guide`, `api_reference` |
| `drift_type` | string | yes | 검색 필터 후보 |
| `principal_kind` | string | yes | `nhi` 또는 `hi`. 현재 seed는 NHI residual access 중심이므로 `nhi`만 생성한다. |
| `action_type` | string | yes | 조치 유형 필터 후보 |
| `chunk_text` | string | yes | 검색과 RAG 입력으로 사용할 짧은 근거 문장. 검증용 여부 같은 운영 메타 설명은 본문에 넣지 않는다. |
| `chunk_hash` | string | yes | chunk text hash |
| `chunk_order` | int | yes | 문서 내 chunk 순서. v1은 0 |
| `source_title` | string | yes | citation에 표시할 source title |
| `source_uri` | string | yes | citation에 표시할 source uri |
| `effective_date` | date | yes | chunk 기준일 |
| `generated_at` | timestamp | yes | chunk 생성 시각 |
| `run_id` | string | yes | 생성 job/run 식별자 |

Seed JSONL에는 `chunk_hash`, `generated_at`, `run_id`를 넣지 않는다. 이 값들은 적재 notebook에서 계산한다.

예시:

```json
{
  "chunk_id": "nhi-policy-owner-credential-001",
  "doc_id": "nhi-security-policy-v01",
  "source_system": "internal",
  "source_area": "security_policy",
  "doc_type": "internal_policy",
  "drift_type": "nhi_residual_access",
  "principal_kind": "nhi",
  "action_type": "review_owner_credential_permission",
  "chunk_order": 0,
  "source_title": "NHI / SaaS Integration 관리 정책 v0.1",
  "source_uri": "internal://security-policy/nhi-saas-integration-v0.1",
  "effective_date": "2026-07-01",
  "chunk_text": "NHI, Service Principal, App Registration, SaaS integration은 현재 운영 담당 owner를 가져야 한다."
}
```

```json
{
  "chunk_id": "entra-application-remove-password-001",
  "doc_id": "entra-application-remove-password",
  "source_system": "azure",
  "source_area": "microsoft_graph",
  "doc_type": "api_reference",
  "drift_type": "nhi_residual_access",
  "principal_kind": "nhi",
  "action_type": "remove_application_password",
  "chunk_order": 0,
  "source_title": "application: removePassword",
  "source_uri": "https://learn.microsoft.com/en-us/graph/api/application-removepassword?view=graph-rest-1.0",
  "effective_date": "2026-07-01",
  "chunk_text": "Remove a password from an application. The request body requires keyId, the unique identifier for the password."
}
```

```json
{
  "chunk_id": "azure-rbac-role-assignment-remove-001",
  "doc_id": "azure-rbac-role-assignment-remove",
  "source_system": "azure",
  "source_area": "azure_rbac",
  "doc_type": "source_guide",
  "drift_type": "nhi_residual_access",
  "principal_kind": "nhi",
  "action_type": "remove_storage_role_assignment",
  "chunk_order": 0,
  "source_title": "Remove Azure role assignments",
  "source_uri": "https://learn.microsoft.com/en-us/azure/role-based-access-control/role-assignments-remove",
  "effective_date": "2026-07-01",
  "chunk_text": "Remove Azure role assignments when access is no longer needed."
}
```

## 검색 키 기준

`rag.doc_chunks`는 Risk Card와 직접 조인하지 않는다.

```text
Risk Card current data -> DS query generation
rag.doc_chunks          -> retrieval corpus
```

DS/AI는 Risk Card 현재값에서 검색 조건을 만들고, `rag.doc_chunks`의 metadata 필드를 filter 또는 rerank 기준으로 사용한다.

| Risk Card 값 | `rag.doc_chunks` 검색 키 | 사용 방식 |
| --- | --- | --- |
| `drift_type` | `drift_type` | 같은 drift 유형의 정책/playbook/source guide 우선 검색 |
| `subject_type` 또는 principal 구분 | `principal_kind` | `nhi`, `hi` 중 대상 주체 유형과 맞는 chunk 우선 검색 |
| source/provider 정보 | `source_system` | `azure`, `github`, `google_workspace`, `internal` 등 source별 guide 검색 |
| source 세부 영역 | `source_area` | `entra_id`, `microsoft_graph`, `azure_rbac`, `github_apps` 등 세부 조치 근거 검색 |
| 필요한 조치 유형 | `action_type` | owner 재지정, credential 회전/삭제, 권한 검토/회수 같은 조치별 근거 검색 |

대표 NHI residual access 케이스에서는 다음 조합을 우선 사용한다.

```text
drift_type = nhi_residual_access
principal_kind = nhi
source_system IN (internal, azure)
source_area IN (security_policy, security_operations, entra_id, microsoft_graph, azure_rbac)
```

검색 결과는 `chunk_id`, `source_title`, `source_uri`를 함께 반환해야 한다.

## 초기 적재 순서

초기 corpus는 대표 NHI residual access 조치에 가까운 순서로 적재한다.

1. NHI / SaaS Integration 관리 정책
2. Remediation Playbook
3. Risk Case sample
4. Microsoft Entra ID / Microsoft Graph
5. GitHub App / token access
6. Google Workspace third-party app access

현재 `principal_kind`는 `nhi`, `hi`만 허용한다. 공통 성격의 문서도 필요한 경우 NHI/HI chunk를 분리한다.

## 금지 사항

- Secret value, token value, private key value를 저장하거나 색인하지 않는다.
- citation 없이 AI 답변 근거로 사용하지 않는다.
- Prompt, 답변 문구, recommended action 최종 표현을 이 계약에서 확정하지 않는다.
- embedding, retrieval 품질, prompt, groundedness/safety evaluation은 DS/AI 영역에서 관리한다.
- Graph/Silver 원천 테이블을 그대로 chunking하지 않는다.
- Risk Case 현재값을 `rag.doc_chunks`에 복사하지 않는다.
