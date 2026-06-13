import json
from pathlib import Path

import pytest

from runtime.workspace_modes import (
    WorkspaceModeValidationError,
    build_unknown_profile,
    infer_workspace_mode,
    load_workspace_profile,
    load_workspace_profile_from_mapping,
)
from runtime.workspace_modes.loader import parse_profile_text
from runtime.workspace_modes.aor_routing_preview import build_aor_workspace_route_preview
from runtime.workspace_modes.profile_draft_packet import build_workspace_profile_draft_packet
from runtime.workspace_modes.profile_rollout_plan import build_workspace_profile_rollout_plan
from runtime.workspace_modes.profile_write_approval_request import (
    build_workspace_profile_write_approval_request,
)
from runtime.workspace_modes.profile_guarded_writer import build_workspace_profile_guarded_write
from runtime.workspace_modes.product_status import (
    build_workspace_mode_approval_ledger,
    build_workspace_mode_product_status,
)
from runtime.workspace_modes.aor_dispatch_gate import build_workspace_mode_aor_dispatch_gate
from runtime.workspace_modes.aor_live_execution_approval_gate import (
    build_workspace_mode_aor_live_execution_approval_gate,
)
from runtime.aor.engine import AORRunResult
import runtime.workspace_modes.aor_dispatch_dry_run_executor as aor_dry_run_executor
import runtime.workspace_modes.aor_live_executor as aor_live_executor


def _valid_profile_dict() -> dict:
    return {
        "workspace_id": "chaseos",
        "workspace_name": "ChaseOS",
        "workspace_mode": "runtime_agent_ops",
        "description": "Local-first human-AI operating framework and runtime control plane.",
        "primary_domains": ["AI Engineering", "Runtime Governance", "Agent Operations"],
        "canonical_state_files": [
            "00_HOME/Now.md",
            "ROADMAP.md",
            "PROJECT_FOUNDATION.md",
            "01_PROJECTS/ChaseOS/ChaseOS-OS.md",
        ],
        "required_read_order": [
            "README.md",
            "PROJECT_FOUNDATION.md",
            "ROADMAP.md",
            "00_HOME/Now.md",
        ],
        "allowed_knowledge_classes": [
            "user-origin",
            "source-derived",
            "synthesized",
            "generated-ideas",
            "system-operational",
            "canonical-state",
        ],
        "default_output_classes": [
            "build-log",
            "agent-activity-log",
            "operator-brief",
            "generated-idea",
            "proposal",
        ],
        "allowed_workflows": [
            "operator_today",
            "operator_close_day",
            "graph_hygiene",
            "graduate_ideas",
        ],
        "runtime_adapter_ceiling": {
            "claude": "tier-2",
            "codex": "tier-2",
            "openclaw": "tier-2-bounded",
            "hermes": "tier-2-bounded",
        },
        "approval_rules": {
            "canonical_state_write": "explicit_user_approval_required",
            "generated_idea_creation": "allowed_with_label",
            "generated_idea_endorsement": "human_only",
            "source_promotion": "gate_required",
            "protected_file_write": "explicit_per_file_approval_required",
            "shell_execution": "blocked_by_default",
            "external_connector_action": "blocked_by_default",
        },
        "graph_rules": {
            "update_domain_index_on_promotion": True,
            "backlinks_required_for_durable_notes": True,
            "orphan_notes_flagged": True,
        },
        "protected_paths": [
            ".env",
            "secrets/",
            "credentials/",
            "00_HOME/Now.md",
            "ROADMAP.md",
            "PROJECT_FOUNDATION.md",
        ],
        "default_write_targets": [
            "07_LOGS/Build-Logs/",
            "07_LOGS/Agent-Activity/",
            "99_ARCHIVE/Documentation-History/",
        ],
        "escalation_rules": {
            "unknown_mode": "stop_and_request_mode",
            "protected_write": "require_explicit_approval",
            "external_action": "require_explicit_approval",
            "runtime_authority_unclear": "fail_closed",
        },
    }


def _write_test_profile(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "workspace_id: runtime",
                "workspace_name: Runtime",
                "workspace_mode: runtime_agent_ops",
                "description: Runtime workspace.",
                "primary_domains:",
                "  - Runtime Governance",
                "canonical_state_files:",
                "  - 00_HOME/Now.md",
                "required_read_order:",
                "  - README.md",
                "allowed_knowledge_classes:",
                "  - user-origin",
                "  - source-derived",
                "  - synthesized",
                "  - generated-ideas",
                "  - system-operational",
                "  - canonical-state",
                "default_output_classes:",
                "  - build-log",
                "allowed_workflows:",
                "  - operator_today",
                "runtime_adapter_ceiling:",
                "  claude: tier-2",
                "  codex: tier-2",
                "  openclaw: tier-2-bounded",
                "  hermes: tier-2-bounded",
                "approval_rules:",
                "  canonical_state_write: explicit_user_approval_required",
                "graph_rules:",
                "  update_domain_index_on_promotion: true",
                "protected_paths:",
                "  - .env",
                "default_write_targets:",
                "  - 07_LOGS/Build-Logs/",
                "escalation_rules:",
                "  runtime_authority_unclear: fail_closed",
            ]
        ),
        encoding="utf-8",
    )


def _write_test_operator_today_manifest(vault_root: Path) -> None:
    manifest_path = vault_root / "runtime" / "workflows" / "registry" / "operator_today.yaml"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        "\n".join(
            [
                "id: operator_today",
                'name: "Operator Today"',
                'version: "1.0"',
                'description: "Test operator briefing"',
                "task_type: operator-briefing",
                "role_card: operator-briefing",
                "trigger_type: manual",
                "owner: operator",
                "status: active",
                "permission_ceiling: no_protected_file_writes",
                "writeback_targets:",
                '  - "07_LOGS/Operator-Briefs/"',
                "failure_behavior: escalate",
                "approval_rule: none",
            ]
        ),
        encoding="utf-8",
    )


def _create_rollout_roots(vault_root: Path) -> None:
    for rel_path in (
        "runtime",
        "06_AGENTS",
        "01_PROJECTS/ChaseOS",
        "04_SOPS",
        "01_PROJECTS/University",
        "00_HOME",
    ):
        (vault_root / rel_path).mkdir(parents=True, exist_ok=True)
    (vault_root / "CLAUDE.md").write_text("# test\n", encoding="utf-8")


def test_valid_profile_load(tmp_path: Path) -> None:
    profile_path = tmp_path / "workspace-mode.yaml"
    profile_path.write_text(
        """
workspace_id: chaseos
workspace_name: ChaseOS
workspace_mode: runtime_agent_ops
description: Local-first human-AI operating framework and runtime control plane.
primary_domains:
  - AI Engineering
  - Runtime Governance
canonical_state_files:
  - 00_HOME/Now.md
required_read_order:
  - README.md
allowed_knowledge_classes:
  - user-origin
  - source-derived
  - synthesized
  - generated-ideas
  - system-operational
  - canonical-state
default_output_classes:
  - build-log
allowed_workflows:
  - operator_today
runtime_adapter_ceiling:
  claude: tier-2
  codex: tier-2
  openclaw: tier-2-bounded
  hermes: tier-2-bounded
approval_rules:
  canonical_state_write: explicit_user_approval_required
  generated_idea_creation: allowed_with_label
graph_rules:
  update_domain_index_on_promotion: true
  backlinks_required_for_durable_notes: true
protected_paths:
  - .env
default_write_targets:
  - 07_LOGS/Build-Logs/
escalation_rules:
  unknown_mode: stop_and_request_mode
  runtime_authority_unclear: fail_closed
""".strip(),
        encoding="utf-8",
    )

    profile = load_workspace_profile(profile_path)

    assert profile.workspace_id == "chaseos"
    assert profile.workspace_mode == "runtime_agent_ops"
    assert profile.adapter_ceiling_for("openclaw") == "tier-2-bounded"


