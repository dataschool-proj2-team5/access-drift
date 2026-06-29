"""Generate a small, reproducible Landing JSONL sample for issue #41."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date, datetime
from pathlib import Path
from uuid import UUID

from faker import Faker


DEFAULT_SEED = 41
REFERENCE_DATE = date(2026, 6, 29)
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "data" / "dev" / "landing" / "raw"

FILE_PATHS = {
    "applications": Path("azure/applications.jsonl"),
    "application_owners": Path("azure/application_owners.jsonl"),
    "password_credentials": Path("azure/password_credentials.jsonl"),
    "lifecycle": Path("identity/lifecycle_seed.jsonl"),
    "assets": Path("assets/assets_seed.jsonl"),
    "access_edges": Path("access/access_edges_seed.jsonl"),
}

EXPECTED_FIELDS = {
    "applications": {"appId", "displayName", "createdDateTime"},
    "application_owners": {"appId", "userPrincipalName"},
    "password_credentials": {
        "appId",
        "keyId",
        "displayName",
        "endDateTime",
        "status",
    },
    "lifecycle": {"userPrincipalName", "employmentStatus", "terminationDate"},
    "assets": {"assetId", "name", "environment", "sensitivity"},
    "access_edges": {
        "principalId",
        "assetId",
        "relationship",
        "permission",
        "status",
        "lastUsedDateTime",
    },
}

FORBIDDEN_FIELDS = {
    "is_planted_risk",
    "is_distractor",
    "expected_severity",
    "truth_class",
    "secretValue",
    "tokenValue",
    "privateKeyValue",
}

SCENARIOS = (
    {
        "case": "critical",
        "app_id": "41000000-0000-4000-8000-000000000001",
        "key_id": "41000000-0000-4000-9000-000000000001",
        "asset_id": "asset-crm-customer-export-prod",
        "employment_status": "terminated",
        "termination_date": "2026-06-10",
        "credential_status": "active",
        "credential_end": "2027-12-31T00:00:00Z",
        "environment": "production",
        "sensitivity": "critical",
        "permission": "read/list",
    },
    {
        "case": "high",
        "app_id": "41000000-0000-4000-8000-000000000002",
        "key_id": "41000000-0000-4000-9000-000000000002",
        "asset_id": "asset-finance-reporting-prod",
        "employment_status": "active",
        "termination_date": None,
        "credential_status": "active",
        "credential_end": "2027-09-30T00:00:00Z",
        "environment": "production",
        "sensitivity": "high",
        "permission": "read",
    },
    {
        "case": "medium",
        "app_id": "41000000-0000-4000-8000-000000000003",
        "key_id": "41000000-0000-4000-9000-000000000003",
        "asset_id": "asset-operations-dashboard",
        "employment_status": "active",
        "termination_date": None,
        "credential_status": "expired",
        "credential_end": "2025-12-31T00:00:00Z",
        "environment": "staging",
        "sensitivity": "medium",
        "permission": "read",
    },
    {
        "case": "normal",
        "app_id": "41000000-0000-4000-8000-000000000004",
        "key_id": "41000000-0000-4000-9000-000000000004",
        "asset_id": "asset-team-notification-dev",
        "employment_status": "active",
        "termination_date": None,
        "credential_status": "active",
        "credential_end": "2027-06-30T00:00:00Z",
        "environment": "development",
        "sensitivity": "low",
        "permission": "invoke",
    },
    {
        "case": "background-01",
        "app_id": "41000000-0000-4000-8000-000000000005",
        "key_id": "41000000-0000-4000-9000-000000000005",
        "asset_id": "asset-inventory-staging",
        "employment_status": "active",
        "termination_date": None,
        "credential_status": "active",
        "credential_end": "2028-01-31T00:00:00Z",
        "environment": "staging",
        "sensitivity": "medium",
        "permission": "read",
    },
    {
        "case": "background-02",
        "app_id": "41000000-0000-4000-8000-000000000006",
        "key_id": "41000000-0000-4000-9000-000000000006",
        "asset_id": "asset-search-index-dev",
        "employment_status": "active",
        "termination_date": None,
        "credential_status": "expired",
        "credential_end": "2025-08-31T00:00:00Z",
        "environment": "development",
        "sensitivity": "low",
        "permission": "write",
    },
    {
        "case": "background-03",
        "app_id": "41000000-0000-4000-8000-000000000007",
        "key_id": "41000000-0000-4000-9000-000000000007",
        "asset_id": "asset-order-events-prod",
        "employment_status": "terminated",
        "termination_date": "2026-05-15",
        "credential_status": "expired",
        "credential_end": "2026-05-01T00:00:00Z",
        "environment": "production",
        "sensitivity": "high",
        "permission": "consume",
    },
    {
        "case": "background-04",
        "app_id": "41000000-0000-4000-8000-000000000008",
        "key_id": "41000000-0000-4000-9000-000000000008",
        "asset_id": "asset-catalog-preview",
        "employment_status": "active",
        "termination_date": None,
        "credential_status": "active",
        "credential_end": "2027-03-31T00:00:00Z",
        "environment": "development",
        "sensitivity": "low",
        "permission": "read",
    },
)


def _timestamp(value: date) -> str:
    return f"{value.isoformat()}T09:00:00Z"


def build_records(seed: int) -> dict[str, list[dict[str, object]]]:
    fake = Faker("en_US")
    fake.seed_instance(seed)
    records: dict[str, list[dict[str, object]]] = {
        name: [] for name in FILE_PATHS
    }

    for scenario in SCENARIOS:
        case = str(scenario["case"])
        user_name = fake.unique.user_name()
        upn = f"{user_name}@example.com"
        created = fake.date_between(start_date=date(2021, 1, 1), end_date=date(2024, 12, 31))
        last_used = fake.date_between(start_date=date(2025, 1, 1), end_date=date(2026, 6, 1))

        if case == "critical":
            app_name = "sp-crm-customer-export-prod"
            asset_name = "crm-customer-export-prod"
        else:
            app_name = f"sp-{fake.word()}-{scenario['environment']}"
            asset_name = f"{fake.word()}-{scenario['environment']}"

        records["applications"].append(
            {
                "appId": scenario["app_id"],
                "displayName": app_name,
                "createdDateTime": _timestamp(created),
            }
        )
        records["application_owners"].append(
            {"appId": scenario["app_id"], "userPrincipalName": upn}
        )
        records["password_credentials"].append(
            {
                "appId": scenario["app_id"],
                "keyId": scenario["key_id"],
                "displayName": f"{fake.word()}-secret-metadata",
                "endDateTime": scenario["credential_end"],
                "status": scenario["credential_status"],
            }
        )
        records["lifecycle"].append(
            {
                "userPrincipalName": upn,
                "employmentStatus": scenario["employment_status"],
                "terminationDate": scenario["termination_date"],
            }
        )
        records["assets"].append(
            {
                "assetId": scenario["asset_id"],
                "name": asset_name,
                "environment": scenario["environment"],
                "sensitivity": scenario["sensitivity"],
            }
        )
        records["access_edges"].append(
            {
                "principalId": scenario["app_id"],
                "assetId": scenario["asset_id"],
                "relationship": "accesses_asset",
                "permission": scenario["permission"],
                "status": "active",
                "lastUsedDateTime": _timestamp(last_used),
            }
        )

    return records


def _require_unique(values: list[object], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"duplicate {label}")


def _parse_timestamp(value: object, label: str) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a string")
    datetime.fromisoformat(value.replace("Z", "+00:00"))


def validate_records(records: dict[str, list[dict[str, object]]]) -> None:
    if set(records) != set(FILE_PATHS):
        raise ValueError("unexpected record groups")

    expected_count = len(SCENARIOS)
    for group, rows in records.items():
        if len(rows) != expected_count:
            raise ValueError(f"{group} must contain {expected_count} rows")
        for row in rows:
            if set(row).intersection(FORBIDDEN_FIELDS):
                raise ValueError(f"{group} contains a forbidden field")
            if set(row) != EXPECTED_FIELDS[group]:
                raise ValueError(f"{group} has unexpected fields: {set(row)}")
            for field, value in row.items():
                if value is None and field == "terminationDate":
                    continue
                if not isinstance(value, str) or not value:
                    raise ValueError(f"{group}.{field} must be a non-empty string")

    app_ids = [row["appId"] for row in records["applications"]]
    owner_app_ids = [row["appId"] for row in records["application_owners"]]
    credential_app_ids = [row["appId"] for row in records["password_credentials"]]
    principal_ids = [row["principalId"] for row in records["access_edges"]]
    asset_ids = [row["assetId"] for row in records["assets"]]
    edge_asset_ids = [row["assetId"] for row in records["access_edges"]]
    owner_upns = [row["userPrincipalName"] for row in records["application_owners"]]
    lifecycle_upns = [row["userPrincipalName"] for row in records["lifecycle"]]
    key_ids = [row["keyId"] for row in records["password_credentials"]]

    for value in app_ids + key_ids:
        UUID(str(value))

    for values, label in (
        (app_ids, "appId"),
        (key_ids, "keyId"),
        (asset_ids, "assetId"),
        (owner_upns, "userPrincipalName"),
    ):
        _require_unique(values, label)

    if set(owner_app_ids) != set(app_ids):
        raise ValueError("application owner references are incomplete")
    if set(credential_app_ids) != set(app_ids):
        raise ValueError("credential appId references are incomplete")
    if set(principal_ids) != set(app_ids):
        raise ValueError("access principalId references are incomplete")
    if set(edge_asset_ids) != set(asset_ids):
        raise ValueError("access assetId references are incomplete")
    if set(owner_upns) != set(lifecycle_upns):
        raise ValueError("owner lifecycle references are incomplete")

    for row in records["applications"]:
        _parse_timestamp(row["createdDateTime"], "createdDateTime")
    for row in records["password_credentials"]:
        _parse_timestamp(row["endDateTime"], "endDateTime")
        end_date = datetime.fromisoformat(
            str(row["endDateTime"]).replace("Z", "+00:00")
        ).date()
        if row["status"] == "active" and end_date <= REFERENCE_DATE:
            raise ValueError("active credential must end after the reference date")
        if row["status"] == "expired" and end_date > REFERENCE_DATE:
            raise ValueError("expired credential must end by the reference date")
    for row in records["access_edges"]:
        _parse_timestamp(row["lastUsedDateTime"], "lastUsedDateTime")
    for row in records["lifecycle"]:
        termination_date = row["terminationDate"]
        if termination_date is not None:
            date.fromisoformat(str(termination_date))
        if row["employmentStatus"] == "terminated" and termination_date is None:
            raise ValueError("terminated owner must have a terminationDate")
        if row["employmentStatus"] == "active" and termination_date is not None:
            raise ValueError("active owner must not have a terminationDate")

    credential_statuses = {row["status"] for row in records["password_credentials"]}
    employment_statuses = {row["employmentStatus"] for row in records["lifecycle"]}
    sensitivities = {row["sensitivity"] for row in records["assets"]}
    if credential_statuses != {"active", "expired"}:
        raise ValueError("active and expired credentials are required")
    if employment_statuses != {"active", "terminated"}:
        raise ValueError("active and terminated owners are required")
    if sensitivities != {"critical", "high", "medium", "low"}:
        raise ValueError("critical, high, medium, and low assets are required")

    owners_by_app = {
        row["appId"]: row for row in records["application_owners"]
    }
    lifecycle_by_upn = {
        row["userPrincipalName"]: row for row in records["lifecycle"]
    }
    credentials_by_app = {
        row["appId"]: row for row in records["password_credentials"]
    }
    assets_by_id = {row["assetId"]: row for row in records["assets"]}
    edges_by_app = {
        row["principalId"]: row for row in records["access_edges"]
    }
    expected_core = {
        "critical": ("terminated", "active", "critical"),
        "high": ("active", "active", "high"),
        "medium": ("active", "expired", "medium"),
        "normal": ("active", "active", "low"),
    }
    for scenario in SCENARIOS[:4]:
        app_id = scenario["app_id"]
        owner = owners_by_app[app_id]
        lifecycle = lifecycle_by_upn[owner["userPrincipalName"]]
        credential = credentials_by_app[app_id]
        edge = edges_by_app[app_id]
        asset = assets_by_id[edge["assetId"]]
        actual = (
            lifecycle["employmentStatus"],
            credential["status"],
            asset["sensitivity"],
        )
        if actual != expected_core[scenario["case"]]:
            raise ValueError(f"{scenario['case']} scenario combination is broken")


def write_records(records: dict[str, list[dict[str, object]]], output_root: Path) -> None:
    for group, relative_path in FILE_PATHS.items():
        path = output_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        content = "".join(
            json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n"
            for row in records[group]
        )
        path.write_bytes(content.encode("utf-8"))


def file_checksums(output_root: Path) -> dict[str, str]:
    return {
        relative_path.as_posix(): hashlib.sha256(
            (output_root / relative_path).read_bytes()
        ).hexdigest()
        for relative_path in FILE_PATHS.values()
    }


def generate(seed: int, output_root: Path) -> dict[str, list[dict[str, object]]]:
    records = build_records(seed)
    validate_records(records)
    write_records(records, output_root)
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    args = parser.parse_args()

    records = generate(args.seed, args.output_root)
    print(f"seed={args.seed}")
    for group, rows in records.items():
        print(f"{group}: rows={len(rows)}")
    for path, checksum in file_checksums(args.output_root).items():
        print(f"sha256 {checksum}  {path}")


if __name__ == "__main__":
    main()
