# Sprint 1 DE Scope

**버전:** v0.1  
**기준:** 2026년 6월 27일  
**상태:** Sprint 1 DE 기준  
**기준 문서:** [Sprint 1 Scope](../product/sprint1-scope.md), [PRD](../product/prd.md), [MVP User Stories](../product/mvp-user-stories.md), [Demo Scenario](../product/demo.md), [PoC Scope](../product/poc-scope.md)

이 문서는 Sprint 1에서 DE팀이 책임질 데이터와 Databricks 실행 기준을 정리한다. 세부 담당자, 일정, 구현 방식은 GitHub Issues에서 관리하고, 이 문서는 팀이 공유할 목표와 완료 기준만 다룬다.

---

## 1. DE팀 Sprint 1 목표

PoC보다 확장된 S1 개발용 합성 데이터를 기준으로 Databricks `Landing -> Bronze -> Silver`까지 재현 가능하게 적재하고, DS가 `Intermediate/Gold`를 만들 수 있는 안정적인 입력 데이터와 검증 기준을 제공한다.

S1에서 DE는 탐지 의미 판단이나 Risk Card 의미 설계를 주도하지 않는다. 다만 DS/PO가 같은 데이터를 보고 작업할 수 있도록 데이터 경로, 스키마, 실행, 검증, 재처리 기준을 정리한다.

---

## 2. 전제

- S1 대표 리스크는 [Demo Scenario](../product/demo.md)의 B-S2 NHI residual access를 기준으로 먼저 구성한다.
- 대표 케이스는 `Azure App Registration / Service Principal -> 고객 데이터 Export Storage` 접근 경로를 기준으로 한다.
- PRD/S1/Demo 문서가 확정되기 전까지 대표 시나리오와 민감도 매핑은 조정될 수 있다.
- 데이터 생성과 적재 구조는 대표 시나리오가 일부 바뀌어도 교체 가능해야 한다.
- eval은 탐지 입력이 아니라 정답지와 검증 용도로만 사용한다.
- eval/distractor의 의미 기준은 DS가 정의하고, DE는 해당 기준을 데이터 생성과 적재에 반영한다.
- raw/bronze/silver에는 planted risk, truth class 같은 정답 라벨을 넣지 않는다.

---

## 3. 책임 범위

### DE가 책임지는 것

- 개발/데모 Databricks 환경 구분 기준
- dev/demo 데이터 저장 및 적재 규칙
- S1 합성 데이터 생성 기준
- Landing/Bronze/Silver 스키마 개선과 확정
- Landing/Bronze/Silver 적재 파이프라인
- Bronze/Silver 스키마 계약과 변경 절차
- Silver 입력 데이터 품질검증
- task 분리, 재실행, 실패 복구 기준
- DS가 사용할 Silver/Eval 준비 완료 확인 기준
- 현재 조치 상태 저장/조회에 필요한 최소 데이터 계약
- DS가 정의한 eval/distractor 기준의 데이터 생성/적재 반영

### DE 단독으로 확정하지 않는 것

- Intermediate/Gold 탐지 의미 계약
- eval/distractor의 의미 기준
- Risk Card 최종 표시 필드와 문구
- AI 조치 권고안 문구
- 현재 조치 상태의 상태값, 저장 위치, 화면 표현
- 조치 상태 이력, 감사 로그 저장 계약
- RAG/Vector Search 기반 AI 권고안 확장 방식
- 최종 민감도 등급 표현과 발표 문구
- Jira 발행, 조치 이력, 감사 로그 범위

---

## 4. S1 DE 완료 기준

1. dev/demo 환경 기준이 정리되어 있고, 팀원이 어떤 환경에서 실행해야 하는지 알 수 있다.
2. S1 대표 B-S2 케이스를 포함한 개발용 합성 데이터를 재생성할 수 있다.
3. 합성 데이터가 Databricks Landing/Bronze/Silver까지 적재된다.
4. 현재 기준 Silver 모델이 DS가 Intermediate/Gold 작업에 사용할 수 있는 상태로 준비된다.
5. eval 정답지는 raw/bronze/silver와 분리되어 있고, 대표 케이스와 Silver key가 매칭된다.
6. Bronze/Silver 입력 데이터에 대해 row count, key, null, enum, 참조 검증을 수행할 수 있다.
7. task별 재실행 기준과 실패 시 재시작 지점이 문서화되어 있다.
8. 현재 조치 상태가 Gold/Risk Card 결과와 연결될 수 있는 최소 저장/조회 계약이 정리되어 있다.
9. Landing 원본 보존과 Bronze/Silver 추적에 필요한 최소 lineage 기준이 정리되어 있다.
10. 확인하지 못한 범위와 후속 작업이 GitHub Issue 또는 PR에 남아 있다.

