# Access Drift Dashboard

Access Drift 대시보드는 Databricks app view를 기반으로 access drift risk를 조회하고, 검토 우선순위와 Risk Card 상세 화면을 제공하는 Streamlit 앱입니다.

현재 대시보드는 실제 Databricks 데이터 연동을 우선 사용하며, 로컬 실행 환경에 Databricks secrets가 없거나 조회에 실패하면 mock data로 자동 fallback합니다.

## 주요 화면

- **Overview**
  - Actions 요약 카드
  - 위험도별 Issues 분포
  - Top Drifts
  - 위험도 기준 Priority Review Top 3
- **Asset List**
  - Priority Review의 확장 목록
  - Critical, High, Medium 항목 중심의 테이블형 목록
  - 표시용 Case ID와 Risk Card 이동 액션 제공
- **Risk Card**
  - 선택한 case의 상세 분석 화면
  - Access Path, Risk Summary, Risk Factors
  - 권장 조치, 참고 문서, 실행 단계, AI Agent placeholder
  - Review Status는 Streamlit session 안에서만 변경됩니다.

## 로컬 실행

```powershell
cd apps/dashboard
pip install -r requirements.txt
streamlit run app.py
```

브라우저에서 Streamlit이 안내하는 로컬 주소로 접속합니다. 기본 포트는 보통 `8501`입니다.

## 데이터 로딩 우선순위

대시보드는 아래 순서로 데이터를 읽습니다.

1. `.streamlit/secrets.toml`에 Databricks 설정이 있으면 Databricks app schema의 dashboard view를 조회합니다.
2. Databricks를 사용할 수 없으면 `src/mock_data.py`에서 mock row를 생성합니다.

mock row를 사용하는 경우 화면에 `Using mock data` 안내가 표시됩니다.

## Databricks 소스

대시보드 화면은 `gold_core`를 직접 화면에 붙이지 않고, app schema의 dashboard용 view를 우선 사용합니다.

- `risk_case_list_view`
- `risk_card_detail_view`
- `risk_access_path_view`
- `risk_action_state`

`gold_core`는 app view가 비어 있을 때 fallback 또는 검증용 원천으로만 사용합니다.

## 로컬 secrets

Databricks 접속 정보는 로컬 Streamlit secrets에만 둡니다.

```text
apps/dashboard/.streamlit/secrets.toml
```

이 파일은 git에 포함하지 않습니다. `.gitignore`에서 `**/.streamlit/secrets.toml`을 무시하도록 설정되어 있습니다.

필요한 secrets 구조는 다음과 같습니다.

```toml
[databricks]
server_hostname = "..."
http_path = "..."
access_token = "..."
catalog = "access_drift_dev"
gold_schema = "gold"
app_schema = "app"
```

토큰, hostname, http path는 코드에 하드코딩하지 않습니다.

## 표시용 Case ID

Databricks의 원본 `risk_case_key`는 내부 조회, navigation, session key로만 사용합니다. 화면에는 원본 key를 직접 노출하지 않습니다.

화면 표시용 `display_case_id`는 `risk_case_key` 원본 문자열의 SHA1 해시 앞 6자리를 사용해 생성합니다.


## 코드 구조

```text
apps/dashboard/
├─ app.py
├─ pages/
│  ├─ 01_Overview.py
│  ├─ 02_Asset_List.py
│  └─ 03_Risk_Card.py
├─ components/
│  ├─ asset_table_fit.py
│  ├─ cards.py
│  ├─ charts.py
│  ├─ risk_text_panels.py
│  └─ styles.py
├─ src/
│  ├─ data_loader.py
│  ├─ mock_data.py
│  ├─ schema.py
│  └─ session_state.py
├─ assets/
│  ├─ badges/
│  └─ icons/
└─ data/
   └─ README.md
```

## 개발 시 수정 기준

- 화면 컴포넌트는 `components/`에 둡니다.
- 페이지별 조합은 `pages/`에서 처리합니다.
- 소스별 컬럼 매핑, display normalization, fallback 로직은 `src/data_loader.py`에 유지합니다.
- 내부 컬럼 계약은 `src/schema.py`와 `data/README.md`를 함께 갱신합니다.
- 실제 write-back, ticket 발급, RAG/AI Agent 연동은 아직 구현하지 않습니다.

## 현재 제한 사항

- Review Status 변경은 현재 Streamlit session 안에서만 반영됩니다.
- Databricks `risk_action_state` write-back은 구현하지 않았습니다.
- `risk_action_event` insert는 구현하지 않았습니다.
- AI Agent, RAG, Ticket API는 placeholder입니다.
