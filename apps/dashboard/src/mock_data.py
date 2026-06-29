from __future__ import annotations

import pandas as pd

from src.schema import EXPECTED_COLUMNS


def generate_mock_access_drift_data(row_count: int = 24) -> pd.DataFrame:
    rows = _demo_rows()
    return pd.DataFrame(rows[:row_count], columns=EXPECTED_COLUMNS)


def _demo_rows() -> list[dict[str, object]]:
    rows = [
        _row(
            case_id="CASE-001",
            risk_title="NHI access drift requiring immediate review",
            overview_title="NHI Access Drift",
            drift_type="NHI Access Drift",
            identity_name="sp-crm-customer-export-prod",
            object_name="sp-crm-customer-export-prod",
            risk_level="Critical",
            review_status="Open",
            identity_type="NHI",
            object_type="Service Principal",
            credential_type="Client Secret",
            credential_status="Active Client Secret",
            owner_name="김민수",
            owner_team="CRM 데이터 운영팀",
            owner_status="Terminated",
            related_person_status="퇴사일자 2026/06/10",
            linked_owner_label="Linked to Kim Min-su",
            last_accessed_at="2026/06/25 18:42",
            detected_at="2026/06/27 14:30",
            created_at="2026/01/08 09:20",
            permission_level="Storage read/list",
            asset_name="Export Storage",
            asset_type="Storage Account",
            data_scope="고객 DB",
            asset_sensitivity="Sensitive",
            data_categories="고객 이름, 전화번호, 배송지, 주문내역",
            rotation_status="Rotation required",
            risk_score=98,
            reviewer="박지연 · SecOps",
            action_owner="이다영 · CRM 데이터 운영팀 Lead",
            risk_summary=(
                "퇴사자와 연결된 NHI client secret이 active 상태로 남아 있으며, "
                "고객 식별 정보와 주문내역이 포함된 Export Storage에 접근 가능"
            ),
            risk_factors=[
                "HR/IdP 계정 비활성화",
                "연결된 Service Principal 활성 상태",
                "client secret metadata 활성 상태",
                "Storage read/list 권한 잔존",
            ],
            recommended_action=(
                "Service Principal의 실제 사용 목적과 Owner를 확인한 후, "
                "퇴사자와 연결된 활성 Client Secret을 즉시 교체해야 합니다."
            ),
            ai_summary=(
                "Service Principal의 실제 사용 목적과 Owner를 확인한 후, 퇴사자와 연결된 활성 Client Secret을 "
                "즉시 교체해야 합니다. 이후 Storage Account의 RBAC 권한 및 공개 접근 설정에 대한 점검이 필요합니다."
            ),
            reference_docs=[
                "Offboarding Runbook / Section §3.2",
                "Service Principal Secret Policy / Section §4.1",
                "Azure Storage Access Control / Runbook §5.1",
                "Customer Data Protection Policy / Section §2.4",
            ],
            action_plan=[
                "사용 목적 확인 및 Owner 재지정",
                "Service Principal의 Storage Account RBAC 권한 회수",
                "Client Secret Rotation",
                "Access Key / SAS Token 발급 여부 점검",
                "Legacy public access 정책 점검",
            ],
            ai_agent_messages=[
                "AccessDrift의 AI Agent는 내부 런북 및 정책 문서를 기반으로 답변합니다.",
                "case-001 뭐부터 해야 돼?",
                "현재 유효한 Secret을 폐기하거나 신규 인증 수단으로 교체하세요.",
            ],
        ),
        _row(
            case_id="CASE-002",
            risk_title="NHI Credential Drift",
            overview_title="NHI Credential Drift",
            drift_type="NHI Credential Drift",
            identity_name="prod_pg_master_secret_key",
            identity_type="NHI",
            object_name="prod_pg_master_secret_key",
            object_type="Secret Key",
            credential_type="Database Secret",
            credential_status="Active",
            owner_name="강대한",
            owner_team="결제 플랫폼팀",
            owner_status="Active",
            related_person_status="Active",
            asset_name="Payment Database",
            asset_type="PostgreSQL",
            asset_sensitivity="Sensitive",
            permission_level="DB master credential",
            detected_at="2026/06/26 10:15",
            last_accessed_at="2026/06/26 09:50",
            created_at="2025/12/11 13:00",
            risk_level="High",
            risk_score=91,
            review_status="In Review",
            reviewer="박지연 · SecOps",
            action_owner="강대한 · 결제 플랫폼팀",
        ),
        _row(
            case_id="CASE-003",
            risk_title="Repo Access Drift",
            overview_title="Repo Access Drift",
            drift_type="Repo Access Drift",
            identity_name="eunji.lee@company.com",
            identity_type="HI",
            object_name="legacy-repo-admin-role",
            object_type="Repository Role",
            credential_type="SSO Session",
            credential_status="Active",
            owner_name="이은지",
            owner_team="IT 개발팀",
            owner_status="Transferred",
            related_person_status="Moved team",
            asset_name="Customer API Repository",
            asset_type="Repository",
            asset_sensitivity="Confidential",
            permission_level="Admin",
            detected_at="2026/06/25 18:20",
            last_accessed_at="2026/06/25 17:45",
            created_at="2025/10/01 11:30",
            risk_level="High",
            risk_score=89,
            review_status="Open",
            reviewer="박지연 · SecOps",
            action_owner="이은지 · IT 개발팀",
        ),
    ]

    rows.extend(
        [
            _simple_row("CASE-004", "NHI Access Drift", "Critical", "Open", "sp-billing-export-prod", 96),
            _simple_row("CASE-005", "NHI Access Drift", "Critical", "In Review", "sp-marketing-sync-prod", 95),
            _simple_row("CASE-006", "Repo Access Drift", "High", "In Review", "release-bot-admin", 88),
            _simple_row("CASE-007", "NHI Credential Drift", "High", "Resolved", "warehouse_loader_secret", 86),
            _simple_row("CASE-008", "NHI Access Drift", "Medium", "Open", "sp-legacy-crm-reader", 77),
            _simple_row("CASE-009", "NHI Access Drift", "Medium", "In Review", "sp-support-export", 75),
            _simple_row("CASE-010", "Repo Access Drift", "Medium", "Open", "contractor.repo.access", 73),
            _simple_row("CASE-011", "NHI Credential Drift", "Medium", "In Review", "etl_sas_token", 71),
            _simple_row("CASE-012", "Legacy public access policy", "Medium", "Resolved", "legacy-storage-policy", 69),
            _simple_row("CASE-013", "NHI Access Drift", "Low", "Open", "sp-report-reader", 52),
            _simple_row("CASE-014", "NHI Access Drift", "Low", "In Review", "sp-catalog-sync", 50),
            _simple_row("CASE-015", "NHI Access Drift", "Low", "Resolved", "sp-archive-export", 48),
            _simple_row("CASE-016", "NHI Access Drift", "Low", "Resolved", "sp-fieldops-reader", 46),
            _simple_row("CASE-017", "Repo Access Drift", "Low", "Open", "old-ci-repo-role", 44),
            _simple_row("CASE-018", "Repo Access Drift", "Low", "In Review", "repo-token-build-agent", 42),
            _simple_row("CASE-019", "Repo Access Drift", "Low", "Resolved", "docs-repo-admin", 40),
            _simple_row("CASE-020", "NHI Credential Drift", "Low", "Resolved", "staging_api_key", 38),
            _simple_row("CASE-021", "Legacy public access policy", "Low", "Open", "public-blob-policy", 36),
            _simple_row("CASE-022", "Legacy public access policy", "Low", "Open", "legacy-static-site-policy", 34),
            _simple_row("CASE-023", "No Active Drift", "None", "Resolved", "quarterly-review-cleanup-1", 0),
            _simple_row("CASE-024", "No Active Drift", "None", "Resolved", "quarterly-review-cleanup-2", 0),
        ]
    )
    return rows