---

## 5. 우선순위

| 우선순위 | 작업 축 | 비고 |
| --- | --- | --- |
| P0 | Databricks 개발/데모 환경 분리 | 개발 실행과 데모 실행 분리 |
| P0 | Landing/Bronze/Silver 스키마 개선과 확정 | 합성 데이터 생성 전 선행 |
| P0 | dev/demo 데이터 저장 및 적재 규칙 | 데모 데이터 보호와 DS 입력 기준 |
| P0 | S1 합성 데이터 설계와 생성 | 대표 B-S2 케이스 포함 |
| P0 | Landing/Bronze/Silver 적재 파이프라인 정리 | DS 작업 시작 조건 |
| P1 | Databricks task 분리와 파이프라인 고도화 | 실패/재실행 기준의 전제 |
| P1 | 실패/재처리와 멱등성 기준 | 최소 재실행 안정성 |
| P1 | Landing 원본 보존 및 Lineage 기준 | 원본 재처리와 근거 추적 기준 |
| P1 | Bronze/Silver 품질검증 | DS 입력 품질 확인 |
| P1 | 최소 Action State 저장/조회 기준 | 현재 조치 상태 반영 기준 |
| P1 | UC 기반 App/Eval 접근 경계 | Gold-only App, eval 격리 |
| P2 | DLT 기반 Bronze/Silver 품질체크 제한 도입 | PoC 결과 기반 제한 적용 |
| P2 | 데이터 계약 변경 프로세스 | 변경 관리 기준 |
| P2 | RAG/Vector Search 기반 참고 근거 준비 | S1 선택사항 또는 S2 후보 |

---

## 6. 주요 작업 축

각 작업 축은 Sprint 1에서 반드시 정리할 최소 범위와 후속 고도화 범위를 구분한다.

### 6.1 Databricks 개발/데모 환경 분리

**목적:** 개발 작업과 데모 실행이 서로 영향을 주지 않도록 Databricks 실행 기준을 분리한다.

**주요 내용**
- 개발 실행과 데모 실행을 분리하기 위한 catalog/schema/target 전략 정리
- Databricks Bundle target 또는 job parameter 분리 방식 정리
- 개발 데이터와 데모 고정 케이스의 적재 위치 정의
- UC catalog/schema/external location 권한 재현 기준 정리
- 필요한 경우 infra/architecture 문서에 환경 구분 반영

**완료 기준**
- 팀원이 dev와 demo 중 어느 환경에서 어떤 job을 실행해야 하는지 알 수 있다.
- 데모 데이터가 개발 중 overwrite로 깨지지 않는다.
- Databricks 구성 변경 사항이 재현 가능한 문서 또는 IaC 기준으로 남는다.

**후속 고도화**
- 세부 권한 매트릭스와 운영용 UC 거버넌스 정책
- 환경별 비용 모니터링과 자동 알림

### 6.2 Landing/Bronze/Silver 스키마 개선과 확정

**목적:** S1 합성 데이터 생성과 적재 전에 DS 입력으로 사용할 Landing/Bronze/Silver 구조와 ID 규칙을 먼저 정리한다.

**주요 내용**
- Landing raw path와 원본 보존 metadata 기준 정리
- Bronze source table과 공통 metadata 컬럼 정리
- 현재 기준 Silver 모델의 필수 컬럼과 ID 규칙 확인
- `source_id`와 내부 `principal_id`/`credential_id`/`asset_id`/`edge_id` 역할 구분
- Demo Scenario의 대표 B-S2 케이스가 현재 Silver 모델로 표현되는지 확인
- 스키마 변경이 필요한 경우 contracts, migration, notebook, seed, 검증 쿼리 영향 범위 정리

**완료 기준**
- S1 합성 데이터가 따라야 할 Landing/Bronze/Silver 입력 계약이 정리된다.
- DS가 사용할 Silver 입력 테이블과 주요 key가 명확하다.
- 대표 B-S2 케이스를 Silver에서 표현하고 추적할 수 있다.

**후속 고도화**
- 추가 SaaS/source별 Bronze 확장 규칙
- Silver 모델 변경 자동 검증
- 대규모 source onboarding 가이드

### 6.3 dev/demo 데이터 저장 및 적재 규칙

**목적:** 개발 데이터와 대표 데모 케이스를 같은 기준으로 관리하되, 데모 케이스가 데이터 안에서 묻히지 않게 한다.

