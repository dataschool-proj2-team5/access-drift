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
  - Review Status 변경 시 Databricks `risk_action_state`와 `risk_action_event`에 저장합니다.

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
2. Databricks Apps 또는 GitHub Actions 배포 환경에서는 환경 변수 기반 설정을 사용합니다.
3. Databricks를 사용할 수 없으면 `src/mock_data.py`에서 mock row를 생성합니다.

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
actor_id = "streamlit_local_user"      # optional
actor_name = "Streamlit Local User"    # optional
```

토큰, hostname, http path는 코드에 하드코딩하지 않습니다.

## Databricks Apps 배포

Databricks Apps 배포 설정은 대시보드 디렉터리 안에 둡니다.

```text
apps/dashboard/app.yml
apps/dashboard/databricks.yml
```

앱 이름은 `access-drift-dashboard-dev`입니다. 배포 전 로컬에서 아래를 확인합니다.

```bash
python3 -m compileall apps/dashboard/src apps/dashboard/pages apps/dashboard/app.py

cd apps/dashboard
databricks bundle validate -t dev
databricks apps deploy -t dev --auto-approve --skip-validation
```

Databricks Apps runtime은 아래 환경 변수를 읽습니다.

| 환경 변수 | 용도 |
| --- | --- |
| `DATABRICKS_HOST` | Databricks workspace host |
| `DATABRICKS_HTTP_PATH` | SQL Warehouse HTTP path |
| `DATABRICKS_TOKEN` | Databricks SQL Statement API 호출 token |
| `ACCESS_DRIFT_CATALOG` | Dashboard view catalog |
| `ACCESS_DRIFT_GOLD_SCHEMA` | Gold fallback schema |
| `ACCESS_DRIFT_APP_SCHEMA` | App view/action state schema |
| `ACCESS_DRIFT_ACTOR_ID` | Action State/Event 작성 actor id |
| `ACCESS_DRIFT_ACTOR_NAME` | Action State/Event 작성 actor name |

## GitHub Actions 자동 CD

`main` 브랜치의 dashboard 관련 파일이 변경되면 `.github/workflows/dashboard-app-deploy.yml`이 Databricks Apps dev 배포를 자동 실행합니다.

자동 CD에 필요한 GitHub Actions secrets는 저장소 Settings → Secrets and variables → Actions에 등록합니다.

| Secret | 용도 |
| --- | --- |
| `AZURE_CLIENT_ID` | Azure OIDC login client id |
| `AZURE_TENANT_ID` | Azure tenant id |
| `AZURE_SUBSCRIPTION_ID` | Azure subscription id |
| `DATABRICKS_HOST` | Databricks workspace host |
| `DATABRICKS_HTTP_PATH` | SQL Warehouse HTTP path |
| `DATABRICKS_TOKEN` | Dashboard runtime SQL Statement API token |
| `ACCESS_DRIFT_CATALOG` | 예: `access_drift_dev` |
| `ACCESS_DRIFT_GOLD_SCHEMA` | 예: `gold` |
| `ACCESS_DRIFT_APP_SCHEMA` | 예: `app` |
| `ACCESS_DRIFT_ACTOR_ID` | 예: `databricks_apps_user` |
| `ACCESS_DRIFT_ACTOR_NAME` | 예: `Databricks Apps User` |

secret 값은 PR, 로그, 문서에 직접 남기지 않습니다.

배포 후 Databricks Apps URL에서 Overview와 Risk Card가 열리는지 확인합니다. Review Status를 변경했다면 아래 SQL로 저장 상태를 확인합니다.

```sql
SELECT risk_case_key, status, updated_by, updated_at
FROM access_drift_dev.app.risk_action_state
ORDER BY updated_at DESC;

SELECT event_id, risk_case_key, event_type, previous_status, new_status, actor_id, actor_name, event_at
FROM access_drift_dev.app.risk_action_event
ORDER BY event_at DESC;
```

## 표시용 Case ID

Databricks의 원본 `risk_case_key`는 내부 조회, navigation, session key로만 사용합니다. 화면에는 원본 key를 직접 노출하지 않습니다.

화면 표시용 `display_case_id`는 `risk_case_key` 원본 문자열의 SHA1 해시 앞 6자리를 사용해 생성합니다.


## 코드 구조

```text
apps/dashboard/
├─ app.py
├─ app.yml
├─ databricks.yml
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
│  ├─ action_state.py
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
- Databricks write-back 로직은 `src/action_state.py`에 유지합니다.
- 내부 컬럼 계약은 `src/schema.py`와 `data/README.md`를 함께 갱신합니다.
- Databricks Apps 배포 설정은 `app.yml`, `databricks.yml`, GitHub Actions workflow를 함께 확인합니다.
- ticket 발급, RAG/AI Agent 연동은 아직 구현하지 않습니다.

## 현재 제한 사항

- Databricks secrets가 없거나 write에 실패하면 Review Status 변경은 Streamlit session 안에서만 반영됩니다.
- Review Status 외 note 입력과 action event note 편집 UI는 구현하지 않았습니다.
- AI Agent, RAG, Ticket API는 placeholder입니다.

## Review Status 저장 확인

Databricks secrets가 있는 상태에서 Risk Card의 Review Status를 변경하면 아래 두 작업을 같은 사용자 조작으로 수행합니다.

```text
app.risk_action_state upsert
  + app.risk_action_event append
```

저장 확인 예시:

```sql
SELECT risk_case_key, status, updated_by, updated_at
FROM access_drift_dev.app.risk_action_state
ORDER BY updated_at DESC;

SELECT event_id, risk_case_key, event_type, previous_status, new_status, actor_id, actor_name, event_at
FROM access_drift_dev.app.risk_action_event
ORDER BY event_at DESC;
```
