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
| Job | `access-drift-pipeline` (migration → synthetic_data → ingest → silver → intermediate → gold, eval은 silver 이후 독립 실행) |

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
| Catalog | `access_drift`, `access_drift_dev` |

스키마(`bronze`, `silver`, `intermediate`, `gold`, `eval`)는 bootstrap 스크립트에서 먼저 생성하고, DDL은 테이블 정의를 적용합니다.

`eval`은 PoC 정답/평가용 격리 스키마이며 ADLS raw 경로를 추가하지 않고 UC managed table로 시작합니다.

### demo / dev target 구분

`databricks.yml`은 `demo`와 `dev` 두 target을 정의합니다. 목적에 따라 `-t` 플래그로 target을 선택합니다.

| target | catalog | ADLS raw 경로 | 용도 | 데이터 성격 |
|--------|---------|--------------|------|------------|
| `demo` | `access_drift` | `lakehouse/raw/demo/` | 발표·검증용 고정 fixture | PoC seed 데이터(10건 × 6종), 재실행해도 같은 결과 |
| `dev` | `access_drift_dev` | `lakehouse/raw/dev/` | 본개발·탐색용 | 파이프라인 변경 검증, seed 재생성, 스키마 실험 |

**중요**: `demo` target을 실행하면 `access_drift` catalog와 `lakehouse/raw/demo/` 입력 데이터를 덮어씁니다. 발표 직전에는 `dev` target으로만 작업하고, `demo`는 fixture 재적재 시에만 사용합니다.

#### PoC fixture vs 본개발 데이터

| 구분 | 위치 | 설명 |
|------|------|------|
| PoC fixture | `data/poc/landing/raw/` (레포) | 10건 × 6종 seed. bundle deploy 시 워크스페이스에 배포 |
| demo raw | ADLS `lakehouse/raw/demo/...` | `demo` target 실행 시 fixture가 복사되는 발표·검증용 입력 경로 |
| dev raw | ADLS `lakehouse/raw/dev/...` | `dev` target 실행 시 fixture가 복사되는 개발·탐색용 입력 경로 |
| 본개발 원본 | ADLS `lakehouse/raw/<source>/...` | 실제 수집기가 쓰는 경로. 레포에 포함되지 않음 |

fixture는 `01_synthetic_data.py`가 target별 ADLS raw 경로로 복사하며, 이후 `02_ingest.py`가 같은 raw 경로를 읽어 Bronze로 적재합니다.

#### `access_drift` catalog (demo)

- bootstrap 스크립트로 이미 생성된 catalog입니다.
- PoC fixture 데이터가 적재된 상태로 유지합니다.
- 발표 영상 촬영 전 `demo` target으로 한 번 실행해 fixture를 최신화합니다.

#### `access_drift_dev` catalog (dev)

처음 사용 전 별도로 생성합니다.

```bash
az login
CATALOG_NAME=access_drift_dev ./infra/databricks/bootstrap-unity-catalog.sh
```

팀 또는 실행 주체에 dev schema 작업 권한을 같이 부여하려면 `GRANT_PRINCIPAL`을 지정합니다.

```bash
CATALOG_NAME=access_drift_dev \
GRANT_PRINCIPAL="access-drift-team" \
./infra/databricks/bootstrap-unity-catalog.sh
```

`GRANT_PRINCIPAL`은 Unity Catalog grants API가 해석할 수 있는 principal이어야 합니다. Workspace-local group이 조회되더라도 UC grant 대상이 아니면 권한 부여가 실패할 수 있으므로, 실패 시 account-level group 또는 사용자 principal 기준으로 다시 확인합니다.

스크립트는 지정된 principal에 다음 권한을 부여합니다.

| 범위 | 권한 |
|------|------|
| Catalog | `USE_CATALOG` |
| Schema | `USE_SCHEMA`, `CREATE_TABLE`, `SELECT`, `MODIFY` |

적용 후 아래 항목을 확인합니다.

```sql
SHOW CATALOGS LIKE 'access_drift_dev';
SHOW SCHEMAS IN access_drift_dev;
SHOW GRANTS ON CATALOG access_drift_dev;
SHOW GRANTS ON SCHEMA access_drift_dev.bronze;
SHOW GRANTS ON SCHEMA access_drift_dev.silver;
SHOW GRANTS ON SCHEMA access_drift_dev.intermediate;
SHOW GRANTS ON SCHEMA access_drift_dev.gold;
SHOW GRANTS ON SCHEMA access_drift_dev.eval;
```

### 배포 전 설정

클러스터를 먼저 생성한 뒤 ID를 레포 루트의 `databricks.yml`에 채웁니다.

```bash
databricks clusters create --json @infra/databricks/resources/clusters.yml
# 출력된 cluster_id를 databricks.yml > targets.dev.variables.cluster_id 에 입력
```

### 배포 및 실행

`databricks.yml`은 레포 루트에 있습니다. **레포 루트에서 실행합니다.**

```bash
# demo target (발표·검증용 — access_drift catalog)
databricks bundle deploy -t demo
databricks bundle run access-drift-pipeline -t demo

# dev target (본개발용 — access_drift_dev catalog, 기본값)
databricks bundle deploy -t dev
databricks bundle run access-drift-pipeline -t dev

# -t 생략 시 dev가 기본 target으로 적용됩니다
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
