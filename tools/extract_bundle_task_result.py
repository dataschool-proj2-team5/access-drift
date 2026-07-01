#!/usr/bin/env python3
"""Extract the first task result string from `databricks bundle run -o json` output."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def extract_result(payload: object) -> str:
    if not isinstance(payload, dict):
        raise ValueError("Bundle run JSON root must be an object.")

    task_outputs = payload.get("task_outputs")
    if not isinstance(task_outputs, list) or not task_outputs:
        raise ValueError("task_outputs is missing or empty.")

    first_task = task_outputs[0]
    if not isinstance(first_task, dict):
        raise ValueError("task_outputs[0] is not an object.")

    output = first_task.get("Output")
    if not isinstance(output, dict):
        raise ValueError("task_outputs[0].Output is missing.")

    result = output.get("result")
    if not isinstance(result, str) or not result:
        raise ValueError("task_outputs[0].Output.result is missing.")

    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract task result from Databricks bundle run JSON output."
    )
    parser.add_argument("json_path", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        payload = json.loads(args.json_path.read_text(encoding="utf-8"))
        print(extract_result(payload))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Failed to extract bundle task result: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
