# RAG Evidence Contract

```text
version: 0.1.0
status: draft
updated_at: 2026-07-01
```

## 범위

이 문서는 RAG / AI Runbook이 참조할 Risk Case 단위 evidence document와 chunk 기준을 정의한다.

RAG evidence는 탐지 결과 자체가 아니라 AI 답변의 근거로 쓰는 조회용 데이터다. 따라서 Gold Core 본문에 직접 섞지 않고, `rag` schema에서 별도 관리한다.

## rag.risk_case_documents

Risk Case 1건을 사람이 읽을 수 있는 근거 문서 1건으로 만든다.

| 컬럼 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `risk_case_key` | string | yes | Gold Core와 조인할 Risk Card key |
| `finding_id` | string | yes | Gold finding id |
| `document_title` | string | yes | 검색 결과나 citation에 표시할 문서 제목 |
| `document_text` | string | yes | RAG 입력으로 사용할 Risk Case 근거 문서 |
| `source_table_refs` | array<string> | yes | 문서 생성에 사용한 테이블 목록 |
| `evidence_keys` | map<string,string> | yes | upstream evidence key 묶음 |
| `generated_at` | timestamp | yes | 문서 생성 시각 |
| `run_id` | string | yes | 생성 job/run 식별자 |

## rag.knowledge_chunks

v1에서는 Risk Case 1건을 chunk 1건으로 둔다. chunk size, overlap, split 방식은 DS/AI가 RAG 품질을 보며 조정한다.

| 컬럼 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `chunk_id` | string | yes | chunk unique key. v1은 `risk_case_key` 기반 deterministic id |
| `risk_case_key` | string | yes | 원본 Risk Case key |
| `chunk_text` | string | yes | Vector Search index 대상 텍스트 |
| `chunk_hash` | string | yes | chunk text hash |
| `chunk_order` | int | yes | 문서 내 chunk 순서. v1은 0 |
| `source_title` | string | yes | citation에 표시할 source title |
| `source_uri` | string | yes | citation에 표시할 source uri |
| `source_table_refs` | array<string> | yes | chunk 생성에 사용한 테이블 목록 |
| `evidence_keys` | map<string,string> | yes | upstream evidence key 묶음 |
| `generated_at` | timestamp | yes | chunk 생성 시각 |

## 조인 기준

Risk Card와 RAG evidence는 `risk_case_key`로 연결한다.

```text
rag.risk_case_documents.risk_case_key = gold_core.risk_case_key
rag.knowledge_chunks.risk_case_key = gold_core.risk_case_key
```

Vector Search 결과는 `chunk_id`와 `risk_case_key`를 함께 반환해야 한다.

## 금지 사항

- Secret value, token value, private key value를 저장하거나 색인하지 않는다.
- citation 없이 AI 답변 근거로 사용하지 않는다.
- Prompt, 답변 문구, recommended action 최종 표현을 이 계약에서 확정하지 않는다.
- Graph/Silver 원천 테이블을 그대로 chunking하지 않는다. Risk Case 단위 evidence document를 만든 뒤 chunking한다.
