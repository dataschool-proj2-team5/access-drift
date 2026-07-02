# Dev Synthetic Data Generator

`data/dev/generator`는 dev Landing/Eval/Context JSONL을 재현 가능하게 생성하고 검증하는 실행 도구다. 데이터셋의 케이스 구성과 대표 케이스 설명은 상위 [data/dev/README.md](../README.md)를 기준으로 한다.

## 설치

저장소 공용 Python 환경을 변경하지 않고 전용 venv를 사용한다.

```bash
cd data/dev/generator
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
```

## 생성

기본 출력 위치는 `data/dev/landing/raw`, `data/dev/eval/ground_truth_case.jsonl`, `data/dev/context`다.

```bash
python data/dev/generator/generate.py --size 20 --seed 35
```

옵션:

| 옵션 | 의미 | 기본값 |
| --- | --- | --- |
| `--size` | 생성할 케이스 수. 양의 정수 | 필수 |
| `--seed` | Faker와 deterministic ID 생성 기준 | `35` |
| `--reference-date` | 날짜 계산 기준일 | `2026-06-29` |
| `--landing-output-root` | Landing JSONL 출력 루트 | `data/dev/landing/raw` |
| `--eval-output-path` | Eval JSONL 출력 파일 | `data/dev/eval/ground_truth_case.jsonl` |
| `--context-output-root` | Risk Card context JSONL 출력 루트 | `data/dev/context` |

생성 파일은 Git에 커밋하지 않는다.

## 출력 파일

Landing:

- `azure/applications.jsonl`
- `azure/application_owners.jsonl`
- `azure/password_credentials.jsonl`
- `identity/lifecycle_seed.jsonl`
- `assets/assets_seed.jsonl`
- `access/access_edges_seed.jsonl`
- `github/apps.jsonl`
- `github/credentials.jsonl`
- `github/repos.jsonl`
- `github/access_edges.jsonl`
- `google_workspace/users.jsonl`
- `google_workspace/assets.jsonl`
- `google_workspace/access_edges.jsonl`
- `slack/users.jsonl`
- `slack/channels.jsonl`
- `slack/access_edges.jsonl`

Eval:

- `ground_truth_case.jsonl`

Context:

- `asset_context.jsonl`
- `assignment_routing.jsonl`

## 검증

```bash
python data/dev/generator/verify.py \
  --landing-root data/dev/landing/raw \
  --eval-path data/dev/eval/ground_truth_case.jsonl \
  --context-root data/dev/context \
  --expected-size 20
```

검증 항목:

- Landing/Eval/Context row count
- required field와 JSONL 포맷
- identity lifecycle의 `displayName` 생성과 Bronze/Silver 표시 이름 매핑 가능성
- app owner, credential, access edge, asset 참조 무결성
- raw Landing의 eval label 금지
- secret value, token value, private key value 금지
- GitHub source id는 `gh-` namespace 사용
- Google Workspace source id는 `gws-` namespace 사용
- Slack source id는 `slack-` namespace 사용
- GitHub/Google Workspace/Slack source 내부 참조 무결성
- expired credential의 `lastUsedDateTime <= endDateTime`
- `lastUsedDateTime`은 KST 기준 09~18시 업무시간 범위 안에서 seed 기반으로 재현 가능하게 분산
- application `displayName`, asset `name`에 생성 index suffix 미노출
- eval key가 Landing source id로 추적 가능한지
- `expected_severity = asset sensitivity` 대문자 매핑
- `seed_finding_type`이 허용된 대시보드 대표 라벨 후보에 속하고 20건 이상 생성 시 6개 후보를 모두 포함하는지
- `asset_context.source_asset_id`가 Landing asset과 매칭되는지
- `assignment_routing` source key가 eval key와 매칭되는지
- 동일 seed/size/reference-date 재생성 결과 byte 일치

## 재현성 규칙

- 같은 `seed`, `size`, `reference-date`는 byte 단위로 동일한 파일을 생성한다.
- `20 -> 100 -> 1000`으로 규모를 키워도 앞선 케이스의 source id, eval key, context key, `case_id`는 유지한다.
- GitHub / Google Workspace / Slack 확장 예시는 size와 무관한 고정 source-like 샘플로 생성한다.
- GitHub / Google Workspace / Slack 확장 예시는 첫 20개 NHI eval/context row 뒤에 append하며 기존 row를 변경하지 않는다.