def test_missing_required_field_fails_validation() -> None:
    data = _valid_profile_dict()
    data.pop("approval_rules")

    with pytest.raises(WorkspaceModeValidationError, match="missing required fields"):
        load_workspace_profile_from_mapping(data)


def test_invalid_mode_and_class_fail_validation() -> None:
    data = _valid_profile_dict()
    data["workspace_mode"] = "enterprise"
    with pytest.raises(WorkspaceModeValidationError, match="invalid workspace_mode"):
        load_workspace_profile_from_mapping(data)

    data = _valid_profile_dict()
    data["allowed_knowledge_classes"] = ["generated-output"]
    with pytest.raises(WorkspaceModeValidationError, match="invalid allowed_knowledge_classes"):
        load_workspace_profile_from_mapping(data)


@pytest.mark.parametrize(
    ("path", "mode"),
    [
        ("00_HOME/Now.md", "personal_os"),
        ("01_PROJECTS/University/Degree-OS.md", "study_research"),
        ("01_PROJECTS/ChaseOS/ChaseOS-OS.md", "runtime_agent_ops"),
        ("01_PROJECTS/StrikeZone/StrikeZone-OS.md", "founder_venture"),
        ("06_AGENTS/Agent-Registry.md", "runtime_agent_ops"),
        ("runtime/aor/engine.py", "runtime_agent_ops"),
        ("04_SOPS/Build-Log-SOP.md", "business_ops"),
        ("some/random/path.md", "unknown"),
    ],
)
def test_safe_path_inference(path: str, mode: str) -> None:
    assert infer_workspace_mode(path) == mode


def test_unknown_profile_fails_closed() -> None:
    profile = build_unknown_profile("loose/path.md")

    assert profile.workspace_mode == "unknown"
    assert profile.allowed_workflows == ()
    assert profile.adapter_ceiling_for("codex") == "blocked"
    assert profile.requires_strict_runtime_controls is True