**주요 내용**
- S1 개발용 합성 데이터 저장 경로 정의
- 대표 데모 케이스를 dev 데이터 안의 고정 시나리오로 둘지, 별도 demo seed로 둘지 결정
- Demo Scenario가 변경될 경우 어떤 seed/config를 수정해야 하는지 정리
- `scenario_id`, `case_id`, `subject_id`, `asset_id`, `drift_type` 식별 규칙 정리
- raw/bronze/silver와 eval 정답지 분리 유지
- 데모 데이터 재적재와 고정 seed 기준 정의

**완료 기준**
- S1 대표 B-S2 케이스가 안정적으로 재생성되고 조회된다.
- DS가 Silver와 eval을 같은 key로 비교할 수 있다.
- 데모 대표 케이스의 subject, asset, drift type을 문서나 쿼리로 확인할 수 있다.

**후속 고도화**
- demo seed와 dev seed의 완전 분리 운영
- 시나리오 버전별 데이터셋 관리
- 장기 보관/삭제 정책

### 6.4 S1 합성 데이터 설계와 생성

**목적:** PoC seed보다 확장된 개발용 합성 데이터를 만들고, 대표 리스크와 대응 정상/함정 케이스를 포함한다.

**주요 내용**
- identity, app registration/NHI, credential metadata, asset, access edge 데이터 설계
- DS가 정의한 positive, normal, distractor 기준을 합성 데이터 생성 규칙에 반영
- DS가 정의한 S1 대표 B-S2 eval 기준에 맞춰 대표 케이스와 대응 distractor 구성
- `created_at`, `offboarded_at`, `last_used_at`, `expires_at` 등 사실 timestamp 보존
- seed 고정으로 같은 입력에서 같은 대표 케이스와 key가 재생성되도록 구성
- 소량 개발 모드와 확장 생성 모드 분리
- raw seed와 eval ground truth 생성 경로 분리

**완료 기준**
- 약 1,000건 규모의 개발용 합성 데이터를 재생성할 수 있다.
- 대표 케이스가 매번 동일한 key로 생성된다.
- 정답 라벨은 eval에만 존재한다.
- 생성 결과의 주요 row count와 샘플 내용을 확인할 수 있다.

**후속 고도화**
- 대량 생성 모드와 성능 검증
- holdout split 자동화
- 다양한 drift type과 distractor 확대

### 6.5 Landing/Bronze/Silver 적재 파이프라인 정리

**목적:** DS가 사용할 Silver 입력 모델을 안정적으로 만들고 재실행 가능하게 한다.

**주요 내용**
- Landing raw path 정책 정리
- Bronze 공통 metadata 컬럼 정리
- Silver ID 생성 규칙 확인
- 현재 기준 Silver 모델의 적재 기준 정리
- PoC notebook/job과 S1 dev 데이터 흐름 차이 정리

**완료 기준**
- dev 합성 데이터가 Databricks에 Landing/Bronze/Silver까지 적재된다.
- 현재 기준 Silver 모델이 DS 입력으로 사용 가능하다.
- 대표 B-S2 케이스가 Silver에서 추적 가능하다.

**후속 고도화**
- API connector 기반 ingestion
- 증분 적재와 schema evolution 처리
- 운영용 orchestration 전환

### 6.6 Databricks task 분리와 파이프라인 고도화

**목적:** PoC job을 S1 개발 흐름에 맞게 정리하고, eval/validation이 탐지 입력 파이프라인에 섞이지 않게 한다.

**주요 내용**
- schema/migration task 분리
- dev seed 생성 task와 raw 배치 task 분리
- ingest, silver task 분리
- eval/context seed task를 본 탐지 입력과 느슨하게 분리
- validation SQL/notebook은 job task가 아니라 read-only 교차 검산 아티팩트로 유지
- S1 범위에서는 가능한 한 Silver task까지 DE 책임으로 명확화
- 필요한 경우 아키텍처 문서에 job/task 구조 반영

**완료 기준**
- `migration`, `generate_dev_seed`, `synthetic/raw 배치`, `ingest`, `silver`의 역할이 구분된다.
- eval/context는 탐지 입력이 아니라 정답지와 Risk Card 보조 context 준비 용도로 분리된다.
- notebook smoke check와 validation SQL의 역할이 구분된다.
- 특정 task 실패 시 어느 지점부터 재실행할지 판단할 수 있다.

**후속 고도화**
- Intermediate/Gold task의 별도 DS pipeline 분리
- 환경별 job parameter 표준화
- 자동 재시도와 alert 정책

### 6.7 실패/재처리와 멱등성 기준

**목적:** S1 데이터 파이프라인을 재실행해도 중복과 누락이 발생하지 않도록 최소 기준을 만든다.

