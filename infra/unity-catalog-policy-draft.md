# Unity Catalog Policy Draft

이 문서는 Access Drift PoC에서 Unity Catalog를 어떻게 구성할지 정리한 초안입니다.
아직 최종 ADR이 아니며, 팀 합의 후 확정 결정은 `docs/adr/`에 별도로 기록합니다.

## 목적

Databricks에서 ADLS Gen2 데이터를 사용할 때 사람 계정의 자격증명, Storage Key, SAS Token을 코드에 넣지 않고 Unity Catalog를 통해 데이터 접근 위치와 권한을 관리합니다.

## PoC 적용 범위

PoC에서는 데이터 흐름 검증과 운영 단순성을 우선합니다.

적용하는 것:

- Catalog는 `access_drift` 하나만 사용합니다.
- Schema는 현재 데이터 계층에 필요한 5개만 생성합니다.
  - `landing`
  - `bronze`
  - `silver`
  - `intermediate`
  - `gold`
- External Location은 ADLS 컨테이너별로 5개를 만듭니다.
- ADLS 접근은 Databricks Access Connector와 Managed Identity를 사용합니다.
- 초기 권한은 workspace admin 중심으로 둡니다.
- Catalog는 현재 Databricks workspace에만 binding합니다.
- PoC 공용 작업 클러스터는 `USER_ISOLATION` access mode로 시작합니다.

적용하지 않는 것:

- 세부 팀 그룹별 권한 분리
- Column Masking
- 추가 schema
- 팀원별 공유 클러스터 또는 SQL warehouse 정책
- 운영용 service principal 기반 job 실행 정책

## 구성 개념

```text
Azure
  acdriftadls
    landing
    bronze
    silver
    intermediate
    gold

Azure
  Databricks Access Connector
    Managed Identity

Azure RBAC
  Managed Identity -> acdriftadls: Storage Blob Data Contributor

Databricks Unity Catalog
  Storage Credential
    -> Databricks Access Connector Managed Identity

  External Locations
    access_drift_landing_ext      -> abfss://landing@acdriftadls.dfs.core.windows.net/
    access_drift_bronze_ext       -> abfss://bronze@acdriftadls.dfs.core.windows.net/
    access_drift_silver_ext       -> abfss://silver@acdriftadls.dfs.core.windows.net/
    access_drift_intermediate_ext -> abfss://intermediate@acdriftadls.dfs.core.windows.net/
    access_drift_gold_ext         -> abfss://gold@acdriftadls.dfs.core.windows.net/

  Catalog
    access_drift

  Schemas
    access_drift.landing
    access_drift.bronze
    access_drift.silver
    access_drift.intermediate
    access_drift.gold
```

Databricks는 catalog 생성 시 `default`와 `information_schema` schema를 자동 생성할 수 있습니다.
PoC에서 직접 관리하는 schema는 위 5개 계층입니다.

## Identity 정책

Databricks가 ADLS에 접근할 때 사람 계정이나 Storage Key를 사용하지 않습니다.

PoC 적용 방식:

1. Azure에 Databricks Access Connector를 생성합니다.
2. Access Connector의 Managed Identity에 ADLS 접근 권한을 부여합니다.
3. Databricks Unity Catalog에서 해당 identity를 Storage Credential로 등록합니다.
4. External Location이 Storage Credential을 사용해 ADLS 컨테이너에 접근합니다.

초기 권한:

- Managed Identity: `acdriftadls`에 `Storage Blob Data Contributor`
- 세부 컨테이너 단위 RBAC 분리는 후속으로 검토합니다.

## External Location 정책

External Location은 컨테이너별로 5개를 만듭니다.

이유:

- 데이터 계층별 위치가 명확합니다.
- 나중에 계층별 접근 권한을 분리하기 쉽습니다.
- 노트북과 job에서 Storage Key 없이 안정적으로 ADLS 경로를 참조할 수 있습니다.

| 계층 | External Location | ADLS 경로 |
| --- | --- | --- |
| landing | `access_drift_landing_ext` | `abfss://landing@acdriftadls.dfs.core.windows.net/` |
| bronze | `access_drift_bronze_ext` | `abfss://bronze@acdriftadls.dfs.core.windows.net/` |
| silver | `access_drift_silver_ext` | `abfss://silver@acdriftadls.dfs.core.windows.net/` |
| intermediate | `access_drift_intermediate_ext` | `abfss://intermediate@acdriftadls.dfs.core.windows.net/` |
| gold | `access_drift_gold_ext` | `abfss://gold@acdriftadls.dfs.core.windows.net/` |

