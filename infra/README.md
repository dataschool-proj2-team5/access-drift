# Infra

## 구조

```
infra/
  azure/          # Azure 리소스 (Bicep)
  databricks/     # Databricks 워크스페이스 오브젝트 (DAB)
```

---

## Azure 리소스

| 리소스 | 이름 | 비고 |
|--------|------|------|
| Resource Group | `dt4_project2_team5` | 기존 리소스 그룹 사용 |
| Databricks Workspace | `acdrift-dbx` | Trial SKU |
| Databricks Access Connector | `acdrift-uc-access` | Unity Catalog ADLS 접근용 Managed Identity |
| ADLS Gen2 | `acdriftadls` | 컨테이너: `lakehouse` 1개, 경로별 레이어 구분 |
| Azure OpenAI | `acdrift-oai` | gpt-4o-mini (GlobalStandard), Korea Central (가용 확인) |

### 배포

**macOS / Linux**
```bash
./infra/azure/deploy.sh
```

**Windows (PowerShell)**
```powershell
.\infra\azure\deploy.ps1
```

### 배포 후

`databricks.yml`의 변수 두 개를 Bicep output 값으로 채웁니다.

```yaml
variables:
  storage_account_name: <Bicep output: storageAccountName>
  openai_endpoint: <Bicep output: openAiEndpoint>
```

Unity Catalog bootstrap에 필요한 Access Connector ID는 Bicep output `unityCatalogAccessConnectorId`로 확인할 수 있습니다.

---

## Databricks 오브젝트

| 오브젝트 | 내용 |
|----------|------|
| Cluster | Single Node, Standard_DS3_v2, 30분 자동 종료 |
| Job | `access-drift-pipeline` (synthetic_data → ingest → silver) |

### Unity Catalog

Unity Catalog 구성 방향과 미결정 사항은 [unity-catalog-policy-draft.md](./unity-catalog-policy-draft.md)를 참고합니다.

Azure 리소스 배포 후 아래 순서로 실행합니다.

**사전 조건**: `az login`으로 Azure CLI 인증 완료 (PAT 불필요)

```bash
az login
./infra/databricks/bootstrap-unity-catalog.sh
```

스크립트는 `az login` 세션을 그대로 사용해 Databricks에 인증합니다. Storage Credential, External Location, Catalog를 idempotent하게 생성합니다.

| UC 오브젝트 | 이름 |
|-------------|------|
| Storage Credential | `access_drift_storage_cred` |
| External Location | `access_drift_lakehouse_ext` |
| Catalog | `access_drift` |

스키마(`bronze`, `silver`, `intermediate`, `gold`, `eval`)는 DDL로 별도 생성합니다.

`eval`은 PoC 정답/평가용 격리 스키마이며 ADLS raw 경로를 추가하지 않고 UC managed table로 시작합니다.

### 배포 전 설정

클러스터를 먼저 생성한 뒤 ID를 레포 루트의 `databricks.yml`에 채웁니다.

```bash
databricks clusters create --json @infra/databricks/resources/clusters.yml
# 출력된 cluster_id를 databricks.yml > targets.dev.variables.cluster_id 에 입력
```

### 배포

`databricks.yml`은 레포 루트에 있습니다. **레포 루트에서 실행합니다.**

```bash
# 레포 루트에서
databricks bundle deploy
databricks bundle run access-drift-pipeline
```

bundle deploy 시 `notebooks/`, `data/poc/landing/raw/`, `data/poc/eval/`이 `/Workspace/Shared/access-drift/files/` 아래에 배포됩니다.

### 셋업 검증

워크스페이스 초대 후 아래 노트북을 실행해 카탈로그·권한·External Location을 확인합니다.

```
infra/databricks/tests/verify-setup.py
```

Databricks 워크스페이스에서 노트북을 import하거나 직접 붙여넣어 셀 단위로 실행합니다.

---

## 주의사항

- Databricks Trial은 14일 제한입니다.
