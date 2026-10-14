# Access Drift 개인 기여 조사

조사 기준일: 2026-10-14 (KST) / 대상 계정: `Pexy99`

## 1. 조사 범위와 판정 기준

- GitHub 전체 PR 79건의 작성자, 본문, 변경 파일, 커밋 작성자, 일반 댓글, 리뷰 및 리뷰 스레드를 조회했다. 71건 병합, 8건 미병합 종료, 조사 당시 열린 PR은 없었다.
- 본인 작성 PR은 49건이며, 45건 병합, 4건 미병합 종료다. PR 건수는 작업 이력 규모이지 제품 성과 KPI가 아니다.
- GitHub 인증 계정은 `Pexy99`이며, 커밋에는 `Ahyun`, `Jaeryun Joo`가 나타난다. 귀속은 표시 이름만으로 판단하지 않고 GitHub 연결 계정과 변경 내용을 함께 확인했다.
- PR 목록 페이지 누락은 없었고, 각 PR의 files/commits/comments/reviews/reviewThreads 조회 건수도 totalCount와 일치했다. 별도 API 조회로 리뷰 스레드 내부 댓글도 totalCount와 조회 건수가 일치함을 확인했다.
- 본인 작성 PR도 모든 변경을 혼자 최초 구현했다는 뜻은 아니다. 다른 팀원의 선행 작업, 충돌 해소, 후속 보강을 구분했다.
- PR 본문의 원격 실행 결과는 **당시 작성자가 기록한 결과**다. 이번 조사에서 Azure/Databricks를 다시 실행하거나 성능을 재측정하지 않았다.
- PR에 배경이 충분한 항목은 PR을 우선 근거로 사용했다. 대화에 나타난 문제의식은 보조 설명이며, 대화만으로 최초 구현자나 실제 성과를 확정하지 않았다.
- 원시 API 응답은 `/tmp/access-drift-pr-audit.json`에 일시 보관했다. 개인 이메일, 인증값, 전체 대화 원문은 이 문서에 복사하지 않았다.

## 2. 기여 요약

| 영역 | 확인된 본인 기여 | 주요 근거 |
| --- | --- | --- |
| 제품·아키텍처 기준 | PoC/MVP 범위, 데이터 레이어 책임, 대표 시나리오, 팀별 실행 기준 문서화 | #5, #26, #120 |
| Azure/Databricks 기반 | Bicep, ADLS Gen2, Access Connector, UC bootstrap, DAB 실행 기반 구성·단순화 | #2, #4, #28, #30 |
| 메달리온 파이프라인 | Landing/Bronze/Silver/Eval 노트북, 계약·DDL, 재현 가능한 합성 입력, SaaS 확장 | #7, #39, #45, #46, #72, #80 |
| 공통 접근 모델 | Principal/Credential/Asset/Edge 모델과 결정론적 ID, 원천 ID 보존, 소유·접근 관계 보강 | #7, #39, #80, #89 |
| 안정성·운영 설계 | DAG 실행 흐름, 재처리 검산 SQL, semantic audit, DLT writer 전환·publish·cutover guard | #60, #64, #108, #111 |
| RAG 데이터 기반 | 12개 근거 chunk 큐레이션·metadata 계약·Delta 적재·검증 | #79 |
| 조치 상태 | 탐지 결과와 사용자 상태 분리, 최신 상태/감사 이벤트 계약·DDL·writeback | #52, #70, #88 |
| 배포·화면 연동 | Databricks Apps CD, 원격 런타임 수정, Jira 환경 설정, source/시간/HI 표시 매핑 | #94, #98, #109, #110, #116 |
| 리뷰·AI 안전성 QA | 계약 근거 오류, 검증의 데이터 변경 부작용, positional write 위험 지적, AI 안전 응답 개선 요청 | #13, #17, #114 |
| 협업·전달 | 팀별 이슈 템플릿, 문서 진입점, 발표자료·README·민감 이메일 제거 | #18, #23, #32, #119, #121 |

## 3. 배경·구현·검증 상세

### 3.1 제품 범위와 팀 간 계약 정리

**배경:** 초기 PoC에서 UI, 실제 연동, 자동 조치까지 한꺼번에 포함하면 팀별 완료 기준과 책임이 불명확해질 수 있었다.

**기여:** #5에서 PoC 완료를 공용 Databricks Gold 결과 조회로 좁히고, 실제 API/자동 회수/UI 등을 제외했다. #26에서는 PRD, User Stories, Sprint 1 Scope, 대표 데모와 민감 자산 분류 기준을 연결했다. #1 리뷰에서는 DS 설계 초안 전체보다 확정 계약과 실행 산출물을 작업 단위로 병합하도록 제안했다.

**결과 근거:** #22에 Gold 2건, eval positive 2건 매칭, normal 1건 제외, 중복/필수 null 0건을 기록했다. 이는 팀의 PoC 결과 정리이며, Gold 탐지 구현 전체를 본인 작업으로 귀속하지 않는다.

