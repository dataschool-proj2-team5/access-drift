**버전:** v0.1

**기준:** 2026년 6월 23일

> 전체 시스템 개요와 의사결정 근거는 `arch-overview` 참조.
> 

> 이 문서는 데이터 레이어 설계 원칙과 테이블 계약을 다룬다.
> 

> 세부 구현 스펙(DLT 코드, DAG 설정, RAG 구성 등)은 PoC 이후 추가 예정.
> 

---

## 1. 데이터 레이어 설계

### 전체 흐름

```
Landing -> Bronze -> Silver -> Intermediate (Graph + Risk Scoring)
                                      \
                                       -> Gold (LLM 조치 보조 포함)
Action state -------------------------/
```

각 단계의 책임:

```
Landing은 source 입력을 보존한다.
Bronze는 source 입력을 원본 데이터로 저장한다.
Silver는 원본 데이터를 공통 모델로 정규화한다.
Intermediate는 공통 모델을 조인해 탐지 결과를 만든다.
Action state는 finding에 대한 검토, 승인, 조치, 검증 상태를 별도로 관리한다.
Gold는 탐지 결과와 Action state를 Risk Card와 dashboard용 데이터로 제공한다.
```

이 문서에서 쓰는 주요 용어:

```
source: 데이터를 가져오는 원천 시스템. 예: Azure, GitHub, Okta
credential: 어떤 주체가 인증에 사용하는 키, 토큰, 인증서 등의 메타데이터
finding: 탐지 룰에 걸린 위험 후보
payload: API 응답이나 파일에 들어 있는 원본 데이터 본문
```

---

### Landing

Landing은 외부 source에서 받은 데이터가 처음 도착하는 경계다.

Landing의 책임은 데이터를 해석하거나 정제하는 것이 아니라, 수집된 입력을 후속 처리 단계로 넘길 수 있게 보존하는 것이다.

Landing에 해당하는 데이터:

```
- API 응답
- export 파일
- source별 원본 파일
```

Landing을 두는 이유:

```
1. 수집과 변환의 책임을 분리한다.
2. 적재 실패 시 원본이 도착했는지 확인할 수 있다.
3. 같은 입력으로 후속 레이어를 재처리할 수 있다.
4. source가 늘어나도 같은 수집 패턴을 유지할 수 있다.
```

---

### Bronze

Bronze는 원본 데이터를 보존하는 레이어다.

Bronze의 목적은 데이터를 분석하기 편하게 만드는 것이 아니다. 나중에 finding이 어떤 원본 데이터에서 나왔는지 추적할 수 있게 하는 것이다.

Bronze에서 중요한 것:

```
- source 식별
- 수집 시각
- 원본 payload
- 원본 위치 또는 참조
- 재처리를 위한 메타데이터
```

Bronze에서 하지 않는 것:

```
- 위험 점수 계산
- severity 판단
- 권장 조치 생성
- 화면 표시용 문장 생성
- secret/token/private key 값 저장
```

Bronze는 source별 구조를 허용한다. source마다 API 응답 구조가 다르기 때문에 이 단계에서 억지로 공통 모델을 만들지 않는다.

합성 데이터도 먼저 source 입력으로 취급한다. API 형태를 모방한 값이든 정책 기반 seed 값이든 Landing/Bronze에 원본 데이터로 보존한 뒤, Silver에서 공통 모델로 정규화한다.

---

### Silver

Silver는 source별 차이를 공통 모델로 정규화하는 레이어다.

Bronze가 source별 구조를 보존한다면, Silver는 source에 종속되지 않는 개념으로 데이터를 재구성한다. 그래야 Azure, GitHub, Okta, AWS 같은 source가 추가되어도 탐지와 Gold 구조가 흔들리지 않는다.

Silver에서는 아직 "위험하다"는 판단을 내리지 않는다. 대신 탐지에 필요한 사실을 일관된 형태로 만든다.

Silver의 역할:

```
1. source마다 다른 identity 표현을 공통화한다.
2. human identity와 non-human identity를 구분한다.
3. credential value가 아니라 credential metadata만 다룬다.
4. 자산의 민감도와 업무 맥락을 탐지에 연결한다.
5. 접근 관계를 source별 컬럼이 아니라 공통 관계로 표현한다.
```