def _simple_row(
    case_id: str,
    drift_type: str,
    risk_level: str,
    review_status: str,
    identity_name: str,
    risk_score: int,
) -> dict[str, object]:
    owner_name = "김민수" if drift_type == "NHI Access Drift" else "Access Review"
    owner_team = "CRM 데이터 운영팀" if drift_type == "NHI Access Drift" else "Security Ops"
    identity_type = "HI" if drift_type == "Repo Access Drift" else "NHI"
    return _row(
        case_id=case_id,
        risk_title=drift_type,
        overview_title=drift_type,
        drift_type=drift_type,
        risk_level=risk_level,
        review_status=review_status,
        identity_name=identity_name,
        identity_type=identity_type,
        object_name=identity_name,
        object_type="Service Principal" if identity_type == "NHI" else "Repository Access",
        credential_type="Client Secret" if identity_type == "NHI" else "Repository Role",
        credential_status="Active" if risk_level != "None" else "Closed",
        owner_name=owner_name,
        owner_team=owner_team,
        owner_status="Active",
        related_person_status="Review required",
        asset_name="Export Storage" if drift_type == "NHI Access Drift" else "Internal Asset",
        asset_type="Storage Account",
        asset_sensitivity="Sensitive" if risk_level in {"Critical", "High"} else "Internal",
        permission_level="Read/List",
        detected_at="2026/06/24 09:00",
        last_accessed_at="2026/06/24 08:45",
        created_at="2026/01/01 09:00",
        risk_score=risk_score,
    )


def _row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "case_id": "",
        "risk_title": "",
        "risk_level": "Low",
        "drift_type": "",
        "identity_name": "",
        "identity_type": "",
        "object_name": "",
        "object_type": "",
        "credential_type": "",
        "credential_status": "",
        "owner_status": "",
        "owner_name": "",
        "owner_team": "",
        "related_person_status": "",
        "linked_owner_label": "",
        "asset_name": "",
        "asset_type": "",
        "asset_sensitivity": "",
        "data_scope": "",
        "data_categories": "",
        "permission_level": "",
        "last_accessed_at": "",
        "detected_at": "",
        "created_at": "",
        "rotation_status": "",
        "risk_score": 0,
        "review_status": "",
        "reviewer": "",
        "action_owner": "",
        "recommended_action": "Review ownership, confirm business need, and remove stale access.",
        "risk_summary": "Placeholder risk summary for demo review.",
        "risk_factors": [],
        "action_plan": [],
        "ai_agent_messages": [],
        "overview_title": "",
        "ai_summary": "Placeholder AI summary for demo review.",
        "reference_docs": [],
    }
    row.update(overrides)
    return row
