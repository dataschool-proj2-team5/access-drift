# RAG Chain Contract (DS)

```text
version: 0.2.0
status: draft
updated_at: 2026-07-02
```

## 범위

이 문서는 DS가 소유하는 RAG **체인**(검색 → 생성 → 평가) 기준을 정의한다.

근거 corpus(`rag.doc_chunks`)와 그 스키마는 [RAG Doc Chunks Contract](./rag-evidence.md)(DE)에서 관리한다. 이 문서는 corpus 위에서 동작하는 검색 index, 질의 생성, 근거 기반 응답, citation 강제, deterministic fallback, 평가 지표를 정의한다.

RAG는 탐지 판단을 새로 하지 않는다. Gold Core `gold_core`에 이미 생성된 Risk Case를 입력으로 받아 근거 기반 권장 조치와 citation을 생성하는 조치 보조 레이어다.

## 구성요소 (Databricks 네이티브)

| 단계 | 구현 | notebook |
| --- | --- | --- |
| 검색 index | Databricks Vector Search, Delta Sync index (`rag.doc_chunks` 자동 동기) | `12_rag_vector_index.ipynb` |
| 임베딩 | FM API `databricks-gte-large-en` | (index 생성 시 지정) |
| 질의 생성 | `gold_core` finding → 질의 텍스트 + metadata 필터 | `13_rag_chain.ipynb` |
| 생성 LLM | Databricks FM API pay-per-token endpoint (기본 `databricks-meta-llama-3-3-70b-instruct`, 외부 API key/개인 결제 불필요). External Model(`access_drift_llm` → OpenAI `gpt-4o-mini`)은 `rag_llm_endpoint` 변수로 교체 가능 | `13_rag_chain.ipynb` |
| trace | MLflow run, finding별 질의/근거/응답 기록 | `13_rag_chain.ipynb` |
| 평가 | retrieval recall / citation rate + Agent Evaluation(groundedness/correctness) | `14_rag_eval.ipynb` |

## 출력 테이블

DS 체인 결과는 `rag` schema에 둔다. corpus(`doc_chunks`)와 분리한다.

- `rag.recommended_action` — finding 1건당 근거 기반 권장 조치 (마이그레이션 `009`)
- `rag.eval_results` — eval set 케이스별 평가 지표 (마이그레이션 `009`)

두 테이블 모두 overwrite 적재한다(기존 Gold/Silver 원칙과 동일). 컬럼은 `sql/databricks/migrations/009_create_rag_chain_tables.sql`을 기준으로 한다.

## 검색 키

`rag.doc_chunks`는 Risk Card와 직접 조인하지 않는다. `gold_core` 현재값에서 질의와 필터를 만든다.

| Gold Core 값 | 검색 사용 |
| --- | --- |
| `drift_type` | Vector Search `filters.drift_type` |
| `subject_type` | `filters.principal_kind` (`nhi`/`hi`로 매핑, 현재 seed는 `nhi`) |
| `asset_display_name`, `asset_sensitivity`, `asset_environment`, `owner_display_name` | 질의 텍스트 구성 |

대표 NHI residual access 케이스 기본 필터:

```text
drift_type = nhi_residual_access
principal_kind = nhi
top_k = 4
```

## 생성 규칙 (citation 강제 / 환각 방지)

1. 검색 결과가 있으면, LLM은 **제공된 근거 chunk에 있는 내용만으로** 조치를 제안하고 각 문장 끝에 `[chunk_id]` citation을 붙인다.
2. 응답이 근거를 하나도 인용하지 않으면 그 응답은 신뢰하지 않고 fallback 한다.
3. 아래 경우는 모두 **deterministic fallback**으로 처리한다 (`answer_source = 'deterministic_fallback'`).
   - 검색 결과가 없음
   - LLM endpoint가 미등록/미가용
   - LLM 호출 실패
   - 응답에 citation 없음
