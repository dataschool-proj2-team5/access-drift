from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import base64
import json
import tomllib
import urllib.error
import urllib.request


DEFAULT_SECRET_PATH = Path(__file__).resolve().parents[1] / ".streamlit" / "secrets.toml"


@dataclass(frozen=True)
class JiraConfig:
    base_url: str
    email: str
    api_token: str
    project_key: str
    issue_type: str


@dataclass(frozen=True)
class JiraIssueResult:
    key: str
    url: str


def load_jira_config() -> JiraConfig | None:
    secrets = _read_jira_secrets()
    required = ["base_url", "email", "api_token", "project_key", "issue_type"]
    if not all(secrets.get(key) for key in required):
        return None
    return JiraConfig(
        base_url=str(secrets["base_url"]).rstrip("/"),
        email=str(secrets["email"]),
        api_token=str(secrets["api_token"]),
        project_key=str(secrets["project_key"]),
        issue_type=str(secrets["issue_type"]),
    )


def create_jira_issue(
    config: JiraConfig,
    *,
    title: str,
    explanation: str,
    priority: str,
    label: str,
    due_date: str = "",
) -> JiraIssueResult:
    fields: dict[str, object] = {
        "project": {"key": config.project_key},
        "summary": title,
        "description": _to_adf(explanation),
        "issuetype": {"name": config.issue_type},
        "priority": {"name": priority},
        "labels": _labels(label),
    }
    if due_date:
        fields["duedate"] = due_date

    payload = json.dumps({"fields": fields}).encode("utf-8")
    token = base64.b64encode(f"{config.email}:{config.api_token}".encode("utf-8")).decode("ascii")
    request = urllib.request.Request(
        f"{config.base_url}/rest/api/3/issue",
        data=payload,
        headers={
            "Authorization": f"Basic {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Jira issue creation failed with HTTP {exc.code}.") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError("Jira issue creation failed due to a network error.") from exc

    issue_key = str(result.get("key") or "")
    if not issue_key:
        raise RuntimeError("Jira issue creation did not return an issue key.")
    return JiraIssueResult(key=issue_key, url=f"{config.base_url}/browse/{issue_key}")


def _read_jira_secrets() -> dict[str, object]:
    try:
        import streamlit as st

        if "jira" in st.secrets:
            return dict(st.secrets["jira"])
    except Exception:
        pass

    if DEFAULT_SECRET_PATH.exists():
        return dict(tomllib.loads(DEFAULT_SECRET_PATH.read_text(encoding="utf-8")).get("jira", {}))
    return {}


def _to_adf(text: str) -> dict[str, object]:
    content = []
    for line in str(text).splitlines():
        if line == "":
            content.append({"type": "paragraph"})
            continue
        content.append(
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": line}],
            }
        )
    return {"type": "doc", "version": 1, "content": content or [{"type": "paragraph"}]}


def _labels(label: str) -> list[str]:
    labels = ["access-drift"]
    clean_label = str(label).strip()
    if clean_label:
        labels.append(clean_label)
    return labels
