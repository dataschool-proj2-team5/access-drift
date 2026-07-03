# ADR-0002: RAG 체인 모델 선택과 deterministic fallback

- **Status**: Proposed
- **Date**: 2026-07-02
- **Deciders**: DS/DE team (KimDana, 정 해원, 주재륜)

## Context

DE가 근거 corpus `rag.doc_chunks`(마이그레이션 008, notebook 10)와 계약([rag-evidence.md](../contracts/rag-evidence.md))을 완료했다. DS는 그 위에서 검색 → 생성 → 평가 체인을 붙여야 한다.

기획서(Databricks 기반 RAG)는 임베딩 `databricks-gte-large-en`, 검색 Vector Search(Delta Sync), 생성 LLM은 FM API 내장(Llama/DBRX) 또는 External Model(Claude/OpenAI) 중 선택으로 열어 두었다. 팀 논의에서 다음이 확정됐다.

- Azure OpenAI(Foundry) 리소스는 제거한다.
- 생성 LLM은 비용 때문에 Databricks External Model로 OpenAI `gpt-4o-mini`를 쓴다.
- External Model endpoint 등록(키/프록시)은 이번 구현 범위에서 제외하고, 체인은 endpoint 이름만 파라미터로 받는다.
- Gold Core는 LLM/RAG 실패와 무관하게 항상 조치를 낸다(ADR-0001 원칙).

## Decision

1. **임베딩**: FM API `databricks-gte-large-en`. Vector Search Delta Sync index(`rag.doc_chunks_index`)의 `embedding_model_endpoint_name`으로 사용한다.
2. **검색**: Databricks Vector Search STANDARD endpoint + Delta Sync(TRIGGERED) index. `chunk_id`가 primary key, `chunk_text`가 embedding source.
3. **생성 LLM**: Databricks External Model endpoint(기본 이름 `access_drift_llm`, 대상 OpenAI `gpt-4o-mini`). endpoint 이름은 notebook/`databricks.yml` 위젯 변수로 주입한다. **endpoint 등록 자체는 이 PR 범위 밖**이다.
4. **deterministic fallback**: 아래는 모두 `gold_core.recommended_action`으로 fallback 한다.
   - 검색 결과 없음 / LLM endpoint 미등록·미가용 / LLM 호출 실패 / 응답에 citation 없음
5. **citation 강제**: rag 답변은 인용된 `[chunk_id]`가 있어야 하며, 없으면 fallback 처리한다. `13_rag_chain`의 smoke test가 이를 검증한다.
6. **평가**: retrieval recall/citation rate는 LLM 없이 측정. groundedness/correctness는 Agent Evaluation(`mlflow.evaluate`, `databricks-agent`)로 endpoint가 있을 때만 채우고 없으면 `null`.


## External Model endpoint 등록 방법 (후속 작업)

이번 PR은 endpoint 이름만 사용하고 등록은 수행하지 않는다. 후속 작업에서 Databricks workspace secret에 OpenAI API key를 저장한 뒤 아래 형태로 `access_drift_llm` Serving endpoint를 만든다.

```python
import mlflow.deployments

client = mlflow.deployments.get_deploy_client("databricks")
client.create_endpoint(
    name="access_drift_llm",
    config={
        "served_entities": [{
            "name": "openai-gpt-4o-mini",
            "external_model": {
                "name": "gpt-4o-mini",
                "provider": "openai",
                "task": "llm/v1/chat",
                "openai_config": {
                    "openai_api_key": "{{secrets/access-drift-openai/api-key}}"
                },
            },
        }]
    },
)
```

API key 원문은 코드, notebook, 문서에 남기지 않는다. endpoint 이름을 바꾸는 경우 `rag_llm_endpoint` bundle 변수만 변경한다.

## Consequences

- **장점**: LLM endpoint가 없어도 전체 체인(index → 검색 → fallback 생성 → 평가)이 끝까지 돌고 데모/검증이 가능하다. endpoint 등록만 되면 코드 변경 없이 rag 생성이 켜진다. 비용은 `gpt-4o-mini` + Vector Search + gte 임베딩으로 제한된다.
- **단점**: endpoint 미등록 상태에서는 모든 답변이 deterministic fallback이라 groundedness/correctness가 비어 실제 생성 품질을 검증하지 못한다. 이 상태는 `rag.recommended_action.answer_source`와 eval의 `llm_available`로 드러난다.
- **후속**: External Model endpoint(`access_drift_llm`) 등록, AI Gateway 가드레일(PII/toxicity, rate limit), Model Serving 배포, 대시보드 "권장 조치" 탭 연동은 별도 범위다. SaaS/HI(A-S1/A-S2) 확장은 corpus에 `hi` chunk가 생기고 별도 drift_type/eval 기준이 정해진 뒤 붙인다.


## Implementation update (2026-07-02)

The repository now includes operational notebooks for endpoint registration, AI Gateway policy logging, UC source document manifest seeding, synthetic remediation history, governance assessment, cost estimate, and dashboard read-view integration.

Endpoint and AI Gateway notebooks are dry-run by default because they require workspace admin/serving permissions and a Databricks secret that stores the OpenAI API key. This keeps CI/dev execution deterministic while making the production activation path executable.

## Decision update (2026-07-02): 기본 생성 LLM을 Databricks FM API로 전환

External Model(`access_drift_llm` → OpenAI `gpt-4o-mini`) 경로는 endpoint 생성과 OpenAI 도달까지 검증했으나, 연결된 OpenAI 계정이 Free tier(credit $0.00)라 `429 insufficient_quota`로 생성이 차단됐다. 학교 팀 프로젝트 원칙상 개인 결제는 하지 않는다.

이에 따라 **기본 생성 LLM을 Databricks Foundation Model API pay-per-token endpoint `databricks-meta-llama-3-3-70b-instruct`로 전환**한다.

- FM API는 workspace 내장 endpoint라 외부 API key/개인 결제 없이 동작하고, 비용은 workspace(팀/학교 리소스) 과금으로 일원화된다. 기획서가 열어 둔 "FM API 내장 모델(Llama)" 옵션에 해당한다.
- `13_rag_chain`/`14_rag_eval`/`19_rag_llm_serving_smoke` 위젯과 `rag_llm_endpoint` bundle 변수 기본값을 FM endpoint로 변경했다. citation 강제·deterministic fallback 규칙은 동일하게 적용된다.
- External Model 경로는 제거하지 않는다. `rag_external_llm_endpoint` bundle 변수(기본 `access_drift_llm`)와 rag-ops job(15/16 notebook)이 계속 관리하며, 팀/학교 공용 OpenAI/Azure OpenAI key 확보 시 `rag_llm_endpoint` 값만 바꾸면 코드 변경 없이 전환된다.
- serving invocation URL은 regional/control-plane host(`ctx.apiUrl`)에서 404가 나는 문제가 있어 workspace URL(`spark.databricks.workspaceUrl`) 기준으로 수정했다.
- 대시보드 "권장 조치" 탭의 AI Agent 패널은 동일한 Vector Search index + FM endpoint를 직접 호출하는 대화형 RAG 챗봇(`apps/dashboard/src/rag_agent.py`)으로 구현했다. 검색 실패/LLM 실패/citation 없음은 전부 deterministic fallback으로 처리한다.
