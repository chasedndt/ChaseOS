from __future__ import annotations

import json
from pathlib import Path

from runtime.mvp_system_control_boundary import build_mvp_system_control_boundary


def _seed_boundary_evidence(root: Path) -> None:
    for relative in [
        "06_AGENTS/Permission-Matrix.md",
        "06_AGENTS/Trust-Tiers.md",
        "runtime/browser_runtime/cdp_executor_spec.py",
        "runtime/browser_runtime/workflow_replay_execution_readiness.py",
        "06_AGENTS/ChaseOS-MVP-Operator-Unblock-Packet.md",
    ]:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# {path.stem}\n", encoding="utf-8")


def test_mvp_system_control_boundary_parks_broad_control_without_execution(tmp_path: Path) -> None:
    _seed_boundary_evidence(tmp_path)
    before = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))

    payload = build_mvp_system_control_boundary(tmp_path)

    after = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))
    serialized = json.dumps(payload, sort_keys=True)

    assert before == after
    assert payload["status"] == "parked_and_gated_until_mvp_proven"
    assert payload["read_only"] is True
    assert payload["authority"]["broad_system_control_allowed"] is False
    assert payload["authority"]["browser_system_automation_allowed_now"] is False
    assert payload["authority"]["host_mutation_allowed_now"] is False
    assert payload["authority"]["workflow_replay_allowed_now"] is False
    assert payload["authority"]["approval_consumption_allowed"] is False
    assert payload["authority"]["credential_value_read_allowed"] is False
    assert payload["authority"]["cookie_or_session_read_allowed"] is False
    assert payload["authority"]["real_browser_profile_allowed"] is False
    assert payload["authority"]["canonical_mutation_allowed"] is False
    assert "ambient_desktop_control" in payload["forbidden_in_mvp"]
    assert "credential_cookie_or_token_read" in payload["forbidden_in_mvp"]
    assert "sk-" not in serialized


def test_mvp_system_control_boundary_requires_separate_cdp_approval(tmp_path: Path) -> None:
    _seed_boundary_evidence(tmp_path)

    payload = build_mvp_system_control_boundary(tmp_path)
    cdp = payload["cdp_read_only_boundary"]

    assert cdp["execution_enabled"] is False
    assert cdp["cdp_read_only_proof_allowed"] is False
    assert cdp["approval_artifact_supplied"] is False
    assert cdp["approval_status_approved"] is False
    assert "approval_artifact_supplied" in cdp["blocked_reasons"]
    assert cdp["browser_launch_attempted"] is False
    assert cdp["cdp_connection_attempted"] is False
    assert cdp["credential_value_read"] is False
    assert cdp["cookie_or_session_read"] is False
    assert cdp["real_profile_used"] is False
    assert cdp["trusted_skill_written"] is False
    assert cdp["canonical_files_mutated"] is False
    assert cdp["approval_request_written"] is False
    assert cdp["files_modified"] is False
