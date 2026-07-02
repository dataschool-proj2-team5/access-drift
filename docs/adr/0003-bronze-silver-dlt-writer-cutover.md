# ADR-0003: Bronze/Silver DLT writer 전환

- **Status**: Proposed
- **Date**: 2026-07-02
- **Deciders**: DE team

## Context

ADR-0002에서는 기존 `02_ingest.ipynb` 기반 Bronze writer를 유지하고
`bronze-dlt-expectations`를 `dlt_test` shadow 검증 경로로 두기로 했다. 당시
보류 사유는 DLT materialized view와 기존 managed Delta table의 lifecycle, owner,
nullability metadata, rollback 기준이 정리되지 않았기 때문이다.

이후 PR #84에서 Silver DLT expectation이 현재 Silver 변환 범위와 같은 Bronze 입력을
사용해 검증됐다. 따라서 DLT를 단순 품질검증 shadow asset으로만 두면 notebook과 DLT
변환 로직이 계속 중복된다. S1에서는 streaming/CDC 운영이 아니라 batch seed/API-export
형태의 Landing 입력을 사용하므로, DLT의 우선 가치는 지속 수집이 아니라 transform,
expectation, event log 기반 품질 gate에 있다.

## Decision

Bronze/Silver 정식 writer를 DLT materialized view 기반 batch pipeline으로 전환한다.

- Bronze는 raw JSONL을 읽어 Bronze source-shaped dataset과 expectation event log를
  생성한다.
- Silver는 Bronze DLT output을 읽어 4개 Silver staging dataset과 integrity audit를
  생성한다.
- 기존 notebook writer인 `02_ingest.ipynb`, `03_silver.ipynb`는 정식 dev DAG에서
  제외하고 rollback/legacy reference로만 남긴다.
- `migration_task`는 Bronze/Silver table 생성이 아니라 DLT 외 객체(eval, context,
  intermediate, gold, app, rag 등) 관리 역할로 축소한다.
- Silver consumer는 안정적인 이름인 `silver_principals`, `silver_credentials`,
  `silver_assets`, `silver_edges`를 계속 읽는다. DLT는 `silver_dlt_*` staging
  dataset을 만들고, DLT update 성공 후 publish step이 stable view를 갱신한다.

### Silver integrity audit

Silver의 cross-table 품질검증은 정식 Silver 테이블로 노출하지 않고 DLT temporary
dataset인 `silver_integrity_audit(check_name, violation_count)`로 수행한다.

이 audit dataset은 `silver_principals`, `silver_credentials`, `silver_assets`,
`silver_edges`를 조인해 단일 테이블 expectation으로 표현하기 어려운 불변조건을
확인한다. 현재 검증 항목은 다음을 포함한다.

- duplicate primary id
- credential -> principal orphan
- edge endpoint orphan
- `owns_principal` edge의 HI -> NHI 방향
- credential이 NHI principal에 bound되는지
- `permission`, `last_used_at`이 `accesses_asset` 외 edge에 존재하지 않는지

`silver_integrity_audit`는 DLT gate 용도이므로 `temporary=True`로 유지한다. 운영
관측이나 품질 이력 누적이 필요해지면 별도 영구 `quality_check_results` 테이블로
승격한다.

이번 결정에서 제외하는 항목은 다음과 같다.

- Auto Loader: 실제 지속 파일 drop/source ingestion이 생기기 전까지 도입하지 않는다.
- Streaming table: 현재 입력은 batch seed/API-export 성격이므로 materialized view로
  충분하다.
- CDC: source change feed와 운영 변경 이벤트가 아직 없으므로 S1 범위에서는 과하다.
- Notebook/DLT 병행 writer: 같은 target의 writer가 둘이 되면 최종 상태와 재실행
  기준이 모호해진다.
- `published_run` pointer 방식: view swap보다 강한 atomic publish 후보로 남기되,
  현재는 구현하지 않는다.

## Consequences

### 장점

- Bronze/Silver transform과 quality gate가 한 경로로 합쳐진다.
- Bronze 실패 시 Silver와 downstream 실행을 차단하는 DAG를 구성할 수 있다.
- DLT event log로 expectation pass/fail과 실패 원인을 추적할 수 있다.
- 기존 Silver consumer 이름은 stable view로 유지하므로 downstream query 변경을
  최소화한다.

### 단점

- 기존 managed Delta table과 DLT materialized view의 lifecycle 전환이 필요하다.
- 기존 `silver_*` table이 있으면 view로 바로 덮을 수 없으므로 legacy rename 또는
  rollback 기준이 필요하다.
- view swap은 4개 view를 순차 갱신하므로 완전한 transaction publish는 아니다.
- `02_ingest.ipynb`, `03_silver.ipynb`는 당분간 legacy reference로 남아 코드가
  완전히 제거되지는 않는다.

### 후속 후보

- `published_run` pointer 방식으로 Silver 4개 table이 항상 같은 성공 run만 보이게
  하는 atomic publish 강화
- 실제 API/file source가 지속적으로 들어오는 시점의 Auto Loader/checkpoint 도입
- source change event가 확보된 뒤 CDC/증분 처리 검토
- DLT pipeline owner를 service principal로 고정하고 grants/backup/restore 절차 자동화