Silver 테이블 계약은 Silver Schema Contract 문서 참조.

---

### Intermediate

Intermediate는 Silver의 사실들을 연결해 탐지 결과를 만드는 레이어다. arch-overview의 Graph + Risk Scoring 단계에 해당한다.

일반적인 메달리온 구조(Bronze/Silver/Gold)와 달리 보안 탐지에서는 Gold 전에 별도 탐지 결과 단계를 분리하는 것이 더 명확하다. 보안 탐지는 단순 집계가 아니라 여러 증거를 연결해 특정 조건을 만족하는 위험 경로를 찾는 작업이기 때문이다.

Intermediate가 답하는 질문:

```
어떤 룰이 어떤 증거 경로를 finding 후보로 만들었는가?
```

Intermediate에 해당하는 데이터:

```
- 룰 실행 결과
- 위험 경로
- 관련 증거 참조
- finding 후보
- detected_at
- first_seen_at / last_seen_at 같은 탐지 관측 시각
```

이렇게 분리하면:

```
1. 탐지 룰과 화면 표현을 분리할 수 있다.
2. 같은 finding을 dashboard, alert, report, LLM draft에서 재사용할 수 있다.
3. 룰이 바뀌어도 원본 보존 구조와 공통 모델을 흔들지 않는다.
4. Gold가 탐지 로직을 과도하게 포함하는 것을 막는다.
```

---

### Action state

Action state는 메달리온 레이어에서 생성되는 데이터가 아니라, finding에 대한 검토, 승인, 조치, 검증 상태를 담는 별도 운영 상태다.

Action state를 분리하는 이유는 source 관측 상태와 대응 상태의 생명주기가 다르기 때문이다. 예를 들어 배치 처리에서는 조치를 완료했더라도 다음 source 수집 전까지 Silver의 source 상태는 아직 active로 남아 있을 수 있다.

Action state의 생성과 갱신 흐름:

```
1. Intermediate finding이 새로 생성되면 Action state 초기 레코드를 자동 생성한다.
   초기 상태는 open 또는 pending_review로 둔다.

2. 이후 보안팀이 UI에서 finding을 검토, 승인, 조치하면 Action state를 갱신한다.
```

생성 트리거는 Intermediate finding이고, 갱신 트리거는 UI/operator다. 이 구조는 review-first 원칙과 맞는다.

Action state에 해당하는 데이터:

```
- 검토 상태
- 승인 상태
- 조치 요청/실행 상태
- 다음 스캔 검증 대기 상태
- 조치 완료 또는 실패 상태
- reviewed_at / executed_at / verified_at 같은 운영 상태 시각
```

---

### Gold

Gold는 사람이 바로 소비할 수 있는 결과를 제공하는 레이어다.

Gold는 탐지 룰을 새로 실행하는 곳이 아니다. Intermediate에서 만들어진 finding과 Action state를 사용자가 이해하고 조치할 수 있는 형태로 정리한다.

Gold는 LLM 조치 보조 텍스트 생성도 포함한다. finding이 Gold에 적재된 시점에 LLM을 호출해 ai_summary, ticket_draft를 생성하고 Gold에 함께 저장한다. 별도 레이어가 아니라 Gold 생성 프로세스의 마지막 단계다.

Gold에 해당하는 데이터:

```
- Risk Card
- dashboard mart
- 팀별/서비스별 요약
- 보고서용 결과
- AI 요약 (ai_summary)
- 티켓 초안 (ticket_draft)
```

Gold의 역할:

```
1. 보안팀이 바로 읽을 수 있는 결과를 제공한다.
2. finding의 이유와 영향을 설명한다.
3. 권장 조치와 우선순위를 제공한다.
4. 화면이나 리포트가 복잡한 조인을 직접 하지 않게 한다.
```

---

## 2. 테이블 계약

| 레이어 | 계약 문서 | 상태 |
| --- | --- | --- |
| Silver | Silver Schema Contract | 완료 |
| Intermediate | intermediate-schema | 작성 예정 (DS팀) |
| Gold | gold-schema | 작성 예정 |
| Action state | action-state-schema | 작성 예정 |