from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field

import pandas as pd

from src.data_loader import DatabricksConfig, _load_databricks_config

# Databricks FM API pay-per-token endpoint. 외부 OpenAI key/결제 없이 workspace 안에서 동작한다.
DEFAULT_LLM_ENDPOINT = "databricks-meta-llama-3-3-70b-instruct"
DEFAULT_VS_INDEX_TABLE = "doc_chunks_index"
DEFAULT_TOP_K = 4
LLM_TIMEOUT_SECONDS = 60

SYSTEM_PROMPT = (
    "너는 Access Drift 대시보드의 보안 조치 보조자다. "
    "아래에 제공된 근거 문서와 Risk Case 정보에 있는 내용만으로 답한다. "
    "항상 한국어 존댓말로만 답하세요. "
    "문장은 '-합니다', '-하세요', '-됩니다' 체로 작성하세요. "
    "'-해야 한다', '-같다', '-하라', 반말/해라체를 사용하지 마세요. "
    "답변은 3~5개의 짧은 bullet로 작성하세요. "
    "각 bullet 끝에는 반드시 근거가 된 [chunk_id] citation을 붙이세요. "
    "제공된 근거로 답할 수 없으면 새로 지어내지 말고 '근거 부족'이라고 답하세요. "
    "권한을 자동으로 회수하거나 삭제하라고 지시하지 말고, 담당자 확인 후 수행하는 절차로 서술하세요. "
    "secret, token, key 원문 값은 답변에 포함하지 마세요."
)


@dataclass(frozen=True)
class AgentAnswer:
    text: str
    source: str  # "rag" | "deterministic_fallback"
    citations: list[dict] = field(default_factory=list)
    llm_endpoint: str = "none"


def is_agent_available() -> bool:
    return _load_databricks_config() is not None


def answer_question(case: pd.Series, question: str, history: list[dict] | None = None) -> AgentAnswer:
    """Risk Card 1건 컨텍스트에서 사용자 질문에 근거 기반으로 답한다.

    검색 실패 / LLM 실패 / citation 없음은 전부 deterministic fallback으로 처리해
    대시보드가 절대 빈 답을 내지 않게 한다 (13_rag_chain과 동일한 규칙).
    """
    config = _load_databricks_config()
    if config is None:
        return _fallback(case, "Databricks 연결이 구성되지 않아 deterministic fallback으로 답변합니다.")

    try:
        docs = _retrieve(config, case, question)
    except Exception:  # noqa: BLE001
        docs = []
    if not docs:
        return _fallback(case, "관련 근거 문서를 찾지 못해 deterministic fallback으로 답변합니다.")

    llm_endpoint = _llm_endpoint_name()
    try:
        answer = _generate(config, llm_endpoint, case, question, docs, history or [])
    except Exception:  # noqa: BLE001
        return _fallback(case, "LLM 호출에 실패해 deterministic fallback으로 답변합니다.")

    cited = [d for d in docs if f"[{d['chunk_id']}]" in answer]
    if not cited:
        # citation 강제: 근거를 인용하지 않은 응답은 신뢰하지 않는다.
        return _fallback(case, "LLM 응답에 citation이 없어 deterministic fallback으로 답변합니다.")

    return AgentAnswer(
        text=answer,
        source="rag",
        citations=[{"chunk_id": d["chunk_id"], "title": d["source_title"], "uri": d["source_uri"]} for d in cited],
        llm_endpoint=llm_endpoint,
    )


def _fallback(case: pd.Series, reason: str) -> AgentAnswer:
    recommended = str(case.get("recommended_action", "") or "").strip()
    text = f"{reason}\n\n권장 조치: {recommended}" if recommended else reason
    return AgentAnswer(text=text, source="deterministic_fallback")


