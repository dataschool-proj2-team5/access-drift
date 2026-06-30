"""Verify dev Landing and Eval JSONL generated for issue #35."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from generate import (
    DEFAULT_REFERENCE_DATE,
    DEFAULT_SEED,
    LANDING_FILE_PATHS,
    build_eval_records,
    build_landing_records,
    build_case_specs,
    file_checksums,
    parse_reference_date,
    validate_eval_records,
    validate_landing_records,
    write_jsonl,
    write_landing_records,
)


def read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def read_landing_records(landing_root: Path) -> dict[str, list[dict[str, object]]]:
    return {
        group: read_jsonl(landing_root / relative_path)
        for group, relative_path in LANDING_FILE_PATHS.items()
    }


def assert_same_files(left: Path, right: Path) -> None:
    for relative_path in LANDING_FILE_PATHS.values():
        if (left / relative_path).read_bytes() != (right / relative_path).read_bytes():
            raise AssertionError(f"landing file differs: {relative_path.as_posix()}")


def assert_same_eval(left: Path, right: Path) -> None:
    if left.read_bytes() != right.read_bytes():
        raise AssertionError("eval file differs")


def print_summary(landing: dict[str, list[dict[str, object]]], eval_rows: list[dict[str, object]]) -> None:
    for group, rows in landing.items():
        print(f"{group}: rows={len(rows)}")
    positives = sum(1 for row in eval_rows if row["is_planted_risk"])
    normal = sum(1 for row in eval_rows if not row["is_planted_risk"] and not row["is_distractor"])
    distractor = sum(1 for row in eval_rows if row["is_distractor"])
    sensitivities = {}
    for row in landing["assets"]:
        sensitivities[row["sensitivity"]] = sensitivities.get(row["sensitivity"], 0) + 1
    credentials = {}
    for row in landing["password_credentials"]:
        credentials[row["status"]] = credentials.get(row["status"], 0) + 1
    owners = {}
    for row in landing["lifecycle"]:
        owners[row["employmentStatus"]] = owners.get(row["employmentStatus"], 0) + 1
    print(f"eval: rows={len(eval_rows)}, positive={positives}, normal={normal}, distractor={distractor}")
    print(f"sensitivity_distribution={dict(sorted(sensitivities.items()))}")
    print(f"credential_status_distribution={dict(sorted(credentials.items()))}")
    print(f"owner_status_distribution={dict(sorted(owners.items()))}")

    representative = eval_rows[0]
    print("representative_case:")
    print(json.dumps(representative, ensure_ascii=False, sort_keys=True))


def verify_reproducible(
    expected_size: int,
    seed: int,
    reference_date,
    landing_root: Path,
    eval_path: Path,
) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp = Path(temp_dir)
        expected_landing = temp / "landing" / "raw"
        expected_eval = temp / "eval" / "ground_truth_case.jsonl"
        specs = build_case_specs(expected_size, seed, reference_date)
        landing = build_landing_records(specs, reference_date)
        eval_rows = build_eval_records(specs, reference_date)
        write_landing_records(landing, expected_landing)
        write_jsonl(eval_rows, expected_eval)
        assert_same_files(landing_root, expected_landing)
        assert_same_eval(eval_path, expected_eval)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--landing-root", type=Path, required=True)
    parser.add_argument("--eval-path", type=Path, required=True)
    parser.add_argument("--expected-size", type=int, required=True)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--reference-date", type=parse_reference_date, default=DEFAULT_REFERENCE_DATE)
    args = parser.parse_args()

    landing = read_landing_records(args.landing_root)
    eval_rows = read_jsonl(args.eval_path)
    validate_landing_records(landing, args.expected_size, args.reference_date)
    validate_eval_records(eval_rows, landing, args.expected_size)
    verify_reproducible(
        args.expected_size,
        args.seed,
        args.reference_date,
        args.landing_root,
        args.eval_path,
    )

    print("PASS: schemas, references, forbidden fields, timestamps, and eval separation")
    print("PASS: generated files are reproducible for the same seed and size")
    print_summary(landing, eval_rows)

    checksum_paths = [args.landing_root / path for path in LANDING_FILE_PATHS.values()]
    checksum_paths.append(args.eval_path)
    for path, checksum in file_checksums(checksum_paths).items():
        print(f"sha256 {checksum}  {path}")


if __name__ == "__main__":
    main()