4. fallback 답변은 `gold_core.recommended_action`을 그대로 사용한다. LLM/RAG 실패와 무관하게 항상 조치가 나온다.
5. secret, token, key 원문 값은 근거에도 답변에도 포함하지 않는다(corpus 계약과 동일).

> LLM endpoint가 아직 없어도 체인은 끝까지 동작한다. 이 경우 모든 답변이 `deterministic_fallback`이 되고, 검색 index/citation 검증은 그대로 수행된다.

## 평가 기준

`14_rag_eval.ipynb`는 `data/dev/rag/rag_eval_set.jsonl`을 채점한다.

| 구분 | 지표 | 방법 | 목표 |
| --- | --- | --- | --- |
| 검색 | retrieval recall@k | `expected_doc_ids` 중 하나라도 top-k에 포함 | 높을수록 좋음 |
| 품질 | citation rate | 응답에 인용된 chunk 존재 비율 | rag 답변은 필수 |
| 품질 | groundedness | Agent Evaluation LLM judge | ≥ 0.9 |
| 품질 | correctness | Agent Evaluation LLM judge (`expected_response` 대비) | eval set 기준 |

retrieval recall / citation rate는 LLM 없이도 측정된다. groundedness / correctness는 LLM endpoint가 있을 때만 채워지고, 없으면 `null`로 저장한다. Eval set의 `expected_facts`는 Agent Evaluation 입력 시 `expected_response`로 변환한다.

eval은 탐지 파이프라인이 읽지 않는 격리 레이어다. `14_rag_eval`은 main pipeline job에 넣지 않고 수동/별도 실행한다.

## 금지 사항

- citation 없이 rag 답변을 신뢰하지 않는다.
- 자동 revoke/delete/suspend를 지시하지 않는다. 담당자 확인 후 수행 절차로 서술한다.
- secret/token/key 원문 값을 저장하거나 LLM에 전달하지 않는다.
- Gold Core `recommended_action`을 대체하는 것이 아니라 근거로 보강한다. 실패 시 항상 fallback 한다.
- corpus 스키마/청킹 기준은 이 문서에서 바꾸지 않는다([rag-evidence.md](./rag-evidence.md) 소관).


## 운영/거버넌스 보강

추가 운영 notebook은 main bronze/silver pipeline과 분리된 `access-drift-rag-ops` job으로 실행한다.

| 범위 | 구현 | notebook / table |
| --- | --- | --- |
| External Model 등록 | `access_drift_llm` -> OpenAI `gpt-4o-mini`, Databricks Secret reference 사용 | `15_register_external_model_endpoint.ipynb` |
| AI Gateway 정책 | rate limit, payload logging, PII/unsafe-content/prompt-injection guardrail 계약을 MLflow에 기록 | `16_configure_ai_gateway_guardrails.ipynb` |
| UC 원문 레이어 | `rag.source_docs` Volume + sanitized source manifest | migration `010`, `rag.source_docs_manifest` |
| 과거 조치 이력 | synthetic remediation history corpus | `rag.remediation_history` |
| 윤리/품질 감사 | citation, fallback, secret leak, destructive action, eval coverage checks | `rag.governance_assessment` |
| 비용 계획 | OpenAI token estimate + Vector Search/Serving endpoint metadata | `rag.cost_estimate` |
| Dashboard 연동 | Risk Card 권장 조치 탭에서 RAG/fallback answer와 reference docs 표시 | `app.risk_card_detail_view`, Streamlit loader |
| Dashboard AI Agent | Risk Card 권장 조치 탭의 대화형 챗봇. 동일한 Vector Search index + FM endpoint를 직접 호출하고 citation 강제/deterministic fallback 규칙을 따른다 | `apps/dashboard/src/rag_agent.py`, `components/risk_text_panels.py` |

`rag_ops_dry_run=true`가 기본값이다. 실제 External Model endpoint 생성과 AI Gateway 적용은 secret scope, preview enablement, workspace 권한 확인 후 `rag_ops_dry_run=false`로 별도 실행한다.
