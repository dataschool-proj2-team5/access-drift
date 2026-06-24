# Unity Catalog Policy Draft

이 문서는 Access Drift PoC에서 Unity Catalog를 어떻게 구성할지 정리한 초안입니다.
아직 최종 ADR이 아니며, 팀 합의 후 확정 결정은 `docs/adr/`에 별도로 기록합니다.

## 목적

Databricks에서 ADLS Gen2 데이터를 사용할 때 사람 계정의 자격증명, Storage Key, SAS Token을 코드에 넣지 않고 Unity Catalog를 통해 데이터 접근 위치와 권한을 관리합니다.

## PoC 적용 범위

### ADLS 구조

| 항목 | 값 |
| --- | --- |
| 컨테이너 | `lakehouse` 1개 |
| 경로 | `raw/`, `bronze/`, `silver/`, `intermediate/`, `gold/`, `checkpoint/` |

### Unity Catalog 구조

| 항목 | 값 |
| --- | --- |
| Catalog | `access_drift` |
| Schemas | `bronze`, `silver`, `intermediate`, `gold`, `eval` |
| External Location | `access_drift_lakehouse_ext` 1개 |
| Access Connector | 사용 (Managed Identity 기반) |

스키마 생성은 `sql/databricks/migrations/`의 DDL로 별도 실행합니다.

### 후속 적용 (PoC 범위 외)

- 팀 그룹별 권한 분리
- Column Masking
- Service Principal 기반 Job 실행 정책

## 구성 개념

```text
Azure
  acdriftadls
    lakehouse/
      raw/
      bronze/
      silver/
      intermediate/
      gold/
      checkpoint/

Azure
  Databricks Access Connector
    Managed Identity

Azure RBAC
  Managed Identity -> acdriftadls: Storage Blob Data Contributor

Databricks Unity Catalog
  Storage Credential
    -> Databricks Access Connector Managed Identity

  External Location
    access_drift_lakehouse_ext -> abfss://lakehouse@acdriftadls.dfs.core.windows.net/

  Catalog
    access_drift

  Schemas (DDL로 생성 — sql/databricks/migrations/)
    access_drift.bronze
    access_drift.silver
    access_drift.intermediate
    access_drift.gold
    access_drift.eval
```

## Identity 정책

Databricks가 ADLS에 접근할 때 사람 계정이나 Storage Key를 사용하지 않습니다.

PoC 적용 방식:

1. Azure에 Databricks Access Connector를 생성합니다.
2. Access Connector의 Managed Identity에 ADLS 접근 권한을 부여합니다.
3. Databricks Unity Catalog에서 해당 identity를 Storage Credential로 등록합니다.
4. External Location이 Storage Credential을 사용해 ADLS 컨테이너에 접근합니다.

초기 권한:

- Managed Identity: `acdriftadls`에 `Storage Blob Data Contributor`

## Bootstrap 인증 방식

`bootstrap-unity-catalog.sh`는 PAT 없이 `az login` 세션을 사용합니다.

```bash
az login
./infra/databricks/bootstrap-unity-catalog.sh
```

스크립트 내부에서 `az account show`로 테넌트 ID를 자동으로 가져와 `ARM_TENANT_ID`에 설정합니다. Databricks 워크스페이스 host는 `https://adb-7405615323116390.10.azuredatabricks.net`로 고정돼 있으며 환경변수 `DATABRICKS_HOST`로 재정의할 수 있습니다.

## External Location 정책

External Location은 `lakehouse` 컨테이너 전체를 1개로 관리합니다.

이유:

- 컨테이너가 1개이므로 External Location도 1개로 충분합니다.
- 경로별 접근 제어는 UC 스키마 권한으로 처리합니다.
- 노트북과 Job에서 Storage Key 없이 ADLS 경로를 참조할 수 있습니다.

| External Location | ADLS 경로 |
| --- | --- |
| `access_drift_lakehouse_ext` | `abfss://lakehouse@acdriftadls.dfs.core.windows.net/` |

## Cluster Access Mode

PoC 공용 작업 클러스터는 `USER_ISOLATION`으로 시작합니다.

- 여러 사용자가 같은 클러스터에 attach할 수 있습니다.
- Unity Catalog에서 각 사용자의 권한을 기준으로 데이터 접근을 평가합니다.
- 클러스터 1개로 비용을 통제합니다.
- 팀원에게는 공용 클러스터 `CAN_ATTACH_TO` 권한만 부여합니다.

## 후속 고려사항

- 팀 그룹명 확정 (예: `data-eng`, `secops-ds`)
- account-level group 기반 권한 정리
- Job 실행 principal 결정 (개인 계정 vs service principal)
- Column Masking 적용 (`principal_email`, `secret_name` 등 — 테이블 스키마 확정 후)

## Eval 권한 원칙

PoC에서는 workspace admin 중심으로 `access_drift.eval` 스키마를 생성할 수 있습니다.

본개발에서는 정답 누수를 막기 위해 detection job principal에는 `eval` read 권한을 부여하지 않습니다. `eval`은 평가 담당자 또는 평가 job principal만 read할 수 있게 분리합니다.

Eval은 UC managed table로 시작하며 별도 ADLS raw 경로를 추가하지 않습니다.
