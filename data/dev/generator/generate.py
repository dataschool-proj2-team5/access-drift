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

SAAS_LANDING_FILE_PATHS = {
    "github_apps": Path("github/apps.jsonl"),
    "github_credentials": Path("github/credentials.jsonl"),
    "github_repos": Path("github/repos.jsonl"),
    "github_access_edges": Path("github/access_edges.jsonl"),
    "google_users": Path("google_workspace/users.jsonl"),
    "google_assets": Path("google_workspace/assets.jsonl"),
    "google_access_edges": Path("google_workspace/access_edges.jsonl"),
    "slack_users": Path("slack/users.jsonl"),
    "slack_channels": Path("slack/channels.jsonl"),
    "slack_access_edges": Path("slack/access_edges.jsonl"),
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
    "lifecycle": {
        "userPrincipalName",
        "displayName",
        "employmentStatus",
        "terminationDate",
    },
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

SAAS_EXPECTED_FIELDS = {
    "github_apps": {
        "appId",
        "slug",
        "displayName",
        "status",
        "ownerEmail",
        "ownerEmploymentStatus",
        "ownerTerminationDate",
    },
    "github_credentials": {
        "appId",
        "credentialId",
        "credentialType",
        "displayName",
        "status",
        "expiresAt",
    },
    "github_repos": {
        "repoId",
        "name",
        "visibility",
        "environment",
        "sensitivity",
    },
    "github_access_edges": {
        "principalId",
        "assetId",
        "relationship",
        "permission",
        "status",
        "lastUsedDateTime",
    },
    "google_users": {
        "userId",
        "email",
        "displayName",
        "status",
        "employmentStatus",
        "terminationDate",
    },
    "google_assets": {
        "assetId",
        "name",
        "assetType",
        "environment",
        "sensitivity",
    },
    "google_access_edges": {
        "principalId",
        "assetId",
        "relationship",
        "permission",
        "status",
        "lastUsedDateTime",
    },
    "slack_users": {
        "userId",
        "email",
        "displayName",
        "status",
        "employmentStatus",
        "terminationDate",
    },
    "slack_channels": {
        "channelId",
        "name",
        "channelType",
        "environment",
        "sensitivity",
    },
    "slack_access_edges": {
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
    "seed_finding_type",
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

SEED_FINDING_TYPES = {
    "NHI Access Drift",
    "NHI Credential Drift",
    "NHI Permission Drift",
    "HI Access Drift",
    "HI Permission Drift",
    "HI Stale Access",
}


@dataclass(frozen=True)
class CaseSpec:
    index: int
    case_kind: str
    app_id: str
    key_id: str
    owner_upn: str
    owner_display_name: str
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


@dataclass(frozen=True)
class SaasCaseSpec:
    source: str
    case_id: str
    scenario_id: str
    scenario_family: str
    subject_type: str
    subject_id: str
    subject_display_name: str
    residual_owner_email: str | None
    residual_status: str
    residual_date: str
    credential_id: str | None
    credential_type: str | None
    credential_display_name: str | None
    asset_id: str
    asset_name: str
    asset_type: str
    environment: str
    sensitivity: str
    permission: str
    drift_type: str
    pattern: str

    seed_finding_type: str

    assignee_name: str
    assignee_team: str
    data_scope_label: str
    sensitive_data_examples: tuple[str, ...]
    sensitivity_reason: str
    label_reason: str


SAAS_CASE_SPECS: tuple[SaasCaseSpec, ...] = (
    SaasCaseSpec(
        source="github",
        case_id="eval-github-nhi-001",
        scenario_id="scenario-github-nhi-001",
        scenario_family="github_app_repo_residual_access",
        subject_type="nhi",
        subject_id="gh-app-prod-deploy-bot",
        subject_display_name="prod-deploy-bot",
        residual_owner_email="kim.minsu@company.com",
        residual_status="terminated",
        residual_date="2026-06-10",
        credential_id="gh-cred-prod-deploy-key",
        credential_type="deploy_key",
        credential_display_name="prod deploy key metadata",
        asset_id="gh-repo-payment-service-prod",
        asset_name="payment-service",
        asset_type="repo",
        environment="production",
        sensitivity="high",
        permission="admin",
        drift_type=DRIFT_TYPE,
        pattern="P2",

        seed_finding_type="NHI Access Drift",

        assignee_name="박서준",
        assignee_team="개발 플랫폼팀",
        data_scope_label="결제 서비스 소스코드",
        sensitive_data_examples=("결제 API 코드", "배포 설정", "운영 workflow"),
        sensitivity_reason="결제 서비스 운영 코드와 배포 설정을 포함하는 private repository",
        label_reason="퇴사 owner kim.minsu@company.com가 남긴 GitHub App prod-deploy-bot이 high 민감도 private repo에 admin 권한으로 접근할 수 있다.",
    ),
    SaasCaseSpec(
        source="github",
        case_id="eval-github-nhi-002",
        scenario_id="scenario-github-nhi-002",
        scenario_family="github_app_repo_residual_access",
        subject_type="nhi",
        subject_id="gh-app-security-audit-bot",
        subject_display_name="security-audit-bot",
        residual_owner_email="jung.woojin@company.com",
        residual_status="terminated",
        residual_date="2026-05-31",
        credential_id="gh-cred-security-audit-pat",
        credential_type="pat",
        credential_display_name="security audit PAT metadata",
        asset_id="gh-repo-infra-secrets-prod",
        asset_name="infra-secrets",
        asset_type="repo",
        environment="production",
        sensitivity="high",
        permission="read",
        drift_type=DRIFT_TYPE,
        pattern="P2",

        seed_finding_type="NHI Credential Drift",

        assignee_name="정우진",
        assignee_team="보안 플랫폼팀",
        data_scope_label="인프라 보안 설정",
        sensitive_data_examples=("Terraform 변수", "권한 정책", "시크릿 참조 경로"),
        sensitivity_reason="운영 인프라 권한 정책과 secret 참조 위치를 포함하는 private repository",
        label_reason="퇴사 owner jung.woojin@company.com가 남긴 GitHub App security-audit-bot이 high 민감도 infra repository에 read 권한으로 접근할 수 있다.",
    ),
    SaasCaseSpec(
        source="github",
        case_id="eval-github-nhi-003",
        scenario_id="scenario-github-nhi-003",
        scenario_family="github_app_repo_residual_access",
        subject_type="nhi",
        subject_id="gh-app-data-export-bot",
        subject_display_name="data-export-bot",
        residual_owner_email="lee.dayoung@company.com",
        residual_status="terminated",
        residual_date="2026-06-03",
        credential_id="gh-cred-data-export-key",
        credential_type="deploy_key",
        credential_display_name="data export deploy key metadata",
        asset_id="gh-repo-customer-export-prod",
        asset_name="customer-export",
        asset_type="repo",
        environment="production",
        sensitivity="high",
        permission="write",
        drift_type=DRIFT_TYPE,
        pattern="P2",

        seed_finding_type="NHI Permission Drift",

        assignee_name="이다영",
        assignee_team="CRM 데이터 운영팀",
        data_scope_label="고객 Export 배치 코드",
        sensitive_data_examples=("고객 export 쿼리", "스케줄 설정", "데이터 경로"),
        sensitivity_reason="고객 데이터 export 경로와 배치 코드를 포함하는 private repository",
        label_reason="퇴사 owner lee.dayoung@company.com가 남긴 GitHub App data-export-bot이 고객 export repository에 write 권한으로 접근할 수 있다.",
    ),
    SaasCaseSpec(
        source="github",
        case_id="eval-github-nhi-004",
        scenario_id="scenario-github-nhi-004",
        scenario_family="github_app_repo_residual_access",
        subject_type="nhi",
        subject_id="gh-app-finance-ci-bot",
        subject_display_name="finance-ci-bot",
        residual_owner_email="park.seojun@company.com",
        residual_status="terminated",
        residual_date="2026-05-27",
        credential_id="gh-cred-finance-ci-pat",
        credential_type="pat",
        credential_display_name="finance ci PAT metadata",
        asset_id="gh-repo-finance-ledger-prod",
        asset_name="finance-ledger",
        asset_type="repo",
        environment="production",
        sensitivity="high",
        permission="write",
        drift_type=DRIFT_TYPE,
        pattern="P2",

        seed_finding_type="NHI Permission Drift",

        assignee_name="박서준",
        assignee_team="재무 데이터팀",
        data_scope_label="재무 원장 처리 코드",
        sensitive_data_examples=("정산 로직", "회계 원장 처리", "배포 workflow"),
        sensitivity_reason="정산과 회계 처리 로직을 포함하는 private repository",
        label_reason="퇴사 owner park.seojun@company.com가 남긴 GitHub App finance-ci-bot이 재무 원장 repository에 write 권한으로 접근할 수 있다.",
    ),
    SaasCaseSpec(
        source="github",
        case_id="eval-github-nhi-005",
        scenario_id="scenario-github-nhi-005",
        scenario_family="github_app_repo_residual_access",
        subject_type="nhi",
        subject_id="gh-app-support-automation-bot",
        subject_display_name="support-automation-bot",
        residual_owner_email="kim.hana@company.com",
        residual_status="terminated",
        residual_date="2026-06-01",
        credential_id="gh-cred-support-automation-key",
        credential_type="deploy_key",
        credential_display_name="support automation key metadata",
        asset_id="gh-repo-support-tools-prod",
        asset_name="support-tools",
        asset_type="repo",
        environment="production",
        sensitivity="medium",
        permission="admin",
        drift_type=DRIFT_TYPE,
        pattern="P2",

        seed_finding_type="NHI Access Drift",

        assignee_name="김하나",
        assignee_team="고객지원 데이터팀",
        data_scope_label="고객지원 자동화 코드",
        sensitive_data_examples=("문의 처리 workflow", "고객지원 연동 설정"),
        sensitivity_reason="고객지원 자동화와 내부 운영 workflow를 포함하는 repository",
        label_reason="퇴사 owner kim.hana@company.com가 남긴 GitHub App support-automation-bot이 support-tools repository에 admin 권한으로 접근할 수 있다.",
    ),
    SaasCaseSpec(
        source="google_workspace",
        case_id="eval-gws-hi-001",
        scenario_id="scenario-gws-hi-001",
        scenario_family="google_workspace_hi_residual_access",
        subject_type="hi",
        subject_id="gws-user-lee.hana",
        subject_display_name="이하나",
        residual_owner_email=None,
        residual_status="terminated",
        residual_date="2026-06-07",
        credential_id=None,
        credential_type=None,
        credential_display_name=None,
        asset_id="gws-drive-customer-support-shared",
        asset_name="customer-support-shared-drive",
        asset_type="workspace",
        environment="production",
        sensitivity="high",
        permission="editor",
        drift_type="hi_residual_access",
        pattern="P1",

        seed_finding_type="HI Access Drift",

        assignee_name="김하나",
        assignee_team="고객지원 데이터팀",
        data_scope_label="고객지원 공유 드라이브",
        sensitive_data_examples=("고객 문의 내역", "고객 연락처", "처리 상태"),
        sensitivity_reason="고객 문의와 연락처 참조 정보를 포함하는 shared drive",
        label_reason="퇴사 후 suspended 상태인 Google Workspace 사용자 lee.hana가 high 민감도 고객지원 공유 드라이브에 editor 권한으로 접근할 수 있다.",
    ),
    SaasCaseSpec(
        source="google_workspace",
        case_id="eval-gws-hi-002",
        scenario_id="scenario-gws-hi-002",
        scenario_family="google_workspace_hi_residual_access",
        subject_type="hi",
        subject_id="gws-user-park.jun",
        subject_display_name="박준",
        residual_owner_email=None,
        residual_status="terminated",
        residual_date="2026-06-04",
        credential_id=None,
        credential_type=None,
        credential_display_name=None,
        asset_id="gws-doc-finance-close-playbook",
        asset_name="finance-close-playbook",
        asset_type="workspace",
        environment="production",
        sensitivity="medium",
        permission="viewer",
        drift_type="hi_residual_access",
        pattern="P1",

        seed_finding_type="HI Permission Drift",

        assignee_name="박서준",
        assignee_team="재무 데이터팀",
        data_scope_label="월마감 재무 문서",
        sensitive_data_examples=("마감 절차", "정산 기준", "내부 승인 흐름"),
        sensitivity_reason="월마감 재무 절차와 승인 기준을 포함하는 내부 문서",
        label_reason="퇴사 후 suspended 상태인 Google Workspace 사용자 park.jun이 재무 마감 문서에 viewer 권한으로 접근할 수 있다.",
    ),
    SaasCaseSpec(
        source="google_workspace",
        case_id="eval-gws-hi-003",
        scenario_id="scenario-gws-hi-003",
        scenario_family="google_workspace_hi_residual_access",
        subject_type="hi",
        subject_id="gws-user-choi.seo",
        subject_display_name="최서윤",
        residual_owner_email=None,
        residual_status="terminated",
        residual_date="2026-05-29",
        credential_id=None,
        credential_type=None,
        credential_display_name=None,
        asset_id="gws-sheet-vip-customer-list",
        asset_name="vip-customer-list",
        asset_type="workspace",
        environment="production",
        sensitivity="critical",
        permission="editor",
        drift_type="hi_residual_access",
        pattern="P1",

        seed_finding_type="HI Access Drift",

        assignee_name="이다영",
        assignee_team="CRM 데이터 운영팀",
        data_scope_label="VIP 고객 리스트",
        sensitive_data_examples=("고객 이름", "연락처", "세그먼트", "구매 등급"),
        sensitivity_reason="고객 식별 정보와 세그먼트 정보를 포함하는 Google Sheet",
        label_reason="퇴사 후 suspended 상태인 Google Workspace 사용자 choi.seo가 critical 민감도 VIP 고객 리스트에 editor 권한으로 접근할 수 있다.",
    ),
    SaasCaseSpec(
        source="google_workspace",
        case_id="eval-gws-hi-004",
        scenario_id="scenario-gws-hi-004",
        scenario_family="google_workspace_hi_residual_access",
        subject_type="hi",
        subject_id="gws-user-jung.woo",
        subject_display_name="정우진",
        residual_owner_email=None,
        residual_status="terminated",
        residual_date="2026-06-12",
        credential_id=None,
        credential_type=None,
        credential_display_name=None,
        asset_id="gws-drive-seller-settlement",
        asset_name="seller-settlement-drive",
        asset_type="workspace",
        environment="production",
        sensitivity="critical",
        permission="viewer",
        drift_type="hi_residual_access",
        pattern="P1",

        seed_finding_type="HI Permission Drift",

        assignee_name="한지민",
        assignee_team="정산 플랫폼팀",
        data_scope_label="판매자 정산 공유 드라이브",
        sensitive_data_examples=("판매자 ID", "정산 금액", "수수료", "지급 상태"),
        sensitivity_reason="판매자 정산과 지급 상태 정보를 포함하는 shared drive",
        label_reason="퇴사 후 suspended 상태인 Google Workspace 사용자 jung.woo가 critical 민감도 판매자 정산 공유 드라이브에 viewer 권한으로 접근할 수 있다.",
    ),
    SaasCaseSpec(
        source="google_workspace",
        case_id="eval-gws-hi-005",
        scenario_id="scenario-gws-hi-005",
        scenario_family="google_workspace_hi_residual_access",
        subject_type="hi",
        subject_id="gws-user-oh.sehun",
        subject_display_name="오세훈",
        residual_owner_email=None,
        residual_status="terminated",
        residual_date="2026-06-02",
        credential_id=None,
        credential_type=None,
        credential_display_name=None,
        asset_id="gws-doc-marketing-segment-plan",
        asset_name="marketing-segment-plan",
        asset_type="workspace",
        environment="production",
        sensitivity="medium",
        permission="editor",
        drift_type="hi_residual_access",
        pattern="P1",

        seed_finding_type="HI Stale Access",

        assignee_name="오세훈",
        assignee_team="마케팅 데이터팀",
        data_scope_label="마케팅 세그먼트 문서",
        sensitive_data_examples=("세그먼트 기준", "캠페인 대상", "관심 카테고리"),
        sensitivity_reason="고객 세그먼트 기준과 캠페인 대상 조건을 포함하는 문서",
        label_reason="퇴사 후 suspended 상태인 Google Workspace 사용자 oh.sehun이 마케팅 세그먼트 문서에 editor 권한으로 접근할 수 있다.",
    ),
    SaasCaseSpec(
        source="slack",
        case_id="eval-slack-hi-001",
        scenario_id="scenario-slack-hi-001",
        scenario_family="slack_channel_hi_residual_access",
        subject_type="hi",
        subject_id="slack-user-kang.yuna",
        subject_display_name="강유나",
        residual_owner_email=None,
        residual_status="terminated",
        residual_date="2026-06-06",
        credential_id=None,
        credential_type=None,
        credential_display_name=None,
        asset_id="slack-channel-customer-support-private",
        asset_name="customer-support-private",
        asset_type="slack_channel",
        environment="production",
        sensitivity="critical",
        permission="member",
        drift_type="hi_residual_access",
        pattern="P1",

        seed_finding_type="HI Access Drift",

        assignee_name="김하나",
        assignee_team="고객지원 데이터팀",
        data_scope_label="고객지원 private channel",
        sensitive_data_examples=("고객 문의", "고객 연락처", "처리 상태"),
        sensitivity_reason="고객 문의와 연락처가 공유되는 private Slack channel",
        label_reason="퇴사 후 deactivated 상태인 Slack 사용자 kang.yuna가 critical 민감도 고객지원 private channel에 member 권한으로 남아 있다.",
    ),
    SaasCaseSpec(
        source="slack",
        case_id="eval-slack-hi-002",
        scenario_id="scenario-slack-hi-002",
        scenario_family="slack_channel_hi_residual_access",
        subject_type="hi",
        subject_id="slack-user-lim.taehyun",
        subject_display_name="임태현",
        residual_owner_email=None,
        residual_status="terminated",
        residual_date="2026-06-09",
        credential_id=None,
        credential_type=None,
        credential_display_name=None,
        asset_id="slack-channel-security-incident",
        asset_name="security-incident",
        asset_type="slack_channel",
        environment="production",
        sensitivity="high",
        permission="member",
        drift_type="hi_residual_access",
        pattern="P1",

        seed_finding_type="HI Stale Access",

        assignee_name="정우진",
        assignee_team="보안 플랫폼팀",
        data_scope_label="보안 incident channel",
        sensitive_data_examples=("보안 사고 대응", "취약점 논의", "권한 변경 이력"),
        sensitivity_reason="보안 사고 대응과 취약점 논의가 포함되는 private Slack channel",
        label_reason="퇴사 후 deactivated 상태인 Slack 사용자 lim.taehyun이 high 민감도 보안 incident channel에 member 권한으로 남아 있다.",
    ),
    SaasCaseSpec(
        source="slack",
        case_id="eval-slack-hi-003",
        scenario_id="scenario-slack-hi-003",
        scenario_family="slack_channel_hi_residual_access",
        subject_type="hi",
        subject_id="slack-user-han.jimin",
        subject_display_name="한지민",
        residual_owner_email=None,
        residual_status="terminated",
        residual_date="2026-06-11",
        credential_id=None,
        credential_type=None,
        credential_display_name=None,
        asset_id="slack-channel-finance-settlement",
        asset_name="finance-settlement",
        asset_type="slack_channel",
        environment="production",
        sensitivity="critical",
        permission="member",
        drift_type="hi_residual_access",
        pattern="P1",

        seed_finding_type="HI Permission Drift",

        assignee_name="한지민",
        assignee_team="정산 플랫폼팀",
        data_scope_label="정산 private channel",
        sensitive_data_examples=("판매자 ID", "정산 금액", "지급 상태"),
        sensitivity_reason="판매자 정산과 지급 상태가 논의되는 private Slack channel",
        label_reason="퇴사 후 deactivated 상태인 Slack 사용자 han.jimin이 critical 민감도 정산 private channel에 member 권한으로 남아 있다.",
    ),
    SaasCaseSpec(
        source="slack",
        case_id="eval-slack-hi-004",
        scenario_id="scenario-slack-hi-004",
        scenario_family="slack_channel_hi_residual_access",
        subject_type="hi",
        subject_id="slack-user-seo.minji",
        subject_display_name="서민지",
        residual_owner_email=None,
        residual_status="terminated",
        residual_date="2026-06-08",
        credential_id=None,
        credential_type=None,
        credential_display_name=None,
        asset_id="slack-channel-vip-customer-ops",
        asset_name="vip-customer-ops",
        asset_type="slack_channel",
        environment="production",
        sensitivity="critical",
        permission="member",
        drift_type="hi_residual_access",
        pattern="P1",

        seed_finding_type="HI Access Drift",

        assignee_name="이다영",
        assignee_team="CRM 데이터 운영팀",
        data_scope_label="VIP 고객 운영 channel",
        sensitive_data_examples=("VIP 고객 이름", "연락처", "구매 등급"),
        sensitivity_reason="VIP 고객 식별 정보와 운영 이슈가 공유되는 private Slack channel",
        label_reason="퇴사 후 deactivated 상태인 Slack 사용자 seo.minji가 critical 민감도 VIP 고객 운영 channel에 member 권한으로 남아 있다.",
    ),
    SaasCaseSpec(
        source="slack",
        case_id="eval-slack-hi-005",
        scenario_id="scenario-slack-hi-005",
        scenario_family="slack_channel_hi_residual_access",
        subject_type="hi",
        subject_id="slack-user-moon.jae",
        subject_display_name="문재현",
        residual_owner_email=None,
        residual_status="terminated",
        residual_date="2026-06-05",
        credential_id=None,
        credential_type=None,
        credential_display_name=None,
        asset_id="slack-channel-ops-runbook",
        asset_name="ops-runbook",
        asset_type="slack_channel",
        environment="production",
        sensitivity="medium",
        permission="member",
        drift_type="hi_residual_access",
        pattern="P1",

        seed_finding_type="HI Stale Access",

        assignee_name="최하은",
        assignee_team="운영 데이터팀",
        data_scope_label="운영 runbook channel",
        sensitive_data_examples=("운영 절차", "장애 대응 흐름", "배포 일정"),
        sensitivity_reason="운영 절차와 장애 대응 흐름이 공유되는 private Slack channel",
        label_reason="퇴사 후 deactivated 상태인 Slack 사용자 moon.jae가 medium 민감도 운영 runbook channel에 member 권한으로 남아 있다.",
    ),
)


SAAS_CASE_COUNT = len(SAAS_CASE_SPECS)


def _iso_ts(value: date) -> str:
    return f"{value.isoformat()}T09:00:00Z"


def _parse_date(value: str) -> date:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).date()


def _saas_last_used_at(reference_date: date, source_offset: int, case_index: int) -> str:
    return _iso_ts(reference_date - timedelta(days=source_offset + case_index + 1))


def _stable_uuid(seed: int, label: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"access-drift:{seed}:{label}"))


KOREAN_OWNER_DISPLAY_NAMES = (
    "정우진",
    "박서준",
    "김하나",
    "최하은",
    "한지민",
    "오세훈",
    "강유나",
    "임태현",
    "서민지",
    "문재현",
    "윤서연",
    "장도윤",
    "배수진",
    "신지호",
    "홍유진",
    "조현우",
    "남가은",
    "유준호",
    "송하린",
)


def _owner_display_name(seed: int, index: int) -> str:
    offset = seed % len(KOREAN_OWNER_DISPLAY_NAMES)
    return KOREAN_OWNER_DISPLAY_NAMES[(index + offset - 1) % len(KOREAN_OWNER_DISPLAY_NAMES)]


def _expected_severity(sensitivity: str) -> str:
    return sensitivity.upper()


def _seed_finding_type_for_spec(spec: CaseSpec) -> str:
    if spec.case_kind == "positive":
        if spec.index % 3 == 2:
            return "NHI Credential Drift"
        if spec.index % 3 == 0:
            return "NHI Permission Drift"
        return "NHI Access Drift"
    if spec.distractor_type == "credential_expired":
        return "NHI Credential Drift"
    if spec.distractor_type == "access_inactive":
        return "NHI Permission Drift"
    return "NHI Access Drift"


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
            owner_display_name="김민수",
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
        owner_display_name=_owner_display_name(seed, index),
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
        "owner_display_name": _owner_display_name(seed, index),
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
        owner_display_name=_owner_display_name(seed, index),
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


def _insert_saas_after_review_window(rows: list[dict[str, object]], saas_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    review_window = min(20, len(rows))
    return [*rows[:review_window], *saas_rows, *rows[review_window:]]


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
                "displayName": spec.owner_display_name,
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


def build_saas_landing_records(reference_date: date) -> dict[str, list[dict[str, object]]]:
    expires_at = f"{(reference_date + timedelta(days=365)).isoformat()}T00:00:00Z"
    github_cases = [case for case in SAAS_CASE_SPECS if case.source == "github"]
    google_cases = [case for case in SAAS_CASE_SPECS if case.source == "google_workspace"]
    slack_cases = [case for case in SAAS_CASE_SPECS if case.source == "slack"]
    return {
        "github_apps": [
            {
                "appId": case.subject_id,
                "slug": case.subject_id.removeprefix("gh-app-"),
                "displayName": case.subject_display_name,
                "status": "active",
                "ownerEmail": case.residual_owner_email,
                "ownerEmploymentStatus": case.residual_status,
                "ownerTerminationDate": case.residual_date,
            }
            for case in github_cases
        ],
        "github_credentials": [
            {
                "appId": case.subject_id,
                "credentialId": case.credential_id,
                "credentialType": case.credential_type,
                "displayName": case.credential_display_name,
                "status": "active",
                "expiresAt": expires_at,
            }
            for case in github_cases
        ],
        "github_repos": [
            {
                "repoId": case.asset_id,
                "name": case.asset_name,
                "visibility": "private",
                "environment": case.environment,
                "sensitivity": case.sensitivity,
            }
            for case in github_cases
        ],
        "github_access_edges": [
            {
                "principalId": case.subject_id,
                "assetId": case.asset_id,
                "relationship": "accesses_asset",
                "permission": case.permission,
                "status": "active",
                "lastUsedDateTime": _saas_last_used_at(reference_date, 10, index),
            }
            for index, case in enumerate(github_cases)
        ],
        "google_users": [
            {
                "userId": case.subject_id,
                "email": f"{case.subject_id.removeprefix('gws-user-')}@company.com",
                "displayName": case.subject_display_name,
                "status": "suspended",
                "employmentStatus": case.residual_status,
                "terminationDate": case.residual_date,
            }
            for case in google_cases
        ],
        "google_assets": [
            {
                "assetId": case.asset_id,
                "name": case.asset_name,
                "assetType": case.asset_type,
                "environment": case.environment,
                "sensitivity": case.sensitivity,
            }
            for case in google_cases
        ],
        "google_access_edges": [
            {
                "principalId": case.subject_id,
                "assetId": case.asset_id,
                "relationship": "accesses_asset",
                "permission": case.permission,
                "status": "active",
                "lastUsedDateTime": _saas_last_used_at(reference_date, 20, index),
            }
            for index, case in enumerate(google_cases)
        ],
        "slack_users": [
            {
                "userId": case.subject_id,
                "email": f"{case.subject_id.removeprefix('slack-user-')}@company.com",
                "displayName": case.subject_display_name,
                "status": "deactivated",
                "employmentStatus": case.residual_status,
                "terminationDate": case.residual_date,
            }
            for case in slack_cases
        ],
        "slack_channels": [
            {
                "channelId": case.asset_id,
                "name": case.asset_name,
                "channelType": "private",
                "environment": case.environment,
                "sensitivity": case.sensitivity,
            }
            for case in slack_cases
        ],
        "slack_access_edges": [
            {
                "principalId": case.subject_id,
                "assetId": case.asset_id,
                "relationship": "accesses_asset",
                "permission": case.permission,
                "status": "active",
                "lastUsedDateTime": _saas_last_used_at(reference_date, 30, index),
            }
            for index, case in enumerate(slack_cases)
        ],
    }


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
                "seed_finding_type": _seed_finding_type_for_spec(spec),
                "label_reason": reason,
                "created_at": created_at,
            }
        )
    saas_rows = []
    for case in SAAS_CASE_SPECS:
        saas_rows.append(
            {
                "case_id": case.case_id,
                "scenario_id": case.scenario_id,
                "scenario_family": case.scenario_family,
                "subject_type": case.subject_type,
                "subject_id": case.subject_id,
                "asset_id": case.asset_id,
                "drift_type": case.drift_type,
                "is_planted_risk": True,
                "is_distractor": False,
                "pattern": case.pattern,
                "expected_severity": _expected_severity(case.sensitivity),

                "seed_finding_type": case.seed_finding_type,

                "label_reason": case.label_reason,
                "created_at": created_at,
            }
        )
    return _insert_saas_after_review_window(rows, saas_rows)


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


