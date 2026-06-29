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
| Job | `access-drift-pipeline` (migration → synthetic_data → ingest → silver → intermediate → gold, eval은 silver 이후 검증용 task로 분리) |

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

### PoC / dev target 구분

`databricks.yml`은 PoC 재현용 `poc` target과 본개발용 `dev` target을 정의합니다. `demo.md`의 대표 데모 케이스는 별도 Databricks target이 아니라, 본개발용 `dev` 합성 데이터 안에 고정 시나리오 또는 식별자로 포함해 관리합니다.

| target | catalog | ADLS raw 경로 | 용도 | 데이터 성격 |
|--------|---------|--------------|------|------------|
| `poc` | `access_drift` | `lakehouse/raw/poc/` | PoC 재현·검증 | PoC seed 데이터(10건 × 6종), PoC 완료 기준 재확인 |
| `dev` | `access_drift_dev` | `lakehouse/raw/dev/` | 본개발·탐색·대표 데모 케이스 검증 | 확장 합성 데이터, 대표 리스크 케이스, 스키마 실험 |

**중요**: `poc`와 `dev`는 catalog와 raw 경로가 분리된 실행 환경입니다. 데모 케이스는 환경이 아니라 데이터 케이스이므로, 발표에서 보여줄 대표 리스크는 `access_drift_dev`의 개발용 합성 데이터 안에서 `scenario_id`, `case_id` 등으로 식별할 수 있게 관리합니다.

#### PoC fixture vs S1 개발 데이터

| 구분 | 위치 | 설명 |
|------|------|------|
| PoC fixture | `data/poc/landing/raw/` (레포) | 10건 × 6종 seed. bundle deploy 시 워크스페이스에 배포 |
| poc raw | ADLS `lakehouse/raw/poc/...` | `poc` target 실행 시 PoC seed가 적재되는 입력 경로 |
| dev raw | ADLS `lakehouse/raw/dev/...` | `dev` target 실행 시 S1 개발 데이터와 대표 데모 케이스가 적재되는 입력 경로 |
| 본개발 원본 | ADLS `lakehouse/raw/<source>/...` | 실제 수집기가 쓰는 경로. 레포에 포함되지 않음 |

현재 `data/poc/landing/raw/`는 PoC seed 경로 이름을 유지합니다. `poc` target은 이 seed를 PoC 재현용 raw 경로로 적재하고, `dev` target은 S1 확장 합성 데이터 생성/적재 기준에 맞춰 dev raw 경로를 사용합니다. 이후 `02_ingest.ipynb`가 target별 raw 경로를 읽어 Bronze로 적재합니다.

#### `access_drift` catalog (PoC)

PoC 재현 또는 과거 완료 기준 확인이 필요할 때 사용합니다.

```bash
az login
CATALOG_NAME=access_drift ./infra/databricks/bootstrap-unity-catalog.sh
```

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

`GRANT_PRINCIPAL`은 Unity Catalog grants API가 해석할 수 있는 principal이어야 합니다. `databricks groups list`에서 workspace group이 조회되더라도 workspace-local group이면 UC grant 대상 principal로 해석되지 않아 `Could not find principal` 오류가 발생할 수 있습니다.

이 경우 기존 workspace-local group은 이름을 바꾸거나 삭제하고, Databricks Account Console에서 같은 이름의 account-level group을 만든 뒤 workspace에 assign합니다. 이후 account-level group 이름으로 다시 grant를 적용합니다. 급한 검증에서는 개별 사용자 또는 service principal을 `GRANT_PRINCIPAL`로 사용할 수 있지만, workspace 전체 `users` 그룹 grant는 권한 범위가 넓어 사용하지 않습니다.

bootstrap 스크립트는 지정된 principal에 다음 권한을 부여합니다.

| 범위 | 권한 |
|------|------|
| Catalog | `USE_CATALOG` |
| Schema | `USE_SCHEMA`, `CREATE_TABLE`, `SELECT`, `MODIFY` |

Account-level group 구성이 바로 어렵다면, dev catalog 검증을 위해 개별 사용자 이메일에 권한을 부여할 수 있습니다.

```bash
PRINCIPALS="4dt002@msacademy.msai.kr 4dt014@msacademy.msai.kr" \
./infra/databricks/grant-dev-user-permissions.sh
```

이 스크립트는 기본적으로 `access_drift_dev` catalog, 하위 schema, `access_drift_lakehouse_ext` external location에 대해 Unity Catalog `ALL_PRIVILEGES`를 부여합니다. External Location은 raw 파일 읽기/쓰기와 외부 테이블 생성에 필요한 권한을 포함합니다.

필요하면 권한 범위를 좁혀 실행할 수 있습니다.

```bash
PRINCIPALS="4dt002@msacademy.msai.kr" \
EXTERNAL_LOCATION_PRIVILEGES="READ_FILES WRITE_FILES" \
./infra/databricks/grant-dev-user-permissions.sh
```

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
SHOW GRANTS ON EXTERNAL LOCATION access_drift_lakehouse_ext;
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
# poc target (PoC 재현·검증용 — access_drift catalog)
databricks bundle deploy -t poc
databricks bundle run access-drift-pipeline -t poc

# dev target (S1 본개발·대표 데모 케이스 검증용 — access_drift_dev catalog, 기본값)
# data/dev/landing/raw 및 data/dev/eval seed가 준비된 뒤 실행합니다.
databricks bundle deploy -t dev
databricks bundle run access-drift-pipeline -t dev

# -t 생략 시 dev가 기본 target으로 적용됩니다
databricks bundle deploy
databricks bundle run access-drift-pipeline
```

bundle deploy 시 `notebooks/`, `data/poc/landing/raw/`, `data/poc/eval/`, `data/dev/`가 `/Workspace/Shared/access-drift/files/` 아래에 배포됩니다.

#### Landing/Bronze/Silver 부분 실행

DE가 Landing/Bronze/Silver 적재만 확인할 때는 Intermediate/Gold task를 제외하고 실행합니다.

```bash
databricks bundle validate -t dev
databricks bundle deploy -t dev
databricks bundle run -t dev access-drift-pipeline \
  --only migration_task,synthetic_data_task,ingest_task,silver_task,eval_seed_task
```

`data/dev/landing/raw/`와 `data/dev/eval/ground_truth_case.jsonl`이 아직 준비되지 않은 동안에는 PoC-shaped seed를 dev catalog/raw 경로에 적재해 파이프라인 smoke test만 수행할 수 있습니다.

```bash
databricks bundle deploy -t dev \
  --var="seed_data_path=data/poc/landing/raw" \
  --var="eval_seed_path=data/poc/eval/ground_truth_case.jsonl"

databricks bundle run -t dev access-drift-pipeline \
  --only migration_task,synthetic_data_task,ingest_task,silver_task,eval_seed_task

# smoke test 후 dev 기본 seed 경로로 job parameter를 되돌립니다.
databricks bundle deploy -t dev
```

이 override는 `access_drift_dev`와 `lakehouse/raw/dev/`에 PoC-shaped seed를 적재하는 검증용 실행이다. 대표 dev 데이터 검증 완료를 의미하지 않는다.

실행 후 row count, required key null, enum, relationship, 참조 무결성, eval 매칭은 아래 SQL로 확인합니다.

```text
sql/databricks/queries/de_lbs_validation.sql
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