**근거:** [#5](https://github.com/dataschool-proj2-team5/access-drift/pull/5), [#26](https://github.com/dataschool-proj2-team5/access-drift/pull/26), [#1 댓글](https://github.com/dataschool-proj2-team5/access-drift/pull/1), [#22](https://github.com/dataschool-proj2-team5/access-drift/pull/22)

### 3.2 실행 인프라와 환경 분리

**배경:** 공용 실행 환경과 원본 보존 기반이 필요했고, PoC 재현용 데이터가 개발 중 변경에 영향을 받지 않아야 했다.

**기여:** #2에서 Azure 리소스 Bicep, Databricks DAB, UC bootstrap과 셋업 확인 노트북을 구성했다. #4에서는 컨테이너/External Location 5개를 1개로 단순화하고 레이어를 경로로 나눴으며, bootstrap 인증을 Azure CLI 세션 재사용으로 변경했다. #28/#30에서 catalog·target·raw 경로를 분리했다. #30은 workspace-local group이 UC grant principal로 해석되지 않는 문제를 진단하고 사용자 grant 스크립트를 추가했다.

**의사결정:** PoC에 필요하지 않은 컨테이너별 RBAC 분리와 별도 bootstrap SP를 추가하지 않았다. 초기 `demo/dev` 구분은 후속 `poc/dev` 정책으로 정리됐으므로 초기 PR 설정을 현재 상태와 동일하게 설명하면 안 된다.

**한계:** UC 인프라·개발 권한 구성과 App/Eval의 운영 최소권한 적용은 별개다. 비용 최소화를 고려했지만 비용 절감률은 측정하지 않았다.

**근거:** [#2](https://github.com/dataschool-proj2-team5/access-drift/pull/2), [#4](https://github.com/dataschool-proj2-team5/access-drift/pull/4), [#28](https://github.com/dataschool-proj2-team5/access-drift/pull/28), [#30](https://github.com/dataschool-proj2-team5/access-drift/pull/30)

### 3.3 Landing/Bronze/Silver/Eval 파이프라인

**배경:** DS가 탐지 로직을 구현하려면 원천 데이터를 읽을 수 있는 공통 모델과 비교 가능한 eval 입력이 먼저 필요했다.

**기여:** #7에서 migration → seed upload → Bronze ingest → Silver transform → eval seed 흐름을 구현했다. 원천 6종을 Bronze 6개 테이블로 적재하고 Silver 4개 테이블로 정규화했다. #39에서 원천 ID와 내부 결정론적 ID, source-like 보강 필드, eval 전용 정보, 저장 금지 인증값을 구분했다. #45에서 dev 입력 경로와 L/B/S 검증 SQL을 연결했다.

**합성 데이터:** #46의 generator/verify로 동일 seed/size의 재현성을 확인하고, raw에 eval 라벨·severity·secret 원문을 넣지 않도록 했다. #72/#80에서 GitHub, Google Workspace, Slack source-like 입력과 변환을 확장했다. #80의 검증에는 Silver 필수 null·orphan 0건과 source namespace 검사가 기록돼 있다.

**주의:** 실제 SaaS connector 구축이 아니라 API/export 형태를 모사한 합성 입력이다. 16개는 Bronze 입력 객체/테이블 수이며, 독립 외부 서비스 16개를 실제 수집한 의미가 아니다. `7개 시스템`이라는 표현은 별도 산정표 없이 이 문서에서 확정하지 않는다.

**근거:** [#7](https://github.com/dataschool-proj2-team5/access-drift/pull/7), [#39](https://github.com/dataschool-proj2-team5/access-drift/pull/39), [#45](https://github.com/dataschool-proj2-team5/access-drift/pull/45), [#46](https://github.com/dataschool-proj2-team5/access-drift/pull/46), [#72](https://github.com/dataschool-proj2-team5/access-drift/pull/72), [#80](https://github.com/dataschool-proj2-team5/access-drift/pull/80)

### 3.4 실제 문제 사례: GitHub 소유자 관계 누락

**배경:** GitHub App이 Silver에 들어와도 owner가 공통 HI/소유 관계로 연결되지 않아 DS/Gold에서 owner status가 NULL로 남는 문제가 있었다.

**해결:** #89에서 `owner_email`을 HI principal의 원천 식별자로, `owner_employment_status`를 공통 status로 매핑하고 HI → GitHub App의 `owns_principal` edge를 생성했다. 새 owner 테이블을 추가하지 않고 기존 4개 테이블 모델을 유지했다.

**검증:** PR 기록상 GitHub owner edge 5건 생성, principal/edge 중복 키 0건, owner edge의 출발 principal 누락 0건을 확인했다. #75는 표시 이름과 조인 식별자를 분리했고, #108은 GitHub owner의 lifecycle seed를 보강해 표시 이름과 담당자 routing 역할이 섞이지 않도록 했다. #108의 원격 semantic audit는 FAIL 0건, WARN 5건으로 기록됐다.

**의미:** 단순 컬럼명 통일을 넘어, 시스템 안에 포함된 소유자 정보를 공통 주체와 관계로 복원한 사례다. 모든 SaaS 사람 계정의 identity resolution을 해결했다는 뜻은 아니다.

**근거:** [#75](https://github.com/dataschool-proj2-team5/access-drift/pull/75), [#89](https://github.com/dataschool-proj2-team5/access-drift/pull/89), [#108](https://github.com/dataschool-proj2-team5/access-drift/pull/108)

### 3.5 재처리·DAG·DLT writer 전환

**배경:** 작은 deterministic dev seed에서는 지속 수집/CDC보다 재현 가능한 배치가 적합했다. DLT 적용 시 기존 managed table과 ownership 충돌, 소비자 이름 변경, 관계 불일치 전파를 다뤄야 했다.

**기여:** #60에서 생성과 ADLS 복사를 task로 분리하고 실행 기준을 정리했다. #64/#101에서 overwrite 재생성과 row count/distinct key/orphan/unmatched 검산 기준, Landing 보존 범위를 기록했다. #111에서 Bronze/Silver를 DLT materialized view writer로 전환하고, staging 출력 → stable Silver view publish → downstream 구조와 cutover guard를 구성했다.

**의사결정:** Auto Loader/streaming/CDC를 즉시 도입하지 않았다. 기존 소비자의 Silver 이름을 유지하고, 기존 Bronze object 교체를 명시적으로 요구하도록 했다. #96/#100에서는 접근 시각을 원천 → Bronze → Silver로 보존하도록 보강했다.

**당시 검증:** #111에 DLT 실행, Silver publish, Intermediate/Gold 및 app view 실행 성공이 기록됐다. Silver는 principals 59 / credentials 25 / assets 35 / edges 65, access 시각 35/35, Gold 22건의 시각 22/22, 검사 대상 키 중복·null/empty 0건이다. dev override에는 12개 task가 정의돼 있으며 기본 job 및 별도 RAG/governance job을 포함한 전체 개수와 혼동하면 안 된다.

**중요 한계:** stable view 4개 갱신은 순차 실행이며 cross-table atomic transaction이 아니다. overwrite/refresh 재실행 확인을 장기 증분 처리의 exactly-once 보장으로 표현하지 않는다. 최초 DLT expectation·fixture·CI 구현은 팀원 작업이고, 본인은 후속 보강과 운영 writer 전환을 담당했다.

**근거:** [#60](https://github.com/dataschool-proj2-team5/access-drift/pull/60), [#64](https://github.com/dataschool-proj2-team5/access-drift/pull/64), [#101](https://github.com/dataschool-proj2-team5/access-drift/pull/101), [#111](https://github.com/dataschool-proj2-team5/access-drift/pull/111), [ADR](../adr/0003-bronze-silver-dlt-writer-cutover.md)

### 3.6 RAG 근거 데이터 설계·적재

**배경:** 대표 리스크의 조치 제안을 위해 내부 정책뿐 아니라 조치 절차·실행 API의 근거가 필요했다.

**기여:** #79에서 `rag.doc_chunks` 계약, JSONL seed, DDL, seed notebook을 구성했다. 문서 본문과 metadata를 분리하고 `chunk_id`, `source_uri`, `doc_type`, `drift_type`, `action_type`, `source_system`, `source_area`, `principal_kind` 등으로 출처·검색 조건을 표현했다. 적재 시 `chunk_hash`, `generated_at`, `run_id`를 계산했다.

**규모·검증:** 12개 chunk는 내부 정책 1, playbook 1, 합성 case 1, Azure/Graph/RBAC 가이드·API 6, GitHub 가이드 2, Google Workspace 가이드 1이다. 이는 chunk 12개이지 원문 문서 12개라는 뜻은 아니다. PR 기록상 적재 12건, distinct ID 12, duplicate 0, forbidden chunk 0, 대표 케이스의 후보 9건을 확인했다.

**트러블슈팅:** 당시 SQL DDL의 CHECK constraint 적용이 실패해 enum 검증을 notebook smoke check로 유지했다. GitHub App 근거도 개인 authorization revoke 문서가 아닌 설치된 App 관리 문서로 수정했다.

**경계:** Vector Search endpoint/index, embedding, retrieval/hybrid 로직, RAG chain 전체는 #79 범위 밖이다. 검색 정확도 향상률, citation 연결률, 검색 시간 단축을 측정한 결과는 이 PR에 없다. 평가 질문 10건의 작성 기여는 별도 최초 추가 commit/대화 확인 없이 확정하지 않는다.

**근거:** [#79](https://github.com/dataschool-proj2-team5/access-drift/pull/79), [계약](../contracts/rag-evidence.md)

### 3.7 조치 상태·감사 이벤트·context 분리

**배경:** Gold를 재생성해도 사용자 검토 상태가 사라지지 않아야 하며, 자산 설명/담당자 context를 탐지 사실과 혼합하지 않아야 했다.

**기여:** #48/#51에서 asset context와 assignment routing 계약·generator·적재를 추가했다. #52/#70에서 `risk_case_key` 기준 최신 상태와 append-only 이벤트를 분리했다. #88은 Risk Card의 상태 변경을 state upsert/event insert와 연결하고 SQL helper를 UI에서 분리했다.

**검증:** #88에 Open → In Review → Open 변경 후 state 1건, event 2건, 최종 status=open이 기록돼 있다.

**한계:** state/event 두 쓰기의 완전 atomicity, 다중 사용자 충돌 해결, 승인 기반 자동 revoke까지 구현한 것은 아니다. write 실패 시 UI session fallback이 DB 저장 성공과 동일하지 않다.

**근거:** [#48](https://github.com/dataschool-proj2-team5/access-drift/pull/48), [#51](https://github.com/dataschool-proj2-team5/access-drift/pull/51), [#52](https://github.com/dataschool-proj2-team5/access-drift/pull/52), [#70](https://github.com/dataschool-proj2-team5/access-drift/pull/70), [#88](https://github.com/dataschool-proj2-team5/access-drift/pull/88)

### 3.8 Apps 배포와 데이터 표시 연결

**기여:** #94에서 Apps bundle/app 설정과 main 변경 시 CD workflow를 추가했다. #98에서는 secrets 파일 없는 런타임의 env 우선 설정과 Streamlit 버전 호환 문제를 수정했다. #109에서 Jira 설정을 CD → bundle 변수 → runtime env로 전달했다. #110/#116에서 view의 source 유형, 최근 접근 시각, HI 이메일을 loader 내부 모델과 화면으로 전달했다.

**검증:** #116에는 mock이 아닌 실제 view loader 22건과 HI 이메일 10건 확인이 기록돼 있다. 이는 화면 매핑 검증이며 사용자 생산성 향상 지표가 아니다.

**경계:** 대시보드 최초 구현은 #81의 ShinDuck 작업이다. 본인은 상태 writeback, CD·런타임·표시 보강을 담당했다. #109는 Jira 설정 전달이며 Jira 연동 전체의 최초 구현을 의미하지 않는다.

**근거:** [#94](https://github.com/dataschool-proj2-team5/access-drift/pull/94), [#98](https://github.com/dataschool-proj2-team5/access-drift/pull/98), [#109](https://github.com/dataschool-proj2-team5/access-drift/pull/109), [#110](https://github.com/dataschool-proj2-team5/access-drift/pull/110), [#116](https://github.com/dataschool-proj2-team5/access-drift/pull/116)

### 3.9 리뷰로 발견·지적한 문제와 AI 안전성 QA

- **#13:** `accesses_asset` edge의 `evidence_source`를 실제 변환 입력과 대조해 `bronze_access_edges_seed`로 바로잡았다. 계약 경로의 PoC 종속성도 수정했다. 본인 작성 수정 commit 2개가 확인된다.
- **#17:** verify notebook이 기존 파이프라인을 다시 실행해 데이터를 변경하는 부작용을 지적하고 read-only 검증으로 분리하도록 요청했다. `insertInto`의 컬럼 순서 의존에 따른 잘못된 필드 저장 위험도 지적했다. 위험 지적을 실제 오염 발생 건수로 표현하지 않는다.
- **#82:** NHI 7건이 credential 활성 조건으로 모두 같은 finding type이 되는 현상과 risk case key 계약 불일치를 질문했다. 미병합 PR이며 해당 댓글만으로 최종 수정 효과를 확정하지 않는다.
- **#113:** 실제 배포 환경 테스트 결과를 댓글로 남겼다. 본인 commit은 main 충돌 해소이며 RAG chain 전체 구현이 아니다.
- **#114:** 정상 조치·근거 질문, 인증정보 원문 요청, 관리자 사칭/정책 무시 요청의 실제 응답을 남기고, 명시적 거절 문구와 안전한 대체 안내를 요청했다.
- **#117:** 팀원 PR 본문은 DE QA 피드백 반영을 명시한다. 그러나 안전 프롬프트는 팀원 commit `84f69fb2c4`에 이미 있고, 본인 commit `ff35d4eda6`의 `rag_agent.py` diff는 LLM endpoint 환경변수 우선 지원이다. 따라서 **안전성 QA·개선 요청**과 **안전 프롬프트 코드 최초 작성**을 구분해야 한다. commit 제목만으로 본인 프롬프트 구현이라고 결론 내리지 않는다.

**근거:** [#13](https://github.com/dataschool-proj2-team5/access-drift/pull/13), [#17](https://github.com/dataschool-proj2-team5/access-drift/pull/17), [#82](https://github.com/dataschool-proj2-team5/access-drift/pull/82), [#113](https://github.com/dataschool-proj2-team5/access-drift/pull/113), [#114](https://github.com/dataschool-proj2-team5/access-drift/pull/114), [#117](https://github.com/dataschool-proj2-team5/access-drift/pull/117)

### 3.10 거버넌스·협업·발표

- #97에서 App/RAG/Gold 조회 경계, Eval 분리, 인증값 저장 금지 원칙을 ADR로 기록했다. **실제 least-privilege grant 적용은 후속 범위**이며 PAT 소유자 권한과 실행 principal 분리 문제를 명시했다.
- #18에서 PO/DE/DS 이슈 템플릿을 추가했다. AGENTS/PR 템플릿의 초기 도입은 본인 initial commit에 나타나지만 이번 PR 49건과 별도 이력이다. 템플릿 덕분에 오류가 발견됐다는 인과 효과는 리뷰 사례만으로 확정하지 않는다.
- #23/#32에서 작업 지침과 문서 진입점을 정리했다.
- #119/#120/#121에서 DE 발표, 아키텍처 설명, README, PDF 링크를 정리하고 추적 문서의 실제 팀 이메일을 예시로 대체했다. PDF 이미지 내부 OCR 검사는 당시 수행하지 않았다.

**근거:** [#97](https://github.com/dataschool-proj2-team5/access-drift/pull/97), [#18](https://github.com/dataschool-proj2-team5/access-drift/pull/18), [#121](https://github.com/dataschool-proj2-team5/access-drift/pull/121), [UC ADR](../adr/0003-uc-app-eval-access-boundary.md)

## 4. 본인 전체 구현으로 귀속하면 안 되는 영역

| 영역 | 선행/주 구현 PR 작성자 | 본인 기여와 구분 |
| --- | --- | --- |
| DLT spike·초기 expectation | Kihun-N: #21, #61, #84 | 본인은 #59 환경, #75/#96 보강, #108 audit, #111 writer 전환 |
| Bronze contract CI·DLT smoke 자동화 | Kihun-N: #74 | CI 전체를 본인 구현으로 표현하지 않음 |
| SQL 운영 Dashboard 쿼리·문서 | Kihun-N: #93 | 본인은 DE 발표·파이프라인 검산·데이터 준비와 구분 |
| Intermediate/Gold 탐지·view | moses415-cell: #17, #62, #95, #115 | 본인은 입력 모델·계약·리뷰·마이그레이션 뼈대·표시 연결 |
| Gold/secret/eval 검증 SQL | danakim1004au-prog: #19, #20 | 본인의 L/B/S·재처리 검증 SQL과 구분 |
| 대시보드 최초 구축 | ShinDuck: #81, #106, #118 | 본인은 상태 저장·배포·런타임·표시 보강 |
| Vector Search/RAG chain·Agent | danakim1004au-prog: #113, #114, #117 | 본인은 #79 corpus/적재, 배포 QA·안전성 피드백·환경 연동 |

## 5. 수치 사용 기준

| 수치 | 출처·범위 | 사용 시 제한 |
| --- | --- | --- |
| 본인 PR 49 / 병합 45 | 조사 이전 전체 PR | 팀 성과·생산성 지표 아님 |
| Bronze 입력 테이블 16 | #84/#111 | 실제 외부 시스템 16개 수집 아님 |
| GitHub owner edge 5건 | #89 원격 검증 | 합성 데이터의 관계 보강 결과 |
| RAG chunk 12 / 중복 0 | #79 적재 검증 | 문서 수·검색 정확도와 다름 |
| state 1 / event 2 | #88 상태 2회 변경 | 감사 쓰기 확인, 트랜잭션 보장 아님 |
| Gold 22 / 접근 시각 22개 | #111 | 팀 downstream 확인, 본인 탐지 정확도 아님 |
| HI 이메일 10 / loader 22 | #116 | 표시 매핑 검사 |

이번 조사에서는 오류 주입 37건 전체 탐지, 검색 정확도 개선률, 실데이터 처리량, 시간 단축률, 비용 절감률을 개인 KPI로 확정하지 않았다. 이를 쓰려면 fixture별 오류 건수와 실제 expectation 결과를 별도로 대조해야 한다.

## 6. 이 정리가 맞는지 검증하는 방법

1. **누락 확인:** `gh pr list --repo dataschool-proj2-team5/access-drift --state all --limit 1000 --json number,author,state` 결과를 아래 전수 목록과 비교한다. 이 문서 추가 PR은 조사 이후 건이므로 79건에 포함되지 않는다.
2. **귀속 확인:** `gh pr view <번호> --repo dataschool-proj2-team5/access-drift --json author,commits,files,body,comments,reviews`로 작성자와 실제 수정 파일을 대조한다. merge/conflict commit만 있으면 최초 구현자로 분류하지 않는다.
3. **내용 확인:** `gh pr diff <번호> --repo dataschool-proj2-team5/access-drift` 또는 `git show <commit> -- <path>`로 대표 주장과 코드 변경이 일치하는지 확인한다. 특히 #79, #89, #111, #117은 우선 확인한다.
4. **성과 확인:** PR의 원격 run ID·출력·query를 원래 Databricks 실행 로그와 대조한다. 단순히 PR 작성자가 성공이라고 적었다는 것과 독립 재검증은 다르다. 현재 데이터로 재실행하면 결과가 달라질 수 있다.
5. **공동 작업 확인:** #61/#74/#84/#93/#113 구현자에게 역할 구분을 확인받는다. PR 작성자, 아이디어 제안자, 코드 작성자, 테스트 수행자를 별도로 확인한다.
6. **배경 확인:** 대화가 필요하면 해당 PR 작업 날짜와 핵심어로 JSONL의 실제 user/assistant 메시지만 확인한다. 현재 채팅의 재인용과 과거 assistant의 추정을 원래 증거로 사용하지 않는다.
7. **비밀정보·링크 확인:** 문서에 인증값/개인 연락처가 없는지 확인하고 상대 링크와 PR 링크가 올바른 번호를 가리키는지 확인한다. PR/대화 원문을 저장소에 통째로 추가하지 않는다.

## 7. 전체 PR 전수 목록

아래 목록은 PR 단위 기록이다. `본인 작성`, `수정 커밋`, `피드백` 표시는 기여 근거의 종류이며 구현량 순위가 아니다. 병합 충돌 해소 commit도 수정 커밋에 포함되므로 상세 절에서 범위를 좁혀 해석한다.

| PR | 제목 | 작성자 | 상태 | 본인 근거 |
| --- | --- | --- | --- | --- |
| [#1](https://github.com/dataschool-proj2-team5/access-drift/pull/1) | docs: add expansion design references | danakim1004au-prog | 병합 | 피드백 |
| [#2](https://github.com/dataschool-proj2-team5/access-drift/pull/2) | feat: POC 인프라 초안 구성 | Pexy99 | 병합 | 본인 작성 · 피드백 |
| [#3](https://github.com/dataschool-proj2-team5/access-drift/pull/3) | refactor(infra): ADLS 컨테이너 단일화 및 bootstrap az-cli 인증 적용 | Pexy99 | 미병합 종료 | 본인 작성 |
| [#4](https://github.com/dataschool-proj2-team5/access-drift/pull/4) | refactor(infra): ADLS 컨테이너 단일화 및 bootstrap az-cli 인증 적용 | Pexy99 | 병합 | 본인 작성 · 피드백 |
| [#5](https://github.com/dataschool-proj2-team5/access-drift/pull/5) | docs: add PoC baseline documents | Pexy99 | 병합 | 본인 작성 |
| [#6](https://github.com/dataschool-proj2-team5/access-drift/pull/6) | test: add tiny smoke test | Kihun-N | 미병합 종료 | 확인된 본인 근거 없음 |
| [#7](https://github.com/dataschool-proj2-team5/access-drift/pull/7) | feat(notebooks): PoC Bronze/Silver/Eval 파이프라인 노트북 구성 | Pexy99 | 병합 | 본인 작성 |
| [#13](https://github.com/dataschool-proj2-team5/access-drift/pull/13) | docs: align Bronze/Silver contract references | Kihun-N | 병합 | 수정 커밋 · 피드백 |
| [#14](https://github.com/dataschool-proj2-team5/access-drift/pull/14) | docs: add DS silver join query samples | Kihun-N | 병합 | 확인된 본인 근거 없음 |
| [#15](https://github.com/dataschool-proj2-team5/access-drift/pull/15) | feat: intermediate gold 스키마 마이그레이션 추가 | Pexy99 | 병합 | 본인 작성 |
| [#17](https://github.com/dataschool-proj2-team5/access-drift/pull/17) | feat: add Gold Core pipeline | moses415-cell | 병합 | 수정 커밋 · 피드백 |
| [#18](https://github.com/dataschool-proj2-team5/access-drift/pull/18) | docs: 팀별 이슈 템플릿 추가 | Pexy99 | 병합 | 본인 작성 |
| [#19](https://github.com/dataschool-proj2-team5/access-drift/pull/19) | [#11] Gold 키/근거추적/재실행 검증 SQL + PoC 검증 가이드 문서 | danakim1004au-prog | 병합 | 피드백 |
| [#20](https://github.com/dataschool-proj2-team5/access-drift/pull/20) | [#12] Secret 미저장 + 최소 eval 검증 SQL | danakim1004au-prog | 병합 | 확인된 본인 근거 없음 |
| [#21](https://github.com/dataschool-proj2-team5/access-drift/pull/21) | feat: add DLT quality check spike for silver_principals | Kihun-N | 병합 | 확인된 본인 근거 없음 |
| [#22](https://github.com/dataschool-proj2-team5/access-drift/pull/22) | docs: PoC 완료 결과 정리 | Pexy99 | 병합 | 본인 작성 |
| [#23](https://github.com/dataschool-proj2-team5/access-drift/pull/23) | docs: 커밋 메시지 요약 한국어 작성 규칙 추가 | Pexy99 | 병합 | 본인 작성 |
| [#25](https://github.com/dataschool-proj2-team5/access-drift/pull/25) | [DE][S] 데이터 계약 변경 프로세스 정리 | Kihun-N | 병합 | 확인된 본인 근거 없음 |
| [#26](https://github.com/dataschool-proj2-team5/access-drift/pull/26) | docs: S1 기준 문서 작성 | Pexy99 | 병합 | 본인 작성 · 피드백 |
| [#28](https://github.com/dataschool-proj2-team5/access-drift/pull/28) | feat: demo/dev bundle target 분리 및 catalog 변수화 | Pexy99 | 병합 | 본인 작성 · 피드백 |
| [#30](https://github.com/dataschool-proj2-team5/access-drift/pull/30) | [DE][P0] Databricks PoC/dev 실행 환경 분리 | Pexy99 | 병합 | 본인 작성 |
| [#32](https://github.com/dataschool-proj2-team5/access-drift/pull/32) | [DE][P1] 저장소 문서 진입점 및 구조 정리 | Pexy99 | 병합 | 본인 작성 |
| [#39](https://github.com/dataschool-proj2-team5/access-drift/pull/39) | docs: Landing/Bronze/Silver 스키마 계약 정리 | Pexy99 | 병합 | 본인 작성 |
| [#42](https://github.com/dataschool-proj2-team5/access-drift/pull/42) | feat: 대표 데모 Landing fixture 추가 | Kihun-N | 병합 | 수정 커밋 |
| [#43](https://github.com/dataschool-proj2-team5/access-drift/pull/43) | docs: dev 데이터 저장 기준 정리 | Pexy99 | 병합 | 본인 작성 |
| [#44](https://github.com/dataschool-proj2-team5/access-drift/pull/44) | [DE][P0] Faker 기반 Landing 샘플 생성 spike | Kihun-N | 병합 | 피드백 |
| [#45](https://github.com/dataschool-proj2-team5/access-drift/pull/45) | feat: LBS 적재 파이프라인 dev 경로 정리 | Pexy99 | 병합 | 본인 작성 |
| [#46](https://github.com/dataschool-proj2-team5/access-drift/pull/46) | feat: dev 합성 데이터 생성기 추가 | Pexy99 | 병합 | 본인 작성 |
| [#48](https://github.com/dataschool-proj2-team5/access-drift/pull/48) | docs: Risk Card context 계약 정리 | Pexy99 | 병합 | 본인 작성 |
| [#50](https://github.com/dataschool-proj2-team5/access-drift/pull/50) | [DE][P1] Bronze/Silver 품질검증 기준 정리 | Kihun-N | 병합 | 수정 커밋 |
| [#51](https://github.com/dataschool-proj2-team5/access-drift/pull/51) | feat: Risk Card context generator 적용 | Pexy99 | 병합 | 본인 작성 |
| [#52](https://github.com/dataschool-proj2-team5/access-drift/pull/52) | feat: 최소 Action State 계약 추가 | Pexy99 | 병합 | 본인 작성 |
| [#53](https://github.com/dataschool-proj2-team5/access-drift/pull/53) | chore: worktree 디렉터리 gitignore 추가 | Pexy99 | 병합 | 본인 작성 |
| [#59](https://github.com/dataschool-proj2-team5/access-drift/pull/59) | chore: dlt test 스키마 infra 반영 | Pexy99 | 병합 | 본인 작성 |
| [#60](https://github.com/dataschool-proj2-team5/access-drift/pull/60) | feat: Databricks task 실행 흐름 정리 | Pexy99 | 병합 | 본인 작성 |
| [#61](https://github.com/dataschool-proj2-team5/access-drift/pull/61) | [DE][P1] Bronze DLT expectation 구현 | Kihun-N | 병합 | 수정 커밋 |
| [#62](https://github.com/dataschool-proj2-team5/access-drift/pull/62) | feat: UI 조회용 Risk Card View 노트북 추가 | moses415-cell | 병합 | 확인된 본인 근거 없음 |
| [#64](https://github.com/dataschool-proj2-team5/access-drift/pull/64) | [DE][P1] 실패/재처리 및 멱등성 기준 정리 | Pexy99 | 병합 | 본인 작성 |
| [#66](https://github.com/dataschool-proj2-team5/access-drift/pull/66) | [DE][P1] Bronze DLT 승격 및 ingest 전환안 검토 | Kihun-N | 병합 | 확인된 본인 근거 없음 |
| [#70](https://github.com/dataschool-proj2-team5/access-drift/pull/70) | [DE][P1] Risk Action Event 감사 로그 테이블 추가 | Pexy99 | 병합 | 본인 작성 |
| [#72](https://github.com/dataschool-proj2-team5/access-drift/pull/72) | [DE][P2] SaaS 합성데이터 시딩 적재 확장 | Pexy99 | 병합 | 본인 작성 |
| [#73](https://github.com/dataschool-proj2-team5/access-drift/pull/73) | test: Databricks smoke check 추가 (CRUD 권한 선결 게이트) | danakim1004au-prog | 미병합 종료 | 확인된 본인 근거 없음 |
| [#74](https://github.com/dataschool-proj2-team5/access-drift/pull/74) | feat: Bronze schema contract + DLT smoke 검증 자동화 | Kihun-N | 병합 | 확인된 본인 근거 없음 |
| [#75](https://github.com/dataschool-proj2-team5/access-drift/pull/75) | feat: identity 표시 이름 Silver 적재 확장 | Pexy99 | 병합 | 본인 작성 |
| [#76](https://github.com/dataschool-proj2-team5/access-drift/pull/76) | test: Databricks smoke check 추가 (CRUD 권한 선결 게이트) | danakim1004au-prog | 병합 | 확인된 본인 근거 없음 |
| [#78](https://github.com/dataschool-proj2-team5/access-drift/pull/78) | [DE][P1] Silver DLT expectation 구현 | Kihun-N | 미병합 종료 | 확인된 본인 근거 없음 |
| [#79](https://github.com/dataschool-proj2-team5/access-drift/pull/79) | [DE][P2] RAG 근거 chunk 기준 정리 | Pexy99 | 병합 | 본인 작성 |
| [#80](https://github.com/dataschool-proj2-team5/access-drift/pull/80) | [DE][P2] GitHub/Google Workspace/Slack 합성 데이터 Silver 적재 확장 | Pexy99 | 병합 | 본인 작성 |
| [#81](https://github.com/dataschool-proj2-team5/access-drift/pull/81) | Streamlit 기반 Access Drift 대시보드 구현 | ShinDuck | 병합 | 수정 커밋 |
| [#82](https://github.com/dataschool-proj2-team5/access-drift/pull/82) | feat: finding type 및 view 메타데이터 반영 | moses415-cell | 미병합 종료 | 피드백 |
| [#84](https://github.com/dataschool-proj2-team5/access-drift/pull/84) | [DE][P1] Silver DLT expectation 구현 | Kihun-N | 병합 | 확인된 본인 근거 없음 |
| [#87](https://github.com/dataschool-proj2-team5/access-drift/pull/87) | feat: 합성데이터 표시 이름 한글화 | Pexy99 | 병합 | 본인 작성 |
| [#88](https://github.com/dataschool-proj2-team5/access-drift/pull/88) | [APP][P1] Streamlit Action State/Event 연동 | Pexy99 | 병합 | 본인 작성 |
| [#89](https://github.com/dataschool-proj2-team5/access-drift/pull/89) | fix: GitHub owner Silver edge 보강 | Pexy99 | 병합 | 본인 작성 |
| [#93](https://github.com/dataschool-proj2-team5/access-drift/pull/93) | [DE][P2] Databricks SQL Dashboard / Alerts 최소 관측 구성 | Kihun-N | 병합 | 확인된 본인 근거 없음 |
| [#94](https://github.com/dataschool-proj2-team5/access-drift/pull/94) | [APP][P1] Databricks Apps 대시보드 자동 CD 구성 | Pexy99 | 병합 | 본인 작성 |
| [#95](https://github.com/dataschool-proj2-team5/access-drift/pull/95) | feat: SaaS finding type 탐지 및 view 메타데이터 반영 | moses415-cell | 병합 | 확인된 본인 근거 없음 |
| [#96](https://github.com/dataschool-proj2-team5/access-drift/pull/96) | feat: silver edge 마지막 사용 시각 추가 | Pexy99 | 병합 | 본인 작성 |
| [#97](https://github.com/dataschool-proj2-team5/access-drift/pull/97) | docs: UC App/Eval 접근 경계 정리 | Pexy99 | 병합 | 본인 작성 |
| [#98](https://github.com/dataschool-proj2-team5/access-drift/pull/98) | fix: Databricks Apps 대시보드 런타임 오류 수정 | Pexy99 | 병합 | 본인 작성 |
| [#99](https://github.com/dataschool-proj2-team5/access-drift/pull/99) | fix: SaaS access edge 마지막 사용 시각 보존 | Pexy99 | 미병합 종료 | 본인 작성 · 피드백 |
| [#100](https://github.com/dataschool-proj2-team5/access-drift/pull/100) | fix: SaaS access edge 마지막 사용 시각 보존 | Pexy99 | 병합 | 본인 작성 |
| [#101](https://github.com/dataschool-proj2-team5/access-drift/pull/101) | docs: 재처리 멱등성과 Landing 보존 결정 기록 | Pexy99 | 병합 | 본인 작성 |
| [#106](https://github.com/dataschool-proj2-team5/access-drift/pull/106) | Access Drift 대시보드 기능 추가 | ShinDuck | 병합 | 수정 커밋 |
| [#107](https://github.com/dataschool-proj2-team5/access-drift/pull/107) | fix: 원격 권장 조치 탭 렌더링 보정 | Pexy99 | 미병합 종료 | 본인 작성 · 피드백 |
| [#108](https://github.com/dataschool-proj2-team5/access-drift/pull/108) | fix: Silver identity 품질 검증 보강 | Pexy99 | 병합 | 본인 작성 |
| [#109](https://github.com/dataschool-proj2-team5/access-drift/pull/109) | fix: 대시보드 Jira 환경 변수 설정 지원 | Pexy99 | 병합 | 본인 작성 |
| [#110](https://github.com/dataschool-proj2-team5/access-drift/pull/110) | fix: 대시보드 최신 접근 시각 매핑 | Pexy99 | 병합 | 본인 작성 |
| [#111](https://github.com/dataschool-proj2-team5/access-drift/pull/111) | feat: Bronze/Silver DLT writer 전환 | Pexy99 | 병합 | 본인 작성 |
| [#112](https://github.com/dataschool-proj2-team5/access-drift/pull/112) | fix: 워크스페이스 환경 라벨 정리 | Pexy99 | 미병합 종료 | 본인 작성 · 피드백 |
| [#113](https://github.com/dataschool-proj2-team5/access-drift/pull/113) | feat: add Databricks RAG chain with Azure OpenAI | danakim1004au-prog | 병합 | 수정 커밋 · 피드백 |
| [#114](https://github.com/dataschool-proj2-team5/access-drift/pull/114) | feat: add RAG AI Agent to dashboard | danakim1004au-prog | 병합 | 피드백 |
| [#115](https://github.com/dataschool-proj2-team5/access-drift/pull/115) | feat: HI 이메일 view 컬럼 추가 | moses415-cell | 병합 | 확인된 본인 근거 없음 |
| [#116](https://github.com/dataschool-proj2-team5/access-drift/pull/116) | fix: 대시보드 표시값 정리 | Pexy99 | 병합 | 본인 작성 |
| [#117](https://github.com/dataschool-proj2-team5/access-drift/pull/117) | feat: add RAG AI Agent to dashboard | danakim1004au-prog | 병합 | 수정 커밋 |
| [#118](https://github.com/dataschool-proj2-team5/access-drift/pull/118) | 대시보드 Risk Card 권장조치 UI 수정 | ShinDuck | 병합 | 확인된 본인 근거 없음 |
| [#119](https://github.com/dataschool-proj2-team5/access-drift/pull/119) | docs: DE 발표자료 초안 정리 | Pexy99 | 병합 | 본인 작성 |
| [#120](https://github.com/dataschool-proj2-team5/access-drift/pull/120) | docs: 아키텍처 오버뷰 최신화 | Pexy99 | 병합 | 본인 작성 |
| [#121](https://github.com/dataschool-proj2-team5/access-drift/pull/121) | docs: 발표자료와 프로젝트 README 정리 | Pexy99 | 병합 | 본인 작성 |