def _retrieve(config: DatabricksConfig, case: pd.Series, question: str) -> list[dict]:
    index_name = f"{config.catalog}.rag.{DEFAULT_VS_INDEX_TABLE}"
    columns = ["chunk_id", "doc_id", "doc_type", "source_title", "source_uri", "chunk_text"]
    query_text = f"{_case_summary(case)} 질문: {question}"
    # 필터가 너무 좁아 0건이면 principal_kind만으로 한 번 완화해 재시도한다.
    # 잘못된 corpus 인용은 citation 강제 + 근거 제한 프롬프트가 막는다.
    full_filters = _retrieval_filters(case)
    relaxed_filters = {"principal_kind": full_filters["principal_kind"]}
    for filters in (full_filters, relaxed_filters):
        payload = {
            "query_text": query_text,
            "columns": columns,
            "num_results": DEFAULT_TOP_K,
            "filters_json": json.dumps(filters),
        }
        result = _post_json(
            config,
            f"{config.host_url}/api/2.0/vector-search/indexes/{index_name}/query",
            payload,
        )
        rows = result.get("result", {}).get("data_array") or []
        if rows:
            return [dict(zip(columns, row)) for row in rows]
    return []


def _generate(
    config: DatabricksConfig,
    llm_endpoint: str,
    case: pd.Series,
    question: str,
    docs: list[dict],
    history: list[dict],
) -> str:
    context = "\n\n".join(f"[{d['chunk_id']}] {d['chunk_text']}" for d in docs)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for turn in history[-6:]:
        role = turn.get("role")
        content = str(turn.get("content", ""))
        if role in {"user", "assistant"} and content:
            messages.append({"role": role, "content": content})
    messages.append(
        {
            "role": "user",
            "content": (
                f"근거:\n{context}\n\nRisk Case:\n{_case_summary(case)}\n\n질문:\n{question}"
            ),
        }
    )
    result = _post_json(
        config,
        f"{config.host_url}/serving-endpoints/{llm_endpoint}/invocations",
        {"messages": messages, "temperature": 0.0, "max_tokens": 512},
        timeout=LLM_TIMEOUT_SECONDS,
    )
    return str(result["choices"][0]["message"]["content"]).strip()


def _case_summary(case: pd.Series) -> str:
    parts = [
        f"drift_type={_normalize_token(case.get('drift_type'))}",
        f"asset={case.get('asset_full_name') or case.get('asset_name')}",
        f"sensitivity={case.get('asset_sensitivity')}",
        f"identity={case.get('identity_name')} ({case.get('identity_type')})",
        f"owner={case.get('owner_name')} ({case.get('related_person_status') or case.get('owner_status')})",
        f"credential={case.get('credential_type')} {case.get('credential_status')}",
    ]
    return ", ".join(str(part) for part in parts if part and "None" not in str(part))


def _retrieval_filters(case: pd.Series) -> dict:
    filters: dict[str, str] = {}
    drift_type = _raw_drift_type(case)
    if drift_type:
        filters["drift_type"] = drift_type
    identity_type = str(case.get("identity_type", "") or "").strip().lower()
    filters["principal_kind"] = "hi" if identity_type == "hi" else "nhi"
    return filters


def _raw_drift_type(case: pd.Series) -> str:
    # 대시보드 drift_type은 표시용 라벨(NHI Credential Drift)이라 corpus의 raw 값과 다르다.
    # risk_case_key 마지막 세그먼트(...:nhi_residual_access)가 raw drift_type이다.
    key = str(case.get("risk_case_key", "") or "")
    if ":" in key:
        candidate = key.rsplit(":", 1)[-1].strip()
        if candidate and "_" in candidate:
            return candidate.lower()
    return _normalize_token(case.get("drift_type"))


def _normalize_token(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    return re.sub(r"[\s\-]+", "_", text).lower()


def _llm_endpoint_name() -> str:
    secrets = _agent_secrets()
    return str(secrets.get("llm_endpoint") or DEFAULT_LLM_ENDPOINT)


def _agent_secrets() -> dict:
    try:
        import streamlit as st

        if "databricks" in st.secrets:
            return dict(st.secrets["databricks"])
    except Exception:  # noqa: BLE001
        pass
    return {}


def _post_json(config: DatabricksConfig, url: str, payload: dict, timeout: int = 30) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {config.access_token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))
