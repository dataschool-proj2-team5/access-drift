#!/usr/bin/env python3
"""Compare before/after Bronze snapshot outputs captured from Databricks notebooks."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _load_notebook_result(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    task_outputs = payload.get("task_outputs")
    if isinstance(task_outputs, list) and task_outputs:
        output = task_outputs[0].get("Output") if isinstance(task_outputs[0], dict) else None
        if isinstance(output, dict) and output.get("result"):
            return json.loads(output["result"])
    notebook_output = payload.get("notebook_output") or {}
    result = notebook_output.get("result")
    if not result:
        raise ValueError(f"Notebook output result is missing in {path}.")
    return json.loads(result)


def compare_snapshots(before_path: Path, after_path: Path) -> list[str]:
    before = _load_notebook_result(before_path)
    after = _load_notebook_result(after_path)
    differences: list[str] = []

    before_tables = before.get("tables", {})
    after_tables = after.get("tables", {})
    if before_tables != after_tables:
        differences.append(
            "Bronze table snapshot changed: "
            f"before={json.dumps(before_tables, sort_keys=True)} "
            f"after={json.dumps(after_tables, sort_keys=True)}"
        )
    return differences


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare Bronze snapshot notebook outputs."
    )
    parser.add_argument("before_path", type=Path)
    parser.add_argument("after_path", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        differences = compare_snapshots(args.before_path, args.after_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Bronze snapshot comparison failed: {exc}", file=sys.stderr)
        return 1

    if differences:
        for difference in differences:
            print(difference, file=sys.stderr)
        return 1

    print("Bronze snapshot comparison passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
