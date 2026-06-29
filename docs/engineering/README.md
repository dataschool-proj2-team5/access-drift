# Engineering Docs

이 디렉터리는 Access Drift의 엔지니어링 실행 기준을 모아두는 공간이다.

제품 요구사항과 스프린트 범위는 `docs/product/`, 아키텍처는 `docs/architecture/`, 데이터 계약은 `docs/contracts/`를 기준으로 한다. 이 디렉터리에는 그 요구사항을 실제 개발·실행·검증으로 옮길 때 필요한 기준 문서를 둔다.

---

## 문서 목록

| 문서 | 내용 |
| --- | --- |
| [sprint1-de-scope.md](./sprint1-de-scope.md) | Sprint 1에서 DE팀이 책임질 데이터, Databricks 실행, 품질검증, 재처리 기준 |

---

## 작성 기준

- 팀별 세부 백로그와 담당자는 GitHub Issues에서 관리한다.
- 이 디렉터리에는 반복해서 참조할 실행 기준, 완료 기준, runbook, 품질검증 기준을 둔다.
- 제품 범위나 사용자 요구사항을 새로 정의하지 않는다. 제품 기준은 `docs/product/`를 우선한다.
- 스키마와 테이블 계약을 새로 정의하지 않는다. 데이터 계약은 `docs/contracts/`를 우선한다.
- 중요한 인프라·운영 결정은 필요 시 ADR로 남긴다.
