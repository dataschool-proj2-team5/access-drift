# PoC Scope

## 문서 목적

이 문서는 Access Drift PoC에서 어디까지 구현하면 완료로 볼지 정의한다.

PoC의 목표는 완성형 제품 데모가 아니라, 데이터 파이프라인이 입력 데이터에서 Gold 테이블까지 정상 동작하는지 확인하는 것이다.

## PoC 목표

합성 입력 데이터를 사용해 다음 흐름이 end-to-end로 동작하는지 검증한다.

```text
Landing -> Bronze -> Silver -> Intermediate -> Gold
```

PoC 완료 시점에는 팀 공용 Databricks workspace에서 Gold 테이블의 Risk Card용 최소 결과를 조회할 수 있어야 한다.

## 대표 케이스

PoC 대표 케이스는 Azure App Registration 형태의 NHI residual access로 한다.

```text
퇴사자 owner
  -> App Registration / NHI
  -> active credential
  -> high sensitivity asset
```

## 입력 Evidence

PoC 입력 데이터는 다음 evidence를 포함한다.

- NHI: App Registration 또는 service principal 역할의 주체
- Credential metadata: client secret의 key id, 이름, 만료일, 활성 여부
- Owner context: owner 계정과 퇴사 또는 비활성 상태
- Asset context: 접근 가능한 자산과 민감도

실제 secret 값은 포함하지 않는다.

## 완료 기준

PoC는 다음 조건을 만족하면 완료로 본다.

- 합성 source 입력이 Landing 또는 Bronze에 적재된다.
- Bronze 데이터가 Silver 공통 모델로 정규화된다.
- Silver 데이터를 기반으로 Intermediate에서 finding 후보가 생성된다.
- Intermediate 결과가 Gold 테이블로 적재된다.
- Gold 테이블에 최소 1건 이상의 Risk Card용 레코드가 존재한다.
- 위 결과를 팀 공용 Databricks workspace에서 조회할 수 있다.
- Gold 레코드에서 다음 정보를 확인할 수 있다.
  - 어떤 주체 또는 권한이 남아 있는지
  - 어떤 자산에 닿는지
  - 왜 finding으로 판단됐는지
  - 다음 조치가 무엇인지

## 포함 범위

- 합성 데이터 기반 입력
- source 1개
- drift pattern 1개
- Landing/Bronze/Silver/Intermediate/Gold 최소 파이프라인
- 팀 공용 Databricks workspace 내 Gold 테이블 적재 확인
- Gold 결과 조회용 검증 SQL 또는 노트북

## 제외 범위

- 완성형 Streamlit UI
- 실제 SaaS 또는 클라우드 API 연동
- 자동 권한 회수
- Jira/GitHub Issue 자동 생성
- 정교한 ML 기반 위험 점수화
- 전체 권한 정책 구현
- 전체 source 확장
- 운영용 모니터링과 알림

## 확인 방법

PoC 검증은 단순히 잡이 성공했는지만 보지 않는다.

다음 항목을 함께 확인한다.

- 각 레이어에 데이터가 적재됐는지
- 공용 Databricks workspace에서 Gold 결과를 조회할 수 있는지
- 레이어 간 주요 키가 유지되는지
- Gold 레코드가 입력 데이터의 어떤 증거에서 나왔는지 추적 가능한지
- Gold 결과가 Risk Card로 표시 가능한 최소 필드를 갖는지
- 동일 입력을 재실행해도 Gold 결과가 중복 증가하지 않는지

## 다음 단계

PoC에서 Gold 테이블 적재가 확인되면 이후 단계에서 UI, 조치 흐름, source 확장, eval 기반 검증을 별도 범위로 다룬다.
