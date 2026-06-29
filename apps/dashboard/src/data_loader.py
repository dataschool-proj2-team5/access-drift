from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.mock_data import generate_mock_access_drift_data
from src.schema import DATE_COLUMNS, EXPECTED_COLUMNS, get_missing_columns


DEFAULT_DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "sample_access_drift.csv"


@dataclass(frozen=True)
class DataLoadResult:
    data: pd.DataFrame
    using_mock: bool
    source_path: Path
    missing_columns: list[str]


def load_access_drift_data(path: str | Path | None = None) -> DataLoadResult:
    source_path = Path(path) if path else DEFAULT_DATA_PATH

    if source_path.exists():
        raw_data = pd.read_csv(source_path)
        using_mock = False
    else:
        raw_data = generate_mock_access_drift_data()
        using_mock = True

    normalized = normalize_to_internal_schema(raw_data)
    missing_columns = get_missing_columns(raw_data.columns.tolist())

    return DataLoadResult(
        data=normalized,
        using_mock=using_mock,
        source_path=source_path,
        missing_columns=missing_columns,
    )


def normalize_to_internal_schema(data: pd.DataFrame) -> pd.DataFrame:
    # TODO: Map final CSV/DB/Gold Layer column names to this internal schema once
    # the source contract is confirmed. Keep UI pages dependent on internal names.
    normalized = data.copy()

    for column in EXPECTED_COLUMNS:
        if column not in normalized.columns:
            normalized[column] = None

    normalized = normalized[EXPECTED_COLUMNS]

    for column in DATE_COLUMNS:
        normalized[column] = pd.to_datetime(normalized[column], errors="coerce")

    normalized["risk_score"] = pd.to_numeric(normalized["risk_score"], errors="coerce").fillna(0)

    return normalized
