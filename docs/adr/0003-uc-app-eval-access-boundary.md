# ADR-0003: UC App/Eval Access Boundary

- **Status**: Accepted
- **Date**: 2026-07-02
- **Deciders**: Access Drift team
- **Related Issue**: #58

## Context

Access Drift는 Databricks Unity Catalog 위에서 탐지 결과, App 조회 데이터, eval 정답지를 함께 관리한다. 보안 프로젝트 성격상 탐지 결과를 보여주는 App과 탐지/검증 파이프라인의 데이터 접근 경계도 설명 가능해야 한다.

현재 Dashboard 코드는 `DATABRICKS_TOKEN`으로 Databricks SQL Statement API를 호출한다. 따라서 실제 쿼리 권한은 Databricks Apps service principal이 아니라 token 소유자 권한일 수 있다. 또한 `access-drift-pipeline` 안에 detection task와 eval/verification task가 함께 있으면 Unity Catalog 권한만으로 특정 notebook이 eval을 못 읽는다고 증명하기 어렵다. UC 권한은 notebook 단위가 아니라 실행 principal 단위로 적용되기 때문이다.

S1에서는 실제 운영용 least-privilege grant를 확정하기보다, App 조회 범위와 eval 격리 정책을 먼저 고정한다.

## Decision

- Dashboard/App의 조회 범위는 `app`, `rag`, `gold` schema로 제한한다.
- Dashboard/App은 `eval`, `silver`, `intermediate`를 직접 조회하지 않는다.
- Dashboard/App은 `app` schema의 dashboard view를 우선 조회한다.
- `gold.gold_core`는 app view fallback 또는 검증용 원천으로만 허용한다.
- RAG/AI 추천 근거 조회가 필요한 경우 `rag.doc_chunks`를 사용한다.
- Detection job은 eval을 탐지 입력으로 읽지 않는다.
- Eval/verification job만 `eval` schema를 읽거나 적재할 수 있다.
- secret value, token value, private key value는 masking 대상이 아니라 저장 금지 대상이다.
- 실제 UC least-privilege grant 적용은 Dashboard runtime token/service principal과 detection/eval job 실행 주체를 분리한 뒤 별도 작업으로 수행한다.

권한 목표는 다음을 기준으로 한다.

| 주체 | App | RAG | Gold | Eval | Silver/Intermediate |
| --- | --- | --- | --- | --- | --- |
| Dashboard/App runtime | read, action state write | read | read/fallback | no | no direct |
| Detection job | no | no | write | no | pipeline role 기준 read/write |
| Eval/verification job | no | no | read | read/write | read |
| 개발자 | dev 편의 권한 | dev 편의 권한 | dev 편의 권한 | 필요 시 검증용 | dev 편의 권한 |

## Consequences

- #58은 실제 grant 변경이 아니라 정책 결정과 코드 참조 경계 확인으로 처리한다.
- 현재 dev 팀원 broad grant는 개발 편의 권한이며 운영 권한 모델로 보지 않는다.
- Dashboard가 PAT 기반으로 SQL API를 호출하는 동안에는 App service principal grant만으로 App 권한 격리를 증명할 수 없다.
- UC 권한 격리를 실제로 증명하려면 Dashboard runtime token/service principal을 확정하고, detection job과 eval/verification job 실행 주체를 분리해야 한다.
- App 화면의 access path는 `app` view와 Gold evidence key를 통해 설명하고, UC lineage는 발표 선택 증빙으로만 사용한다.
