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
| ADLS Gen2 | `acdriftadls` | 컨테이너: landing / bronze / silver / intermediate / gold |
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

Azure 리소스 배포 후 Databricks CLI 인증을 완료한 뒤 아래 스크립트로 PoC용 catalog, schema, storage credential, external location을 생성합니다.

```bash
./infra/databricks/bootstrap-unity-catalog.sh
```

### 배포 전 설정

클러스터를 먼저 생성한 뒤 ID를 `databricks.yml`에 채웁니다.

```bash
databricks clusters create --json @infra/databricks/resources/clusters.yml
# 출력된 cluster_id를 databricks.yml의 cluster_id 변수에 입력
```

### 배포

```bash
databricks bundle deploy
databricks bundle run access-drift-pipeline
```

### 셋업 검증

워크스페이스 초대 후 아래 노트북을 실행해 카탈로그·권한·External Location을 확인합니다.

```
infra/databricks/tests/verify-setup.py
```

Databricks 워크스페이스에서 노트북을 import하거나 직접 붙여넣어 셀 단위로 실행합니다.

---

## 주의사항

- Databricks Trial은 14일 제한입니다.
