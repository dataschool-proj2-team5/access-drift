#!/usr/bin/env python3
"""Validate the Bronze schema contract markdown against the Bronze DDL."""

from __future__ import annotations

import argparse
import re
import sys
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path


COMMON_SECTION = "공통 컬럼"
TABLE_PREFIX = "bronze_"
DEFAULT_CONTRACT = Path("docs/contracts/bronze-schema.md")
DEFAULT_DDL = Path("sql/databricks/migrations/001_create_bronze_tables.sql")


@dataclass(frozen=True)
class Column:
    name: str
    data_type: str


class ParseError(RuntimeError):
    """Raised when the input file cannot be parsed into a contract shape."""


def _normalize_type(raw_type: str) -> str:
    return raw_type.strip().lower()


def _normalize_column_name(raw_name: str) -> str:
    return raw_name.strip().strip("`")


def _parse_markdown_table(lines: list[str], start_index: int) -> tuple[list[Column], int]:
    rows: list[Column] = []
    index = start_index

    while index < len(lines):
        line = lines[index].strip()
        if not line.startswith("|"):
            break
        if re.fullmatch(r"\|\s*-+\s*(\|\s*-+\s*)+\|?", line):
            index += 1
            continue

        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 2 or cells[0] == "컬럼":
            index += 1
            continue
        rows.append(
            Column(
                name=_normalize_column_name(cells[0]),
                data_type=_normalize_type(cells[1]),
            )
        )
        index += 1

    if not rows:
        raise ParseError("Markdown table rows were not found.")
    return rows, index


def parse_contract_markdown(text: str) -> OrderedDict[str, list[Column]]:
    lines = text.splitlines()
    sections: OrderedDict[str, list[Column]] = OrderedDict()
    index = 0

    while index < len(lines):
        line = lines[index].strip()
        if line.startswith("## "):
            title = line[3:].strip()
            index += 1
            while index < len(lines) and not lines[index].strip().startswith("|"):
                if lines[index].strip().startswith("## "):
                    break
                index += 1

            if index < len(lines) and lines[index].strip().startswith("|"):
                sections[title], index = _parse_markdown_table(lines, index)
                continue
        index += 1

    if COMMON_SECTION not in sections:
        raise ParseError(f"'{COMMON_SECTION}' section was not found in the contract.")

    common_columns = sections[COMMON_SECTION]
    bronze_tables = OrderedDict(
        (
            title,
            [*common_columns, *columns],
        )
        for title, columns in sections.items()
        if title.startswith(TABLE_PREFIX)
    )

    if not bronze_tables:
        raise ParseError("No bronze_* sections were found in the contract.")

    return bronze_tables


def parse_bronze_ddl(text: str) -> OrderedDict[str, list[Column]]:
    pattern = re.compile(
        r"CREATE TABLE IF NOT EXISTS \${catalog}\.\${schema}\.(?P<table>\w+)\s*\((?P<body>.*?)\)\s*USING DELTA;",
        re.DOTALL,
    )
    ddl_tables: OrderedDict[str, list[Column]] = OrderedDict()

    for match in pattern.finditer(text):
        table_name = match.group("table")
        body = match.group("body")
        columns: list[Column] = []
        for raw_line in body.splitlines():
            line = raw_line.strip().rstrip(",")
            if not line or line.startswith("--"):
                continue
            column_match = re.match(r"(?P<name>\w+)\s+(?P<type>\w+)", line)
            if not column_match:
                raise ParseError(
                    f"Could not parse DDL column definition in {table_name}: {raw_line!r}"
                )
            columns.append(
                Column(
                    name=column_match.group("name"),
                    data_type=_normalize_type(column_match.group("type")),
                )
            )

        if not columns:
            raise ParseError(f"No columns were parsed for DDL table {table_name}.")
        ddl_tables[table_name] = columns

    if not ddl_tables:
        raise ParseError("No CREATE TABLE statements were parsed from the DDL.")

    return ddl_tables


def _column_lookup(columns: list[Column]) -> OrderedDict[str, str]:
    return OrderedDict((column.name, column.data_type) for column in columns)


def diff_contract_to_ddl(
    contract_tables: OrderedDict[str, list[Column]],
    ddl_tables: OrderedDict[str, list[Column]],
) -> list[str]:
    diffs: list[str] = []
    contract_names = list(contract_tables.keys())
    ddl_names = list(ddl_tables.keys())

    missing_tables = [name for name in contract_names if name not in ddl_tables]
    extra_tables = [name for name in ddl_names if name not in contract_tables]

    if missing_tables:
        diffs.append(f"Missing tables in DDL: {', '.join(missing_tables)}")
    if extra_tables:
        diffs.append(f"Extra tables in DDL: {', '.join(extra_tables)}")

    for table_name in contract_names:
        if table_name not in ddl_tables:
            continue

        contract_columns = contract_tables[table_name]
        ddl_columns = ddl_tables[table_name]
        contract_lookup = _column_lookup(contract_columns)
        ddl_lookup = _column_lookup(ddl_columns)

        missing_columns = [name for name in contract_lookup if name not in ddl_lookup]
        extra_columns = [name for name in ddl_lookup if name not in contract_lookup]
        type_mismatches = [
            f"{name}: contract={contract_lookup[name]} ddl={ddl_lookup[name]}"
            for name in contract_lookup
            if name in ddl_lookup and contract_lookup[name] != ddl_lookup[name]
        ]

        if missing_columns:
            diffs.append(
                f"{table_name}: missing columns in DDL -> {', '.join(missing_columns)}"
            )
        if extra_columns:
            diffs.append(
                f"{table_name}: extra columns in DDL -> {', '.join(extra_columns)}"
            )
        if type_mismatches:
            diffs.append(
                f"{table_name}: type mismatches -> {', '.join(type_mismatches)}"
            )

        shared_names = [name for name in contract_lookup if name in ddl_lookup]
        contract_order = [name for name in contract_lookup if name in shared_names]
        ddl_order = [name for name in ddl_lookup if name in shared_names]
        if contract_order != ddl_order:
            diffs.append(
                f"{table_name}: column order mismatch -> "
                f"contract={contract_order} ddl={ddl_order}"
            )

    return diffs


def validate_contract(contract_path: Path, ddl_path: Path) -> list[str]:
    contract_tables = parse_contract_markdown(contract_path.read_text(encoding="utf-8"))
    ddl_tables = parse_bronze_ddl(ddl_path.read_text(encoding="utf-8"))
    return diff_contract_to_ddl(contract_tables, ddl_tables)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate the Bronze schema contract markdown against the Bronze DDL."
    )
    parser.add_argument(
        "--contract",
        type=Path,
        default=DEFAULT_CONTRACT,
        help=f"Path to the Bronze contract markdown. Default: {DEFAULT_CONTRACT}",
    )
    parser.add_argument(
        "--ddl",
        type=Path,
        default=DEFAULT_DDL,
        help=f"Path to the Bronze DDL SQL file. Default: {DEFAULT_DDL}",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        diffs = validate_contract(args.contract, args.ddl)
    except (OSError, ParseError) as exc:
        print(f"Bronze contract validation failed: {exc}", file=sys.stderr)
        return 1

    if diffs:
        print("Bronze contract validation failed:")
        for diff in diffs:
            print(f"- {diff}")
        return 1

    print(
        "Bronze contract validation passed: "
        f"{args.contract} matches {args.ddl}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