def test_fallback_yaml_parser_supports_inline_empty_collections(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("runtime.workspace_modes.loader.yaml", None)

    data = parse_profile_text(
        """
workspace_id: demo
workspace_name: Demo
workspace_mode: business_ops
description: Demo profile.
primary_domains:
  - Demo
canonical_state_files: []
required_read_order: []
allowed_knowledge_classes:
  - user-origin
default_output_classes: []
allowed_workflows: []
runtime_adapter_ceiling:
  codex: tier-2-bounded
approval_rules: {}
graph_rules: {}
protected_paths: []
default_write_targets: []
escalation_rules: {}
""".strip()
    )

    assert data["allowed_workflows"] == []
    assert data["approval_rules"] == {}


def test_runtime_mode_strictness_and_exposed_rules() -> None:
    profile = load_workspace_profile_from_mapping(_valid_profile_dict())

    assert profile.requires_strict_runtime_controls is True
    assert profile.canonical_writes_require_approval is True
    assert profile.approval_rules["protected_file_write"] == "explicit_per_file_approval_required"
    assert "07_LOGS/Agent-Activity/" in profile.default_write_targets
    assert profile.runtime_adapter_ceiling["hermes"] == "tier-2-bounded"


def test_personal_mode_is_less_runtime_strict_but_still_requires_canonical_approval() -> None:
    data = _valid_profile_dict()
    data["workspace_mode"] = "personal_os"
    data["runtime_adapter_ceiling"] = {
        "claude": "tier-3",
        "codex": "blocked",
        "openclaw": "blocked",
        "hermes": "blocked",
    }

    profile = load_workspace_profile_from_mapping(data)

    assert profile.requires_strict_runtime_controls is False
    assert profile.canonical_writes_require_approval is True
    assert profile.adapter_ceiling_for("openclaw") == "blocked"


def test_aor_route_preview_uses_explicit_profile_without_dispatch(tmp_path: Path) -> None:
    data = _valid_profile_dict()
    data["allowed_workflows"] = ["operator_today"]
    profile_path = tmp_path / "workspace-mode.yaml"
    profile_path.write_text(
        "\n".join(
            [
                "workspace_id: chaseos",
                "workspace_name: ChaseOS",
                "workspace_mode: runtime_agent_ops",
                "description: Runtime workspace.",
                "primary_domains:",
                "  - Runtime Governance",
                "canonical_state_files:",
                "  - 00_HOME/Now.md",
                "required_read_order:",
                "  - README.md",
                "allowed_knowledge_classes:",
                "  - user-origin",
                "  - source-derived",
                "  - synthesized",
                "  - generated-ideas",
                "  - system-operational",
                "  - canonical-state",
                "default_output_classes:",
                "  - build-log",
                "allowed_workflows:",
                "  - operator_today",
                "runtime_adapter_ceiling:",
                "  claude: tier-2",
                "  codex: tier-2",
                "  openclaw: tier-2-bounded",
                "  hermes: tier-2-bounded",
                "approval_rules:",
                "  canonical_state_write: explicit_user_approval_required",
                "graph_rules:",
                "  update_domain_index_on_promotion: true",
                "protected_paths:",
                "  - .env",
                "default_write_targets:",
                "  - 07_LOGS/Build-Logs/",
                "escalation_rules:",
                "  runtime_authority_unclear: fail_closed",
            ]
        ),
        encoding="utf-8",
    )

    payload = build_aor_workspace_route_preview(
        workspace_path="runtime/aor/engine.py",
        workflow_id="operator_today",
        adapter="codex",
        profile_path=profile_path,
    )

    assert payload["preview_only"] is True
    assert payload["workflow_execution_performed"] is False
    assert payload["agent_bus_task_written"] is False
    assert payload["approval_consumed"] is False
    assert payload["workspace_mode"] == "runtime_agent_ops"
    assert payload["profile_source"] == "explicit_profile"
    assert payload["adapter_ceiling"] == "tier-2"
    assert payload["workflow_allowed_by_profile"] is True
    assert payload["ready_for_aor_dispatch"] is True
    assert payload["dispatch_blockers"] == []


def test_aor_route_preview_inferred_mode_requires_explicit_profile(tmp_path: Path) -> None:
    (tmp_path / "04_SOPS").mkdir()
    (tmp_path / "CLAUDE.md").write_text("# test\n", encoding="utf-8")
    _write_test_operator_today_manifest(tmp_path)

    payload = build_aor_workspace_route_preview(
        workspace_path="04_SOPS/Build-Log-SOP.md",
        workflow_id="operator_today",
        adapter="codex",
        vault_root=tmp_path,
    )

    assert payload["workspace_mode"] == "business_ops"
    assert payload["profile_source"] == "path_inference"
    assert payload["adapter_ceiling"] == "tier-2-bounded"
    assert payload["ready_for_aor_dispatch"] is False
    assert "workflow_not_authorized_without_explicit_profile" in payload["dispatch_blockers"]
    assert "explicit_workspace_profile_required_for_aor_dispatch" in payload["dispatch_blockers"]
    assert payload["workflow_execution_performed"] is False


def test_aor_route_preview_unknown_path_blocks_dispatch() -> None:
    payload = build_aor_workspace_route_preview(
        workspace_path="loose/unmapped/path.md",
        workflow_id="operator_today",
        adapter="openclaw",
    )

    assert payload["workspace_mode"] == "unknown"
    assert payload["adapter_ceiling"] == "blocked"
    assert payload["ready_for_aor_dispatch"] is False
    assert "workspace_mode_unknown" in payload["dispatch_blockers"]
    assert "adapter_blocked:openclaw" in payload["dispatch_blockers"]


def test_canonical_cli_exposes_workspace_mode_route_preview(capsys) -> None:
    from runtime.cli.main import main as cli_main

    exit_code = cli_main(
        [
            "runtime",
            "workspace-mode",
            "route-preview",
            "--workspace-path",
            "runtime/aor/engine.py",
            "--workflow-id",
            "operator_today",
            "--adapter",
            "codex",
            "--json",
        ]
    )

    output = json.loads(capsys.readouterr().out)
    payload = output["result"]
    assert exit_code == 0
    assert output["ok"] is True
    assert output["action"] == "runtime.workspace-mode"
    assert payload["preview_only"] is True
    assert payload["workspace_mode"] == "runtime_agent_ops"
    assert payload["workflow_execution_performed"] is False
    assert payload["agent_bus_task_written"] is False
    assert payload["profile_source"] == "discovered_profile"
    assert payload["profile_source_path"] == "runtime/.workspace-mode.yaml"
    assert payload["ready_for_aor_dispatch"] is True
    assert payload["dispatch_blockers"] == []


def test_profile_rollout_plan_is_review_only(tmp_path: Path) -> None:
    (tmp_path / "runtime").mkdir()
    (tmp_path / "06_AGENTS").mkdir()
    (tmp_path / "01_PROJECTS" / "ChaseOS").mkdir(parents=True)
    (tmp_path / "04_SOPS").mkdir()
    (tmp_path / "01_PROJECTS" / "University").mkdir(parents=True)
    (tmp_path / "00_HOME").mkdir()
    (tmp_path / "CLAUDE.md").write_text("# test\n", encoding="utf-8")
    payload = build_workspace_profile_rollout_plan(vault_root=tmp_path)

    assert payload["surface"] == "workspace_mode_profile_rollout_plan"
    assert payload["preview_only"] is True
    assert payload["profile_files_written"] is False
    assert payload["aor_dispatch_enabled"] is False
    assert payload["workflow_execution_performed"] is False
    assert payload["agent_bus_task_written"] is False
    assert payload["approval_consumed"] is False
    assert payload["candidate_count"] >= 6
    assert "runtime/.workspace-mode.yaml" in payload["recommended_sequence"]
    runtime_candidate = next(
        item for item in payload["candidates"] if item["workspace_path"] == "runtime/"
    )
    assert runtime_candidate["recommended_mode"] == "runtime_agent_ops"
    assert runtime_candidate["write_allowed_in_this_pass"] is False
    assert runtime_candidate["proposed_profile"]["allowed_workflows"] == [
        "operator_today",
        "operator_close_day",
    ]


def test_profile_rollout_plan_can_target_one_workspace() -> None:
    payload = build_workspace_profile_rollout_plan(workspace_path="04_SOPS/Build-Log-SOP.md")

    assert payload["scope"] == "targeted_workspace"
    assert payload["candidate_count"] == 1
    candidate = payload["candidates"][0]
    assert candidate["workspace_path"] == "04_SOPS/Build-Log-SOP.md"
    assert candidate["recommended_mode"] == "business_ops"
    assert candidate["profile_path"] == "04_SOPS/.workspace-mode.yaml"
    assert candidate["dispatch_ready_after_this_plan"] is False
    assert candidate["proposed_profile"]["workspace_id"] == "04-sops"
    assert candidate["proposed_profile"]["runtime_adapter_ceiling"]["codex"] == "tier-2-bounded"


def test_canonical_cli_exposes_workspace_mode_rollout_plan(capsys) -> None:
    from runtime.cli.main import main as cli_main

    exit_code = cli_main(["runtime", "workspace-mode", "rollout-plan", "--json"])

    output = json.loads(capsys.readouterr().out)
    payload = output["result"]
    assert exit_code == 0
    assert output["ok"] is True
    assert output["action"] == "runtime.workspace-mode"
    assert payload["surface"] == "workspace_mode_profile_rollout_plan"
    assert payload["preview_only"] is True
    assert payload["profile_files_written"] is False
    assert payload["aor_dispatch_enabled"] is False
    assert payload["agent_bus_task_written"] is False


def test_profile_draft_packet_validates_recommended_runtime_foundation() -> None:
    payload = build_workspace_profile_draft_packet()

    assert payload["surface"] == "workspace_mode_profile_draft_packet"
    assert payload["scope"] == "recommended_runtime_foundation"
    assert payload["preview_only"] is True
    assert payload["draft_packet_only"] is True
    assert payload["profile_files_written"] is False
    assert payload["profile_write_performed"] is False
    assert payload["aor_dispatch_enabled"] is False
    assert payload["agent_bus_task_written"] is False
    assert payload["approval_consumed"] is False
    assert payload["profile_write_ready_for_operator_review"] is True
    assert payload["draft_count"] == 3
    draft_paths = [draft["profile_path"] for draft in payload["drafts"]]
    assert draft_paths == [
        "runtime/.workspace-mode.yaml",
        "06_AGENTS/.workspace-mode.yaml",
        "01_PROJECTS/ChaseOS/workspace-mode.yaml",
    ]
    runtime_draft = payload["drafts"][0]
    assert "workspace_id: runtime" in runtime_draft["draft_yaml"]
    assert runtime_draft["validation"]["mapping_validation_ok"] is True
    assert runtime_draft["validation"]["yaml_roundtrip_validation_ok"] is True
    assert runtime_draft["write_allowed_in_this_pass"] is False


def test_profile_draft_packet_blocks_existing_profile_overwrite(tmp_path: Path) -> None:
    (tmp_path / "runtime").mkdir()
    (tmp_path / "CLAUDE.md").write_text("# test\n", encoding="utf-8")
    (tmp_path / "runtime" / ".workspace-mode.yaml").write_text("existing: true\n", encoding="utf-8")

    payload = build_workspace_profile_draft_packet(
        vault_root=tmp_path,
        workspace_path="runtime/",
    )

    assert payload["scope"] == "targeted_workspace"
    assert payload["draft_count"] == 1
    draft = payload["drafts"][0]
    assert draft["profile_path"] == "runtime/.workspace-mode.yaml"
    assert draft["profile_present"] is True
    assert draft["validation"]["yaml_roundtrip_validation_ok"] is True
    assert "profile_path_already_exists_no_overwrite_without_explicit_approval" in draft["write_blockers"]
    assert "one_or_more_profile_paths_already_exist" in payload["packet_blockers"]
    assert payload["profile_files_written"] is False


def test_canonical_cli_exposes_workspace_mode_draft_packet(capsys) -> None:
    from runtime.cli.main import main as cli_main

    exit_code = cli_main(["runtime", "workspace-mode", "draft-packet", "--json"])

    output = json.loads(capsys.readouterr().out)
    payload = output["result"]
    assert exit_code == 0
    assert output["ok"] is True
    assert output["action"] == "runtime.workspace-mode"
    assert payload["surface"] == "workspace_mode_profile_draft_packet"
    assert payload["draft_count"] == 3
    assert payload["profile_files_written"] is False
    assert payload["aor_dispatch_enabled"] is False
    assert payload["agent_bus_task_written"] is False


def test_profile_write_approval_request_is_no_profile_write_preview(tmp_path: Path) -> None:
    (tmp_path / "runtime").mkdir()
    (tmp_path / "06_AGENTS").mkdir()
    (tmp_path / "01_PROJECTS" / "ChaseOS").mkdir(parents=True)
    (tmp_path / "CLAUDE.md").write_text("# test\n", encoding="utf-8")
    payload = build_workspace_profile_write_approval_request(vault_root=tmp_path)

    assert payload["surface"] == "workspace_mode_profile_write_approval_request"
    assert payload["preview_only"] is True
    assert payload["approval_request_surface_only"] is True
    assert payload["approval_request_written"] is False
    assert payload["profile_files_written"] is False
    assert payload["profile_write_performed"] is False
    assert payload["aor_dispatch_enabled"] is False
    assert payload["workflow_execution_performed"] is False
    assert payload["agent_bus_task_written"] is False
    assert payload["approval_consumed"] is False
    assert payload["canonical_write_performed"] is False
    assert payload["ready_for_operator_decision"] is True
    assert payload["selected_profile_paths"] == [
        "runtime/.workspace-mode.yaml",
        "06_AGENTS/.workspace-mode.yaml",
        "01_PROJECTS/ChaseOS/workspace-mode.yaml",
    ]
    assert "APPROVE WML PROFILE FILE CREATION ONLY:" in payload["operator_confirmation_text"]
    assert "No AOR dispatch." in payload["operator_confirmation_text"]


def test_profile_write_approval_request_can_write_pending_artifact_without_profiles(tmp_path: Path) -> None:
    (tmp_path / "runtime").mkdir()
    (tmp_path / "06_AGENTS").mkdir()
    (tmp_path / "01_PROJECTS" / "ChaseOS").mkdir(parents=True)
    (tmp_path / "CLAUDE.md").write_text("# test\n", encoding="utf-8")

    payload = build_workspace_profile_write_approval_request(
        vault_root=tmp_path,
        requested_by="Codex",
        approval_packet_id="wml-profile-write-appr-test",
        write_approval_request=True,
    )

    artifact_path = tmp_path / payload["approval_artifact_path"]
    assert payload["approval_request_written"] is True
    assert artifact_path.exists()
    approval = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert approval["status"] == "pending_operator_decision"
    assert approval["approval_scope"]["profile_file_creation_only"] is True
    assert approval["approval_scope"]["aor_dispatch_allowed"] is False
    assert (tmp_path / "runtime" / ".workspace-mode.yaml").exists() is False
    assert (tmp_path / "06_AGENTS" / ".workspace-mode.yaml").exists() is False
    assert (tmp_path / "01_PROJECTS" / "ChaseOS" / "workspace-mode.yaml").exists() is False

    duplicate = build_workspace_profile_write_approval_request(
        vault_root=tmp_path,
        requested_by="Codex",
        approval_packet_id="wml-profile-write-appr-test",
        write_approval_request=True,
    )
    assert duplicate["approval_request_written"] is False
    assert "approval_artifact_already_exists_no_overwrite" in duplicate["blockers"]


def test_guarded_profile_writer_blocks_without_matching_id_and_confirm(tmp_path: Path) -> None:
    (tmp_path / "runtime").mkdir()
    (tmp_path / "06_AGENTS").mkdir()
    (tmp_path / "01_PROJECTS" / "ChaseOS").mkdir(parents=True)
    (tmp_path / "CLAUDE.md").write_text("# test\n", encoding="utf-8")

    payload = build_workspace_profile_guarded_write(
        vault_root=tmp_path,
        approval_packet_id="wrong-id",
        requested_by="Codex",
    )

    assert payload["surface"] == "workspace_mode_profile_guarded_writer"
    assert payload["profile_files_written"] is False
    assert payload["profile_write_performed"] is False
    assert payload["aor_dispatch_enabled"] is False
    assert payload["workflow_execution_performed"] is False
    assert payload["agent_bus_task_written"] is False
    assert payload["approval_consumed"] is False
    assert "approval_packet_id_required_or_mismatched" in payload["blockers"]
    assert "confirm_required" in payload["blockers"]
    assert (tmp_path / "runtime" / ".workspace-mode.yaml").exists() is False
    assert (tmp_path / "06_AGENTS" / ".workspace-mode.yaml").exists() is False
    assert (tmp_path / "01_PROJECTS" / "ChaseOS" / "workspace-mode.yaml").exists() is False


def test_guarded_profile_writer_creates_only_approved_profiles(tmp_path: Path) -> None:
    (tmp_path / "runtime").mkdir()
    (tmp_path / "06_AGENTS").mkdir()
    (tmp_path / "01_PROJECTS" / "ChaseOS").mkdir(parents=True)
    (tmp_path / "CLAUDE.md").write_text("# test\n", encoding="utf-8")
    approval = build_workspace_profile_write_approval_request(vault_root=tmp_path)

    payload = build_workspace_profile_guarded_write(
        vault_root=tmp_path,
        approval_packet_id=approval["approval_packet_id"],
        requested_by="Codex",
        confirm=True,
    )

    assert payload["ok"] is True
    assert payload["approval_packet_matched"] is True
    assert payload["operator_confirmed"] is True
    assert payload["ready_for_profile_write"] is True
    assert payload["profile_files_written"] is True
    assert payload["profile_write_performed"] is True
    assert payload["profile_overwrite_performed"] is False
    assert payload["written_profile_count"] == 3
    assert payload["approval_artifact_consumed"] is False
    assert payload["approval_consumed"] is False
    assert payload["aor_dispatch_enabled"] is False
    assert payload["workflow_execution_performed"] is False
    assert payload["agent_bus_task_written"] is False
    assert (tmp_path / "runtime" / ".workspace-mode.yaml").exists()
    assert (tmp_path / "06_AGENTS" / ".workspace-mode.yaml").exists()
    assert (tmp_path / "01_PROJECTS" / "ChaseOS" / "workspace-mode.yaml").exists()
    assert load_workspace_profile(tmp_path / "runtime" / ".workspace-mode.yaml").workspace_mode == "runtime_agent_ops"

    duplicate = build_workspace_profile_guarded_write(
        vault_root=tmp_path,
        approval_packet_id=approval["approval_packet_id"],
        requested_by="Codex",
        confirm=True,
    )
    assert duplicate["profile_files_written"] is False
    assert "profile_path_already_exists_no_overwrite:runtime/.workspace-mode.yaml" in duplicate["blockers"]


def test_canonical_cli_exposes_workspace_mode_guarded_profile_writer(capsys, tmp_path: Path) -> None:
    from runtime.cli.main import main as cli_main

    (tmp_path / "runtime").mkdir()
    (tmp_path / "06_AGENTS").mkdir()
    (tmp_path / "01_PROJECTS" / "ChaseOS").mkdir(parents=True)
    (tmp_path / "CLAUDE.md").write_text("# test\n", encoding="utf-8")
    approval = build_workspace_profile_write_approval_request(vault_root=tmp_path)

    exit_code = cli_main(
        [
            "runtime",
            "workspace-mode",
            "write-profiles",
            "--vault-root",
            str(tmp_path),
            "--gate-approval-id",
            approval["approval_packet_id"],
            "--requested-by",
            "Codex",
            "--confirm",
            "--json",
        ]
    )

    output = json.loads(capsys.readouterr().out)
    payload = output["result"]
    assert exit_code == 0
    assert output["ok"] is True
    assert output["action"] == "runtime.workspace-mode"
    assert payload["surface"] == "workspace_mode_profile_guarded_writer"
    assert payload["profile_files_written"] is True
    assert payload["profile_write_performed"] is True
    assert payload["workflow_execution_performed"] is False
    assert payload["agent_bus_task_written"] is False


def test_full_product_profile_scope_writes_remaining_missing_profiles(tmp_path: Path) -> None:
    _create_rollout_roots(tmp_path)

    foundation_approval = build_workspace_profile_write_approval_request(
        vault_root=tmp_path,
        requested_by="Codex",
    )
    foundation_write = build_workspace_profile_guarded_write(
        vault_root=tmp_path,
        approval_packet_id=foundation_approval["approval_packet_id"],
        requested_by="Codex",
        confirm=True,
    )
    assert foundation_write["profile_files_written"] is True
    assert foundation_write["written_profile_count"] == 3

    full_approval = build_workspace_profile_write_approval_request(
        vault_root=tmp_path,
        profile_scope="full-product",
        requested_by="Codex",
    )

    assert full_approval["draft_packet"]["scope"] == "full_product_missing_profiles"
    assert full_approval["selected_profile_paths"] == [
        "04_SOPS/.workspace-mode.yaml",
        "01_PROJECTS/University/workspace-mode.yaml",
        "00_HOME/.workspace-mode.yaml",
    ]
    assert full_approval["ready_for_operator_decision"] is True

    full_write = build_workspace_profile_guarded_write(
        vault_root=tmp_path,
        profile_scope="full-product",
        approval_packet_id=full_approval["approval_packet_id"],
        requested_by="Codex",
        confirm=True,
    )

    assert full_write["profile_files_written"] is True
    assert full_write["written_profile_count"] == 3
    assert (tmp_path / "04_SOPS" / ".workspace-mode.yaml").exists()
    assert (tmp_path / "01_PROJECTS" / "University" / "workspace-mode.yaml").exists()
    assert (tmp_path / "00_HOME" / ".workspace-mode.yaml").exists()
    assert full_write["workflow_execution_performed"] is False
    assert full_write["agent_bus_task_written"] is False
    assert full_write["canonical_write_performed"] is False


def test_workspace_mode_product_status_reports_profile_coverage(tmp_path: Path) -> None:
    _create_rollout_roots(tmp_path)
    foundation_approval = build_workspace_profile_write_approval_request(
        vault_root=tmp_path,
        requested_by="Codex",
    )
    build_workspace_profile_guarded_write(
        vault_root=tmp_path,
        approval_packet_id=foundation_approval["approval_packet_id"],
        requested_by="Codex",
        confirm=True,
    )
    full_approval = build_workspace_profile_write_approval_request(
        vault_root=tmp_path,
        profile_scope="full-product",
        requested_by="Codex",
    )
    build_workspace_profile_guarded_write(
        vault_root=tmp_path,
        profile_scope="full-product",
        approval_packet_id=full_approval["approval_packet_id"],
        requested_by="Codex",
        confirm=True,
    )

    payload = build_workspace_mode_product_status(vault_root=tmp_path)

    assert payload["surface"] == "workspace_mode_product_status"
    assert payload["preview_only"] is True
    assert payload["profile_coverage"]["profile_coverage_complete"] is True
    assert payload["profile_coverage"]["profiles_valid_count"] == 6
    assert payload["authority_flags"]["workflow_execution_performed"] is False
    assert payload["authority_flags"]["approval_consumed"] is False


def test_workspace_mode_approval_ledger_is_read_only(tmp_path: Path) -> None:
    _create_rollout_roots(tmp_path)
    approval = build_workspace_profile_write_approval_request(
        vault_root=tmp_path,
        profile_scope="full-product",
        requested_by="Codex",
        write_approval_request=True,
    )

    payload = build_workspace_mode_approval_ledger(vault_root=tmp_path)

    assert approval["approval_request_written"] is True
    assert payload["surface"] == "workspace_mode_approval_ledger"
    assert payload["total_artifacts"] == 1
    assert payload["sections"]["profile_write_requests"]["count"] == 1
    assert payload["profile_files_written"] is False
    assert payload["workflow_execution_performed"] is False
    assert payload["approval_consumed"] is False


def test_canonical_cli_exposes_workspace_mode_product_status_and_ledger(capsys, tmp_path: Path) -> None:
    from runtime.cli.main import main as cli_main

    _create_rollout_roots(tmp_path)

    status_exit = cli_main(
        [
            "runtime",
            "workspace-mode",
            "product-status",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    status_output = json.loads(capsys.readouterr().out)
    assert status_exit == 0
    assert status_output["action"] == "runtime.workspace-mode"
    assert status_output["result"]["surface"] == "workspace_mode_product_status"

    ledger_exit = cli_main(
        [
            "runtime",
            "workspace-mode",
            "approval-ledger",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    ledger_output = json.loads(capsys.readouterr().out)
    assert ledger_exit == 0
    assert ledger_output["action"] == "runtime.workspace-mode"
    assert ledger_output["result"]["surface"] == "workspace_mode_approval_ledger"


def test_aor_dispatch_gate_blocks_without_confirmation() -> None:
    payload = build_workspace_mode_aor_dispatch_gate(
        workspace_path="runtime/aor/engine.py",
        workflow_id="operator_today",
        adapter="codex",
        requested_by="Codex",
    )

    assert payload["surface"] == "workspace_mode_aor_dispatch_gate"
    assert payload["preview_only"] is True
    assert payload["dispatch_gate_only"] is True
    assert payload["route_preview_ready_for_aor_dispatch"] is True
    assert payload["dispatch_gate_cleared"] is False
    assert payload["ready_for_guarded_aor_executor"] is False
    assert "confirm_required_to_clear_dispatch_gate" in payload["blockers"]
    assert payload["aor_dispatch_enabled"] is False
    assert payload["run_workflow_called"] is False
    assert payload["workflow_execution_performed"] is False
    assert payload["workflow_writeback_performed"] is False
    assert payload["agent_bus_task_written"] is False
    assert payload["approval_consumed"] is False


def test_aor_dispatch_gate_clears_confirmed_explicit_profile_without_execution() -> None:
    payload = build_workspace_mode_aor_dispatch_gate(
        workspace_path="runtime/aor/engine.py",
        workflow_id="operator_today",
        adapter="codex",
        requested_by="Codex",
        confirm=True,
    )

    assert payload["dispatch_gate_cleared"] is True
    assert payload["ready_for_guarded_aor_executor"] is True
    assert payload["profile_source"] == "discovered_profile"
    assert payload["profile_source_path"] == "runtime/.workspace-mode.yaml"
    assert payload["workspace_mode"] == "runtime_agent_ops"
    assert payload["requested_workflow_id"] == "operator_today"
    assert payload["requested_adapter"] == "codex"
    assert payload["blockers"] == []
    assert payload["aor_dispatch_enabled"] is False
    assert payload["run_workflow_called"] is False
    assert payload["workflow_execution_performed"] is False
    assert payload["workflow_writeback_performed"] is False
    assert payload["next_recommended_pass"] == "workspace-mode-aor-dispatch-dry-run-executor"


def test_aor_dispatch_gate_keeps_inferred_mode_blocked_even_with_confirmation(tmp_path: Path) -> None:
    (tmp_path / "04_SOPS").mkdir()
    (tmp_path / "CLAUDE.md").write_text("# test\n", encoding="utf-8")
    _write_test_operator_today_manifest(tmp_path)

    payload = build_workspace_mode_aor_dispatch_gate(
        workspace_path="04_SOPS/Build-Log-SOP.md",
        workflow_id="operator_today",
        adapter="codex",
        vault_root=tmp_path,
        requested_by="Codex",
        confirm=True,
    )

    assert payload["workspace_mode"] == "business_ops"
    assert payload["profile_source"] == "path_inference"
    assert payload["dispatch_gate_cleared"] is False
    assert "explicit_workspace_profile_required_for_aor_dispatch" in payload["blockers"]
    assert "route_preview_not_ready_for_aor_dispatch" in payload["blockers"]
    assert payload["run_workflow_called"] is False
    assert payload["workflow_execution_performed"] is False


def test_canonical_cli_exposes_workspace_mode_aor_dispatch_gate(capsys) -> None:
    from runtime.cli.main import main as cli_main

    exit_code = cli_main(
        [
            "runtime",
            "workspace-mode",
            "dispatch-gate",
            "--workspace-path",
            "runtime/aor/engine.py",
            "--workflow-id",
            "operator_today",
            "--adapter",
            "codex",
            "--requested-by",
            "Codex",
            "--confirm",
            "--json",
        ]
    )

    output = json.loads(capsys.readouterr().out)
    payload = output["result"]
    assert exit_code == 0
    assert output["ok"] is True
    assert output["action"] == "runtime.workspace-mode"
    assert payload["surface"] == "workspace_mode_aor_dispatch_gate"
    assert payload["dispatch_gate_cleared"] is True
    assert payload["run_workflow_called"] is False
    assert payload["workflow_execution_performed"] is False
    assert payload["agent_bus_task_written"] is False


def test_aor_dispatch_dry_run_executor_calls_run_workflow_dry_run_only(monkeypatch) -> None:
    calls: list[dict[str, object]] = []

    def fake_run_workflow(workflow_id, *, inputs, vault_root=None, dry_run=False):
        calls.append(
            {
                "workflow_id": workflow_id,
                "inputs": inputs,
                "vault_root": vault_root,
                "dry_run": dry_run,
            }
        )
        return AORRunResult(
            workflow_id=workflow_id,
            status="dry_run_ok",
            audit_id="audit-test",
            stage_reached="dry_run_exit",
            outputs={"dry_run": True},
        )

    monkeypatch.setattr(aor_dry_run_executor, "run_workflow", fake_run_workflow)

    payload = aor_dry_run_executor.build_workspace_mode_aor_dispatch_dry_run_executor(
        workspace_path="runtime/aor/engine.py",
        workflow_id="operator_today",
        adapter="codex",
        requested_by="Codex",
        confirm=True,
    )

    assert payload["ok"] is True
    assert payload["dispatch_gate_cleared"] is True
    assert payload["aor_dry_run_performed"] is True
    assert payload["run_workflow_called"] is True
    assert payload["run_workflow_dry_run"] is True
    assert payload["workflow_execution_performed"] is False
    assert payload["workflow_writeback_performed"] is False
    assert payload["agent_bus_task_written"] is False
    assert payload["aor_result"]["status"] == "dry_run_ok"
    assert payload["aor_dry_run_audit_id"] == "audit-test"
    assert calls == [
        {
            "workflow_id": "operator_today",
            "inputs": {
                "workspace_path": "runtime/aor/engine.py",
                "requested_by": "Codex",
                "wml_dispatch_gate_packet_id": payload["dispatch_gate_packet_id"],
            },
            "vault_root": Path(payload["dispatch_gate"]["vault_root"]),
            "dry_run": True,
        }
    ]


def test_aor_dispatch_dry_run_executor_blocks_before_run_workflow(monkeypatch, tmp_path: Path) -> None:
    (tmp_path / "04_SOPS").mkdir()
    (tmp_path / "CLAUDE.md").write_text("# test\n", encoding="utf-8")
    _write_test_operator_today_manifest(tmp_path)
    calls: list[object] = []
    monkeypatch.setattr(
        aor_dry_run_executor,
        "run_workflow",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    payload = aor_dry_run_executor.build_workspace_mode_aor_dispatch_dry_run_executor(
        workspace_path="04_SOPS/Build-Log-SOP.md",
        workflow_id="operator_today",
        adapter="codex",
        vault_root=tmp_path,
        requested_by="Codex",
        confirm=True,
    )

    assert payload["ok"] is False
    assert payload["dispatch_gate_cleared"] is False
    assert payload["aor_dry_run_performed"] is False
    assert payload["run_workflow_called"] is False
    assert payload["workflow_execution_performed"] is False
    assert "explicit_workspace_profile_required_for_aor_dispatch" in payload["blockers"]
    assert calls == []


def test_canonical_cli_exposes_workspace_mode_aor_dispatch_dry_run_executor(capsys, monkeypatch) -> None:
    from runtime.cli.main import main as cli_main

    def fake_run_workflow(workflow_id, *, inputs, vault_root=None, dry_run=False):
        return AORRunResult(
            workflow_id=workflow_id,
            status="dry_run_ok",
            audit_id="audit-cli",
            stage_reached="dry_run_exit",
            outputs={"dry_run": True},
        )

    monkeypatch.setattr(aor_dry_run_executor, "run_workflow", fake_run_workflow)

    exit_code = cli_main(
        [
            "runtime",
            "workspace-mode",
            "dispatch-dry-run",
            "--workspace-path",
            "runtime/aor/engine.py",
            "--workflow-id",
            "operator_today",
            "--adapter",
            "codex",
            "--requested-by",
            "Codex",
            "--confirm",
            "--json",
        ]
    )

    output = json.loads(capsys.readouterr().out)
    payload = output["result"]
    assert exit_code == 0
    assert output["ok"] is True
    assert output["action"] == "runtime.workspace-mode"
    assert payload["surface"] == "workspace_mode_aor_dispatch_dry_run_executor"
    assert payload["dispatch_gate_cleared"] is True
    assert payload["run_workflow_called"] is True
    assert payload["run_workflow_dry_run"] is True
    assert payload["workflow_execution_performed"] is False
    assert payload["workflow_writeback_performed"] is False


def test_aor_live_execution_approval_gate_previews_without_live_execution(tmp_path: Path) -> None:
    (tmp_path / "runtime" / "aor").mkdir(parents=True)
    (tmp_path / "CLAUDE.md").write_text("# test\n", encoding="utf-8")
    _write_test_profile(tmp_path / "runtime" / ".workspace-mode.yaml")
    _write_test_operator_today_manifest(tmp_path)

    payload = build_workspace_mode_aor_live_execution_approval_gate(
        vault_root=tmp_path,
        workspace_path="runtime/aor/engine.py",
        workflow_id="operator_today",
        adapter="codex",
        requested_by="Codex",
        confirm=True,
    )

    assert payload["ok"] is True
    assert payload["surface"] == "workspace_mode_aor_live_execution_approval_gate"
    assert payload["approval_request_surface_only"] is True
    assert payload["preview_only"] is True
    assert payload["approval_request_written"] is False
    assert payload["ready_for_operator_decision"] is True
    assert payload["dispatch_gate_cleared"] is True
    assert payload["live_execution_approval_required"] is True
    assert payload["live_execution_approved"] is False
    assert payload["run_workflow_called"] is False
    assert payload["run_workflow_live_called"] is False
    assert payload["workflow_execution_performed"] is False
    assert payload["workflow_writeback_performed"] is False
    assert payload["agent_bus_task_written"] is False
    assert payload["approval_consumed"] is False
    assert payload["canonical_write_performed"] is False
    assert "APPROVE WML-GATED LIVE AOR EXECUTION ONLY:" in payload["operator_confirmation_text"]
    assert "requires_fresh_aor_dry_run_evidence" in payload["approval_artifact_preview"]["approval_scope"]


def test_aor_live_execution_approval_gate_writes_pending_artifact_create_only(tmp_path: Path) -> None:
    (tmp_path / "runtime" / "aor").mkdir(parents=True)
    (tmp_path / "CLAUDE.md").write_text("# test\n", encoding="utf-8")
    _write_test_profile(tmp_path / "runtime" / ".workspace-mode.yaml")
    _write_test_operator_today_manifest(tmp_path)

    payload = build_workspace_mode_aor_live_execution_approval_gate(
        vault_root=tmp_path,
        workspace_path="runtime/aor/engine.py",
        workflow_id="operator_today",
        adapter="codex",
        requested_by="Codex",
        approval_packet_id="wml-aor-live-exec-appr-test",
        write_approval_request=True,
        confirm=True,
    )

    artifact_path = tmp_path / payload["approval_artifact_path"]
    assert payload["ok"] is True
    assert payload["approval_request_written"] is True
    assert artifact_path.exists()
    approval = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert approval["status"] == "pending_operator_decision"
    assert approval["approval_scope"]["workflow_id"] == "operator_today"
    assert approval["approval_scope"]["live_aor_execution_allowed_after_separate_consumption"] is True
    assert approval["approval_scope"]["agent_bus_task_allowed"] is False
    assert approval["authority_flags"]["run_workflow_live_called"] is False
    assert payload["run_workflow_called"] is False
    assert payload["workflow_execution_performed"] is False
    assert payload["workflow_writeback_performed"] is False

    duplicate = build_workspace_mode_aor_live_execution_approval_gate(
        vault_root=tmp_path,
        workspace_path="runtime/aor/engine.py",
        workflow_id="operator_today",
        adapter="codex",
        requested_by="Codex",
        approval_packet_id="wml-aor-live-exec-appr-test",
        write_approval_request=True,
        confirm=True,
    )
    assert duplicate["ok"] is False
    assert duplicate["approval_request_written"] is False
    assert "approval_artifact_already_exists_no_overwrite" in duplicate["blockers"]


def test_aor_live_execution_approval_gate_blocks_before_artifact_when_dispatch_gate_blocks(tmp_path: Path) -> None:
    (tmp_path / "04_SOPS").mkdir()
    (tmp_path / "CLAUDE.md").write_text("# test\n", encoding="utf-8")
    _write_test_operator_today_manifest(tmp_path)

    payload = build_workspace_mode_aor_live_execution_approval_gate(
        vault_root=tmp_path,
        workspace_path="04_SOPS/Build-Log-SOP.md",
        workflow_id="operator_today",
        adapter="codex",
        requested_by="Codex",
        write_approval_request=True,
        confirm=True,
    )

    assert payload["ok"] is False
    assert payload["approval_request_written"] is False
    assert payload["dispatch_gate_cleared"] is False
    assert "dispatch_gate_not_cleared" in payload["blockers"]
    assert "explicit_workspace_profile_required_for_aor_dispatch" in payload["blockers"]
    assert payload["run_workflow_called"] is False
    assert payload["workflow_execution_performed"] is False


def test_canonical_cli_exposes_workspace_mode_aor_live_execution_approval_gate(capsys, tmp_path: Path) -> None:
    from runtime.cli.main import main as cli_main

    (tmp_path / "runtime" / "aor").mkdir(parents=True)
    (tmp_path / "CLAUDE.md").write_text("# test\n", encoding="utf-8")
    _write_test_profile(tmp_path / "runtime" / ".workspace-mode.yaml")
    _write_test_operator_today_manifest(tmp_path)

    exit_code = cli_main(
        [
            "runtime",
            "workspace-mode",
            "live-execution-approval-gate",
            "--vault-root",
            str(tmp_path),
            "--workspace-path",
            "runtime/aor/engine.py",
            "--workflow-id",
            "operator_today",
            "--adapter",
            "codex",
            "--requested-by",
            "Codex",
            "--confirm",
            "--json",
        ]
    )

    output = json.loads(capsys.readouterr().out)
    payload = output["result"]
    assert exit_code == 0
    assert output["ok"] is True
    assert output["action"] == "runtime.workspace-mode"
    assert payload["surface"] == "workspace_mode_aor_live_execution_approval_gate"
    assert payload["ready_for_operator_decision"] is True
    assert payload["approval_request_written"] is False
    assert payload["run_workflow_called"] is False
    assert payload["workflow_execution_performed"] is False
    assert payload["workflow_writeback_performed"] is False


def test_aor_live_executor_consumes_approved_packet_exact_once(monkeypatch, tmp_path: Path) -> None:
    (tmp_path / "runtime" / "aor").mkdir(parents=True)
    (tmp_path / "CLAUDE.md").write_text("# test\n", encoding="utf-8")
    _write_test_profile(tmp_path / "runtime" / ".workspace-mode.yaml")
    _write_test_operator_today_manifest(tmp_path)
    approval = build_workspace_mode_aor_live_execution_approval_gate(
        vault_root=tmp_path,
        workspace_path="runtime/aor/engine.py",
        workflow_id="operator_today",
        adapter="codex",
        requested_by="Codex",
        approval_packet_id="wml-aor-live-exec-appr-test",
        write_approval_request=True,
        confirm=True,
    )
    calls: list[dict[str, object]] = []

    def fake_dry_run(**kwargs):
        return {
            "ok": True,
            "aor_dry_run_performed": True,
            "aor_dry_run_audit_id": "dry-audit-test",
            "aor_result": {"status": "dry_run_ok", "audit_id": "dry-audit-test"},
            "blockers": [],
        }

    def fake_run_workflow(workflow_id, *, inputs, vault_root=None, dry_run=False):
        calls.append(
            {
                "workflow_id": workflow_id,
                "inputs": inputs,
                "vault_root": vault_root,
                "dry_run": dry_run,
            }
        )
        return AORRunResult(
            workflow_id=workflow_id,
            status="success",
            audit_id="live-audit-test",
            stage_reached="audit_record",
            outputs={
                "run": {"handler_status": "executed"},
                "writeback": {"written": [{"path": "07_LOGS/Operator-Briefs/test.md"}]},
            },
        )

    monkeypatch.setattr(aor_live_executor, "build_workspace_mode_aor_dispatch_dry_run_executor", fake_dry_run)
    monkeypatch.setattr(aor_live_executor, "run_workflow", fake_run_workflow)

    payload = aor_live_executor.build_workspace_mode_aor_live_executor(
        vault_root=tmp_path,
        workspace_path="runtime/aor/engine.py",
        workflow_id="operator_today",
        adapter="codex",
        gate_approval_id=approval["approval_packet_id"],
        requested_by="Codex",
        decision="approved",
        write_approval_decision=True,
        write_approval_consumption=True,
        write_consumption_marker=True,
        confirm=True,
    )

    assert payload["ok"] is True
    assert payload["approval_consumed"] is True
    assert payload["decision_artifact_written"] is True
    assert payload["consumption_marker_written"] is True
    assert payload["consumption_artifact_written"] is True
    assert payload["fresh_aor_dry_run_performed"] is True
    assert payload["fresh_aor_dry_run_audit_id"] == "dry-audit-test"
    assert payload["run_workflow_called"] is True
    assert payload["run_workflow_live_called"] is True
    assert payload["workflow_execution_performed"] is True
    assert payload["workflow_writeback_performed"] is True
    assert payload["agent_bus_task_written"] is False
    assert payload["provider_or_model_call_performed"] is False
    assert payload["browser_or_external_action_performed"] is False
    assert payload["canonical_write_performed"] is False
    assert payload["aor_live_result"]["status"] == "success"
    assert (tmp_path / payload["decision_artifact_path"]).exists()
    assert (tmp_path / payload["exact_once_marker_path"]).exists()
    assert (tmp_path / payload["consumption_artifact_path"]).exists()
    assert calls == [
        {
            "workflow_id": "operator_today",
            "inputs": {
                "workspace_path": "runtime/aor/engine.py",
                "requested_by": "Codex",
                "wml_live_execution_approval_packet_id": approval["approval_packet_id"],
                "wml_dispatch_gate_packet_id": payload["dispatch_gate_packet_id"],
                "wml_fresh_dry_run_audit_id": "dry-audit-test",
            },
            "vault_root": tmp_path.resolve(),
            "dry_run": False,
        }
    ]


def test_aor_live_executor_blocks_duplicate_before_live_run(monkeypatch, tmp_path: Path) -> None:
    (tmp_path / "runtime" / "aor").mkdir(parents=True)
    (tmp_path / "CLAUDE.md").write_text("# test\n", encoding="utf-8")
    _write_test_profile(tmp_path / "runtime" / ".workspace-mode.yaml")
    _write_test_operator_today_manifest(tmp_path)
    approval = build_workspace_mode_aor_live_execution_approval_gate(
        vault_root=tmp_path,
        workspace_path="runtime/aor/engine.py",
        workflow_id="operator_today",
        adapter="codex",
        requested_by="Codex",
        approval_packet_id="wml-aor-live-exec-appr-test",
        write_approval_request=True,
        confirm=True,
    )

    def fake_dry_run(**kwargs):
        return {
            "ok": True,
            "aor_dry_run_performed": True,
            "aor_dry_run_audit_id": "dry-audit-test",
            "aor_result": {"status": "dry_run_ok", "audit_id": "dry-audit-test"},
            "blockers": [],
        }

    monkeypatch.setattr(aor_live_executor, "build_workspace_mode_aor_dispatch_dry_run_executor", fake_dry_run)
    monkeypatch.setattr(
        aor_live_executor,
        "run_workflow",
        lambda *args, **kwargs: AORRunResult(
            workflow_id="operator_today",
            status="success",
            audit_id="live-audit-test",
            stage_reached="audit_record",
            outputs={},
        ),
    )
    first = aor_live_executor.build_workspace_mode_aor_live_executor(
        vault_root=tmp_path,
        workspace_path="runtime/aor/engine.py",
        workflow_id="operator_today",
        adapter="codex",
        gate_approval_id=approval["approval_packet_id"],
        requested_by="Codex",
        decision="approved",
        write_approval_decision=True,
        write_approval_consumption=True,
        write_consumption_marker=True,
        confirm=True,
    )
    assert first["ok"] is True

    calls: list[object] = []
    monkeypatch.setattr(aor_live_executor, "run_workflow", lambda *args, **kwargs: calls.append((args, kwargs)))

    duplicate = aor_live_executor.build_workspace_mode_aor_live_executor(
        vault_root=tmp_path,
        workspace_path="runtime/aor/engine.py",
        workflow_id="operator_today",
        adapter="codex",
        gate_approval_id=approval["approval_packet_id"],
        requested_by="Codex",
        decision="approved",
        write_approval_decision=True,
        write_approval_consumption=True,
        write_consumption_marker=True,
        confirm=True,
    )

    assert duplicate["ok"] is False
    assert duplicate["run_workflow_called"] is False
    assert duplicate["workflow_execution_performed"] is False
    assert "exact_once_marker_already_present" in duplicate["blockers"]
    assert calls == []


def test_canonical_cli_exposes_workspace_mode_aor_live_executor(capsys, monkeypatch, tmp_path: Path) -> None:
    from runtime.cli.main import main as cli_main

    (tmp_path / "runtime" / "aor").mkdir(parents=True)
    (tmp_path / "CLAUDE.md").write_text("# test\n", encoding="utf-8")
    _write_test_profile(tmp_path / "runtime" / ".workspace-mode.yaml")
    _write_test_operator_today_manifest(tmp_path)
    approval = build_workspace_mode_aor_live_execution_approval_gate(
        vault_root=tmp_path,
        workspace_path="runtime/aor/engine.py",
        workflow_id="operator_today",
        adapter="codex",
        requested_by="Codex",
        approval_packet_id="wml-aor-live-exec-appr-test",
        write_approval_request=True,
        confirm=True,
    )

    monkeypatch.setattr(
        aor_live_executor,
        "build_workspace_mode_aor_dispatch_dry_run_executor",
        lambda **kwargs: {
            "ok": True,
            "aor_dry_run_performed": True,
            "aor_dry_run_audit_id": "dry-audit-cli",
            "aor_result": {"status": "dry_run_ok", "audit_id": "dry-audit-cli"},
            "blockers": [],
        },
    )
    monkeypatch.setattr(
        aor_live_executor,
        "run_workflow",
        lambda workflow_id, *, inputs, vault_root=None, dry_run=False: AORRunResult(
            workflow_id=workflow_id,
            status="success",
            audit_id="live-audit-cli",
            stage_reached="audit_record",
            outputs={"run": {}, "writeback": {}},
        ),
    )

    exit_code = cli_main(
        [
            "runtime",
            "workspace-mode",
            "live-executor",
            "--vault-root",
            str(tmp_path),
            "--workspace-path",
            "runtime/aor/engine.py",
            "--workflow-id",
            "operator_today",
            "--adapter",
            "codex",
            "--requested-by",
            "Codex",
            "--gate-approval-id",
            approval["approval_packet_id"],
            "--decision",
            "approved",
            "--write-approval-decision",
            "--write-approval-consumption",
            "--write-consumption-marker",
            "--confirm",
            "--json",
        ]
    )

    output = json.loads(capsys.readouterr().out)
    payload = output["result"]
    assert exit_code == 0
    assert output["ok"] is True
    assert output["action"] == "runtime.workspace-mode"
    assert payload["surface"] == "workspace_mode_aor_live_executor"
    assert payload["approval_consumed"] is True
    assert payload["run_workflow_live_called"] is True
    assert payload["workflow_execution_performed"] is True
    assert payload["workflow_writeback_performed"] is True


def test_canonical_cli_exposes_workspace_mode_write_approval_request(capsys) -> None:
    from runtime.cli.main import main as cli_main

    exit_code = cli_main(
        [
            "runtime",
            "workspace-mode",
            "write-approval-request",
            "--requested-by",
            "Codex",
            "--json",
        ]
    )

    output = json.loads(capsys.readouterr().out)
    payload = output["result"]
    assert exit_code == 0
    assert output["ok"] is True
    assert output["action"] == "runtime.workspace-mode"
    assert payload["surface"] == "workspace_mode_profile_write_approval_request"
    assert payload["approval_request_written"] is False
    assert payload["profile_files_written"] is False
    assert payload["aor_dispatch_enabled"] is False
    assert payload["agent_bus_task_written"] is False
