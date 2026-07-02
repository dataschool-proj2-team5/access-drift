# Engineering Docs

이 디렉터리는 Access Drift의 엔지니어링 실행 기준을 모아두는 공간이다.

---

## 문서 목록

| 문서 | 내용 |
| --- | --- |
| [sprint1-de-scope.md](./sprint1-de-scope.md) | Sprint 1에서 DE팀이 책임질 데이터, Databricks 실행, 품질검증, 재처리 기준 |
| [databricks-environment-policy.md](./databricks-environment-policy.md) | PoC/dev catalog, Databricks target, raw 경로, 대표 데모 케이스 관리 기준 |
| [retry-idempotency-policy.md](./retry-idempotency-policy.md) | dev seed 기준 실패 재실행, overwrite 멱등성, 검증 기준 |
| [ADR-0004](../adr/0004-dev-retry-idempotency-and-landing-lineage.md) | dev 재처리 멱등성과 Landing 원본 보존 범위 결정 |

---

## 작성 기준

- 팀별 세부 백로그와 담당자는 GitHub Issues에서 관리한다.
- 이 디렉터리에는 반복해서 참조할 실행 기준, 완료 기준, runbook, 품질검증 기준을 둔다.
- 제품 범위, 사용자 요구사항, 스키마 계약은 여기서 새로 정의하지 않는다.
- 중요한 인프라·운영 결정은 필요 시 ADR로 남긴다.
