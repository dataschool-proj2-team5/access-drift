# RAG / AI Runbook 역할 경계

이 문서는 RAG / AI Runbook 작업에서 DE, DS/AI, PO/Security의 책임 경계를 정리한다.

## 기본 원칙

RAG 구현과 답변 품질 튜닝은 DS/AI가 주도한다. DE는 DS/AI가 사용할 수 있는 근거 데이터, chunk, citation metadata, Vector Search index 기반을 안정적으로 제공한다.

AI 윤리와 신뢰성은 프롬프트만의 책임이 아니다. DE는 안전하고 추적 가능한 근거 데이터와 접근 경계를 책임지고, DS/AI는 retrieval·prompt·답변 가드레일을 책임지며, PO/Security는 사용자 노출 범위와 조치 책임 경계를 정의한다.

## 역할 경계

| 영역 | 주 담당 | 설명 |
| --- | --- | --- |
| Evidence document | DE | Gold/Core와 context를 조합해 Risk Case 단위 근거 문서를 생성한다. |
| Chunk/Citation metadata | DE | `chunk_id`, `source_title`, `source_uri`, `evidence_keys`, `chunk_hash`를 관리한다. |
| Vector Search endpoint/index | DE | endpoint/index 생성, 권한, 재실행 기준을 관리한다. |
| Prompt / 답변 형식 | DS/AI | system/user prompt, 답변 형식, refusal/uncertainty 표현을 설계한다. |
| Retrieval 품질 | DS/AI | embedding model, top-k, threshold, chunking 개선을 결정한다. |
| AI 윤리/가드레일 | DS/AI + PO/Security, DE 협업 | hallucination, 근거 부족 답변, 민감값 노출, 자동 조치 오해를 방지한다. |
| 사용자 노출 범위 | PO/Security | 어떤 근거와 권고를 SecOps에게 보여줄지 결정한다. |

## DS/AI Handoff

DE가 제공하는 기본 입력은 다음과 같다.

```text
rag.risk_case_documents
rag.knowledge_chunks
Vector Search index 후보: access_drift_dev.rag.knowledge_chunks_index
```

DS/AI가 조정할 항목은 다음과 같다.

- chunk size와 overlap
- embedding model
- retrieval top-k와 score threshold
- prompt와 answer schema
- citation 없는 답변 처리
- groundedness/safety evaluation

## Runbook Source 우선순위

Azure, GitHub 같은 공식 조치 런북은 전체 문서 크롤링보다 대표 조치 케이스에 맞춘 소수 문서 큐레이션이 ROI가 높다.

1. 대표 Risk Case의 `drift_type`과 `recommended_action`에 직접 연결되는 공식 문서를 먼저 고른다.
2. 문서 전체가 아니라 조치 판단에 필요한 섹션만 chunk 후보로 둔다.
3. 각 source에는 `source_title`, `source_uri`, 적용 대상, 기준일을 남긴다.
4. DS/AI는 이 근거로 답변 품질과 citation 동작을 먼저 검증한다.

초기 대상은 다음 정도로 제한한다.

| 대상 | 목적 |
| --- | --- |
| Microsoft Entra ID App / Service Principal credential 관리 문서 | NHI credential 만료·삭제 권고 근거 |
| Microsoft Entra ID owner / app registration 관리 문서 | 퇴사자 owner 정리 권고 근거 |
| GitHub token / app access 관리 문서 | GitHub 계정·토큰 잔여 접근 후속 확장 근거 |

광범위한 공식 문서 수집, 자동 크롤링, 주기적 문서 동기화는 초기 범위가 아니다.

## AI 윤리 최소 확인 항목

- 제공된 근거 밖의 사실 생성 금지
- citation 없는 조치 권고 금지
- secret value, token value, private key value 출력 금지
- 자동 권한 회수/삭제를 단정적으로 지시하지 않기
- 근거가 부족하면 근거 부족으로 답하기
- AI 권고는 자동 조치가 아니라 SecOps 검토 보조로 표시하기

## DE 확인 항목

- RAG index에 권한 없는 문서나 민감값이 포함되지 않는다.
- chunk에는 citation에 필요한 metadata가 포함된다.
- 같은 입력으로 evidence document/chunk를 재생성해도 key가 안정적이다.
- Vector Search index 생성 또는 실패 사유가 PR에 기록된다.
