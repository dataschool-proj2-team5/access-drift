# RAG Doc Chunks Contract

```text
version: 0.1.0
status: draft
updated_at: 2026-07-01
```

## 범위

이 문서는 RAG / AI Runbook이 참조할 공식 조치 문서 chunk 기준을 정의한다.

RAG chunk는 탐지 결과 자체가 아니라 AI 답변의 근거로 쓰는 조회용 데이터다. 따라서 Gold Core 본문에 직접 섞지 않고, `rag` schema의 `doc_chunks` 테이블에서 별도 관리한다.

Risk Card 현재값은 DS/AI가 질의 생성 시 `gold_core`, `asset_context`, `assignment_routing`, `risk_action_state`에서 읽는다. `rag.doc_chunks`에는 공식 런북·정책 문서처럼 검색 대상이 되는 corpus만 저장한다.

## rag.doc_chunks

v1에서는 공식 조치 문서를 사람이 큐레이션한 짧은 chunk로 둔다. chunk size/overlap 조정은 DS/AI가 RAG 품질을 보며 후속 조정한다.

| 컬럼 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `chunk_id` | string | yes | chunk unique key |
| `doc_id` | string | yes | 원본 문서 단위 id |
| `provider` | string | yes | `microsoft`, `github`, `google` 같은 provider |
| `service` | string | yes | `entra_id`, `microsoft_graph`, `github_apps`, `google_workspace` 같은 service |
| `doc_type` | string | yes | 문서 유형. 예: `api_reference`, `admin_guide` |
| `drift_type` | string | yes | 검색 필터 후보 |
| `action_type` | string | yes | 조치 유형 필터 후보 |
| `chunk_text` | string | yes | 검색과 RAG 입력으로 사용할 짧은 공식 원문 excerpt 또는 원문에 가까운 사실 문장. 케이스 해석이나 내부 조치 권고문은 넣지 않는다. |
| `chunk_hash` | string | yes | chunk text hash |
| `chunk_order` | int | yes | 문서 내 chunk 순서. v1은 0 |
| `source_title` | string | yes | citation에 표시할 source title |
| `source_uri` | string | yes | citation에 표시할 source uri |
| `effective_date` | date | yes | chunk 기준일 |
| `generated_at` | timestamp | yes | chunk 생성 시각 |
| `run_id` | string | yes | 생성 job/run 식별자 |

## 조인 기준

`rag.doc_chunks`는 Risk Card와 직접 조인하지 않는다.

```text
Risk Card current data -> DS query generation
rag.doc_chunks          -> retrieval corpus
```

검색 결과는 `chunk_id`, `source_title`, `source_uri`를 함께 반환해야 한다.

## 초기 적재 순서

초기 corpus는 대표 NHI residual access 조치에 가까운 순서로 적재한다.

1. Microsoft Entra ID / Microsoft Graph
2. GitHub App / token access
3. Google Workspace third-party app access

## 금지 사항

- Secret value, token value, private key value를 저장하거나 색인하지 않는다.
- citation 없이 AI 답변 근거로 사용하지 않는다.
- Prompt, 답변 문구, recommended action 최종 표현을 이 계약에서 확정하지 않는다.
- embedding, retrieval 품질, prompt, groundedness/safety evaluation은 DS/AI 영역에서 관리한다.
- Graph/Silver 원천 테이블을 그대로 chunking하지 않는다.
- Risk Case 현재값을 `rag.doc_chunks`에 복사하지 않는다.
