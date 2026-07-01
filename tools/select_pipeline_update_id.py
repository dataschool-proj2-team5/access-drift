#!/usr/bin/env python3
"""Select the newest pipeline update_id from list-updates output."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _load_payload(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _collect_updates(payload: object) -> list[dict]:
    if isinstance(payload, dict):
        if isinstance(payload.get("updates"), list):
            return [item for item in payload["updates"] if isinstance(item, dict)]
        if isinstance(payload.get("items"), list):
            return [item for item in payload["items"] if isinstance(item, dict)]
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    raise ValueError("Unsupported list-updates JSON shape.")


def _read_excludes(paths: list[Path]) -> set[str]:
    excludes: set[str] = set()
    for path in paths:
        value = path.read_text(encoding="utf-8").strip()
        if value:
            excludes.add(value)
    return excludes


def _timestamp_value(update: dict) -> tuple[int, str]:
    for key in ("creation_time", "created_time", "start_time", "timestamp"):
        value = update.get(key)
        if isinstance(value, (int, float)):
            return int(value), key
        if isinstance(value, str) and value.strip():
            return 0, value
    return 0, ""


def _pick_update_id(updates: list[dict], excludes: set[str]) -> str:
    ranked_updates = sorted(updates, key=_timestamp_value, reverse=True)
    for update in ranked_updates:
        update_id = update.get("update_id") or update.get("updateId")
        if isinstance(update_id, str) and update_id and update_id not in excludes:
            return update_id
    raise KeyError("Could not find a new update_id in pipeline updates output.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Select the newest non-excluded update_id from pipelines list-updates JSON."
    )
    parser.add_argument("json_path", type=Path)
    parser.add_argument(
        "--exclude-file",
        action="append",
        default=[],
        type=Path,
        help="File containing an update_id to exclude. Can be repeated.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        payload = _load_payload(args.json_path)
        updates = _collect_updates(payload)
        excludes = _read_excludes(args.exclude_file)
        print(_pick_update_id(updates, excludes))
    except (OSError, json.JSONDecodeError, ValueError, KeyError) as exc:
        print(f"Failed to select update_id: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
