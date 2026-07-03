# 대시보드 + AI Agent 챗봇 로컬 실행 가이드 (팀원용)

이 문서는 팀원이 각자 PC에서 Access Drift 대시보드를 띄우고, Risk Card "권장 조치" 탭의 **AI Agent 챗봇**(Databricks Vector Search + FM LLM 기반 RAG)을 직접 써 보기 위한 절차다.

## 0. 사전 조건 (한 번만)

- Python 3.10+ (권장 3.11 / 3.12)
- 팀 Databricks 워크스페이스 로그인 계정 (본인 것)
- RAG 결과 테이블이 이미 적재돼 있어야 함
  - `access_drift_dev.rag.recommended_action` (AI Summary용)
  - `access_drift_dev.rag.doc_chunks_index` (Vector Search index, 챗봇 검색용)
  - Vector Search 엔드포인트 `access_drift_vs` 가 `ONLINE` 상태
  - (이미 적재/ONLINE 상태 — 비어 있으면 `notebooks/12_rag_vector_index`, `13_rag_chain` 을 먼저 실행)

## 1. 의존성 설치

```bash
cd apps/dashboard
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Databricks 연결 정보 설정 (secrets)

```bash
cd apps/dashboard/.streamlit
cp secrets.toml.example secrets.toml
```

`secrets.toml` 을 열어 `access_token` 을 **본인 PAT** 로 바꾼다.

- PAT 발급: 워크스페이스 → 프로필 → **Settings → Developer → Access tokens → Generate new token**
- 로컬에 Databricks CLI 가 있으면 `~/.databrickscfg` 의 `token` 값을 재사용해도 됨
- `server_hostname` / `http_path` / `catalog` 등은 템플릿 기본값 그대로 두면 됨 (팀 공용 워크스페이스)

> `secrets.toml` 은 `.gitignore` 에 걸려 있어 커밋되지 않는다. **토큰을 절대 커밋하지 말 것.**
> secrets 를 만들지 않으면 대시보드는 mock 데이터로 자동 fallback 하며, 챗봇은 deterministic fallback 답변만 낸다.

## 3. 실행

```bash
cd apps/dashboard
streamlit run app.py
```

브라우저에서 안내되는 주소(기본 `http://localhost:8501`)로 접속 → 좌측 사이드바 **Risk Card** → **권장 조치** 탭.

- 왼쪽 **AI Summary**: 파이프라인이 미리 만든 RAG 권장 조치 + 참조 문서 (자동 표시, 실시간 호출 없음)
- 오른쪽 **AI Agent**: 질문 입력 후 Send → 근거 검색 + LLM 생성으로 실시간 답변 (citation 포함)

### 데모 추천 질문 (NHI 케이스에서)
- "이 credential을 바로 삭제해도 되나요?"
- "owner 재지정은 누구에게 해야 하나요?"
- "이 조치를 자동으로 실행해도 되나요?"

## 4. 자주 나는 문제

| 증상 | 원인 / 해결 |
| --- | --- |
| 화면에 `Using mock data` | secrets.toml 없음/오타 → `access_token`·`http_path` 확인 |
| 챗봇이 계속 "deterministic fallback" | Vector Search 엔드포인트 `access_drift_vs` 가 OFFLINE 이거나 index 비어 있음 → `12_rag_vector_index` 재실행 |
| 챗봇 응답이 느림(5~10초) | 정상. FM LLM 호출 왕복 시간 (Llama 3.3 70B) |
| `ModuleNotFoundError` | venv 활성화 후 `pip install -r requirements.txt` 재확인 |

## 5. 비용 참고

- LLM 토큰 비용은 매우 작음 (답변 1건 ≈ $0.0005). 챗봇 수백 번 눌러도 $1 미만.
- 상시 과금은 Vector Search 엔드포인트(24/7). 데모 기간 유지 비용이며 개인 PC 실행과 무관하게 워크스페이스에 과금됨.