## 권한 정책

PoC에서는 실제 팀 그룹별 권한 차단보다 데이터 흐름 검증을 우선합니다.

초기 적용:

- workspace admin이 catalog, schema, external location을 관리합니다.
- `access_drift` catalog는 `ISOLATED`로 설정하고 현재 workspace에만 `READ_WRITE` binding합니다.
- 팀 그룹별 read/write 분리는 적용하지 않습니다.
- PoC 팀원 read/write 권한은 Databricks account group 확정 전까지 개인 principal 기준으로 부여합니다.
- 민감 컬럼 마스킹은 적용하지 않습니다.

후속 목표 권한 모델:

| 계층 | 목표 접근 권한 | Column Masking 후보 |
| --- | --- | --- |
| bronze | DE/job write, DS/SecOps read | 없음 |
| silver | DE/job write, DS/SecOps read | `principal_email`, `secret_name` |
| intermediate | 탐지 job read/write, SecOps read | 필요 시 검토 |
| gold | mart job write, SecOps/dashboard read | `principal_email`, `secret_name` |

Column Masking은 초기 PoC에서는 적용하지 않습니다.
테이블 스키마, 팀 그룹, full 노출 대상이 확정된 뒤 적용합니다.

## Cluster Access Mode

PoC 공용 작업 클러스터는 `USER_ISOLATION`으로 시작합니다.

의미:

- 여러 사용자가 같은 클러스터에 attach할 수 있습니다.
- Unity Catalog에서는 각 사용자의 권한을 기준으로 데이터 접근을 평가합니다.
- 사용자 수만큼 클러스터를 만들 필요가 없어 비용 통제가 쉽습니다.

초기 적용:

- 클러스터 수는 1개로 유지합니다.
- `USER_ISOLATION` access mode를 사용합니다.
- 팀원에게는 공용 클러스터 `CAN_ATTACH_TO` 권한만 부여합니다.

## 적용 대상 파일

예상 수정 범위:

- `infra/azure/`
  - Databricks Access Connector
  - Managed Identity
  - ADLS role assignment
- `infra/databricks/`
  - Unity Catalog catalog/schema/external location bootstrap
  - cluster access mode
  - job 변수와 catalog/schema/table 경로
- `infra/README.md`
  - 배포 순서와 수동 확인 절차

## 후속 고려사항

- Unity Catalog bootstrap 도구
  - 후보: Databricks CLI 스크립트, Databricks Asset Bundles, Terraform
  - PoC 추천: Databricks CLI 스크립트
- 팀 그룹명 확정
  - 예: `data-eng`, `secops-ds`, `dashboard`
  - workspace-local group은 Unity Catalog grant principal로 바로 인식되지 않을 수 있으므로, 운영 전 account-level group 기준으로 정리합니다.
- job 실행 principal
  - 개인 계정으로 실행할지, service principal을 만들지 결정 필요
- 추가 schema
  - 현재 5개 계층 외 schema는 목적과 권한 요구가 확정된 뒤 생성합니다.
- Column Masking
  - `principal_email`, `secret_name` 등 민감 컬럼 후보는 테이블 스키마 확정 후 적용합니다.
- 팀원별 권한 확인 방식
  - SQL warehouse, 개인 compute, shared cluster 중 선택 필요

## 권한 확인용 SQL 초안

팀원이 자기 계정으로 Databricks에 접속한 뒤 실행합니다.

```sql
SELECT current_user();

SHOW CATALOGS LIKE 'access_drift';
SHOW SCHEMAS IN access_drift;

SHOW GRANTS ON CATALOG access_drift;
SHOW GRANTS ON SCHEMA access_drift.landing;
SHOW GRANTS ON SCHEMA access_drift.bronze;
SHOW GRANTS ON SCHEMA access_drift.silver;
SHOW GRANTS ON SCHEMA access_drift.intermediate;
SHOW GRANTS ON SCHEMA access_drift.gold;
```
