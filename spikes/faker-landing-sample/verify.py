"""Verify Landing sample integrity and byte-for-byte reproducibility."""

from __future__ import annotations

from copy import deepcopy
import tempfile
from pathlib import Path

from generate import (
    DEFAULT_SEED,
    FILE_PATHS,
    build_records,
    file_checksums,
    generate,
    validate_records,
)


def _assert_same_files(left: Path, right: Path) -> None:
    for relative_path in FILE_PATHS.values():
        if (left / relative_path).read_bytes() != (right / relative_path).read_bytes():
            raise AssertionError(f"file differs: {relative_path.as_posix()}")


def _assert_invalid(records: dict, label: str) -> None:
    try:
        validate_records(records)
    except ValueError:
        print(f"PASS: rejected {label}")
        return
    raise AssertionError(f"validator accepted {label}")


def main() -> None:
    with tempfile.TemporaryDirectory() as first_dir, tempfile.TemporaryDirectory() as second_dir:
        first = Path(first_dir)
        second = Path(second_dir)
        generate(DEFAULT_SEED, first)
        generate(DEFAULT_SEED, second)
        _assert_same_files(first, second)

        print(f"PASS: seed {DEFAULT_SEED} produced identical files twice")
        print("PASS: schemas, formats, references, duplicates, and forbidden fields")

        orphan = deepcopy(build_records(DEFAULT_SEED))
        orphan["access_edges"][0]["assetId"] = "asset-missing"
        _assert_invalid(orphan, "orphan access edge")

        duplicate = deepcopy(build_records(DEFAULT_SEED))
        duplicate["applications"][1]["appId"] = duplicate["applications"][0]["appId"]
        _assert_invalid(duplicate, "duplicate appId")

        forbidden = deepcopy(build_records(DEFAULT_SEED))
        forbidden["applications"][0]["expected_severity"] = "critical"
        _assert_invalid(forbidden, "eval label in Landing")

        for path, checksum in file_checksums(first).items():
            print(f"sha256 {checksum}  {path}")


if __name__ == "__main__":
    main()