상세 기준은 [retry-idempotency-policy.md](./retry-idempotency-policy.md)를 따른다.

**주요 내용**
- task별 overwrite/merge/append 기준 정리
- `run_id`와 `as_of_date` 사용 기준 정리
- Landing/dev seed 기준 backfill 가능성 정리
- Silver 재생성 시 기존 데이터 처리 방식 정의
- eval seed 재실행 시 중복 방지 기준 정의
- 실패 시 재시작 지점 문서화

**완료 기준**
- 같은 seed로 2회 실행해도 대표 row count와 key가 안정적이다.
- 실패한 task부터 재실행 가능한 기준이 있다.
- 재처리 시 외부 원천 호출이 아니라 Landing/dev seed 기준으로 복구할 수 있다.

**후속 고도화**
- run history 기반 재처리 UI 또는 운영 runbook
- source별 backfill 전략
- 장기 운영용 merge/upsert 표준화

### 6.8 Landing 원본 보존 및 Lineage 기준

**목적:** Landing을 원본 보존과 재처리 기준점으로 정의하고, Bronze/Silver/Intermediate/Gold 결과가 원천 데이터까지 추적 가능하도록 최소 기준을 정리한다.

**주요 내용**
- Landing 원본 보존 원칙 정리
- API 응답 또는 seed 원본 저장 시 필수 metadata 후보 정리
- 저장 금지 데이터 기준 정리
- `_src_file_path`, `_raw_payload`, `_checksum`, `_run_id`, `_batch_id` 역할 정리
- Bronze/Silver에서 Landing 원본을 찾기 위한 key 후보 정리
- Landing 기준 백필/재처리 흐름 정리

**완료 기준**
- Landing zone의 원본 보존 기준이 있다.
- Bronze record에서 Landing 원본 파일 또는 record를 찾을 수 있는 key 후보가 있다.
- secret value, token, private key 같은 민감값을 저장하지 않는 기준이 있다.
- 실패 시 Landing 기준으로 Bronze/Silver를 재처리하는 흐름이 설명된다.

**후속 고도화**
- Intermediate/Gold/Risk Card에서 Landing 원본까지의 end-to-end lineage 자동 검증
- 운영용 lineage 시스템 도입
- API connector별 request/response metadata 표준화

### 6.9 Bronze/Silver 품질검증

**목적:** DS 작업 전 Bronze/Silver 입력 데이터의 신뢰성을 확인한다.

**주요 내용**
- 레이어별 row count 검증
- 필수 ID null 체크
- key 중복 체크
- enum 값 검증
- credential -> principal 참조 검증
- edge -> principal/asset 참조 검증
- eval subject/asset key가 Silver와 매칭되는지 확인

**완료 기준**
- 검증 쿼리 또는 notebook으로 Bronze/Silver 입력 데이터 품질을 확인할 수 있다.
- 실패 시 어느 레이어에서 깨졌는지 확인할 수 있다.
- 재실행 후 대표 row count와 key가 안정적으로 유지된다.

**후속 고도화**
- Gold/Intermediate 품질검증 확장
- 품질검증 결과 대시보드화
- alert 연동

### 6.10 UC 기반 App/Eval 접근 경계

**목적:** S1에서 앱/대시보드는 Gold 결과만 읽고, eval 정답지는 탐지 입력과 앱 접근에서 분리되도록 Unity Catalog 기준을 정리한다.

**주요 내용**
- App 또는 Dashboard가 조회할 Gold schema/table 기준 정리
- App runtime 또는 viewer 권한을 Gold SELECT 중심으로 제한하는 기준 정리
- eval schema는 탐지 job과 앱 접근 대상에서 제외
- eval은 검증 SQL 또는 평가 job에서만 사용하는 원칙 정리
- secret value는 마스킹 대상이 아니라 저장 금지 대상으로 유지

**완료 기준**
- App/Dashboard가 Gold 결과만 조회한다는 기준이 있다.
- eval이 탐지 입력과 앱 접근에서 분리된다는 기준이 있다.
- S1 데모에서 "Gold-only App 접근"과 "eval 격리"를 설명할 수 있다.

**후속 고도화**
- 역할별 접근 권한 매트릭스 구체화
- Gold -> Intermediate -> Silver -> Bronze/Landing lineage 검증 확대
- 공식 catalog/schema/table 운영 정책
- SecOps 외 viewer를 위한 column masking 검토
- UC 권한 IaC 자동화와 운영 권한 감사

### 6.11 DLT 기반 Bronze/Silver 품질체크 제한 도입

**목적:** DLT PoC 결과를 바탕으로 Bronze/Silver 레이어 일부에 품질검증을 제한적으로 붙여본다.