## GitHub / Google Workspace / Slack 확장 예시

확장 예시는 기존 Entra ID 기반 NHI 데이터와 섞이지 않도록 source namespace를 분리한다.

| source | 파일 | 건수 | namespace | Silver 매핑 후보 |
| --- | --- | ---: | --- | --- |
| GitHub | `github/apps.jsonl` | 5 | `gh-app-...` | `silver_principals`, `principal_kind=NHI`, `principal_type=github_app` |
| GitHub | `github/credentials.jsonl` | 5 | `gh-cred-...` | `silver_credentials`, `credential_type=deploy_key` 또는 `pat` |
| GitHub | `github/repos.jsonl` | 5 | `gh-repo-...` | `silver_assets`, `asset_type=repo` |
| GitHub | `github/access_edges.jsonl` | 5 | `gh-...` | `silver_edges`, `relationship=accesses_asset` |
| Google Workspace | `google_workspace/users.jsonl` | 5 | `gws-user-...` | `silver_principals`, `principal_kind=HI`, `principal_type=user` |
| Google Workspace | `google_workspace/assets.jsonl` | 5 | `gws-...` | `silver_assets`, `asset_type=workspace` |
| Google Workspace | `google_workspace/access_edges.jsonl` | 5 | `gws-...` | `silver_edges`, `relationship=accesses_asset` |
| Slack | `slack/users.jsonl` | 5 | `slack-user-...` | `silver_principals`, `principal_kind=HI`, `principal_type=user` |
| Slack | `slack/channels.jsonl` | 5 | `slack-channel-...` | `silver_assets`, `asset_type=slack_channel` |
| Slack | `slack/access_edges.jsonl` | 5 | `slack-...` | `silver_edges`, `relationship=accesses_asset` |

현재 확장 예시는 첫 20개 NHI eval/context 뒤에 append된다. GitHub는 `subject_type=nhi`, `pattern=P2`, `drift_type=nhi_residual_access`로 두고, Google Workspace와 Slack은 `subject_type=hi`, `pattern=P1`, `drift_type=hi_residual_access`로 둔다.

GitHub 케이스의 residual 근거는 `github/apps.jsonl`의 `ownerEmail`, `ownerEmploymentStatus`, `ownerTerminationDate`에 둔다. Google Workspace 케이스의 residual 근거는 `google_workspace/users.jsonl`의 `status`, `employmentStatus`, `terminationDate`에 두고, Slack 케이스의 residual 근거는 `slack/users.jsonl`의 `status`, `employmentStatus`, `terminationDate`에 둔다.

## 분포 규칙

생성기는 전체를 size별로 다시 섞지 않고, 고정된 전역 케이스 순서에서 앞의 N개를 자른다. 따라서 규모를 키워도 기존 케이스의 ID와 라벨은 유지된다.

- `20`건 기준: 사람이 검토할 수 있도록 positive 4건, distractor 12건, normal 4건을 포함한다.
- `20~100` 구간: positive 비율을 높게 유지해 규칙 검증용 positive를 충분히 확보한다.
- `100`건 기준: positive 20건, distractor 60건, normal 20건을 포함한다.
- `100`건 초과: positive는 최대 40건까지만 증가한다.
- `1000`건 기준: positive 40건, distractor 600건, normal 360건을 포함한다.
- `1000`건 초과: positive는 40건으로 고정하고, 추가 row는 distractor:normal을 3:2 비율로 생성한다.

## Databricks 적재

공식 dev 데이터 생성은 Databricks task 기준으로 실행한다.

```bash
databricks bundle run -t dev access-drift-pipeline --only generate_dev_seed_task
```

이 task는 workspace files 아래 `data/dev/landing/raw`, `data/dev/eval`, `data/dev/context`에 JSONL을 생성한다. 이후 `synthetic_data_task`가 Landing seed를 ADLS `raw/dev` 경로로 복사하고, `eval_seed_task`, `context_seed_task`가 각각 UC managed table로 적재한다.

로컬 생성은 generator 개발, 20건 샘플 검수, PR 정적 확인 용도로 사용한다. 생성 파일은 커밋하지 않는다.
