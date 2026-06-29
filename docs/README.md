# Docs

이 디렉터리는 Access Drift의 제품, 아키텍처, 데이터 계약, 엔지니어링 실행 기준을 모아둔다.

작업을 시작할 때는 이 문서에서 작업 유형에 맞는 문서를 찾고, 직접 관련된 문서만 추가로 읽는다.

---

## 문서 구조

| 위치 | 역할 | 먼저 볼 상황 |
| --- | --- | --- |
| [product/](./product/) | 제품 요구사항, 스프린트 범위, 데모 시나리오 | 기능 범위, 사용자 흐름, 데모 케이스 확인 |
| [engineering/](./engineering/) | 개발 실행 기준, DE scope, Databricks 환경 정책 | 파이프라인, 데이터 생성, Databricks 실행 기준 확인 |
| [contracts/](./contracts/) | 데이터 계약, 스키마, 민감 자산 taxonomy | 테이블, 컬럼, ID, eval, schema 변경 확인 |
| [architecture/](./architecture/) | 시스템 구성과 데이터 흐름 개요 | 컴포넌트 관계와 상위 구조 확인 |
| [adr/](./adr/) | 중요한 기술·운영 결정 기록 | 인프라, 데이터, 보안, 비용 영향이 있는 결정 확인 |

인프라 실행 절차와 Databricks bootstrap 명령은 [infra/README.md](../infra/README.md)를 기준으로 한다.