**주요 내용**
- DLT PoC 결과 정리
- 적용 대상 Bronze/Silver 테이블 1~2개 선정
- 필수 컬럼 null, enum, key 중복, 참조 무결성 expectation 정의
- 기존 SQL/notebook 검증과 DLT expectation의 역할 구분
- 적용 전후 장단점과 tradeoff 기록
- 실패 시 개발자가 확인할 로그와 결과 위치 정리
- Intermediate/Gold 등 DS 담당 영역은 S1 DE 품질체크 적용 범위에서 제외하고, DS 구현 이후 별도 확장으로 둔다.

**완료 기준**
- Bronze/Silver 레이어 최소 1개 테이블에 DLT 품질체크가 적용되거나 적용 가능성이 검증된다.
- 어떤 품질 오류를 잡는지 예시가 있다.
- S1에서는 보조 검증으로 둘지, 후속 스프린트에서 필수 검증으로 승격할지 판단할 수 있다.

**후속 고도화**
- Bronze/Silver 전체 테이블로 DLT expectation 확대
- Intermediate/Gold 품질검증 확장
- DLT pipeline 운영 비용과 장애 대응 기준 정리

### 6.12 최소 Action State 저장/조회 기준

**목적:** 사용자가 변경한 현재 조치 상태가 Gold/Risk Card 결과와 연결되고, 파이프라인 재실행으로 덮어쓰이지 않도록 최소 데이터 계약을 정리한다.

**주요 내용**
- 현재 조치 상태 저장 대상과 연결 key 기준 정리
- Gold/Risk Card 결과와 조치 상태의 결합 방식 정리
- 현재 상태만 저장하고 상태 변경 이력, 감사 로그, Jira/Revoke 연동은 제외
- 상태값과 화면 표현은 PO/FE와 협의
- 저장 위치와 조회 방식은 DS/PO/FE 구현 흐름과 함께 확정

**완료 기준**
- 현재 조치 상태를 저장/조회할 수 있는 최소 스키마 또는 계약 초안이 있다.
- Gold/Risk Card 결과와 조치 상태를 연결할 key 기준이 있다.
- 파이프라인 재실행 시 사용자가 변경한 현재 조치 상태가 덮어쓰이지 않는 구조가 설명된다.

**후속 고도화**
- 상태 변경 이력 저장
- 감사 로그와 권한 정책
- Jira/Revoke 연동

### 6.13 데이터 계약 변경 프로세스

**목적:** S1 중 스키마, seed, DDL, notebook 변경이 흩어지지 않게 한다.

**주요 내용**
- Bronze/Silver 계약 문서 변경 기준 정리
- migration 변경 시 같이 봐야 할 파일 정리
- seed 변경 시 eval/검증 쿼리 영향 확인 기준 정리
- PR에 남겨야 할 데이터 검증 항목 정리

**완료 기준**
- 스키마 변경 시 문서, DDL, notebook, seed, 검증이 함께 갱신되는 기준이 있다.
- 계약 변경의 진입점을 `docs/contracts/`에서 확인할 수 있다.
- PR 작성자가 데이터 변경의 영향과 검증 결과를 남길 수 있다.

**후속 고도화**
- 계약 변경 자동 검증
- schema diff 자동화
- CI 기반 contract check

### 6.14 RAG 기반 참고 근거 준비

**목적:** S1에서 RAG 기반 참고 근거 출력을 선택사항으로 검토할 수 있도록, DE 관점에서 필요한 근거 문서 chunk와 검색 source table 기준을 정리한다.

**주요 내용**
- 보안 런북/조치 가이드 문서 chunk의 저장 위치 정리
- DS/AI가 Vector Search source로 사용할 수 있는 `rag.doc_chunks` 기준 정리
- Risk Card 현재값은 DS/AI 질의 생성 입력으로 보고, `rag.doc_chunks`에는 정책/playbook/source guide/API reference corpus를 저장
- embedding, retrieval 품질, prompt, citation 없는 답변 처리, AI 윤리/가드레일은 DS/AI와 PO/Security 범위로 분리
- S1 필수 완료 기준이 아니라 선택사항 또는 S2 후보로 관리

**완료 기준**
- RAG를 S1에서 시도할지 S2로 넘길지 판단할 수 있는 DE 관점 검토 결과가 있다.
- 시도할 경우 필요한 근거 문서 chunk, citation metadata, DS/AI handoff 기준이 정리되어 있다.

**후속 고도화**
- Vector Search endpoint/index 생성과 retrieval 품질 검증
- citation metadata 품질검증
- RAG 답변 품질 평가와 fallback 정책