def _asset_context_for_saas_case(case: SaasCaseSpec) -> dict[str, object]:
    return {
        "source_asset_id": case.asset_id,
        "data_scope_label": case.data_scope_label,
        "sensitive_data_examples": list(case.sensitive_data_examples),
        "sensitivity_reason": case.sensitivity_reason,
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


def _assignment_routing_for_saas_case(case: SaasCaseSpec) -> dict[str, object]:
    return {
        "subject_type": case.subject_type,
        "subject_id": case.subject_id,
        "asset_id": case.asset_id,
        "drift_type": case.drift_type,
        "assignee_name": case.assignee_name,
        "assignee_team": case.assignee_team,
        "routing_reason": f"{case.subject_display_name}와 {case.asset_name}의 운영 책임 팀",
    }


def build_context_records(specs: Iterable[CaseSpec]) -> dict[str, list[dict[str, object]]]:
    spec_list = list(specs)
    asset_context = [_asset_context_for_spec(spec) for spec in spec_list]
    assignment_routing = [_assignment_routing_for_spec(spec) for spec in spec_list]
    saas_asset_context = [_asset_context_for_saas_case(case) for case in SAAS_CASE_SPECS]
    saas_assignment_routing = [_assignment_routing_for_saas_case(case) for case in SAAS_CASE_SPECS]
    return {
        "asset_context": _insert_saas_after_review_window(asset_context, saas_asset_context),
        "assignment_routing": _insert_saas_after_review_window(assignment_routing, saas_assignment_routing),
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


def validate_saas_landing_records(
    records: dict[str, list[dict[str, object]]], reference_date: date
) -> None:
    if set(records) != set(SAAS_LANDING_FILE_PATHS):
        raise ValueError("unexpected SaaS landing record groups")

    for group, rows in records.items():
        expected_rows = 5
        if len(rows) != expected_rows:
            raise ValueError(f"{group} expected {expected_rows}, got {len(rows)}")
        for row in rows:
            if set(row).intersection(FORBIDDEN_FIELDS):
                raise ValueError(f"{group} contains a forbidden field")
            if set(row) != SAAS_EXPECTED_FIELDS[group]:
                raise ValueError(f"{group} has unexpected fields: {set(row)}")
            for field, value in row.items():
                if not isinstance(value, str) or not value:
                    raise ValueError(f"{group}.{field} must be a non-empty string")

    github_app_ids = {row["appId"] for row in records["github_apps"]}
    github_repo_ids = {row["repoId"] for row in records["github_repos"]}
    google_user_ids = {row["userId"] for row in records["google_users"]}
    google_asset_ids = {row["assetId"] for row in records["google_assets"]}
    slack_user_ids = {row["userId"] for row in records["slack_users"]}
    slack_channel_ids = {row["channelId"] for row in records["slack_channels"]}

    if not all(str(value).startswith("gh-") for value in github_app_ids):
        raise ValueError("GitHub appId must use gh- namespace")
    if not all(str(value).startswith("gh-") for value in github_repo_ids):
        raise ValueError("GitHub repoId must use gh- namespace")
    if not all(str(value).startswith("gws-") for value in google_user_ids):
        raise ValueError("Google userId must use gws- namespace")
    if not all(str(value).startswith("gws-") for value in google_asset_ids):
        raise ValueError("Google assetId must use gws- namespace")
    if not all(str(value).startswith("slack-") for value in slack_user_ids):
        raise ValueError("Slack userId must use slack- namespace")
    if not all(str(value).startswith("slack-") for value in slack_channel_ids):
        raise ValueError("Slack channelId must use slack- namespace")

    for row in records["github_apps"]:
        if row["status"] != "active":
            raise ValueError("GitHub app status must be active")
        if row["ownerEmploymentStatus"] != "terminated":
            raise ValueError("GitHub app ownerEmploymentStatus must be terminated")
        date.fromisoformat(str(row["ownerTerminationDate"]))

    for row in records["google_users"]:
        if row["status"] != "suspended":
            raise ValueError("Google user status must be suspended")
        if row["employmentStatus"] != "terminated":
            raise ValueError("Google user employmentStatus must be terminated")
        date.fromisoformat(str(row["terminationDate"]))

    for row in records["slack_users"]:
        if row["status"] != "deactivated":
            raise ValueError("Slack user status must be deactivated")
        if row["employmentStatus"] != "terminated":
            raise ValueError("Slack user employmentStatus must be terminated")
        date.fromisoformat(str(row["terminationDate"]))

    if {row["appId"] for row in records["github_credentials"]} != github_app_ids:
        raise ValueError("GitHub credentials must match GitHub apps")
    if {row["principalId"] for row in records["github_access_edges"]} != github_app_ids:
        raise ValueError("GitHub access edge principalId must match GitHub apps")
    if {row["assetId"] for row in records["github_access_edges"]} != github_repo_ids:
        raise ValueError("GitHub access edge assetId must match GitHub repos")
    if {row["principalId"] for row in records["google_access_edges"]} != google_user_ids:
        raise ValueError("Google access edge principalId must match Google users")
    if {row["assetId"] for row in records["google_access_edges"]} != google_asset_ids:
        raise ValueError("Google access edge assetId must match Google assets")
    if {row["principalId"] for row in records["slack_access_edges"]} != slack_user_ids:
        raise ValueError("Slack access edge principalId must match Slack users")
    if {row["assetId"] for row in records["slack_access_edges"]} != slack_channel_ids:
        raise ValueError("Slack access edge assetId must match Slack channels")

    for group in ("github_access_edges", "google_access_edges", "slack_access_edges"):
        for row in records[group]:
            _validate_timestamp(row["lastUsedDateTime"], f"{group}.lastUsedDateTime")
            if _parse_date(str(row["lastUsedDateTime"])) > reference_date:
                raise ValueError(f"{group}.lastUsedDateTime must not be after reference_date")

    for row in records["github_credentials"]:
        _validate_timestamp(row["expiresAt"], "expiresAt")


def validate_eval_records(
    eval_rows: list[dict[str, object]],
    landing_records: dict[str, list[dict[str, object]]],
    saas_landing_records: dict[str, list[dict[str, object]]],
    expected_size: int,
) -> None:
    expected_eval_size = expected_size + SAAS_CASE_COUNT
    if len(eval_rows) != expected_eval_size:
        raise ValueError(f"eval expected {expected_eval_size}, got {len(eval_rows)}")

    app_ids = {row["appId"] for row in landing_records["applications"]}
    asset_by_id = {row["assetId"]: row for row in landing_records["assets"]}
    github_app_ids = {row["appId"] for row in saas_landing_records["github_apps"]}
    github_asset_by_id = {row["repoId"]: row for row in saas_landing_records["github_repos"]}
    google_user_ids = {row["userId"] for row in saas_landing_records["google_users"]}
    google_asset_by_id = {row["assetId"]: row for row in saas_landing_records["google_assets"]}
    slack_user_ids = {row["userId"] for row in saas_landing_records["slack_users"]}
    slack_asset_by_id = {row["channelId"]: row for row in saas_landing_records["slack_channels"]}
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
        "seed_finding_type",
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
        subject_type = row["subject_type"]
        subject_id = row["subject_id"]
        asset_id = row["asset_id"]
        if subject_type == "nhi" and subject_id in app_ids:
            if asset_id not in asset_by_id:
                raise ValueError("eval asset_id does not match asset seed")
            asset = asset_by_id[asset_id]
            if row["drift_type"] != DRIFT_TYPE:
                raise ValueError("NHI eval drift_type mismatch")
        elif subject_type == "nhi" and subject_id in github_app_ids:
            if asset_id not in github_asset_by_id:
                raise ValueError("GitHub eval asset_id does not match GitHub repo")
            asset = github_asset_by_id[asset_id]
            if row["drift_type"] != DRIFT_TYPE:
                raise ValueError("GitHub NHI eval drift_type mismatch")
        elif subject_type == "hi" and subject_id in google_user_ids:
            if asset_id not in google_asset_by_id:
                raise ValueError("Google eval asset_id does not match Google asset")
            asset = google_asset_by_id[asset_id]
            if row["drift_type"] != "hi_residual_access":
                raise ValueError("Google HI eval drift_type mismatch")
        elif subject_type == "hi" and subject_id in slack_user_ids:
            if asset_id not in slack_asset_by_id:
                raise ValueError("Slack eval asset_id does not match Slack channel")
            asset = slack_asset_by_id[asset_id]
            if row["drift_type"] != "hi_residual_access":
                raise ValueError("Slack HI eval drift_type mismatch")
        else:
            raise ValueError("eval subject_id does not match known principal source")
        if row["is_distractor"] is True:
            distractors += 1
        if row["is_planted_risk"] is True:
            positives += 1
        if row["expected_severity"] != _expected_severity(str(asset["sensitivity"])):
            raise ValueError("expected_severity must match asset sensitivity uppercase")
        if row["seed_finding_type"] not in SEED_FINDING_TYPES:
            raise ValueError("unknown seed_finding_type")
        _validate_timestamp(row["created_at"], "created_at")

    mix = expected_counts_for_size(expected_size)
    if positives != mix["positive"] + SAAS_CASE_COUNT:
        raise ValueError("unexpected positive eval count")
    if distractors != mix["distractor"]:
        raise ValueError("unexpected distractor eval count")
    missing_finding_types = SEED_FINDING_TYPES - {
        str(row["seed_finding_type"]) for row in eval_rows
    }
    if expected_size >= 20 and missing_finding_types:
        missing = ", ".join(sorted(missing_finding_types))
        raise ValueError(f"seed_finding_type coverage missing: {missing}")


def validate_context_records(
    context_records: dict[str, list[dict[str, object]]],
    landing_records: dict[str, list[dict[str, object]]],
    saas_landing_records: dict[str, list[dict[str, object]]],
    eval_rows: list[dict[str, object]],
    expected_size: int,
) -> None:
    if set(context_records) != set(CONTEXT_FILE_PATHS):
        raise ValueError("unexpected context record groups")

    for group, rows in context_records.items():
        expected_context_size = expected_size + SAAS_CASE_COUNT
        if len(rows) != expected_context_size:
            raise ValueError(f"{group} expected {expected_context_size}, got {len(rows)}")
        for row in rows:
            if set(row).intersection(FORBIDDEN_FIELDS):
                raise ValueError(f"{group} contains a forbidden field")
            if set(row) != CONTEXT_EXPECTED_FIELDS[group]:
                raise ValueError(f"{group} has unexpected fields: {set(row)}")

    asset_ids = {row["assetId"] for row in landing_records["assets"]}
    asset_ids.update(row["repoId"] for row in saas_landing_records["github_repos"])
    asset_ids.update(row["assetId"] for row in saas_landing_records["google_assets"])
    asset_ids.update(row["channelId"] for row in saas_landing_records["slack_channels"])
    app_ids = {row["appId"] for row in landing_records["applications"]}
    app_ids.update(row["appId"] for row in saas_landing_records["github_apps"])
    app_ids.update(row["userId"] for row in saas_landing_records["google_users"])
    app_ids.update(row["userId"] for row in saas_landing_records["slack_users"])
    eval_keys = {
        (row["subject_type"], row["subject_id"], row["asset_id"], row["drift_type"])
        for row in eval_rows
    }

    asset_context_ids = [row["source_asset_id"] for row in context_records["asset_context"]]
    if len(set(asset_context_ids)) != expected_size + SAAS_CASE_COUNT:
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
        if row["subject_type"] not in {"hi", "nhi"}:
            raise ValueError("assignment_routing.subject_type must be hi or nhi")
        if row["subject_id"] not in app_ids:
            raise ValueError("assignment_routing.subject_id must match known principal source")
        if row["asset_id"] not in asset_ids:
            raise ValueError("assignment_routing.asset_id must match known asset source")
        if row["drift_type"] not in {DRIFT_TYPE, "hi_residual_access"}:
            raise ValueError("assignment_routing.drift_type mismatch")
        for field in ("assignee_name", "assignee_team"):
            if not isinstance(row[field], str) or not row[field]:
                raise ValueError(f"assignment_routing.{field} must be a non-empty string")
        if not isinstance(row["routing_reason"], str):
            raise ValueError("assignment_routing.routing_reason must be a string")

    if len(set(routing_keys)) != expected_size + SAAS_CASE_COUNT:
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


def write_saas_landing_records(records: dict[str, list[dict[str, object]]], output_root: Path) -> None:
    for group, relative_path in SAAS_LANDING_FILE_PATHS.items():
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
    dict[str, list[dict[str, object]]],
    list[dict[str, object]],
    dict[str, list[dict[str, object]]],
]:
    specs = build_case_specs(size, seed, reference_date)
    landing = build_landing_records(specs, reference_date)
    saas_landing = build_saas_landing_records(reference_date)
    eval_rows = build_eval_records(specs, reference_date)
    context = build_context_records(specs)
    validate_landing_records(landing, size, reference_date)
    validate_saas_landing_records(saas_landing, reference_date)
    validate_eval_records(eval_rows, landing, saas_landing, size)
    validate_context_records(context, landing, saas_landing, eval_rows, size)
    write_landing_records(landing, landing_output_root)
    write_saas_landing_records(saas_landing, landing_output_root)
    write_jsonl(eval_rows, eval_output_path)
    write_context_records(context, context_output_root)
    return landing, saas_landing, eval_rows, context


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

    landing, saas_landing, eval_rows, context = generate(
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
    for group, rows in saas_landing.items():
        print(f"{group}: rows={len(rows)}")
    positives = sum(1 for row in eval_rows if row["is_planted_risk"])
    distractors = sum(1 for row in eval_rows if row["is_distractor"])
    normal = sum(1 for row in eval_rows if not row["is_planted_risk"] and not row["is_distractor"])
    finding_types = {}
    for row in eval_rows:
        value = row["seed_finding_type"]
        finding_types[value] = finding_types.get(value, 0) + 1
    print(f"eval: rows={len(eval_rows)}, positive={positives}, normal={normal}, distractor={distractors}")
    print(f"seed_finding_type_distribution={dict(sorted(finding_types.items()))}")
    for group, rows in context.items():
        print(f"{group}: rows={len(rows)}")
    checksum_paths = [landing_output_root / path for path in LANDING_FILE_PATHS.values()]
    checksum_paths.extend(landing_output_root / path for path in SAAS_LANDING_FILE_PATHS.values())
    checksum_paths.append(eval_output_path)
    checksum_paths.extend(context_output_root / path for path in CONTEXT_FILE_PATHS.values())
    for path, checksum in file_checksums(checksum_paths).items():
        print(f"sha256 {checksum}  {path}")


if __name__ == "__main__":
    main()
