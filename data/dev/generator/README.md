# Dev Synthetic Data Generator

`data/dev/generator`는 dev Landing/Eval JSONL을 재현 가능하게 생성하고 검증하는 실행 도구다. 데이터셋의 케이스 구성과 대표 케이스 설명은 상위 [data/dev/README.md](../README.md)를 기준으로 한다.

## 설치

저장소 공용 Python 환경을 변경하지 않고 전용 venv를 사용한다.

```bash
cd data/dev/generator
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
```

## 생성

기본 출력 위치는 `data/dev/landing/raw`와 `data/dev/eval/ground_truth_case.jsonl`이다.

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

생성 파일은 Git에 커밋하지 않는다.

## 출력 파일

Landing:

- `azure/applications.jsonl`
- `azure/application_owners.jsonl`
- `azure/password_credentials.jsonl`
- `identity/lifecycle_seed.jsonl`
- `assets/assets_seed.jsonl`
- `access/access_edges_seed.jsonl`

Eval:

- `ground_truth_case.jsonl`

## 검증

```bash
python data/dev/generator/verify.py \
  --landing-root data/dev/landing/raw \
  --eval-path data/dev/eval/ground_truth_case.jsonl \
  --expected-size 20
```

검증 항목:

- Landing/Eval row count
- required field와 JSONL 포맷
- app owner, credential, access edge, asset 참조 무결성
- raw Landing의 eval label 금지
- secret value, token value, private key value 금지
- expired credential의 `lastUsedDateTime <= endDateTime`
- application `displayName`, asset `name`에 생성 index suffix 미노출
- eval key가 Landing source id로 추적 가능한지
- `expected_severity = asset sensitivity` 대문자 매핑
- 동일 seed/size/reference-date 재생성 결과 byte 일치

## 재현성 규칙

- 같은 `seed`, `size`, `reference-date`는 byte 단위로 동일한 파일을 생성한다.
- `20 -> 100 -> 1000`으로 규모를 키워도 앞선 케이스의 source id, eval key, `case_id`는 유지한다.

## 분포 규칙

생성기는 전체를 size별로 다시 섞지 않고, 고정된 전역 케이스 순서에서 앞의 N개를 자른다. 따라서 규모를 키워도 기존 케이스의 ID와 라벨은 유지된다.

- `20`건 기준: 사람이 검토할 수 있도록 positive 4건, distractor 12건, normal 4건을 포함한다.
- `20~100` 구간: positive 비율을 높게 유지해 규칙 검증용 positive를 충분히 확보한다.
- `100`건 기준: positive 20건, distractor 60건, normal 20건을 포함한다.
- `100`건 초과: positive는 최대 40건까지만 증가한다.
- `1000`건 기준: positive 40건, distractor 600건, normal 360건을 포함한다.
- `1000`건 초과: positive는 40건으로 고정하고, 추가 row는 distractor:normal을 3:2 비율로 생성한다.

## Databricks 적재

Databricks 적재는 사용자 허가 후 실행한다. 생성 파일을 커밋하지 않고, 로컬 생성 결과를 dev target 입력으로 사용한다.
