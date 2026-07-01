#!/usr/bin/env python3
"""Extract a run metadata value from Databricks CLI JSON output."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


KEY_ALIASES = {
    "run_id": {"run_id", "runId"},
    "update_id": {"update_id", "updateId"},
    "pipeline_id": {"pipeline_id", "pipelineId"},
}


def _walk(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from _walk(value)
    elif isinstance(node, list):
        for item in node:
            yield from _walk(item)


def extract_value(payload: object, logical_key: str) -> str:
    aliases = KEY_ALIASES[logical_key]
    for node in _walk(payload):
        for alias in aliases:
            value = node.get(alias) if isinstance(node, dict) else None
            if value not in (None, ""):
                return str(value)
    raise KeyError(f"Could not find {logical_key} in Databricks CLI JSON output.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract run_id or update_id from Databricks CLI JSON output."
    )
    parser.add_argument("json_path", type=Path, help="Path to the JSON file.")
    parser.add_argument(
        "logical_key",
        choices=sorted(KEY_ALIASES),
        help="The logical metadata key to extract.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        payload = json.loads(args.json_path.read_text(encoding="utf-8"))
        print(extract_value(payload, args.logical_key))
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        print(f"Failed to extract {args.logical_key}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
