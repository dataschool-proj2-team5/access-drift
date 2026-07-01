from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE_PATH = REPO_ROOT / "tools" / "validate_bronze_contract.py"
SPEC = importlib.util.spec_from_file_location("validate_bronze_contract", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


MATCHING_CONTRACT = """# Bronze Schema Contract

## 공통 컬럼

| 컬럼 | 타입 | 필수 |
| --- | --- | --- |
| _src_system | string | yes |
| _raw_payload | string | yes |

## bronze_example

| 컬럼 | 타입 | 필수 |
| --- | --- | --- |
| app_id | string | no |
| created_at | timestamp | no |
"""

MATCHING_DDL = """CREATE TABLE IF NOT EXISTS ${catalog}.${schema}.bronze_example (
  _src_system STRING NOT NULL,
  _raw_payload STRING NOT NULL,
  app_id STRING,
  created_at TIMESTAMP
)
USING DELTA;
"""


class ValidateBronzeContractTests(unittest.TestCase):
    def write_temp_file(self, directory: Path, name: str, contents: str) -> Path:
        path = directory / name
        path.write_text(contents, encoding="utf-8")
        return path

    def test_actual_contract_and_ddl_match(self) -> None:
        diffs = MODULE.validate_contract(
            REPO_ROOT / "docs" / "contracts" / "bronze-schema.md",
            REPO_ROOT / "sql" / "databricks" / "migrations" / "001_create_bronze_tables.sql",
        )
        self.assertEqual(diffs, [])

    def test_matching_fixture_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            contract_path = self.write_temp_file(directory, "contract.md", MATCHING_CONTRACT)
            ddl_path = self.write_temp_file(directory, "ddl.sql", MATCHING_DDL)

            diffs = MODULE.validate_contract(contract_path, ddl_path)

        self.assertEqual(diffs, [])

    def test_missing_column_is_reported(self) -> None:
        ddl = MATCHING_DDL.replace("  created_at TIMESTAMP\n", "")
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            contract_path = self.write_temp_file(directory, "contract.md", MATCHING_CONTRACT)
            ddl_path = self.write_temp_file(directory, "ddl.sql", ddl)

            diffs = MODULE.validate_contract(contract_path, ddl_path)

        self.assertIn("bronze_example: missing columns in DDL -> created_at", diffs)

    def test_extra_column_is_reported(self) -> None:
        ddl = MATCHING_DDL.replace(
            "  created_at TIMESTAMP\n",
            "  created_at TIMESTAMP,\n  unexpected STRING\n",
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            contract_path = self.write_temp_file(directory, "contract.md", MATCHING_CONTRACT)
            ddl_path = self.write_temp_file(directory, "ddl.sql", ddl)

            diffs = MODULE.validate_contract(contract_path, ddl_path)

        self.assertIn("bronze_example: extra columns in DDL -> unexpected", diffs)

    def test_type_mismatch_is_reported(self) -> None:
        ddl = MATCHING_DDL.replace("created_at TIMESTAMP", "created_at DATE")
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            contract_path = self.write_temp_file(directory, "contract.md", MATCHING_CONTRACT)
            ddl_path = self.write_temp_file(directory, "ddl.sql", ddl)

            diffs = MODULE.validate_contract(contract_path, ddl_path)

        self.assertIn(
            "bronze_example: type mismatches -> created_at: contract=timestamp ddl=date",
            diffs,
        )

    def test_missing_bronze_sections_raise_parse_error(self) -> None:
        with self.assertRaises(MODULE.ParseError):
            MODULE.parse_contract_markdown(
                """## 공통 컬럼

| 컬럼 | 타입 | 필수 |
| --- | --- | --- |
| _src_system | string | yes |
"""
            )


if __name__ == "__main__":
    unittest.main()
