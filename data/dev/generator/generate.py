"""Generate reproducible dev Landing and Eval JSONL data for issue #35."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable

from faker import Faker


DEFAULT_SEED = 35
DEFAULT_REFERENCE_DATE = date(2026, 6, 29)
DEFAULT_OUTPUT_ROOT = Path("data/dev")
SCENARIO_FAMILY = "azure_app_registration_nhi_residual_access"
DRIFT_TYPE = "nhi_residual_access"

LANDING_FILE_PATHS = {
    "applications": Path("azure/applications.jsonl"),
    "application_owners": Path("azure/application_owners.jsonl"),
    "password_credentials": Path("azure/password_credentials.jsonl"),
    "lifecycle": Path("identity/lifecycle_seed.jsonl"),
    "assets": Path("assets/assets_seed.jsonl"),
    "access_edges": Path("access/access_edges_seed.jsonl"),
}

CONTEXT_FILE_PATHS = {
    "asset_context": Path("asset_context.jsonl"),
    "assignment_routing": Path("assignment_routing.jsonl"),
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

CONTEXT_EXPECTED_FIELDS = {
    "asset_context": {
        "source_asset_id",
        "data_scope_label",
        "sensitive_data_examples",
        "sensitivity_reason",
    },
    "assignment_routing": {
        "subject_type",
        "subject_id",
        "asset_id",
        "drift_type",
        "assignee_name",
        "assignee_team",
        "routing_reason",
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
GENERATED_SUFFIX_PATTERN = re.compile(r"-\d{4}$")

DISTRACTOR_TYPES = (
    "owner_active",
    "credential_expired",
    "access_inactive",
    "asset_low_dev",
)
DISTRACTOR_SERVICE_SLUGS = {
    "owner_active": (
        "customer-profile-export",
        "customer-order-export",
        "loyalty-segment-export",
    ),
    "credential_expired": (
        "refund-report-export",
        "seller-settlement-export",
        "finance-ledger-export",
    ),
    "access_inactive": (
        "marketing-segment-export",
        "support-case-export",
        "crm-audience-export",
    ),
    "asset_low_dev": (
        "team-notification",
        "catalog-preview",
        "qa-dashboard",
    ),
}


@dataclass(frozen=True)
class CaseSpec:
    index: int
    case_kind: str
    app_id: str
    key_id: str
    owner_upn: str
    asset_id: str
    app_name: str
    asset_name: str
    credential_name: str
    app_created_at: str | None
    employment_status: str
    termination_date: str | None
    credential_status: str
    credential_end: str
    environment: str
    sensitivity: str
    permission: str
    is_planted_risk: bool
    is_distractor: bool
    distractor_type: str | None


def _iso_ts(value: date) -> str:
    return f"{value.isoformat()}T09:00:00Z"


def _parse_date(value: str) -> date:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).date()


def _stable_uuid(seed: int, label: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"access-drift:{seed}:{label}"))


def _expected_severity(sensitivity: str) -> str:
    return sensitivity.upper()


def _service_name(slug: str, environment: str) -> str:
    suffix_by_env = {
        "production": "prod",
        "staging": "staging",
        "development": "dev",
    }
    suffix = suffix_by_env[environment]
    if slug.endswith(f"-{suffix}"):
        return slug
    return f"{slug}-{suffix}"


def _secret_name(environment: str) -> str:
    suffix_by_env = {
        "production": "prod",
        "staging": "staging",
        "development": "dev",
    }
    return f"{suffix_by_env[environment]}-secret"


def _case_kind_for_index(index: int) -> str:
    if 2 <= index <= 4:
        return "positive"
    if index == 1:
        return "positive"
    if 5 <= index <= 16:
        return "distractor"
    if 17 <= index <= 20:
        return "normal"
    if 21 <= index <= 36:
        return "positive"
    if 37 <= index <= 84:
        return "distractor"
    if 101 <= index <= 120:
        return "positive"
    if 121 <= index <= 660:
        return "distractor"
    if index > 1000:
        # After the 1,000-row validation target, positive is capped at 40.
        # Additional rows keep a simple 3:2 distractor/normal ratio.
        return "distractor" if (index - 1001) % 5 < 3 else "normal"
    return "normal"


def expected_counts_for_size(size: int) -> dict[str, int]:
    counts = {"positive": 0, "distractor": 0, "normal": 0}
    for index in range(1, size + 1):
        counts[_case_kind_for_index(index)] += 1
    return counts


def _distractor_type_for_index(index: int) -> str:
    if index < 5:
        raise ValueError("distractor index must be >= 5")
    return DISTRACTOR_TYPES[(index - 5) % len(DISTRACTOR_TYPES)]


def _distractor_service_slug(index: int, distractor_type: str) -> str:
    options = DISTRACTOR_SERVICE_SLUGS[distractor_type]
    occurrence = (index - 5) // len(DISTRACTOR_TYPES)
    return options[occurrence % len(options)]


def _positive_spec(seed: int, index: int, fake: Faker, reference_date: date) -> CaseSpec:
    if index == 1:
        return CaseSpec(
            index=index,
            case_kind="positive",
            app_id="d8f4a5b6-7c8d-4e91-9f02-1a2b3c4d5e6f",
            key_id="c0ffee12-3456-7890-abcd-1234567890ab",
            owner_upn="kim.minsu@company.com",
            asset_id="asset-customer-export-storage-prod",
            app_name="sp-crm-customer-export-prod",
            asset_name="customer-export-storage-prod",
            credential_name="prod-secret",
            app_created_at="2026-03-15T09:00:00Z",
            employment_status="terminated",
            termination_date="2026-06-10",
            credential_status="active",
            credential_end="2027-12-31T00:00:00Z",
            environment="production",
            sensitivity="critical",
            permission="read/list",
            is_planted_risk=True,
            is_distractor=False,
            distractor_type=None,
        )

    sensitivity_cycle = ("critical", "high", "medium")
    sensitivity = sensitivity_cycle[(index - 2) % len(sensitivity_cycle)]
    env = "production" if sensitivity in {"critical", "high"} else "staging"
    asset_slug = {
        "critical": "customer-profile-export",
        "high": "finance-reporting",
        "medium": "operations-dashboard",
    }[sensitivity]
    owner = f"{fake.unique.user_name()}@company.com"
    termination = reference_date - timedelta(days=15 + index)
    credential_end = reference_date + timedelta(days=180 + index)

    return CaseSpec(
        index=index,
        case_kind="positive",
        app_id=_stable_uuid(seed, f"app-positive-{index}"),
        key_id=_stable_uuid(seed, f"credential-positive-{index}"),
        owner_upn=owner,
        asset_id=f"asset-{asset_slug}-{index:04d}",
        app_name=_service_name(asset_slug, env),
        asset_name=_service_name(asset_slug, env),
        credential_name=_secret_name(env),
        app_created_at=None,
        employment_status="terminated",
        termination_date=termination.isoformat(),
        credential_status="active",
        credential_end=f"{credential_end.isoformat()}T00:00:00Z",
        environment=env,
        sensitivity=sensitivity,
        permission="read/list" if sensitivity == "critical" else "read",
        is_planted_risk=True,
        is_distractor=False,
        distractor_type=None,
    )


def _base_negative_spec(seed: int, index: int, fake: Faker, reference_date: date) -> dict[str, object]:
    owner = f"{fake.unique.user_name()}@company.com"
    asset_id = f"asset-customer-profile-export-{index:04d}"
    return {
        "index": index,
        "case_kind": "distractor",
        "app_id": _stable_uuid(seed, f"app-negative-{index}"),
        "key_id": _stable_uuid(seed, f"credential-negative-{index}"),
        "owner_upn": owner,
        "asset_id": asset_id,
        "app_name": "customer-profile-export-prod",
        "asset_name": "customer-profile-export-prod",
        "credential_name": "prod-secret",
        "app_created_at": None,
        "employment_status": "terminated",
        "termination_date": (reference_date - timedelta(days=15 + index)).isoformat(),
        "credential_status": "active",
        "credential_end": f"{(reference_date + timedelta(days=180 + index)).isoformat()}T00:00:00Z",
        "environment": "production",
        "sensitivity": "critical",
        "permission": "read/list",
    }


def _distractor_spec(
    seed: int,
    index: int,
    distractor_type: str,
    fake: Faker,
    reference_date: date,
) -> CaseSpec:
    values = _base_negative_spec(seed, index, fake, reference_date)
    asset_slug = _distractor_service_slug(index, distractor_type)
    env = "development" if distractor_type == "asset_low_dev" else "production"
    asset_id = f"asset-{asset_slug}-{index:04d}"
    service_name = _service_name(asset_slug, env)
    values["asset_id"] = asset_id
    values["app_name"] = service_name
    values["asset_name"] = service_name
    values["credential_name"] = _secret_name(env)
    values["environment"] = env

    if distractor_type == "owner_active":
        values["employment_status"] = "active"
        values["termination_date"] = None
    elif distractor_type == "credential_expired":
        end_date = reference_date - timedelta(days=20 + index)
        values["credential_status"] = "expired"
        values["credential_end"] = f"{end_date.isoformat()}T00:00:00Z"
    elif distractor_type == "access_inactive":
        values["permission"] = "read/list"
    elif distractor_type == "asset_low_dev":
        values["sensitivity"] = "low"
        values["permission"] = "read"
    else:
        raise ValueError(f"unknown distractor_type: {distractor_type}")

    return CaseSpec(
        **values,
        is_planted_risk=False,
        is_distractor=True,
        distractor_type=distractor_type,
    )


def _normal_spec(seed: int, index: int, fake: Faker, reference_date: date) -> CaseSpec:
    variant = index % 4
    owner = f"{fake.unique.user_name()}@company.com"

    if variant == 0:
        employment_status = "active"
        termination_date = None
        credential_status = "active"
        credential_end_date = reference_date + timedelta(days=90 + index)
        sensitivity = "low"
        env = "development"
        permission = "read"
        asset_slug = "team-notification-dev"
    elif variant == 1:
        employment_status = "active"
        termination_date = None
        credential_status = "expired"
        credential_end_date = reference_date - timedelta(days=30 + index)
        sensitivity = "medium"
        env = "staging"
        permission = "read"
        asset_slug = "operations-dashboard"
    elif variant == 2:
        employment_status = "active"
        termination_date = None
        credential_status = "expired"
        credential_end_date = reference_date - timedelta(days=10 + index)
        sensitivity = "high"
        env = "production"
        permission = "consume"
        asset_slug = "order-events-prod"
    else:
        employment_status = "active"
        termination_date = None
        credential_status = "active"
        credential_end_date = reference_date + timedelta(days=120 + index)
        sensitivity = "low"
        env = "development"
        permission = "invoke"
        asset_slug = "catalog-preview"

    asset_id = f"asset-{asset_slug}-{index:04d}"
    return CaseSpec(
        index=index,
        case_kind="normal",
        app_id=_stable_uuid(seed, f"app-normal-{index}"),
        key_id=_stable_uuid(seed, f"credential-normal-{index}"),
        owner_upn=owner,
        asset_id=asset_id,
        app_name=_service_name(asset_slug, env),
        asset_name=_service_name(asset_slug, env),
        credential_name=_secret_name(env),
        app_created_at=None,
        employment_status=employment_status,
        termination_date=termination_date,
        credential_status=credential_status,
        credential_end=f"{credential_end_date.isoformat()}T00:00:00Z",
        environment=env,
        sensitivity=sensitivity,
        permission=permission,
        is_planted_risk=False,
        is_distractor=False,
        distractor_type=None,
    )


def build_case_specs(size: int, seed: int, reference_date: date) -> list[CaseSpec]:
    if size <= 0:
        raise ValueError("size must be a positive integer")

    fake = Faker("en_US")
    fake.seed_instance(seed)
    specs: list[CaseSpec] = []

    for index in range(1, size + 1):
        kind = _case_kind_for_index(index)
        if kind == "positive":
            specs.append(_positive_spec(seed, index, fake, reference_date))
        elif kind == "distractor":
            distractor_type = _distractor_type_for_index(index)
            specs.append(_distractor_spec(seed, index, distractor_type, fake, reference_date))
        else:
            specs.append(_normal_spec(seed, index, fake, reference_date))

    return specs


def build_landing_records(
    specs: Iterable[CaseSpec], reference_date: date
) -> dict[str, list[dict[str, object]]]:
    records: dict[str, list[dict[str, object]]] = {
        name: [] for name in LANDING_FILE_PATHS
    }

    for spec in specs:
        created = reference_date - timedelta(days=365 + spec.index)
        credential_end = _parse_date(spec.credential_end)
        if spec.credential_status == "expired":
            last_used = credential_end - timedelta(days=7)
        else:
            last_used = reference_date - timedelta(days=(spec.index % 180) + 1)

        records["applications"].append(
            {
                "appId": spec.app_id,
                "displayName": spec.app_name,
                "createdDateTime": spec.app_created_at or _iso_ts(created),
            }
        )
        records["application_owners"].append(
            {"appId": spec.app_id, "userPrincipalName": spec.owner_upn}
        )
        records["password_credentials"].append(
            {
                "appId": spec.app_id,
                "keyId": spec.key_id,
                "displayName": spec.credential_name,
                "endDateTime": spec.credential_end,
                "status": spec.credential_status,
            }
        )
        records["lifecycle"].append(
            {
                "userPrincipalName": spec.owner_upn,
                "employmentStatus": spec.employment_status,
                "terminationDate": spec.termination_date,
            }
        )
        records["assets"].append(
            {
                "assetId": spec.asset_id,
                "name": spec.asset_name,
                "environment": spec.environment,
                "sensitivity": spec.sensitivity,
            }
        )
        edge_status = "inactive" if spec.distractor_type == "access_inactive" else "active"
        records["access_edges"].append(
            {
                "principalId": spec.app_id,
                "assetId": spec.asset_id,
                "relationship": "accesses_asset",
                "permission": spec.permission,
                "status": edge_status,
                "lastUsedDateTime": _iso_ts(last_used),
            }
        )

    return records


def build_eval_records(
    specs: Iterable[CaseSpec], reference_date: date
) -> list[dict[str, object]]:
    created_at = f"{reference_date.isoformat()}T00:00:00Z"
    rows: list[dict[str, object]] = []
    for spec in specs:
        case_id = f"eval-nhi-{spec.index:03d}"
        scenario_id = f"scenario-nhi-{spec.index:03d}"
        if spec.is_planted_risk:
            reason = (
                f"{spec.owner_upn}는 퇴사 상태이고, {spec.app_name}에는 active "
                f"credential metadata가 남아 있으며, 해당 NHI가 {spec.asset_name}에 접근할 수 있다."
            )
        elif spec.is_distractor:
            reason = (
                f"{spec.app_name}은 NHI residual access positive와 유사하지만 "
                f"{spec.distractor_type} 조건만 깨져 정답은 false인 distractor다."
            )
        else:
            reason = (
                f"{spec.app_name}은 NHI residual access positive 조건 조합을 "
                f"만족하지 않는 normal 샘플이다."
            )
        rows.append(
            {
                "case_id": case_id,
                "scenario_id": scenario_id,
                "scenario_family": SCENARIO_FAMILY,
                "subject_type": "nhi",
                "subject_id": spec.app_id,
                "asset_id": spec.asset_id,
                "drift_type": DRIFT_TYPE,
                "is_planted_risk": spec.is_planted_risk,
                "is_distractor": spec.is_distractor,
                "pattern": "P2",
                "expected_severity": _expected_severity(spec.sensitivity),
                "label_reason": reason,
                "created_at": created_at,
            }
        )
    return rows


def _asset_context_for_spec(spec: CaseSpec) -> dict[str, object]:
    if spec.asset_id == "asset-customer-export-storage-prod":
        return {
            "source_asset_id": spec.asset_id,
            "data_scope_label": "고객 DB",
            "sensitive_data_examples": ["고객 이름", "전화번호", "배송지", "주문내역"],
            "sensitivity_reason": "고객 식별 정보와 배송지/주문내역을 포함하는 export storage",
        }

    asset_key = spec.asset_id.removeprefix("asset-")
    context_by_pattern = (
        (
            ("customer-profile", "customer-order", "crm-audience", "loyalty-segment"),
            (
                "고객 CRM 데이터",
                ["고객 식별 정보", "고객 세그먼트", "주문/프로필 속성"],
                "고객 식별 정보와 CRM 세그먼트/프로필 속성을 포함하는 export 자산",
            ),
        ),
        (
            ("refund-report",),
            (
                "환불/결제 운영 데이터",
                ["환불 금액", "환불 상태", "PG 거래 식별자"],
                "결제·환불 처리와 거래 식별자를 포함하는 운영 자산",
            ),
        ),
        (
            ("seller-settlement",),
            (
                "판매자 정산 데이터",
                ["판매자 ID", "정산 금액", "수수료", "지급 상태"],
                "판매자 정산과 회계 원장 정보를 포함하는 재무 자산",
            ),
        ),
        (
            ("finance-ledger",),
            (
                "재무 원장 데이터",
                ["회계 계정", "거래 금액", "정산 원장"],
                "회계 처리와 정산 원장 정보를 포함하는 재무 자산",
            ),
        ),
        (
            ("finance-reporting",),
            (
                "재무 리포팅 데이터",
                ["일별 매출", "환불 금액", "순매출"],
                "전사 매출과 정산 리포팅에 사용되는 핵심 비즈니스 자산",
            ),
        ),
        (
            ("marketing-segment",),
            (
                "마케팅 세그먼트 데이터",
                ["세그먼트 유형", "관심 카테고리", "캠페인 대상 조건"],
                "고객 세그먼트와 캠페인 대상 조건을 포함하는 마케팅 자산",
            ),
        ),
        (
            ("support-case",),
            (
                "고객지원 케이스 데이터",
                ["문의 유형", "처리 상태", "고객 연락처 참조"],
                "고객 문의와 지원 처리 이력을 포함하는 운영 자산",
            ),
        ),
        (
            ("order-events",),
            (
                "주문 이벤트 데이터",
                ["주문 이벤트", "주문 상태", "처리 시각"],
                "주문 처리 흐름과 이벤트를 포함하는 핵심 비즈니스 자산",
            ),
        ),
    )
    for prefixes, context in context_by_pattern:
        if asset_key.startswith(prefixes):
            label, examples, reason = context
            return {
                "source_asset_id": spec.asset_id,
                "data_scope_label": label,
                "sensitive_data_examples": examples,
                "sensitivity_reason": reason,
            }

    context_by_sensitivity = {
        "medium": (
            "내부 운영 데이터",
            ["비식별 운영 지표", "스테이징 업무 정보"],
            "사내 업무상 공유되지만 외부 공개 대상은 아닌 내부 운영 자산",
        ),
        "low": (
            "비민감 개발 데이터",
            ["개발 알림", "프리뷰 설정", "QA 대시보드"],
            "민감 자산 taxonomy에 직접 매핑하지 않는 normal/distractor용 non-sensitive 자산",
        ),
    }
    label, examples, reason = context_by_sensitivity[spec.sensitivity]
    return {
        "source_asset_id": spec.asset_id,
        "data_scope_label": label,
        "sensitive_data_examples": examples,
        "sensitivity_reason": reason,
    }


def _assignment_routing_for_spec(spec: CaseSpec) -> dict[str, object]:
    asset_key = spec.asset_id.removeprefix("asset-")
    team_by_pattern = (
        (("customer", "crm", "loyalty"), ("이다영", "CRM 데이터 운영팀")),
        (("refund", "seller-settlement"), ("한지민", "정산 플랫폼팀")),
        (("finance",), ("박서준", "재무 데이터팀")),
        (("marketing",), ("오세훈", "마케팅 데이터팀")),
        (("support",), ("김하나", "고객지원 데이터팀")),
        (("order-events",), ("박서준", "비즈니스 플랫폼팀")),
        (("operations",), ("최하은", "운영 데이터팀")),
        (("team-notification", "catalog-preview", "qa-dashboard"), ("정우진", "개발 플랫폼팀")),
    )
    assignee_name = "최하은"
    assignee_team = "운영 데이터팀"
    for prefixes, assignee in team_by_pattern:
        if asset_key.startswith(prefixes):
            assignee_name, assignee_team = assignee
            break
    reason = (
        f"{spec.app_name}와 {spec.asset_name}의 운영 책임 팀"
        if spec.index == 1
        else ""
    )
    return {
        "subject_type": "nhi",
        "subject_id": spec.app_id,
        "asset_id": spec.asset_id,
        "drift_type": DRIFT_TYPE,
        "assignee_name": assignee_name,
        "assignee_team": assignee_team,
        "routing_reason": reason,
    }


def build_context_records(specs: Iterable[CaseSpec]) -> dict[str, list[dict[str, object]]]:
    spec_list = list(specs)
    return {
        "asset_context": [_asset_context_for_spec(spec) for spec in spec_list],
        "assignment_routing": [_assignment_routing_for_spec(spec) for spec in spec_list],
    }


def _validate_timestamp(value: object, label: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")
    datetime.fromisoformat(value.replace("Z", "+00:00"))


def validate_landing_records(
    records: dict[str, list[dict[str, object]]],
    expected_size: int,
    reference_date: date,
) -> None:
    if set(records) != set(LANDING_FILE_PATHS):
        raise ValueError("unexpected landing record groups")

    for group, rows in records.items():
        if len(rows) != expected_size:
            raise ValueError(f"{group} expected {expected_size}, got {len(rows)}")
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

    apps = {row["appId"]: row for row in records["applications"]}
    owners = {row["appId"]: row for row in records["application_owners"]}
    credentials = {row["appId"]: row for row in records["password_credentials"]}
    lifecycle = {row["userPrincipalName"]: row for row in records["lifecycle"]}
    assets = {row["assetId"]: row for row in records["assets"]}
    edges = {row["principalId"]: row for row in records["access_edges"]}

    if len(apps) != expected_size:
        raise ValueError("duplicate appId")
    if len({row["keyId"] for row in records["password_credentials"]}) != expected_size:
        raise ValueError("duplicate keyId")
    if len(assets) != expected_size:
        raise ValueError("duplicate assetId")
    if len(lifecycle) != expected_size:
        raise ValueError("duplicate userPrincipalName")

    if set(owners) != set(apps):
        raise ValueError("owner app references do not match applications")
    if set(credentials) != set(apps):
        raise ValueError("credential app references do not match applications")
    if set(edges) != set(apps):
        raise ValueError("access edge principal references do not match applications")
    if {row["assetId"] for row in records["access_edges"]} != set(assets):
        raise ValueError("access edge asset references do not match assets")
    if {row["userPrincipalName"] for row in records["application_owners"]} != set(lifecycle):
        raise ValueError("owner lifecycle references do not match")

    for app_id in apps:
        owner = owners[app_id]
        owner_state = lifecycle[owner["userPrincipalName"]]
        credential = credentials[app_id]
        edge = edges[app_id]
        asset = assets[edge["assetId"]]

        uuid.UUID(str(app_id))
        uuid.UUID(str(credential["keyId"]))
        _validate_timestamp(apps[app_id]["createdDateTime"], "createdDateTime")
        _validate_timestamp(credential["endDateTime"], "endDateTime")
        _validate_timestamp(edge["lastUsedDateTime"], "lastUsedDateTime")

        credential_end = _parse_date(str(credential["endDateTime"]))
        last_used = _parse_date(str(edge["lastUsedDateTime"]))
        if credential["status"] == "active" and credential_end <= reference_date:
            raise ValueError("active credential must end after reference date")
        if credential["status"] == "expired" and credential_end > reference_date:
            raise ValueError("expired credential must end by reference date")
        if credential["status"] == "expired" and last_used > credential_end:
            raise ValueError("expired credential lastUsedDateTime must not exceed endDateTime")

        if owner_state["employmentStatus"] == "terminated" and owner_state["terminationDate"] is None:
            raise ValueError("terminated owner must have a terminationDate")
        if owner_state["employmentStatus"] == "active" and owner_state["terminationDate"] is not None:
            raise ValueError("active owner must not have a terminationDate")
        if owner_state["terminationDate"] is not None:
            date.fromisoformat(str(owner_state["terminationDate"]))

        for label, value in (
            ("application displayName", apps[app_id]["displayName"]),
            ("credential displayName", credential["displayName"]),
            ("asset name", asset["name"]),
        ):
            if GENERATED_SUFFIX_PATTERN.search(str(value)):
                raise ValueError(f"{label} must not expose generated index suffix")


def validate_eval_records(
    eval_rows: list[dict[str, object]],
    landing_records: dict[str, list[dict[str, object]]],
    expected_size: int,
) -> None:
    if len(eval_rows) != expected_size:
        raise ValueError(f"eval expected {expected_size}, got {len(eval_rows)}")

    app_ids = {row["appId"] for row in landing_records["applications"]}
    asset_by_id = {row["assetId"]: row for row in landing_records["assets"]}
    required = {
        "case_id",
        "scenario_id",
        "scenario_family",
        "subject_type",
        "subject_id",
        "asset_id",
        "drift_type",
        "is_planted_risk",
        "is_distractor",
        "pattern",
        "expected_severity",
        "label_reason",
        "created_at",
    }
    seen_case_ids: set[object] = set()
    positives = 0
    distractors = 0
    for row in eval_rows:
        if set(row) != required:
            raise ValueError(f"eval row has unexpected fields: {set(row)}")
        if row["case_id"] in seen_case_ids:
            raise ValueError("duplicate eval case_id")
        seen_case_ids.add(row["case_id"])
        if row["subject_type"] != "nhi":
            raise ValueError("eval subject_type must be nhi")
        if row["subject_id"] not in app_ids:
            raise ValueError("eval subject_id does not match application appId")
        if row["asset_id"] not in asset_by_id:
            raise ValueError("eval asset_id does not match asset seed")
        if row["drift_type"] != DRIFT_TYPE:
            raise ValueError("eval drift_type mismatch")
        if row["is_distractor"] is True:
            distractors += 1
        if row["is_planted_risk"] is True:
            positives += 1
        asset = asset_by_id[row["asset_id"]]
        if row["expected_severity"] != _expected_severity(str(asset["sensitivity"])):
            raise ValueError("expected_severity must match asset sensitivity uppercase")
        _validate_timestamp(row["created_at"], "created_at")

    mix = expected_counts_for_size(expected_size)
    if positives != mix["positive"]:
        raise ValueError("unexpected positive eval count")
    if distractors != mix["distractor"]:
        raise ValueError("unexpected distractor eval count")


def validate_context_records(
    context_records: dict[str, list[dict[str, object]]],
    landing_records: dict[str, list[dict[str, object]]],
    eval_rows: list[dict[str, object]],
    expected_size: int,
) -> None:
    if set(context_records) != set(CONTEXT_FILE_PATHS):
        raise ValueError("unexpected context record groups")

    for group, rows in context_records.items():
        if len(rows) != expected_size:
            raise ValueError(f"{group} expected {expected_size}, got {len(rows)}")
        for row in rows:
            if set(row).intersection(FORBIDDEN_FIELDS):
                raise ValueError(f"{group} contains a forbidden field")
            if set(row) != CONTEXT_EXPECTED_FIELDS[group]:
                raise ValueError(f"{group} has unexpected fields: {set(row)}")

    asset_ids = {row["assetId"] for row in landing_records["assets"]}
    app_ids = {row["appId"] for row in landing_records["applications"]}
    eval_keys = {
        (row["subject_type"], row["subject_id"], row["asset_id"], row["drift_type"])
        for row in eval_rows
    }

    asset_context_ids = [row["source_asset_id"] for row in context_records["asset_context"]]
    if len(set(asset_context_ids)) != expected_size:
        raise ValueError("duplicate asset_context.source_asset_id")
    if set(asset_context_ids) != asset_ids:
        raise ValueError("asset_context source_asset_id must match landing assets")

    for row in context_records["asset_context"]:
        examples = row["sensitive_data_examples"]
        if not isinstance(examples, list) or not examples:
            raise ValueError("sensitive_data_examples must be a non-empty array")
        if not all(isinstance(item, str) and item for item in examples):
            raise ValueError("sensitive_data_examples must contain non-empty strings")
        for field in ("data_scope_label", "sensitivity_reason"):
            if not isinstance(row[field], str) or not row[field]:
                raise ValueError(f"asset_context.{field} must be a non-empty string")

    routing_keys = []
    for row in context_records["assignment_routing"]:
        key = (row["subject_type"], row["subject_id"], row["asset_id"], row["drift_type"])
        routing_keys.append(key)
        if row["subject_type"] != "nhi":
            raise ValueError("assignment_routing.subject_type must be nhi")
        if row["subject_id"] not in app_ids:
            raise ValueError("assignment_routing.subject_id must match application appId")
        if row["asset_id"] not in asset_ids:
            raise ValueError("assignment_routing.asset_id must match landing assetId")
        if row["drift_type"] != DRIFT_TYPE:
            raise ValueError("assignment_routing.drift_type mismatch")
        for field in ("assignee_name", "assignee_team"):
            if not isinstance(row[field], str) or not row[field]:
                raise ValueError(f"assignment_routing.{field} must be a non-empty string")
        if not isinstance(row["routing_reason"], str):
            raise ValueError("assignment_routing.routing_reason must be a string")

    if len(set(routing_keys)) != expected_size:
        raise ValueError("duplicate assignment_routing source key")
    if set(routing_keys) != eval_keys:
        raise ValueError("assignment_routing source keys must match eval source keys")


def write_jsonl(rows: Iterable[dict[str, object]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "".join(
        json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n"
        for row in rows
    )
    path.write_bytes(content.encode("utf-8"))


def write_landing_records(records: dict[str, list[dict[str, object]]], output_root: Path) -> None:
    for group, relative_path in LANDING_FILE_PATHS.items():
        write_jsonl(records[group], output_root / relative_path)


def write_context_records(records: dict[str, list[dict[str, object]]], output_root: Path) -> None:
    for group, relative_path in CONTEXT_FILE_PATHS.items():
        write_jsonl(records[group], output_root / relative_path)


def file_checksums(paths: Iterable[Path]) -> dict[str, str]:
    return {
        path.as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in paths
    }


def generate(
    size: int,
    seed: int,
    reference_date: date,
    landing_output_root: Path,
    eval_output_path: Path,
    context_output_root: Path,
) -> tuple[
    dict[str, list[dict[str, object]]],
    list[dict[str, object]],
    dict[str, list[dict[str, object]]],
]:
    specs = build_case_specs(size, seed, reference_date)
    landing = build_landing_records(specs, reference_date)
    eval_rows = build_eval_records(specs, reference_date)
    context = build_context_records(specs)
    validate_landing_records(landing, size, reference_date)
    validate_eval_records(eval_rows, landing, size)
    validate_context_records(context, landing, eval_rows, size)
    write_landing_records(landing, landing_output_root)
    write_jsonl(eval_rows, eval_output_path)
    write_context_records(context, context_output_root)
    return landing, eval_rows, context


def parse_reference_date(value: str) -> date:
    return date.fromisoformat(value)


def default_paths(size: int) -> tuple[Path, Path, Path]:
    return (
        DEFAULT_OUTPUT_ROOT / "landing" / "raw",
        DEFAULT_OUTPUT_ROOT / "eval" / "ground_truth_case.jsonl",
        DEFAULT_OUTPUT_ROOT / "context",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--size", type=int, required=True)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--reference-date", type=parse_reference_date, default=DEFAULT_REFERENCE_DATE)
    parser.add_argument("--landing-output-root", type=Path)
    parser.add_argument("--eval-output-path", type=Path)
    parser.add_argument("--context-output-root", type=Path)
    args = parser.parse_args()

    default_landing, default_eval, default_context = default_paths(args.size)
    landing_output_root = args.landing_output_root or default_landing
    eval_output_path = args.eval_output_path or default_eval
    context_output_root = args.context_output_root or default_context

    landing, eval_rows, context = generate(
        args.size,
        args.seed,
        args.reference_date,
        landing_output_root,
        eval_output_path,
        context_output_root,
    )

    print(f"size={args.size}")
    print(f"seed={args.seed}")
    print(f"reference_date={args.reference_date.isoformat()}")
    for group, rows in landing.items():
        print(f"{group}: rows={len(rows)}")
    positives = sum(1 for row in eval_rows if row["is_planted_risk"])
    distractors = sum(1 for row in eval_rows if row["is_distractor"])
    normal = sum(1 for row in eval_rows if not row["is_planted_risk"] and not row["is_distractor"])
    print(f"eval: rows={len(eval_rows)}, positive={positives}, normal={normal}, distractor={distractors}")
    for group, rows in context.items():
        print(f"{group}: rows={len(rows)}")
    checksum_paths = [landing_output_root / path for path in LANDING_FILE_PATHS.values()]
    checksum_paths.append(eval_output_path)
    checksum_paths.extend(context_output_root / path for path in CONTEXT_FILE_PATHS.values())
    for path, checksum in file_checksums(checksum_paths).items():
        print(f"sha256 {checksum}  {path}")


if __name__ == "__main__":
    main()
