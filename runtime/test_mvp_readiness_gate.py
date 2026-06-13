from __future__ import annotations

import json
import re
import sqlite3
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import runtime.cli.main as cli  # noqa: E402
from runtime.mvp_readiness_gate import (  # noqa: E402
    PENDING_CHAT_APPROVAL_ID,
    build_mvp_completion_audit,
    build_mvp_credential_handoff,
    build_mvp_current_state,
    build_mvp_operator_action_required,
    build_mvp_operator_input_template_packet,
    build_mvp_operator_input_validation,
    build_mvp_operator_unblock_packet,
    build_mvp_readiness_gate,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _seed_minimal_vault(root: Path, *, secret_target: str = "SET_OPENAI_SECRET_REF") -> None:
    _write_json(
        root / "runtime" / "setup_state.json",
        {
            "providers": {
                "openai": {
                    "configured": True,
                    "default_model": "gpt-5.5",
                    "secret_reference_kind": "env-var-or-local-secret-ref",
                    "secret_reference_present": True,
                    "secret_reference_target": secret_target,
                }
            },
            "integrations": {},
        },
    )
    _write_json(
        root / "runtime" / "studio" / "approvals" / f"{PENDING_CHAT_APPROVAL_ID}.json",
        {
            "approval_id": PENDING_CHAT_APPROVAL_ID,
            "status": "pending",
            "submitted_at": "2026-05-13T11:11:12Z",
            "action_spec": {
                "action_type": "create_file",
                "target_path": "01_PROJECTS/_chat_proposals/example.md",
                "submitted_by": "studio-chat",
            },
        },
    )
    _write_json(
        root / "runtime" / "studio" / "approvals" / "executed-example.json",
        {
            "approval_id": "executed-example",
            "status": "executed",
            "execution_status": "succeeded",
            "result_action_id": "task-executed-example",
            "action_spec": {
                "action_type": "agent_bus_task",
                "metadata": {
                    "agent_bus_task_write_performed": True,
                    "provider_call_performed": False,
                    "browser_control_performed": False,
                    "target_vault_write_performed": False,
                    "workflow_dispatched": False,
                    "canonical_mutation_performed": False,
                },
            },
        },
    )
    _write_json(
        root
        / "runtime"
        / "studio"
        / "approvals"
        / "_runtime_dispatch_markers"
        / "executed-example.json",
        {
            "approval_id": "executed-example",
            "status": "executed",
            "agent_bus_task_written": True,
            "task_id": "task-executed-example",
            "provider_call_performed": False,
            "browser_control_performed": False,
            "target_write_performed": False,
            "workflow_dispatched": False,
            "canonical_mutation_performed": False,
        },
    )


def _seed_source_context_fixture(root: Path) -> None:
    for name in ["Agent-Control-Plane", "Permission-Matrix", "Trust-Tiers", "Backends-Supported"]:
        (root / "06_AGENTS").mkdir(parents=True, exist_ok=True)
        (root / "06_AGENTS" / f"{name}.md").write_text(f"# {name}\n", encoding="utf-8")

    workflow_manifest = root / "runtime" / "workflows" / "registry" / "ventureops_ai_runtime_security_audit.yaml"
    workflow_manifest.parent.mkdir(parents=True, exist_ok=True)
    workflow_manifest.write_text(
        "\n".join(
            [
                "id: ventureops_ai_runtime_security_audit",
                "required_reads:",
                '  - "06_AGENTS/Agent-Control-Plane.md"',
                '  - "06_AGENTS/Permission-Matrix.md"',
                '  - "06_AGENTS/Trust-Tiers.md"',
                '  - "06_AGENTS/Backends-Supported.md"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    package_path = root / "runtime" / "source_intelligence" / "workspaces" / "phase7-test" / "sources" / "demo.json"
    _write_json(package_path, {"id": "source-1"})
    _write_json(
        root / "runtime" / "source_intelligence" / "workspaces" / "phase7-test" / "workspace.json",
        {
            "slug": "phase7-test",
            "status": "active",
            "source_count": 1,
            "index_status": "indexed",
            "query_scope": "workspace-only",
            "source_refs": {
                "source-1": {
                    "source_package_id": "source-1",
                    "source_package_path": str(package_path),
                    "source_type": "research-digest",
                    "title": "Demo Source",
                    "origin_path": str(root / "03_INPUTS" / "demo.md"),
                    "extraction_status": "complete",
                    "embedding_status": "embedded",
                    "user_trust_level": "untrusted",
                }
            },
        },
    )


def _seed_ventureops_live_client_workflow_proof(root: Path) -> None:
    source_path = root / "README.md"
    source_path.write_text("approved source\n", encoding="utf-8")
    approved_paths = ["README.md"]
    approval_path = "07_LOGS/Workflow-Proofs/client-alpha-scope-approval.json"
    scope_path = "07_LOGS/Workflow-Proofs/client-alpha-scope-evidence.json"
    _write_json(
        root / approval_path,
        {
            "type": "ventureops-real-client-scope-approval",
            "approval_id": "approval-alpha",
            "client_label": "Client Alpha",
            "client_approved_scope_id": "scope-alpha",
            "approval_status": "approved",
            "approval_decision": "approved",
            "approved_read_paths": approved_paths,
            "redaction_policy": "client_safe_summary_only",
            "delivery_boundary": "no_external_delivery",
            "operator_attested_scope_approved": True,
            "external_send_authorized": False,
            "payment_mutation_authorized": False,
            "crm_mutation_authorized": False,
            "provider_calls_authorized": False,
            "browser_actions_authorized": False,
            "revenue_claim_authorized": False,
        },
    )
    _write_json(
        root / scope_path,
        {
            "type": "ventureops-real-client-scope-evidence",
            "client_approved_scope_id": "scope-alpha",
            "client_label": "Client Alpha",
            "approval_id": "approval-alpha",
            "approval_status": "approved",
            "approval_artifact_path": approval_path,
            "approved_read_paths": approved_paths,
            "redaction_policy": "client_safe_summary_only",
            "delivery_boundary": "no_external_delivery",
        },
    )
    _write_json(
        root / "07_LOGS" / "Workflow-Proofs" / "client-alpha-live-client-workflow-proof.json",
        {
            "type": "ventureops-live-client-workflow-proof",
            "status": "live_client_workflow_proof_written",
            "workflow_id": "agent_runtime_governance_audit",
            "run_id": "client-alpha-run",
            "date": "2026-05-13",
            "scope_packet_path": scope_path,
            "client_approved_scope_id": "scope-alpha",
            "client_label": "Client Alpha",
            "approval_id": "approval-alpha",
            "approval_status": "approved",
            "approved_read_paths": approved_paths,
            "approved_read_path_count": 1,
            "source_digest_count": 1,
            "source_digests": [
                {
                    "path": "README.md",
                    "sha256": "a" * 64,
                    "byte_count": 16,
                }
            ],
            "scope_proof_gate_path": "07_LOGS/Workflow-Proofs/client-alpha-scope-gate.json",
            "client_report_path": "07_LOGS/Workflow-Proofs/client-alpha-report.md",
            "scorecard_path": "07_LOGS/Workflow-Proofs/client-alpha-scorecard.json",
            "live_client_workflow_proof_performed": True,
            "scoped_client_data_ingested": True,
            "broad_client_data_ingested": False,
            "live_external_delivery_performed": False,
            "external_send_performed": False,
            "crm_mutation_performed": False,
            "payment_mutation_performed": False,
            "provider_calls": 0,
            "browser_actions": 0,
            "revenue_claim_made": False,
        },
    )


def _seed_current_mvp_truth_surfaces(root: Path) -> None:
    for relative in [
        "PROJECT_FOUNDATION.md",
        "ROADMAP.md",
        "00_HOME/Now.md",
        "06_AGENTS/ChaseOS-MVP-Current-Goal-and-Pass-Plan.md",
        "06_AGENTS/ChaseOS-MVP-Consolidation-Map.md",
        "06_AGENTS/ChaseOS-MVP-Operator-Unblock-Packet.md",
        "06_AGENTS/ChaseOS-MVP-Completion-Audit.md",
        "06_AGENTS/ChaseOS-MVP-Credential-Readiness-Checklist.md",
        "07_LOGS/Operator-Briefs/2026-05-13-mvp-next-action-card.md",
        "runtime/studio/runtime_startup_controls.py",
        "runtime/browser_runtime/cdp_executor_spec.py",
        "runtime/browser_runtime/workflow_replay_execution_readiness.py",
    ]:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# {path.stem}\n", encoding="utf-8")


def _seed_setup_scope_fixture(root: Path) -> None:
    _write_json(
        root / "runtime" / "setup_registry.json",
        {
            "providers": [
                {"id": "claude"},
                {"id": "openai"},
                {"id": "local_oss"},
                {"id": "n8n"},
            ],
            "integrations": [
                {"id": "discord"},
                {
                    "id": "telegram",
                    "validation_checks": [
                        "configured",
                        "binding_present",
                        "secret_reference_present",
                    ],
                },
                {
                    "id": "slack",
                    "validation_checks": [
                        "configured",
                        "binding_present",
                        "secret_reference_present",
                    ],
                },
            ],
        },
    )
    _write_json(
        root / "runtime" / "setup_provider_profiles.json",
        {
            "claude": {
                "validation_checks": [
                    "auth_present",
                    "model_selected",
                    "secret_reference_present",
                ]
            },
            "openai": {
                "validation_checks": [
                    "api_key_present",
                    "model_selected",
                    "secret_reference_present",
                ]
            },
            "local_oss": {
                "validation_checks": ["endpoint_present", "model_target_present"]
            },
            "n8n": {"validation_checks": ["base_url_present", "auth_present"]},
        },
    )
    _write_json(
        root / "runtime" / "setup_state.json",
        {
            "providers": {
                "claude": {
                    "configured": False,
                    "auth_present": False,
                    "model_selected": False,
                    "secret_reference_present": False,
                },
                "openai": {
                    "configured": True,
                    "default_model": "gpt-5.5",
                    "api_key_present": True,
                    "model_selected": True,
                    "secret_reference_kind": "env-var-or-local-secret-ref",
                    "secret_reference_present": True,
                    "secret_reference_target": "SET_OPENAI_SECRET_REF",
                },
                "local_oss": {
                    "configured": False,
                    "endpoint_present": False,
                    "model_target_present": False,
                },
                "n8n": {
                    "configured": False,
                    "base_url_present": False,
                    "auth_present": False,
                },
            },
            "integrations": {
                "discord": {"configured": True, "binding_present": True},
                "telegram": {
                    "configured": False,
                    "binding_present": False,
                    "secret_reference_present": False,
                },
                "slack": {
                    "configured": False,
                    "binding_present": False,
                    "secret_reference_present": False,
                },
            },
        },
    )


def _seed_agent_bus_lifecycle_proof(root: Path) -> None:
    task_id = "task-e417a38df4d0"
    run_id = "run-e417a38df4d0"
    created_at = "2026-05-13T10:47:17Z"
    updated_at = "2026-05-13T10:48:17Z"
    run_dir_rel = f"runtime/adapters/codex/runs/20260513T104717Z-{task_id}"
    result_rel = f"{run_dir_rel}/codex-adapter-result.json"
    stdout_rel = f"{run_dir_rel}/codex-stdout.md"
    stderr_rel = f"{run_dir_rel}/codex-stderr.log"

    db_path = root / "runtime" / "agent_bus" / "agent_bus.sqlite"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE tasks (
          task_id TEXT PRIMARY KEY,
          run_id TEXT NOT NULL,
          reply_to TEXT,
          sender TEXT NOT NULL,
          recipient TEXT NOT NULL,
          intent TEXT NOT NULL,
          status TEXT NOT NULL,
          priority TEXT NOT NULL DEFAULT 'normal',
          owner TEXT,
          owner_instance TEXT,
          request TEXT NOT NULL,
          expected_output TEXT NOT NULL,
          depends_on_json TEXT NOT NULL DEFAULT '[]',
          artifacts_json TEXT NOT NULL DEFAULT '[]',
          ingress_context_json TEXT NOT NULL DEFAULT '{}',
          execution_constraints_json TEXT NOT NULL DEFAULT '{}',
          work_fingerprint TEXT,
          notes TEXT,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL,
          expires_at TEXT
        );
        CREATE TABLE events (
          event_id TEXT PRIMARY KEY,
          task_id TEXT NOT NULL,
          run_id TEXT NOT NULL,
          sender TEXT NOT NULL,
          event_type TEXT NOT NULL,
          message TEXT NOT NULL,
          artifacts_json TEXT NOT NULL DEFAULT '[]',
          created_at TEXT NOT NULL
        );
        """
    )
    conn.execute(
        """
        INSERT INTO tasks (
          task_id, run_id, reply_to, sender, recipient, intent, status, priority,
          owner, owner_instance, request, expected_output, depends_on_json,
          artifacts_json, ingress_context_json, execution_constraints_json,
          work_fingerprint, notes, created_at, updated_at, expires_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            task_id,
            run_id,
            None,
            "Hermes",
            "Codex",
            "TASK",
            "done",
            "normal",
            "Codex",
            "Axiom-Codex",
            "Prove one bounded Codex task lifecycle.",
            "Adapter result artifact and completion event.",
            "[]",
            json.dumps([result_rel]),
            "{}",
            "{}",
            "fingerprint-e417a38df4d0",
            None,
            created_at,
            updated_at,
            None,
        ),
    )
    for index, event_type in enumerate(["created", "claimed", "started", "result_attached", "completed"], start=1):
        conn.execute(
            """
            INSERT INTO events (
              event_id, task_id, run_id, sender, event_type, message, artifacts_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"evt-{task_id}-{event_type}",
                task_id,
                run_id,
                "Codex",
                event_type,
                event_type.replace("_", " "),
                json.dumps([result_rel]) if event_type == "result_attached" else "[]",
                f"2026-05-13T10:48:{index:02d}Z",
            ),
        )
    conn.commit()
    conn.close()

    run_dir = root / run_dir_rel
    run_dir.mkdir(parents=True, exist_ok=True)
    (root / stdout_rel).write_text("bounded result\n", encoding="utf-8")
    (root / stderr_rel).write_text("", encoding="utf-8")
    _write_json(
        root / result_rel,
        {
            "task_id": task_id,
            "run_id": run_id,
            "from": "Codex",
            "event_type": "proposal",
            "artifacts": [
                {"path": stdout_rel},
                {"path": stderr_rel},
            ],
        },
    )


def _seed_operator_input_template(root: Path) -> Path:
    template_path = root / "07_LOGS" / "Operator-Briefs" / "2026-05-13-mvp-operator-input-template.json"
    _write_json(
        template_path,
        {
            "surface": "chaseos_mvp_operator_input_values_template",
            "operator_input_values": {
                "openai_secret_reference": {"secret_reference_target": "OPENAI_API_KEY"},
                "pending_chat_approval_decision": {
                    "approval_id": PENDING_CHAT_APPROVAL_ID,
                    "decision": "leave_pending",
                },
            },
            "boundary": {"secret_values_allowed": False},
        },
    )
    return template_path


def test_mvp_readiness_gate_reports_current_operator_blockers_without_secrets(tmp_path: Path, monkeypatch) -> None:
    secret_value = "test-key-test-secret-value-that-must-not-appear"
    monkeypatch.setenv("OPENAI_API_KEY", secret_value)
    _seed_minimal_vault(tmp_path)

    payload = build_mvp_readiness_gate(tmp_path)
    serialized = json.dumps(payload, sort_keys=True)

    assert payload["ok"] is True
    assert payload["readiness_status"] == "blocked_operator_input_required"
    assert payload["overall_goal_complete"] is False
    assert payload["objective_achieved"] is False
    assert payload["safe_to_call_update_goal_complete"] is False
    assert payload["operator_input_ids"] == [
        "openai_secret_reference",
        "ventureops_real_client_scope",
        "pending_chat_approval_decision",
    ]
    assert payload["p0_blocker_ids"] == [
        "openai_secret_reference",
        "ventureops_real_client_scope",
    ]
    assert payload["p1_decision_ids"] == ["pending_chat_approval_decision"]
    assert payload["completion_decision"]["operator_input_ids"] == payload["operator_input_ids"]
    assert payload["completion_decision"]["safe_to_call_update_goal_complete"] is False
    assert payload["no_safe_autonomous_completion_pass_available"] is True
    assert payload["update_goal_allowed"] is False
    assert payload["next_operator_action_id"] == "openai_secret_reference"
    assert payload["next_recommended_pass"] == "operator-provide-openai-secret-reference"
    assert payload["next_operator_action_id"] == payload["autonomous_completion_barrier"][
        "next_operator_action_id"
    ]
    assert payload["next_recommended_pass"] == payload["autonomous_completion_barrier"][
        "next_recommended_pass"
    ]
    assert payload["canonical_operator_handoff"]["path"] == (
        "07_LOGS/Operator-Briefs/2026-05-13-mvp-next-action-card.md"
    )
    assert payload["canonical_operator_handoff"]["contains_secret_values"] is False
    assert payload["canonical_operator_handoff"]["execution_authority_granted"] is False
    assert payload["operator_input_template_artifact"] == {
        "path": "07_LOGS/Operator-Briefs/2026-05-13-mvp-operator-input-template.json",
        "exists": False,
        "contains_secret_values": False,
        "validation_command": "python -m runtime.cli.main mvp validate-operator-input --input 07_LOGS/Operator-Briefs/2026-05-13-mvp-operator-input-template.json --json",
        "write_command": "python -m runtime.cli.main mvp operator-input-template --write-template 07_LOGS/Operator-Briefs/2026-05-13-mvp-operator-input-template.json --json",
    }
    assert payload["setup_scope_boundary"]["status"] == (
        "setup_wide_validation_expected_to_fail_current_mvp_blocker"
    )
    assert payload["setup_scope_boundary"]["mvp_current_setup_blocker_ids"] == [
        "openai_secret_reference"
    ]
    assert payload["setup_scope_boundary"]["setup_wide_invalid_provider_ids"] == [
        "openai"
    ]
    assert payload["setup_scope_boundary"]["non_mvp_setup_gap_ids"] == []
    assert (
        payload["setup_scope_boundary"]["non_mvp_setup_gaps_are_current_mvp_blockers"]
        is False
    )
    assert payload["authority"]["secret_values_read"] is False
    assert payload["authority"]["provider_calls_performed"] is False
    assert secret_value not in serialized
    approvals = payload["checks"]["studio_approvals"]
    assert approvals["pending_count"] == 1
    assert approvals["tracked_pending_count"] == 1
    assert approvals["untracked_pending_approval_count"] == 0
    assert approvals["tracked_chat_approval_is_current_mvp_decision"] is True
    assert approvals["untracked_pending_approvals_are_current_mvp_blockers"] is False
    assert PENDING_CHAT_APPROVAL_ID in approvals["untracked_pending_approval_boundary"]
    assert {
        "openai_secret_reference",
        "ventureops_real_client_scope",
        "pending_chat_approval_decision",
    } <= {item["id"] for item in payload["operator_inputs_required"]}
    assert [item["id"] for item in payload["next_action_queue"]] == [
        "openai_secret_reference",
        "ventureops_real_client_scope",
        "pending_chat_approval_decision",
    ]
    assert payload["summary"]["next_operator_action_id"] == "openai_secret_reference"
    assert payload["summary"]["completion_matrix_count"] == 10
    assert len(payload["completion_matrix"]) == 10
    snapshot = payload["mvp_usecase_snapshot"]
    assert snapshot["surface"] == "chaseos_mvp_usecase_snapshot"
    assert snapshot["current_sector"] == "MVP Integration / Operator Workflow Activation"
    assert snapshot["readiness_status"] == "blocked_operator_input_required"
    assert snapshot["p0_blocker_ids"] == ["openai_secret_reference", "ventureops_real_client_scope"]
    assert snapshot["p1_decision_ids"] == ["pending_chat_approval_decision"]
    assert {
        "provider_backed_chat_studio",
        "ventureops_real_client_scope",
        "pending_chat_approval_decision",
    } <= {item["id"] for item in snapshot["blocked_now"]}
    assert "full_system_control" in {item["id"] for item in snapshot["parked_or_later"]}
    assert snapshot["authority"]["provider_calls_performed"] is False
    assert snapshot["authority"]["approval_consumption_performed"] is False
    assert "ventureops_real_use" in payload["completion_audit"]["blocked_requirement_ids"]
    assert payload["next_operator_action"]["can_codex_execute_now"] is False
    assert payload["next_operator_action"]["requires_operator_secret_reference"] is True
    assert payload["next_operator_action"]["live_execution_allowed_now"] is False
    handoff_steps = payload["next_operator_action"]["operator_handoff_steps"]
    assert [step["id"] for step in handoff_steps] == [
        "set_outside_repo_secret_reference",
        "preview_setup_metadata_reference",
        "update_setup_metadata_reference",
        "validate_reference_without_secret_read",
        "request_guarded_live_probe_approval",
    ]
    assert handoff_steps[0]["manual_only"] is True
    assert handoff_steps[0]["secret_value_allowed_in_repo_or_chat"] is False
    assert handoff_steps[1]["command_template"] == (
        "python -m runtime.cli.main setup set provider openai secret_reference_kind=env-var-or-local-secret-ref secret_reference_present=true secret_reference_target=OPENAI_API_KEY --dry-run --json"
    )
    assert handoff_steps[1]["codex_can_execute"] is True
    assert handoff_steps[2]["command_template"] == (
        "python -m runtime.cli.main setup set provider openai secret_reference_kind=env-var-or-local-secret-ref secret_reference_present=true secret_reference_target=OPENAI_API_KEY --json"
    )
    assert handoff_steps[3]["codex_can_execute"] is True
    assert handoff_steps[4]["command_template"] == (
        "python -m runtime.cli.main runtime provider live-probe-target-approval-plan primary --json"
    )
    pending_action = next(item for item in payload["next_action_queue"] if item["id"] == "pending_chat_approval_decision")
    pending_handoff_steps = pending_action["operator_handoff_steps"]
    assert [step["id"] for step in pending_handoff_steps] == [
        "inspect_pending_chat_approval",
        "preview_pending_chat_exact_once_consumption_readiness",
        "choose_pending_chat_approval_decision",
        "validate_pending_chat_approval_decision_packet",
        "run_separate_exact_once_consumption_pass_if_approved",
    ]
    assert pending_handoff_steps[0]["command_template"] == (
        "python -m runtime.cli.main studio approval-center-panel --json"
    )
    assert pending_handoff_steps[1]["command_template"] == (
        "python -m runtime.cli.main studio phase11-chat-approval-consumption-readiness-contract --approval-id 5849a53f-10e0-46af-a89a-7de06150f7f8 --json"
    )
    assert pending_handoff_steps[1]["approval_consumption_allowed_now"] is False
    assert pending_handoff_steps[2]["allowed_decisions"] == ["approve", "reject", "leave_pending"]
    assert pending_handoff_steps[2]["codex_can_decide"] is False
    assert pending_handoff_steps[4]["command_template"] == (
        "python -m runtime.cli.main studio phase11-chat-approval-consumption-executor --approval-id 5849a53f-10e0-46af-a89a-7de06150f7f8 --expected-consumption-digest <digest_from_readiness> --json"
    )
    assert pending_handoff_steps[4]["approval_consumption_allowed_now"] is False
    assert payload["checks"]["provider_credentials"]["secret_reference_target_is_placeholder"] is True
    assert payload["checks"]["provider_credentials"]["secret_reference_resolvable"] is False
    assert payload["checks"]["provider_credentials"]["secret_reference_probe_error"] == "reference_not_found"
    assert payload["checks"]["provider_credentials"]["operator_handoff_step_count"] == 5
    assert (
        payload["checks"]["provider_credentials"]["safe_next_command"]
        == "python -m runtime.cli.main setup set provider openai secret_reference_kind=env-var-or-local-secret-ref secret_reference_present=true secret_reference_target=OPENAI_API_KEY --dry-run --json"
    )
    provider_input = next(
        item for item in payload["operator_inputs_required"] if item["id"] == "openai_secret_reference"
    )
    assert provider_input["validation_command"] == "python -m runtime.cli.main setup provider validate openai --json"
    assert payload["checks"]["ventureops"]["missing_inputs"]
    assert payload["checks"]["ventureops"]["real_client_input_manifest_command"] == (
        "python -m runtime.cli.main ventureops real-client-input-manifest --json"
    )
    assert payload["checks"]["ventureops"]["provided_inputs"] == {
        "client_label": False,
        "client_approved_scope_id": False,
        "approval_id": False,
        "approved_read_paths": False,
        "approval_output_path": False,
        "approval_artifact_path": False,
        "scope_packet_output_path": False,
    }
    ventureops_input = next(
        item for item in payload["operator_inputs_required"] if item["id"] == "ventureops_real_client_scope"
    )
    assert ventureops_input["validation_command"] == (
        "python -m runtime.cli.main ventureops real-client-input-manifest --json"
    )
    assert ventureops_input["next_required_action"].startswith("provide real client label")
    assert ventureops_input["ready_for_live_client_workflow_proof"] is False
    ventureops_action = next(item for item in payload["next_action_queue"] if item["id"] == "ventureops_real_client_scope")
    assert ventureops_action["requires_operator_client_input"] is True
    assert "client_label" in ventureops_action["missing_inputs"]
    ventureops_row = next(item for item in payload["completion_matrix"] if item["id"] == "ventureops_real_use")
    assert ventureops_row["criterion_satisfied"] is False
    assert "live-client workflow proof" in ventureops_row["required_evidence"]
    assert ventureops_row["remaining_required_evidence"]


def test_mvp_readiness_gate_accepts_valid_ventureops_live_client_workflow_proof(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    _seed_minimal_vault(tmp_path)
    _seed_ventureops_live_client_workflow_proof(tmp_path)

    payload = build_mvp_readiness_gate(tmp_path)

    ventureops = payload["checks"]["ventureops"]
    assert ventureops["status"] == "complete_for_one_live_client_workflow_proof"
    assert ventureops["live_client_workflow_proof_artifact_valid"] is True
    assert ventureops["typed_scope_approval_artifact_valid"] is True
    assert ventureops["scope_evidence_packet_valid"] is True
    assert ventureops["live_client_workflow_proof_valid"] is True
    assert ventureops["not_synthetic_demo_evidence"] is True
    assert ventureops["approved_read_path_count"] == 1
    assert ventureops["ventureops_side_effects_blocked"] is True
    assert ventureops["selected_scope_packet_path"] == "07_LOGS/Workflow-Proofs/client-alpha-scope-evidence.json"
    assert ventureops["selected_scope_approval_artifact_path"] == (
        "07_LOGS/Workflow-Proofs/client-alpha-scope-approval.json"
    )
    assert ventureops["selected_live_client_workflow_proof_path"] == (
        "07_LOGS/Workflow-Proofs/client-alpha-live-client-workflow-proof.json"
    )
    assert "ventureops_real_use" not in payload["completion_audit"]["blocked_requirement_ids"]
    assert "ventureops_real_client_scope" not in {item["id"] for item in payload["operator_inputs_required"]}
    assert [item["id"] for item in payload["next_action_queue"]] == [
        "openai_secret_reference",
        "pending_chat_approval_decision",
    ]
    snapshot = payload["mvp_usecase_snapshot"]
    assert snapshot["p0_blocker_ids"] == ["openai_secret_reference"]
    assert "ventureops_scoped_workflow_proof" in {item["id"] for item in snapshot["usable_now"]}
    assert "ventureops_real_client_scope" not in {item["id"] for item in snapshot["blocked_now"]}
    assert "provider_backed_chat_studio" in {item["id"] for item in snapshot["blocked_now"]}
    assert "pending_chat_approval_decision" in {item["id"] for item in snapshot["blocked_now"]}
    ventureops_row = next(item for item in payload["completion_matrix"] if item["id"] == "ventureops_real_use")
    assert ventureops_row["criterion_satisfied"] is True
    assert ventureops_row["remaining_required_evidence"] == []
    assert "not synthetic/demo evidence" in ventureops_row["required_evidence"]
    assert "external/provider/browser/revenue side effects false" in ventureops_row["required_evidence"]
    assert any("client-alpha-scope-approval.json" in ref for ref in ventureops_row["evidence_refs"])
    assert any("client-alpha-live-client-workflow-proof.json" in ref for ref in ventureops_row["evidence_refs"])


def test_mvp_operator_unblock_packet_summarizes_next_actions_without_secrets(
    tmp_path: Path, monkeypatch
) -> None:
    secret_value = "test-key-unblock-packet-secret-that-must-not-appear"
    monkeypatch.setenv("OPENAI_API_KEY", secret_value)
    _seed_minimal_vault(tmp_path)

    payload = build_mvp_operator_unblock_packet(tmp_path)
    serialized = json.dumps(payload, sort_keys=True)

    assert payload["surface"] == "chaseos_mvp_operator_unblock_packet"
    assert payload["readiness_status"] == "blocked_operator_input_required"
    assert payload["objective_achieved"] is False
    assert payload["safe_to_call_update_goal_complete"] is False
    assert payload["operator_input_ids"] == [
        "openai_secret_reference",
        "ventureops_real_client_scope",
        "pending_chat_approval_decision",
    ]
    assert payload["p0_blocker_ids"] == [
        "openai_secret_reference",
        "ventureops_real_client_scope",
    ]
    assert payload["p1_decision_ids"] == ["pending_chat_approval_decision"]
    assert payload["completion_decision"]["operator_input_ids"] == payload["operator_input_ids"]
    assert payload["completion_decision"]["safe_to_call_update_goal_complete"] is False
    assert payload["autonomous_completion_barrier"]["active"] is True
    assert payload["autonomous_completion_barrier"]["update_goal_allowed"] is False
    assert payload["setup_scope_boundary"]["status"] == (
        "setup_wide_validation_expected_to_fail_current_mvp_blocker"
    )
    assert payload["setup_scope_boundary"]["mvp_current_setup_blocker_ids"] == [
        "openai_secret_reference"
    ]
    assert payload["setup_scope_boundary"]["setup_wide_invalid_provider_ids"] == [
        "openai"
    ]
    assert payload["setup_scope_boundary"]["setup_wide_invalid_integration_ids"] == []
    assert payload["setup_scope_boundary"]["non_mvp_setup_gap_ids"] == []
    assert (
        payload["setup_scope_boundary"]["non_mvp_setup_gaps_are_current_mvp_blockers"]
        is False
    )
    assert payload["no_safe_autonomous_completion_pass_available"] is True
    assert payload["update_goal_allowed"] is False
    assert payload["autonomous_completion_barrier"]["operator_input_ids"] == payload[
        "operator_input_ids"
    ]
    assert payload["required_operator_inputs"] == payload["operator_inputs_required"]
    pending_input = next(
        item
        for item in payload["operator_inputs_required"]
        if item["id"] == "pending_chat_approval_decision"
    )
    assert pending_input["approval_id"] == PENDING_CHAT_APPROVAL_ID
    assert pending_input["safe_next_command"] == (
        "python -m runtime.cli.main studio phase11-chat-approval-consumption-readiness-contract "
        f"--approval-id {PENDING_CHAT_APPROVAL_ID} --json"
    )
    assert pending_input["approval_consumption_readiness_command"] == pending_input[
        "safe_next_command"
    ]
    assert pending_input["approval_consumption_executor_command_template"] == (
        "python -m runtime.cli.main studio phase11-chat-approval-consumption-executor "
        f"--approval-id {PENDING_CHAT_APPROVAL_ID} "
        "--expected-consumption-digest <digest_from_readiness> --json"
    )
    assert pending_input["approval_consumption_allowed_now"] is False
    assert pending_input["requires_operator_approval_decision"] is True
    assert payload["next_operator_action_id"] == "openai_secret_reference"
    assert payload["next_recommended_pass"] == "operator-provide-openai-secret-reference"
    assert [item["id"] for item in payload["next_action_queue"]] == [
        "openai_secret_reference",
        "ventureops_real_client_scope",
        "pending_chat_approval_decision",
    ]
    snapshot = payload["mvp_usecase_snapshot"]
    assert snapshot["surface"] == "chaseos_mvp_usecase_snapshot"
    assert snapshot["current_mvp_usecase"].startswith("Governed local operator workflow")
    assert "provider_backed_chat_studio" in {item["id"] for item in snapshot["blocked_now"]}
    assert "full_system_control" in {item["id"] for item in snapshot["parked_or_later"]}
    assert snapshot["next_operator_action_id"] == "openai_secret_reference"
    assert "ventureops_real_use" in payload["completion_summary"]["blocked_requirement_ids"]
    assert {
        "openai_secret_reference",
        "ventureops_real_client_scope",
    } <= {item["id"] for item in payload["safe_commands"]}
    assert payload["operator_input_schema_version"] == "chaseos.mvp_operator_input_schema.v1"
    schema_by_id = {item["id"]: item for item in payload["operator_input_schema"]}
    assert {
        "openai_secret_reference",
        "ventureops_real_client_scope",
        "pending_chat_approval_decision",
    } <= set(schema_by_id)
    openai_fields = {field["name"]: field for field in schema_by_id["openai_secret_reference"]["fields"]}
    assert openai_fields["secret_reference_target"]["type"] == "secret-reference-name"
    assert openai_fields["secret_reference_target"]["secret_policy"] == "reference_name_only_no_secret_value"
    assert openai_fields["secret_reference_target"]["current_state"]["reference_resolvable"] is False
    assert [step["id"] for step in schema_by_id["openai_secret_reference"]["operator_handoff_steps"]] == [
        "set_outside_repo_secret_reference",
        "preview_setup_metadata_reference",
        "update_setup_metadata_reference",
        "validate_reference_without_secret_read",
        "request_guarded_live_probe_approval",
    ]
    assert schema_by_id["openai_secret_reference"]["boundary"]["outside_repo_secret_reference_required_first"] is True
    ventureops_fields = {field["name"]: field for field in schema_by_id["ventureops_real_client_scope"]["fields"]}
    assert ventureops_fields["approved_read_paths"]["type"] == "list[repo-relative-path]"
    assert ventureops_fields["approved_read_paths"]["secret_policy"] == "paths_only_no_client_data_inline"
    assert ventureops_fields["approval_output_path"]["requirement"] == (
        "at_least_one_of:approval_output_path,approval_artifact_path"
    )
    assert ventureops_fields["scope_packet_output_path"]["requirement"] == (
        "required_after_valid_approval_artifact_matches_manifest_inputs"
    )
    decision_fields = {field["name"]: field for field in schema_by_id["pending_chat_approval_decision"]["fields"]}
    assert decision_fields["decision"]["allowed_values"] == ["approve", "reject", "leave_pending"]
    assert schema_by_id["pending_chat_approval_decision"]["boundary"]["approval_consumption_allowed_by_schema"] is False
    assert schema_by_id["pending_chat_approval_decision"]["boundary"]["studio_decision_controls_present"] is False
    assert schema_by_id["pending_chat_approval_decision"]["boundary"][
        "separate_consumption_pass_required_if_approved"
    ] is True
    assert [step["id"] for step in schema_by_id["pending_chat_approval_decision"]["operator_handoff_steps"]] == [
        "inspect_pending_chat_approval",
        "preview_pending_chat_exact_once_consumption_readiness",
        "choose_pending_chat_approval_decision",
        "validate_pending_chat_approval_decision_packet",
        "run_separate_exact_once_consumption_pass_if_approved",
    ]
    assert payload["operator_input_template_version"] == "chaseos.mvp_operator_input_template.v1"
    assert payload["operator_input_template_artifact"] == {
        "path": "07_LOGS/Operator-Briefs/2026-05-13-mvp-operator-input-template.json",
        "exists": False,
        "contains_secret_values": False,
        "validation_command": "python -m runtime.cli.main mvp validate-operator-input --input 07_LOGS/Operator-Briefs/2026-05-13-mvp-operator-input-template.json --json",
        "write_command": "python -m runtime.cli.main mvp operator-input-template --write-template 07_LOGS/Operator-Briefs/2026-05-13-mvp-operator-input-template.json --json",
    }
    template = payload["operator_input_template"]
    assert template["read_only"] is True
    assert template["boundary"]["secret_values_allowed"] is False
    assert template["boundary"]["private_client_material_inline_allowed"] is False
    template_by_id = {item["id"]: item for item in template["groups"]}
    assert template_by_id["openai_secret_reference"]["template_values"] == {
        "secret_reference_target": "OPENAI_API_KEY"
    }
    assert template_by_id["ventureops_real_client_scope"]["template_values"]["approved_read_paths"] == [
        "03_INPUTS/<approved-client-scope>/redacted-source.md"
    ]
    assert template_by_id["ventureops_real_client_scope"]["template_values"]["scope_packet_output_path"].endswith(
        "_ventureops-scope-evidence.json"
    )
    assert template_by_id["pending_chat_approval_decision"]["template_values"] == {
        "approval_id": "5849a53f-10e0-46af-a89a-7de06150f7f8",
        "decision": "leave_pending",
    }
    assert "secret_value" in template["forbidden_values"]
    assert payload["boundary"]["secret_values_read"] is False
    assert payload["boundary"]["provider_calls_performed"] is False
    assert secret_value not in serialized


def test_mvp_operator_unblock_packet_cli_uses_json_envelope(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    _seed_minimal_vault(tmp_path)

    exit_code = cli.main(["mvp", "operator-unblock-packet", "--vault-root", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "mvp.operator-unblock-packet"
    assert payload["result"]["surface"] == "chaseos_mvp_operator_unblock_packet"
    assert payload["result"]["safe_to_call_update_goal_complete"] is False
    assert payload["result"]["operator_input_ids"] == [
        "openai_secret_reference",
        "ventureops_real_client_scope",
        "pending_chat_approval_decision",
    ]
    assert payload["result"]["completion_decision"]["operator_input_ids"] == payload["result"][
        "operator_input_ids"
    ]
    assert payload["result"]["autonomous_completion_barrier"]["active"] is True
    assert payload["result"]["autonomous_completion_barrier"]["update_goal_allowed"] is False
    assert payload["result"]["setup_scope_boundary"]["mvp_current_setup_blocker_ids"] == [
        "openai_secret_reference"
    ]
    assert (
        payload["result"]["setup_scope_boundary"][
            "non_mvp_setup_gaps_are_current_mvp_blockers"
        ]
        is False
    )
    assert payload["result"]["no_safe_autonomous_completion_pass_available"] is True
    assert payload["result"]["update_goal_allowed"] is False
    assert payload["result"]["required_operator_inputs"] == payload["result"][
        "operator_inputs_required"
    ]
    pending_input = next(
        item
        for item in payload["result"]["operator_inputs_required"]
        if item["id"] == "pending_chat_approval_decision"
    )
    assert pending_input["approval_id"] == PENDING_CHAT_APPROVAL_ID
    assert pending_input["approval_consumption_readiness_command"] == (
        "python -m runtime.cli.main studio phase11-chat-approval-consumption-readiness-contract "
        f"--approval-id {PENDING_CHAT_APPROVAL_ID} --json"
    )
    assert pending_input["approval_consumption_executor_command_template"] == (
        "python -m runtime.cli.main studio phase11-chat-approval-consumption-executor "
        f"--approval-id {PENDING_CHAT_APPROVAL_ID} "
        "--expected-consumption-digest <digest_from_readiness> --json"
    )
    assert pending_input["approval_consumption_allowed_now"] is False
    assert payload["result"]["next_operator_action_id"] == "openai_secret_reference"
    assert payload["result"]["next_recommended_pass"] == "operator-provide-openai-secret-reference"
    assert payload["result"]["operator_input_schema_version"] == "chaseos.mvp_operator_input_schema.v1"
    assert [item["id"] for item in payload["result"]["operator_input_schema"]] == [
        "openai_secret_reference",
        "ventureops_real_client_scope",
        "pending_chat_approval_decision",
    ]
    assert payload["result"]["operator_input_template_version"] == "chaseos.mvp_operator_input_template.v1"
    assert payload["result"]["operator_input_template_artifact"]["path"] == (
        "07_LOGS/Operator-Briefs/2026-05-13-mvp-operator-input-template.json"
    )
    assert payload["result"]["operator_input_template_artifact"]["exists"] is False
    assert payload["result"]["operator_input_template_artifact"]["contains_secret_values"] is False
    assert payload["result"]["setup_scope_boundary"]["mvp_current_setup_blocker_ids"] == [
        "openai_secret_reference"
    ]
    assert (
        payload["result"]["setup_scope_boundary"][
            "non_mvp_setup_gaps_are_current_mvp_blockers"
        ]
        is False
    )
    assert payload["result"]["mvp_usecase_snapshot"]["surface"] == "chaseos_mvp_usecase_snapshot"
    assert payload["result"]["mvp_usecase_snapshot"]["next_operator_action_id"] == "openai_secret_reference"
    assert [item["id"] for item in payload["result"]["operator_input_template"]["groups"]] == [
        "openai_secret_reference",
        "ventureops_real_client_scope",
        "pending_chat_approval_decision",
    ]


def test_mvp_readiness_gate_keeps_chat_approval_covered_after_tracked_approval_executes(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    _seed_minimal_vault(tmp_path)
    _write_json(
        tmp_path / "runtime" / "studio" / "approvals" / f"{PENDING_CHAT_APPROVAL_ID}.json",
        {
            "approval_id": PENDING_CHAT_APPROVAL_ID,
            "status": "executed",
            "execution_status": "completed",
            "submitted_at": "2026-05-13T11:11:12Z",
            "updated_at": "2026-05-14T18:57:18Z",
            "action_spec": {
                "action_type": "create_file",
                "target_path": "01_PROJECTS/_chat_proposals/example.md",
                "submitted_by": "studio-chat",
                "metadata": {
                    "target_vault_write_performed": False,
                    "provider_call_performed": False,
                    "browser_control_performed": False,
                    "canonical_mutation_performed": False,
                },
            },
        },
    )

    payload = build_mvp_readiness_gate(tmp_path)
    rows = {item["id"]: item for item in payload["completion_matrix"]}

    assert rows["chat_to_approval"]["criterion_satisfied"] is True
    assert rows["chat_to_approval"]["status"] == "complete_for_one_supported_proposal_lane"
    approvals = payload["checks"]["studio_approvals"]
    assert approvals["pending_count"] == 0
    assert approvals["tracked_pending_count"] == 0
    assert approvals["untracked_pending_approval_count"] == 0
    assert approvals["tracked_chat_approval_is_current_mvp_decision"] is False
    assert approvals["untracked_pending_approvals_are_current_mvp_blockers"] is False
    assert "pending_chat_approval_decision" not in payload["p1_decision_ids"]
    assert "pending_chat_approval_decision" not in {
        item["id"] for item in payload["operator_inputs_required"]
    }


def test_mvp_current_state_maps_ten_passes_and_scope_without_secrets(
    tmp_path: Path, monkeypatch
) -> None:
    secret_value = "FAKE_CURRENT_STATE_SECRET_THAT_MUST_NOT_APPEAR"
    monkeypatch.setenv("OPENAI_API_KEY", secret_value)
    _seed_minimal_vault(tmp_path)
    _seed_current_mvp_truth_surfaces(tmp_path)
    _seed_operator_input_template(tmp_path)

    payload = build_mvp_current_state(tmp_path)
    serialized = json.dumps(payload, sort_keys=True)

    assert payload["surface"] == "chaseos_mvp_current_state_map"
    assert payload["read_only"] is True
    assert payload["current_sector"] == "MVP Integration / Operator Workflow Activation"
    assert payload["readiness_status"] == "blocked_operator_input_required"
    assert payload["overall_goal_complete"] is False
    assert payload["objective_achieved"] is False
    assert payload["safe_to_call_update_goal_complete"] is False
    assert payload["canonical_operator_handoff"]["path"] == (
        "07_LOGS/Operator-Briefs/2026-05-13-mvp-next-action-card.md"
    )
    assert payload["canonical_operator_handoff"]["exists"] is True
    assert payload["canonical_operator_handoff"]["contains_secret_values"] is False
    assert payload["canonical_operator_handoff"]["execution_authority_granted"] is False
    assert payload["operator_input_template_artifact"] == {
        "path": "07_LOGS/Operator-Briefs/2026-05-13-mvp-operator-input-template.json",
        "exists": True,
        "contains_secret_values": False,
        "validation_command": "python -m runtime.cli.main mvp validate-operator-input --input 07_LOGS/Operator-Briefs/2026-05-13-mvp-operator-input-template.json --json",
        "write_command": "python -m runtime.cli.main mvp operator-input-template --write-template 07_LOGS/Operator-Briefs/2026-05-13-mvp-operator-input-template.json --json",
    }
    assert payload["operator_input_ids"] == payload["completion_decision"]["operator_input_ids"]
    assert payload["p0_blocker_ids"] == payload["completion_decision"]["p0_blocker_ids"]
    assert payload["p1_decision_ids"] == payload["completion_decision"]["p1_decision_ids"]
    assert payload["blocked_requirement_ids"] == payload["completion_decision"]["blocked_requirement_ids"]
    assert payload["incomplete_or_operator_blocked_requirements"] == payload[
        "completion_decision"
    ]["incomplete_or_operator_blocked_requirements"]
    assert payload["completion_decision"]["safe_to_call_update_goal_complete"] is False
    assert payload["autonomous_completion_barrier"]["active"] is True
    assert payload["autonomous_completion_barrier"]["update_goal_allowed"] is False
    assert payload["autonomous_completion_barrier"]["blocked_by_operator_input"] is True
    assert payload["update_goal_allowed"] is False
    assert payload["no_safe_autonomous_completion_pass_available"] is True
    assert payload["completion_safety_contract"]["status"] == (
        "blocked_do_not_call_update_goal_complete"
    )
    assert payload["completion_safety_contract"]["update_goal_allowed"] is False
    assert payload["completion_safety_contract"][
        "safe_to_call_update_goal_complete"
    ] is False
    assert payload["completion_safety_contract"]["operator_input_ids"] == payload[
        "operator_input_ids"
    ]
    assert payload["operator_action_required"]["completion_safety_contract"] == payload[
        "completion_safety_contract"
    ]
    assert payload["autonomous_completion_barrier"]["operator_input_ids"] == payload[
        "operator_input_ids"
    ]
    assert payload["next_operator_action_id"] == payload["autonomous_completion_barrier"][
        "next_operator_action_id"
    ]
    assert payload["next_recommended_pass"] == payload["autonomous_completion_barrier"][
        "next_recommended_pass"
    ]
    assert payload["pass_status_count"] == 10
    assert len(payload["pass_statuses"]) == 10
    assert "README.md" in payload["source_docs"]
    assert "PROJECT_FOUNDATION.md" in payload["source_docs"]
    assert "ROADMAP.md" in payload["source_docs"]
    assert "00_HOME/Now.md" in payload["source_docs"]
    assert "07_LOGS/Build-Logs/Build-Logs-Index.md" in payload["source_docs"]
    assert (
        "07_LOGS/Build-Logs/2026-05-14-ChaseOS-mvp-current-state-rollover-audit.md"
        in payload["source_docs"]
    )
    assert (
        "99_ARCHIVE/Documentation-History/2026-05-14_mvp-current-state-rollover-audit.md"
        in payload["source_docs"]
    )
    assert "07_LOGS/Daily/2026-05-14.md" in payload["source_docs"]
    assert (
        "07_LOGS/Agent-Activity/2026-05-14-codex-mvp-current-state-rollover-audit.md"
        in payload["source_docs"]
    )
    assert set(payload["pass_status_by_id"]) == {item["id"] for item in payload["pass_statuses"]}
    assert payload["pass_status_by_id"]["credential_readiness"]["status"] == (
        "blocked_operator_input_required"
    )
    assert "07_LOGS/Build-Logs/Build-Logs-Index.md" in payload["pass_status_by_id"][
        "repo_truth_consolidation"
    ]["evidence_refs"]
    assert (
        "07_LOGS/Build-Logs/2026-05-14-ChaseOS-mvp-current-state-rollover-audit.md"
        in payload["pass_status_by_id"]["repo_truth_consolidation"]["evidence_refs"]
    )
    assert "07_LOGS/Operator-Briefs/2026-05-14-openai-api-key-later-guide.md" in payload[
        "pass_status_by_id"
    ]["credential_readiness"]["evidence_refs"]
    chat_refs = payload["pass_status_by_id"]["chat_to_approval"]["evidence_refs"]
    approval_action_refs = payload["pass_status_by_id"]["approval_to_action"]["evidence_refs"]
    assert f"runtime/studio/approvals/{PENDING_CHAT_APPROVAL_ID}.json" in chat_refs
    assert "runtime/studio/approvals/executed-example.json" in approval_action_refs
    assert (
        "runtime/studio/approvals/_runtime_dispatch_markers/executed-example.json"
        in approval_action_refs
    )
    assert len(chat_refs) <= 5
    assert len(approval_action_refs) <= 5
    assert [item["id"] for item in payload["scope_lock"]["p0_first_usable_mvp"]] == [
        "repo_truth_consolidation",
        "mvp_scope_lock",
        "credential_readiness",
        "chat_to_approval",
        "approval_to_action",
        "agent_bus_lifecycle",
        "ventureops_real_use",
        "studio_cockpit",
        "graph_source_intelligence",
        "full_system_control_boundary",
    ]
    assert payload["scope_lock"]["p0_current_blocker_ids"] == payload["p0_blocker_ids"]
    assert payload["scope_lock"]["p1_pending_decision_ids"] == payload["p1_decision_ids"]
    assert "provider_backed_chat_studio" in {item["id"] for item in payload["blocked_now"]}
    assert "full_system_control" in {item["id"] for item in payload["scope_lock"]["p2_parked_or_gated"]}
    assert payload["approval_queue_boundary"] == {
        "status": "pending_operator_review",
        "approval_artifact_count": 2,
        "pending_count": 1,
        "tracked_pending_count": 1,
        "untracked_pending_approval_count": 0,
        "tracked_chat_approval_id": PENDING_CHAT_APPROVAL_ID,
        "tracked_chat_approval_status": "pending",
        "tracked_chat_approval_is_current_mvp_decision": True,
        "untracked_pending_approvals_are_current_mvp_blockers": False,
        "boundary": (
            "Visible in Studio approval queues, but excluded from the current MVP P1 blocker set "
            f"unless explicitly selected by a separate governed pass; tracked MVP approval is {PENDING_CHAT_APPROVAL_ID}."
        ),
    }
    assert payload["setup_scope_boundary"]["status"] == (
        "setup_wide_validation_expected_to_fail_current_mvp_blocker"
    )
    assert payload["setup_scope_boundary"]["setup_wide_validation_command"] == (
        "python -m runtime.cli.main setup validate --json"
    )
    assert payload["setup_scope_boundary"]["mvp_required_provider_ids"] == ["openai"]
    assert payload["setup_scope_boundary"]["mvp_required_secret_reference_ids"] == [
        "openai_secret_reference"
    ]
    assert payload["setup_scope_boundary"]["mvp_current_setup_blocker_ids"] == [
        "openai_secret_reference"
    ]
    assert payload["setup_scope_boundary"]["current_mvp_next_operator_action_id"] == (
        "openai_secret_reference"
    )
    assert payload["setup_scope_boundary"]["setup_wide_invalid_provider_ids"] == [
        "openai"
    ]
    assert payload["setup_scope_boundary"]["setup_wide_invalid_integration_ids"] == []
    assert payload["setup_scope_boundary"]["non_mvp_setup_gap_ids"] == []
    assert (
        payload["setup_scope_boundary"]["non_mvp_setup_gaps_are_current_mvp_blockers"]
        is False
    )
    assert payload["setup_scope_boundary"]["secret_values_read"] is False
    assert payload["setup_scope_boundary"]["provider_calls_performed"] is False
    assert payload["operator_action_required"]["required"] is True
    assert payload["operator_action_required"]["no_safe_autonomous_completion_pass_available"] is True
    assert payload["operator_action_required"]["next_operator_action_id"] == "openai_secret_reference"
    openai_next_action = next(
        item
        for item in payload["operator_action_required"]["next_action_queue"]
        if item["id"] == "openai_secret_reference"
    )
    assert openai_next_action["handoff_guide_path"] == (
        "07_LOGS/Operator-Briefs/2026-05-14-openai-api-key-later-guide.md"
    )
    assert openai_next_action["current_secret_reference_target"] == "SET_OPENAI_SECRET_REF"
    assert openai_next_action["current_secret_reference_target_is_placeholder"] is True
    assert openai_next_action["current_secret_reference_resolvable"] is False
    assert openai_next_action["secret_reference_probe_error"] == "reference_not_found"
    assert openai_next_action["provider_live_smoke_readiness_command"] == (
        "python -m runtime.cli.main runtime provider live-smoke-readiness --json"
    )
    assert openai_next_action["reference_presence_check_commands"] == [
        '[bool][Environment]::GetEnvironmentVariable("OPENAI_API_KEY", "User")',
        '[bool][Environment]::GetEnvironmentVariable("OPENAI_API_KEY", "Process")',
    ]
    assert openai_next_action["reference_presence_check_outputs_secret_value"] is False
    assert openai_next_action["secret_value_read"] is False
    assert openai_next_action["live_network_call_attempted"] is False
    assert payload["operator_action_required"]["canonical_operator_handoff"] == payload[
        "canonical_operator_handoff"
    ]
    assert payload["operator_action_required"]["operator_input_template_artifact"] == payload[
        "operator_input_template_artifact"
    ]
    assert {
        "openai_secret_reference",
        "ventureops_real_client_scope",
        "pending_chat_approval_decision",
    } <= set(payload["operator_action_required"]["operator_input_ids"])
    assert payload["source_commands"]["completion_audit"] == (
        "python -m runtime.cli.main mvp completion-audit --json"
    )
    assert payload["source_commands"]["setup_wide_validation"] == (
        "python -m runtime.cli.main setup validate --json"
    )
    assert payload["authority"]["secret_values_read"] is False
    assert payload["authority"]["provider_calls_performed"] is False
    assert payload["authority"]["approval_consumption_performed"] is False
    assert secret_value not in serialized


def test_mvp_current_state_separates_setup_wide_gaps_from_current_mvp_blockers(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    _seed_minimal_vault(tmp_path)
    _seed_current_mvp_truth_surfaces(tmp_path)
    _seed_operator_input_template(tmp_path)
    _seed_setup_scope_fixture(tmp_path)

    payload = build_mvp_current_state(tmp_path)
    setup_scope = payload["setup_scope_boundary"]

    assert setup_scope["status"] == (
        "setup_wide_validation_expected_to_fail_mvp_blocker_and_non_mvp_gaps"
    )
    assert setup_scope["setup_wide_validation_expected_to_pass_now"] is False
    assert setup_scope["setup_wide_validation_can_fail_on_non_mvp_items"] is True
    assert setup_scope["mvp_current_setup_blocker_ids"] == ["openai_secret_reference"]
    assert setup_scope["current_mvp_next_operator_action_id"] == "openai_secret_reference"
    assert setup_scope["setup_wide_invalid_provider_ids"] == [
        "claude",
        "openai",
        "local_oss",
        "n8n",
    ]
    assert setup_scope["setup_wide_invalid_integration_ids"] == [
        "telegram",
        "slack",
    ]
    assert setup_scope["non_mvp_setup_gap_ids"] == [
        "provider:claude",
        "provider:local_oss",
        "provider:n8n",
        "integration:telegram",
        "integration:slack",
    ]
    assert setup_scope["non_mvp_setup_gaps_are_current_mvp_blockers"] is False
    assert setup_scope["secret_values_read"] is False
    assert setup_scope["provider_calls_performed"] is False
    assert "openai_secret_reference" in payload["p0_blocker_ids"]
    assert all(
        gap_id not in payload["p0_blocker_ids"]
        for gap_id in setup_scope["non_mvp_setup_gap_ids"]
    )


def test_mvp_current_state_cli_uses_json_envelope(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    _seed_minimal_vault(tmp_path)
    _seed_current_mvp_truth_surfaces(tmp_path)
    _seed_operator_input_template(tmp_path)

    exit_code = cli.main(["mvp", "current-state", "--vault-root", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "mvp.current-state"
    assert payload["result"]["surface"] == "chaseos_mvp_current_state_map"
    assert payload["result"]["pass_status_count"] == 10
    assert payload["result"]["pass_status_by_id"]["credential_readiness"]["status"] == (
        "blocked_operator_input_required"
    )
    assert payload["result"]["safe_to_call_update_goal_complete"] is False
    assert payload["result"]["canonical_operator_handoff"]["path"] == (
        "07_LOGS/Operator-Briefs/2026-05-13-mvp-next-action-card.md"
    )
    assert payload["result"]["canonical_operator_handoff"]["exists"] is True
    assert payload["result"]["canonical_operator_handoff"]["execution_authority_granted"] is False
    assert payload["result"]["operator_input_template_artifact"]["path"] == (
        "07_LOGS/Operator-Briefs/2026-05-13-mvp-operator-input-template.json"
    )
    assert payload["result"]["operator_input_template_artifact"]["exists"] is True
    assert payload["result"]["operator_input_template_artifact"]["contains_secret_values"] is False
    assert payload["result"]["operator_input_ids"] == payload["result"]["completion_decision"][
        "operator_input_ids"
    ]
    assert payload["result"]["next_operator_action_id"] == "openai_secret_reference"
    assert payload["result"]["next_recommended_pass"] == "operator-provide-openai-secret-reference"
    assert payload["result"]["next_operator_action_id"] == payload["result"][
        "autonomous_completion_barrier"
    ]["next_operator_action_id"]
    assert payload["result"]["next_recommended_pass"] == payload["result"][
        "autonomous_completion_barrier"
    ]["next_recommended_pass"]
    assert payload["result"]["update_goal_allowed"] is False
    assert payload["result"]["no_safe_autonomous_completion_pass_available"] is True
    assert payload["result"]["completion_safety_contract"]["status"] == (
        "blocked_do_not_call_update_goal_complete"
    )
    assert payload["result"]["completion_safety_contract"]["update_goal_allowed"] is False
    assert payload["result"]["completion_safety_contract"]["operator_input_ids"] == payload[
        "result"
    ]["operator_input_ids"]
    assert payload["result"]["operator_action_required"]["completion_safety_contract"] == payload[
        "result"
    ]["completion_safety_contract"]
    assert payload["result"]["approval_queue_boundary"]["tracked_pending_count"] == 1
    assert payload["result"]["approval_queue_boundary"][
        "tracked_chat_approval_is_current_mvp_decision"
    ] is True
    assert payload["result"]["approval_queue_boundary"][
        "untracked_pending_approvals_are_current_mvp_blockers"
    ] is False
    assert payload["result"]["setup_scope_boundary"]["mvp_current_setup_blocker_ids"] == [
        "openai_secret_reference"
    ]
    assert payload["result"]["setup_scope_boundary"][
        "non_mvp_setup_gaps_are_current_mvp_blockers"
    ] is False
    assert payload["result"]["operator_action_required"]["next_operator_action_id"] == "openai_secret_reference"


def test_mvp_current_state_text_output_shows_completion_barrier(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    _seed_minimal_vault(tmp_path)
    _seed_current_mvp_truth_surfaces(tmp_path)
    _seed_operator_input_template(tmp_path)

    exit_code = cli.main(["mvp", "current-state", "--vault-root", str(tmp_path)])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "objective_achieved: False" in output
    assert "safe_to_call_update_goal_complete: False" in output
    assert "autonomous_completion_barrier:" in output
    assert "completion_safety_contract:" in output
    assert "update_goal_allowed=False" in output
    assert "update_goal_allowed=False" in output
    assert "setup_scope:" in output
    assert "non_mvp_are_mvp_blockers=False" in output
    assert (
        'presence_check: [bool][Environment]::GetEnvironmentVariable("OPENAI_API_KEY", "User")'
        in output
    )
    assert '[bool][Environment]::GetEnvironmentVariable("OPENAI_API_KEY", "Process")' in output
    assert "sk-" not in output


def test_mvp_operator_input_template_packet_is_standalone_and_no_secret(
    tmp_path: Path, monkeypatch
) -> None:
    secret_value = "test-key-template-packet-secret-that-must-not-appear"
    monkeypatch.setenv("OPENAI_API_KEY", secret_value)
    _seed_minimal_vault(tmp_path)

    payload = build_mvp_operator_input_template_packet(tmp_path)
    serialized = json.dumps(payload, sort_keys=True)

    assert payload["surface"] == "chaseos_mvp_operator_input_template_packet"
    assert payload["read_only"] is True
    assert payload["validation_command"] == (
        "python -m runtime.cli.main mvp validate-operator-input --input <OPERATOR_INPUT_JSON> --json"
    )
    assert payload["objective_achieved"] is False
    assert payload["safe_to_call_update_goal_complete"] is False
    assert payload["operator_input_ids"] == [
        "openai_secret_reference",
        "ventureops_real_client_scope",
        "pending_chat_approval_decision",
    ]
    assert payload["p0_blocker_ids"] == [
        "openai_secret_reference",
        "ventureops_real_client_scope",
    ]
    assert payload["p1_decision_ids"] == ["pending_chat_approval_decision"]
    assert payload["completion_decision"]["operator_input_ids"] == payload["operator_input_ids"]
    assert payload["autonomous_completion_barrier"]["active"] is True
    assert payload["autonomous_completion_barrier"]["update_goal_allowed"] is False
    assert payload["completion_safety_contract"]["status"] == (
        "blocked_do_not_call_update_goal_complete"
    )
    assert payload["completion_safety_contract"]["update_goal_allowed"] is False
    assert payload["completion_safety_contract"]["checklist_coverage_is_not_completion"] is True
    assert payload["completion_safety_contract"]["operator_input_ids"] == payload[
        "operator_input_ids"
    ]
    assert payload["setup_scope_boundary"]["mvp_current_setup_blocker_ids"] == [
        "openai_secret_reference"
    ]
    assert payload["setup_scope_boundary"]["non_mvp_setup_gap_ids"] == []
    assert (
        payload["setup_scope_boundary"]["non_mvp_setup_gaps_are_current_mvp_blockers"]
        is False
    )
    assert payload["no_safe_autonomous_completion_pass_available"] is True
    assert payload["update_goal_allowed"] is False
    assert payload["next_operator_action_id"] == "openai_secret_reference"
    assert payload["next_recommended_pass"] == "operator-provide-openai-secret-reference"
    assert payload["required_operator_inputs"]
    assert payload["operator_input_template_version"] == "chaseos.mvp_operator_input_template.v1"
    assert payload["operator_input_template_artifact"] == {
        "path": "07_LOGS/Operator-Briefs/2026-05-13-mvp-operator-input-template.json",
        "exists": False,
        "contains_secret_values": False,
        "validation_command": "python -m runtime.cli.main mvp validate-operator-input --input 07_LOGS/Operator-Briefs/2026-05-13-mvp-operator-input-template.json --json",
        "write_command": "python -m runtime.cli.main mvp operator-input-template --write-template 07_LOGS/Operator-Briefs/2026-05-13-mvp-operator-input-template.json --json",
    }
    assert set(payload["operator_input_values"]) == {
        "openai_secret_reference",
        "ventureops_real_client_scope",
        "pending_chat_approval_decision",
    }
    assert payload["operator_input_values"]["openai_secret_reference"] == {
        "secret_reference_target": "OPENAI_API_KEY"
    }
    assert payload["operator_input_values"]["pending_chat_approval_decision"] == {
        "approval_id": PENDING_CHAT_APPROVAL_ID,
        "decision": "leave_pending",
    }
    assert payload["boundary"]["secret_values_allowed"] is False
    assert payload["boundary"]["setup_metadata_write_performed"] is False
    assert payload["boundary"]["approval_consumption_performed"] is False
    assert secret_value not in serialized


def test_mvp_operator_input_template_cli_uses_json_envelope(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    _seed_minimal_vault(tmp_path)

    exit_code = cli.main(["mvp", "operator-input-template", "--vault-root", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "mvp.operator-input-template"
    assert payload["result"]["surface"] == "chaseos_mvp_operator_input_template_packet"
    assert payload["result"]["operator_input_template_artifact"]["path"] == (
        "07_LOGS/Operator-Briefs/2026-05-13-mvp-operator-input-template.json"
    )
    assert payload["result"]["operator_input_template_artifact"]["exists"] is False
    assert payload["result"]["operator_input_template_artifact"]["contains_secret_values"] is False
    assert payload["result"]["safe_to_call_update_goal_complete"] is False
    assert payload["result"]["operator_input_ids"] == payload["result"]["completion_decision"][
        "operator_input_ids"
    ]
    assert payload["result"]["autonomous_completion_barrier"]["active"] is True
    assert payload["result"]["autonomous_completion_barrier"]["update_goal_allowed"] is False
    assert payload["result"]["completion_safety_contract"]["status"] == (
        "blocked_do_not_call_update_goal_complete"
    )
    assert payload["result"]["completion_safety_contract"]["update_goal_allowed"] is False
    assert payload["result"]["completion_safety_contract"]["operator_input_ids"] == payload[
        "result"
    ]["operator_input_ids"]
    assert payload["result"]["setup_scope_boundary"]["mvp_current_setup_blocker_ids"] == [
        "openai_secret_reference"
    ]
    assert (
        payload["result"]["setup_scope_boundary"][
            "non_mvp_setup_gaps_are_current_mvp_blockers"
        ]
        is False
    )
    assert payload["result"]["no_safe_autonomous_completion_pass_available"] is True
    assert payload["result"]["update_goal_allowed"] is False
    assert payload["result"]["next_operator_action_id"] == "openai_secret_reference"
    assert payload["result"]["next_recommended_pass"] == "operator-provide-openai-secret-reference"
    assert payload["result"]["required_operator_inputs"]
    assert payload["result"]["operator_input_values"]["openai_secret_reference"] == {
        "secret_reference_target": "OPENAI_API_KEY"
    }


def test_mvp_operator_input_template_text_prints_presence_check(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    _seed_minimal_vault(tmp_path)

    exit_code = cli.main(["mvp", "operator-input-template", "--vault-root", str(tmp_path)])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "next_operator_action: openai_secret_reference" in output
    assert "completion_safety_contract:" in output
    assert "checklist_coverage_is_not_completion=True" in output
    assert "setup_scope: status=setup_wide_validation_expected_to_fail_current_mvp_blocker" in output
    assert "non_mvp_are_mvp_blockers=False" in output
    assert (
        'presence_check: [bool][Environment]::GetEnvironmentVariable("OPENAI_API_KEY", "User")'
        in output
    )
    assert '[bool][Environment]::GetEnvironmentVariable("OPENAI_API_KEY", "Process")' in output
    assert "secret_reference_target=OPENAI_API_KEY" in output
    assert "sk-" not in output


def test_mvp_operator_unblock_packet_text_prints_presence_check(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    _seed_minimal_vault(tmp_path)

    exit_code = cli.main(["mvp", "operator-unblock-packet", "--vault-root", str(tmp_path)])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "next_operator_action: openai_secret_reference" in output
    assert (
        'presence_check: [bool][Environment]::GetEnvironmentVariable("OPENAI_API_KEY", "User")'
        in output
    )
    assert '[bool][Environment]::GetEnvironmentVariable("OPENAI_API_KEY", "Process")' in output
    assert "sk-" not in output


def test_mvp_primary_status_text_outputs_print_presence_check(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    _seed_minimal_vault(tmp_path)

    commands = [
        ["mvp", "readiness-gate", "--vault-root", str(tmp_path)],
        ["mvp", "completion-audit", "--vault-root", str(tmp_path)],
    ]
    for command in commands:
        exit_code = cli.main(command)
        output = capsys.readouterr().out

        assert exit_code == 0
        assert (
            'presence_check: [bool][Environment]::GetEnvironmentVariable("OPENAI_API_KEY", "User")'
            in output
        )
        assert '[bool][Environment]::GetEnvironmentVariable("OPENAI_API_KEY", "Process")' in output
        assert "sk-" not in output


def test_mvp_operator_input_template_cli_writes_no_secret_template_inside_vault(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    secret_value = "test-key-template-write-secret-that-must-not-appear"
    monkeypatch.setenv("OPENAI_API_KEY", secret_value)
    _seed_minimal_vault(tmp_path)
    output_path = "07_LOGS/Operator-Briefs/mvp-operator-input-template.json"

    exit_code = cli.main(
        [
            "mvp",
            "operator-input-template",
            "--vault-root",
            str(tmp_path),
            "--write-template",
            output_path,
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    written = tmp_path / output_path
    artifact = json.loads(written.read_text(encoding="utf-8"))
    serialized = json.dumps({"payload": payload, "artifact": artifact}, sort_keys=True)

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["result"]["read_only"] is False
    assert payload["result"]["template_write"]["written"] is True
    assert payload["result"]["template_write"]["vault_relative_path"] == output_path
    assert payload["result"]["template_write"]["contains_secret_values"] is False
    assert payload["result"]["template_write"]["setup_metadata_write_performed"] is False
    assert payload["result"]["template_write"]["approval_consumption_performed"] is False
    assert artifact["surface"] == "chaseos_mvp_operator_input_values_template"
    assert artifact["operator_input_values"]["openai_secret_reference"] == {
        "secret_reference_target": "OPENAI_API_KEY"
    }
    assert artifact["objective_achieved"] is False
    assert artifact["safe_to_call_update_goal_complete"] is False
    assert artifact["operator_input_ids"] == payload["result"]["operator_input_ids"]
    assert artifact["completion_decision"]["operator_input_ids"] == payload["result"][
        "operator_input_ids"
    ]
    assert artifact["autonomous_completion_barrier"]["active"] is True
    assert artifact["autonomous_completion_barrier"]["update_goal_allowed"] is False
    assert artifact["completion_safety_contract"]["status"] == (
        "blocked_do_not_call_update_goal_complete"
    )
    assert artifact["completion_safety_contract"]["update_goal_allowed"] is False
    assert artifact["completion_safety_contract"]["operator_input_ids"] == artifact[
        "operator_input_ids"
    ]
    assert artifact["required_operator_inputs"]
    openai_input = next(
        item for item in artifact["required_operator_inputs"] if item["id"] == "openai_secret_reference"
    )
    assert openai_input["reference_presence_check_commands"] == [
        '[bool][Environment]::GetEnvironmentVariable("OPENAI_API_KEY", "User")',
        '[bool][Environment]::GetEnvironmentVariable("OPENAI_API_KEY", "Process")',
    ]
    assert openai_input["reference_presence_check_outputs_secret_value"] is False
    pending_input = next(
        item
        for item in artifact["required_operator_inputs"]
        if item["id"] == "pending_chat_approval_decision"
    )
    assert pending_input["approval_id"] == PENDING_CHAT_APPROVAL_ID
    assert pending_input["approval_consumption_readiness_command"] == (
        "python -m runtime.cli.main studio phase11-chat-approval-consumption-readiness-contract "
        f"--approval-id {PENDING_CHAT_APPROVAL_ID} --json"
    )
    assert pending_input["approval_consumption_executor_command_template"] == (
        "python -m runtime.cli.main studio phase11-chat-approval-consumption-executor "
        f"--approval-id {PENDING_CHAT_APPROVAL_ID} "
        "--expected-consumption-digest <digest_from_readiness> --json"
    )
    assert pending_input["approval_consumption_allowed_now"] is False
    assert pending_input["requires_operator_approval_decision"] is True
    assert artifact["boundary"]["secret_values_allowed"] is False
    assert secret_value not in serialized


def test_mvp_operator_input_template_cli_rejects_write_outside_vault(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    _seed_minimal_vault(tmp_path)
    outside = tmp_path.parent / "outside-template.json"

    exit_code = cli.main(
        [
            "mvp",
            "operator-input-template",
            "--vault-root",
            str(tmp_path),
            "--write-template",
            str(outside),
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["ok"] is False
    assert "must stay inside vault root" in payload["result"]["error"]
    assert not outside.exists()


def test_mvp_operator_input_validation_accepts_filled_references_without_echoing_values(
    tmp_path: Path, monkeypatch
) -> None:
    secret_value = "test-key-validator-secret-that-must-not-appear"
    monkeypatch.setenv("OPENAI_API_KEY", secret_value)
    _seed_minimal_vault(tmp_path)
    source_path = tmp_path / "03_INPUTS" / "client-alpha" / "redacted-source.md"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text("approved redacted source\n", encoding="utf-8")
    client_label = "Client Alpha"

    payload = {
        "operator_input_values": {
            "openai_secret_reference": {
                "secret_reference_target": "OPENAI_API_KEY",
            },
            "ventureops_real_client_scope": {
                "client_label": client_label,
                "client_approved_scope_id": "scope-alpha",
                "approval_id": "approval-alpha",
                "approved_read_paths": ["03_INPUTS/client-alpha/redacted-source.md"],
                "approval_output_path": "07_LOGS/Workflow-Proofs/client-alpha-scope-approval.json",
                "scope_packet_output_path": "07_LOGS/Workflow-Proofs/client-alpha-scope-evidence.json",
            },
            "pending_chat_approval_decision": {
                "approval_id": PENDING_CHAT_APPROVAL_ID,
                "decision": "leave_pending",
            },
        }
    }

    result = build_mvp_operator_input_validation(tmp_path, payload)
    serialized = json.dumps(result, sort_keys=True)

    assert result["surface"] == "chaseos_mvp_operator_input_validation"
    assert result["ok"] is True
    assert result["accepted_for_safe_followup"] is True
    assert result["valid"] is True
    assert result["safe_to_call_update_goal_complete"] is False
    assert result["operator_input_ids"] == result["completion_decision"]["operator_input_ids"]
    assert result["autonomous_completion_barrier"]["active"] is True
    assert result["autonomous_completion_barrier"]["update_goal_allowed"] is False
    assert result["completion_safety_contract"]["status"] == (
        "blocked_do_not_call_update_goal_complete"
    )
    assert result["completion_safety_contract"]["update_goal_allowed"] is False
    assert result["completion_safety_contract"]["operator_input_ids"] == result[
        "operator_input_ids"
    ]
    assert result["no_safe_autonomous_completion_pass_available"] is True
    assert result["update_goal_allowed"] is False
    assert result["next_operator_action_id"] == "openai_secret_reference"
    assert result["next_recommended_pass"] == "operator-provide-openai-secret-reference"
    assert result["setup_scope_boundary"]["mvp_current_setup_blocker_ids"] == [
        "openai_secret_reference"
    ]
    assert result["setup_scope_boundary"]["non_mvp_setup_gap_ids"] == []
    assert (
        result["setup_scope_boundary"]["non_mvp_setup_gaps_are_current_mvp_blockers"]
        is False
    )
    assert result["source_completion_context"]["present"] is False
    assert result["source_completion_context"]["matches_current"] is None
    assert result["required_operator_inputs"]
    assert result["blocked_group_ids"] == []
    assert result["source_values_echoed"] is False
    assert result["candidate_values_visible"] is False
    assert secret_value not in serialized
    assert client_label not in serialized
    groups = {item["id"]: item for item in result["groups"]}
    openai_field = groups["openai_secret_reference"]["field_results"][0]
    assert openai_field["secret_reference_probe"]["exists"] is True
    assert openai_field["candidate_value_visible"] is False
    paths_field = next(
        item for item in groups["ventureops_real_client_scope"]["field_results"]
        if item["name"] == "approved_read_paths"
    )
    assert paths_field["path_policy"]["existing_path_count"] == 1
    assert groups["pending_chat_approval_decision"]["status"] == "valid_for_safe_followup"
    plan = result["safe_followup_plan"]
    assert plan["status"] == "ready_for_operator_confirmed_followup"
    assert plan["candidate_values_visible"] is False
    assert plan["execution_authority_granted"] is False
    assert [step["id"] for step in plan["next_steps"]] == [
        "setup_provider_secret_reference_metadata",
        "author_ventureops_scope_approval_packet",
        "review_pending_chat_approval_decision",
    ]
    assert all(step["execution_allowed_now"] is False for step in plan["next_steps"])
    assert plan["next_steps"][0]["command_template"] == (
        "python -m runtime.cli.main setup set provider openai secret_reference_kind=env-var-or-local-secret-ref secret_reference_present=true secret_reference_target=OPENAI_API_KEY --dry-run --json"
    )
    assert plan["next_steps"][0]["confirmation_command_template"] == (
        "python -m runtime.cli.main setup set provider openai secret_reference_kind=env-var-or-local-secret-ref secret_reference_present=true secret_reference_target=OPENAI_API_KEY --json"
    )
    assert plan["next_steps"][0]["preconditions"] == [
        "operator has already created or confirmed the local gitignored secret reference",
        "dry-run preview reports writes_setup_state=false before live metadata write",
        "no API key value is pasted into repo, chat, logs, or setup metadata",
    ]
    assert plan["next_steps"][2]["preconditions"] == [
        "operator has chosen approve, reject, or leave_pending",
        "exact-once consumption readiness preview has been inspected for this approval id",
        "approval consumption remains a separate governed pass",
    ]
    assert plan["next_steps"][2]["command_template"] == (
        "python -m runtime.cli.main studio phase11-chat-approval-consumption-readiness-contract --approval-id 5849a53f-10e0-46af-a89a-7de06150f7f8 --json"
    )
    assert plan["next_steps"][2]["confirmation_command_template"] == (
        "python -m runtime.cli.main studio phase11-chat-approval-consumption-executor --approval-id 5849a53f-10e0-46af-a89a-7de06150f7f8 --expected-consumption-digest <digest_from_readiness> --json"
    )


def test_mvp_operator_input_validation_blocks_stale_embedded_completion_context(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-validator-secret-that-must-not-appear")
    _seed_minimal_vault(tmp_path, secret_target="OPENAI_API_KEY")
    source_path = tmp_path / "03_INPUTS" / "client-alpha" / "redacted-source.md"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text("approved redacted source\n", encoding="utf-8")
    packet = build_mvp_operator_input_template_packet(tmp_path)
    completion_decision = dict(packet["completion_decision"])
    completion_decision["safe_to_call_update_goal_complete"] = True

    payload = {
        "completion_decision": completion_decision,
        "autonomous_completion_barrier": dict(packet["autonomous_completion_barrier"]),
        "operator_input_values": {
            "openai_secret_reference": {"secret_reference_target": "OPENAI_API_KEY"},
            "ventureops_real_client_scope": {
                "client_label": "Client Alpha",
                "client_approved_scope_id": "scope-alpha",
                "approval_id": "approval-alpha",
                "approved_read_paths": ["03_INPUTS/client-alpha/redacted-source.md"],
                "approval_output_path": "07_LOGS/Workflow-Proofs/client-alpha-scope-approval.json",
                "scope_packet_output_path": "07_LOGS/Workflow-Proofs/client-alpha-scope-evidence.json",
            },
            "pending_chat_approval_decision": {
                "approval_id": PENDING_CHAT_APPROVAL_ID,
                "decision": "leave_pending",
            },
        },
    }

    result = build_mvp_operator_input_validation(tmp_path, payload)
    serialized = json.dumps(result, sort_keys=True)

    assert result["ok"] is False
    assert result["accepted_for_safe_followup"] is False
    assert result["valid"] is False
    assert result["blocked_group_ids"] == []
    assert result["source_completion_context"]["present"] is True
    assert result["source_completion_context"]["matches_current"] is False
    assert result["source_completion_context"]["stale_context_detected"] is True
    assert result["source_completion_context"]["mismatch_fields"] == [
        "completion_decision.safe_to_call_update_goal_complete"
    ]
    assert result["safe_followup_plan"]["status"] == "blocked_until_input_validation_passes"
    assert "test-key-validator-secret-that-must-not-appear" not in serialized


def test_mvp_operator_input_validation_blocks_placeholders_and_secret_like_reference(
    tmp_path: Path, monkeypatch
) -> None:
    secret_value = "test-key-validator-secret-that-must-not-appear"
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    _seed_minimal_vault(tmp_path)

    payload = build_mvp_operator_unblock_packet(tmp_path)["operator_input_template"]
    payload["groups"][0]["template_values"]["secret_reference_target"] = secret_value

    result = build_mvp_operator_input_validation(tmp_path, payload)
    serialized = json.dumps(result, sort_keys=True)

    assert result["ok"] is False
    assert result["accepted_for_safe_followup"] is False
    assert result["valid"] is False
    assert result["safe_to_call_update_goal_complete"] is False
    assert result["operator_input_ids"] == result["completion_decision"]["operator_input_ids"]
    assert result["autonomous_completion_barrier"]["active"] is True
    assert result["autonomous_completion_barrier"]["update_goal_allowed"] is False
    assert {
        "openai_secret_reference",
        "ventureops_real_client_scope",
    } <= set(result["blocked_group_ids"])
    openai_group = next(item for item in result["groups"] if item["id"] == "openai_secret_reference")
    assert any(
        "candidate_looks_like_secret_value_not_reference_name" in error
        for error in openai_group["errors"]
    )
    ventureops_group = next(item for item in result["groups"] if item["id"] == "ventureops_real_client_scope")
    assert any("placeholder_not_replaced" in error for error in ventureops_group["errors"])
    assert result["safe_followup_plan"]["status"] == "blocked_until_input_validation_passes"
    assert {
        "setup_provider_secret_reference_metadata",
        "author_ventureops_scope_approval_packet",
    } <= set(result["safe_followup_plan"]["blocked_step_ids"])
    assert secret_value not in serialized


def test_mvp_operator_input_validation_cli_uses_json_envelope(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-cli-validator-secret-that-must-not-appear")
    _seed_minimal_vault(tmp_path)
    source_path = tmp_path / "03_INPUTS" / "client-alpha" / "redacted-source.md"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text("approved redacted source\n", encoding="utf-8")
    input_path = tmp_path / "operator-input.json"
    _write_json(
        input_path,
        {
            "operator_input_values": {
                "openai_secret_reference": {"secret_reference_target": "OPENAI_API_KEY"},
                "ventureops_real_client_scope": {
                    "client_label": "Client Alpha",
                    "client_approved_scope_id": "scope-alpha",
                    "approval_id": "approval-alpha",
                    "approved_read_paths": ["03_INPUTS/client-alpha/redacted-source.md"],
                    "approval_output_path": "07_LOGS/Workflow-Proofs/client-alpha-scope-approval.json",
                },
                "pending_chat_approval_decision": {
                    "approval_id": PENDING_CHAT_APPROVAL_ID,
                    "decision": "leave_pending",
                },
            }
        },
    )

    exit_code = cli.main([
        "mvp",
        "validate-operator-input",
        "--vault-root",
        str(tmp_path),
        "--input",
        str(input_path),
        "--json",
    ])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "mvp.validate-operator-input"
    assert payload["result"]["surface"] == "chaseos_mvp_operator_input_validation"
    assert payload["result"]["accepted_for_safe_followup"] is True
    assert payload["result"]["valid"] is True
    assert payload["result"]["safe_to_call_update_goal_complete"] is False
    assert payload["result"]["autonomous_completion_barrier"]["active"] is True
    assert payload["result"]["autonomous_completion_barrier"]["update_goal_allowed"] is False
    assert payload["result"]["no_safe_autonomous_completion_pass_available"] is True
    assert payload["result"]["update_goal_allowed"] is False
    assert payload["result"]["next_operator_action_id"] == "openai_secret_reference"
    assert payload["result"]["next_recommended_pass"] == "operator-provide-openai-secret-reference"
    assert payload["result"]["setup_scope_boundary"]["mvp_current_setup_blocker_ids"] == [
        "openai_secret_reference"
    ]
    assert (
        payload["result"]["setup_scope_boundary"][
            "non_mvp_setup_gaps_are_current_mvp_blockers"
        ]
        is False
    )
    assert payload["result"]["required_operator_inputs"]
    assert payload["result"]["candidate_values_visible"] is False
    assert payload["result"]["safe_followup_plan"]["status"] == "ready_for_operator_confirmed_followup"


def test_mvp_operator_input_validation_text_reports_source_completion_context(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    _seed_minimal_vault(tmp_path)
    input_path = tmp_path / "operator-input-template.json"

    write_exit_code = cli.main([
        "mvp",
        "operator-input-template",
        "--vault-root",
        str(tmp_path),
        "--write-template",
        str(input_path),
        "--json",
    ])
    capsys.readouterr()

    assert write_exit_code == 0

    validate_exit_code = cli.main([
        "mvp",
        "validate-operator-input",
        "--vault-root",
        str(tmp_path),
        "--input",
        str(input_path),
    ])
    output = capsys.readouterr().out

    assert validate_exit_code == 0
    assert "source_completion_context:" in output
    assert "completion_safety_contract:" in output
    assert "checklist_coverage_is_not_completion=True" in output
    assert "present=True" in output
    assert "matches_current=True" in output
    assert "stale_context_detected=False" in output
    assert "setup_scope: status=setup_wide_validation_expected_to_fail_current_mvp_blocker" in output
    assert "non_mvp_are_mvp_blockers=False" in output
    assert "current_secret_reference: target=SET_OPENAI_SECRET_REF" in output
    assert "placeholder=True" in output
    assert "resolvable=False" in output
    assert "error=reference_not_found" in output
    assert (
        "provider_live_smoke_readiness: "
        "python -m runtime.cli.main runtime provider live-smoke-readiness --json"
    ) in output


def test_mvp_validate_operator_input_current_repo_template_stays_blocked_only_on_openai_reference(
    capsys, monkeypatch
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    input_path = ROOT / "07_LOGS" / "Operator-Briefs" / "2026-05-13-mvp-operator-input-template.json"

    exit_code = cli.main([
        "mvp",
        "validate-operator-input",
        "--vault-root",
        str(ROOT),
        "--input",
        str(input_path),
        "--json",
    ])
    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "mvp.validate-operator-input"
    assert result["surface"] == "chaseos_mvp_operator_input_validation"
    assert result["ok"] is False
    assert result["accepted_for_safe_followup"] is False
    assert result["valid"] is False
    assert result["safe_to_call_update_goal_complete"] is False
    assert result["operator_input_ids"] == result["completion_decision"]["operator_input_ids"]
    assert result["autonomous_completion_barrier"]["active"] is True
    assert result["autonomous_completion_barrier"]["update_goal_allowed"] is False
    assert result["completion_safety_contract"]["status"] == (
        "blocked_do_not_call_update_goal_complete"
    )
    assert result["completion_safety_contract"]["update_goal_allowed"] is False
    assert result["completion_safety_contract"]["operator_input_ids"] == result[
        "operator_input_ids"
    ]
    assert result["source_completion_context"]["present"] is True
    assert result["source_completion_context"]["matches_current"] is True
    assert result["source_completion_context"]["stale_context_detected"] is False
    assert result["required_operator_inputs"]
    required_inputs = {item["id"]: item for item in result["required_operator_inputs"]}
    assert required_inputs["openai_secret_reference"]["reference_presence_check_commands"] == [
        '[bool][Environment]::GetEnvironmentVariable("OPENAI_API_KEY", "User")',
        '[bool][Environment]::GetEnvironmentVariable("OPENAI_API_KEY", "Process")',
    ]
    assert (
        required_inputs["openai_secret_reference"][
            "reference_presence_check_outputs_secret_value"
        ]
        is False
    )
    assert result["operator_input_ids"] == ["openai_secret_reference"]
    assert result["p1_decision_ids"] == []
    assert result["setup_scope_boundary"]["mvp_current_setup_blocker_ids"] == [
        "openai_secret_reference"
    ]
    assert result["setup_scope_boundary"]["non_mvp_setup_gap_ids"] == [
        "provider:claude",
        "provider:local_oss",
        "provider:n8n",
        "integration:telegram",
        "integration:slack",
    ]
    assert (
        result["setup_scope_boundary"]["non_mvp_setup_gaps_are_current_mvp_blockers"]
        is False
    )
    assert result["blocked_group_ids"] == ["openai_secret_reference"]
    groups = {item["id"]: item for item in result["groups"]}
    assert groups["openai_secret_reference"]["status"] == "blocked_input_validation"
    assert groups["openai_secret_reference"]["errors"] == [
        "secret_reference_target:secret_reference_not_resolved"
    ]
    assert groups["openai_secret_reference"]["current_secret_reference_target"] == (
        "OPENAI_API_KEY"
    )
    assert groups["openai_secret_reference"][
        "current_secret_reference_target_is_placeholder"
    ] is False
    assert groups["openai_secret_reference"]["current_secret_reference_resolvable"] is False
    assert groups["openai_secret_reference"]["secret_reference_probe_error"] == (
        "reference_not_found"
    )
    assert groups["openai_secret_reference"]["provider_live_smoke_readiness_command"] == (
        "python -m runtime.cli.main runtime provider live-smoke-readiness --json"
    )
    assert groups["openai_secret_reference"]["secret_value_read"] is False
    assert groups["openai_secret_reference"]["secret_value_allowed_in_repo_or_chat"] is False
    assert "pending_chat_approval_decision" not in groups
    assert result["safe_followup_plan"]["status"] == "blocked_until_input_validation_passes"
    assert result["boundary"]["secret_values_visible"] is False
    assert result["boundary"]["provider_calls_performed"] is False
    assert result["boundary"]["setup_metadata_mutated"] is False
    assert result["boundary"]["approval_consumption_performed"] is False


def test_mvp_protected_operator_docs_match_current_repo_p0_only_gate(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    current_state = build_mvp_current_state(ROOT)

    assert current_state["operator_input_ids"] == ["openai_secret_reference"]
    assert current_state["p1_decision_ids"] == []

    docs = [
        ROOT / "06_AGENTS" / "ChaseOS-MVP-Current-Goal-and-Pass-Plan.md",
        ROOT / "06_AGENTS" / "ChaseOS-MVP-Consolidation-Map.md",
        ROOT / "06_AGENTS" / "ChaseOS-MVP-Operator-Unblock-Packet.md",
    ]
    stale_current_claims = [
        "P1 decision: `pending_chat_approval_decision`",
        "P1 operator decision: pending Chat approval",
        "required actions `openai_secret_reference` and `pending_chat_approval_decision`",
        "`next_action_queue`: `openai_secret_reference` -> `pending_chat_approval_decision`",
        "current groups `openai_secret_reference` and `pending_chat_approval_decision`",
        'operator_input_ids=["openai_secret_reference", "pending_chat_approval_decision"]',
        "pending Chat approval remains an operator follow-up",
        "approval remains pending",
    ]

    for doc in docs:
        text = doc.read_text(encoding="utf-8")
        for stale_claim in stale_current_claims:
            assert stale_claim not in text, f"{doc} still has stale current claim: {stale_claim}"


def test_mvp_chronological_truth_surfaces_supersede_historical_p1_claims(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    current_state = build_mvp_current_state(ROOT)

    assert current_state["operator_input_ids"] == ["openai_secret_reference"]
    assert current_state["p1_decision_ids"] == []

    now_text = (ROOT / "00_HOME" / "Now.md").read_text(encoding="utf-8")
    profile_text = (ROOT / "06_AGENTS" / "Codex-Runtime-Profile.md").read_text(encoding="utf-8")

    for text in (now_text, profile_text):
        assert "Current live gate truth is P0 `openai_secret_reference` only" in text
        assert "no current P1 decision ids" in text
        assert "executed/marker-present" in text


def test_mvp_protected_current_truth_docs_are_synced_to_latest_evidence(
    monkeypatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    current_state = build_mvp_current_state(ROOT)
    audit = build_mvp_completion_audit(ROOT)

    assert current_state["safe_to_call_update_goal_complete"] is False
    assert audit["completion_decision"]["p0_blocker_ids"] == ["openai_secret_reference"]
    assert audit["completion_decision"]["p1_decision_ids"] == []

    docs = {
        "README.md": (ROOT / "README.md").read_text(encoding="utf-8"),
        "PROJECT_FOUNDATION.md": (ROOT / "PROJECT_FOUNDATION.md").read_text(
            encoding="utf-8"
        ),
        "ROADMAP.md": (ROOT / "ROADMAP.md").read_text(encoding="utf-8"),
        "00_HOME/Now.md": (ROOT / "00_HOME" / "Now.md").read_text(
            encoding="utf-8"
        ),
    }

    required_snippets = {
        "README.md": [
            "Current MVP status (2026-05-15)",
            "latest MVP writeback evidence",
        ],
        "PROJECT_FOUNDATION.md": [
            "2026-05-15 MVP continuation status",
            "discover latest MVP writeback evidence",
        ],
        "ROADMAP.md": [
            "**Last updated:** 2026-05-15",
            "MVP consolidation latest-evidence addendum (2026-05-15)",
        ],
        "00_HOME/Now.md": [
            "updated: 2026-05-15",
            "Current MVP Snapshot - 2026-05-15",
            "2026-05-15 latest evidence sync",
            "completion_safety_contract",
            "checklist_coverage_is_not_completion=true",
        ],
    }

    for doc, snippets in required_snippets.items():
        for snippet in snippets:
            assert snippet in docs[doc], f"{doc} missing {snippet!r}"
        assert "safe_to_call_update_goal_complete=false" in docs[doc]
        assert "openai_secret_reference" in docs[doc]
        assert "SET_OPENAI_SECRET_REF" in docs[doc]
        assert re.search(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}", docs[doc]) is None


def test_mvp_current_state_current_repo_includes_latest_mvp_writeback_records(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    current_state = build_mvp_current_state(ROOT)
    audit = build_mvp_completion_audit(ROOT)
    repo_refs = current_state["pass_status_by_id"]["repo_truth_consolidation"][
        "evidence_refs"
    ]
    checklist_by_id = {
        item["id"]: item for item in audit["prompt_to_artifact_checklist"]
    }
    audit_refs = checklist_by_id["repo_truth_consolidation"]["evidence_refs"]
    evidence_surfaces = [current_state["source_docs"], repo_refs, audit_refs]
    latest_groups = [
        "07_LOGS/Build-Logs/2026-05-15-ChaseOS-mvp-",
        "99_ARCHIVE/Documentation-History/2026-05-15_mvp-",
        "07_LOGS/Daily/2026-05-15.md",
        "07_LOGS/Agent-Activity/2026-05-15-codex-mvp-",
    ]

    for refs in evidence_surfaces:
        for group in latest_groups:
            assert any(str(ref).startswith(group) for ref in refs), group


def test_mvp_operator_handoff_cards_surface_provider_blocker_aliases_without_secrets(
    monkeypatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    current_state = build_mvp_current_state(ROOT)

    assert current_state["operator_input_ids"] == ["openai_secret_reference"]
    assert current_state["safe_to_call_update_goal_complete"] is False

    docs = [
        ROOT / "07_LOGS" / "Operator-Briefs" / "2026-05-13-mvp-next-action-card.md",
        ROOT / "07_LOGS" / "Operator-Briefs" / "2026-05-13-mvp-openai-secret-reference-handoff-card.md",
    ]
    required_snippets = [
        "SET_OPENAI_SECRET_REF",
        "secret_reference_target_is_placeholder=true",
        "secret_reference_resolvable=false",
        "secret_reference_probe_error=reference_not_found",
        "python -m runtime.cli.main runtime provider live-smoke-readiness --json",
        "secret_value_read=false",
    ]

    for doc in docs:
        text = doc.read_text(encoding="utf-8")
        for snippet in required_snippets:
            assert snippet in text, f"{doc} missing {snippet}"
        assert "test-key-secret-that-must-not-leak" not in text


def test_mvp_operator_handoff_cards_include_local_env_helper_without_secret_literals() -> None:
    docs = [
        ROOT / "07_LOGS" / "Operator-Briefs" / "2026-05-13-mvp-next-action-card.md",
        ROOT / "07_LOGS" / "Operator-Briefs" / "2026-05-13-mvp-openai-secret-reference-handoff-card.md",
        ROOT / "07_LOGS" / "Operator-Briefs" / "2026-05-14-openai-api-key-later-guide.md",
    ]
    required_snippets = [
        'Read-Host "OpenAI API key" -AsSecureString',
        '[Environment]::SetEnvironmentVariable("OPENAI_API_KEY", $plain, "User")',
        '[bool][Environment]::GetEnvironmentVariable("OPENAI_API_KEY", "User")',
        '[bool][Environment]::GetEnvironmentVariable("OPENAI_API_KEY", "Process")',
        "do not print the key value",
    ]
    forbidden_snippets = ["OPENAI_API_KEY=", "api_key:", "api_key ="]

    for doc in docs:
        text = doc.read_text(encoding="utf-8")
        for snippet in required_snippets:
            assert snippet in text, f"{doc} missing {snippet}"
        assert text.index('[bool][Environment]::GetEnvironmentVariable("OPENAI_API_KEY", "User")') < text.index(
            "python -m runtime.cli.main setup set provider openai"
        )
        assert re.search(r"sk-[A-Za-z0-9_-]{8,}", text) is None
        for snippet in forbidden_snippets:
            assert snippet not in text, f"{doc} contains forbidden snippet {snippet}"


def test_mvp_readiness_gate_checks_env_reference_by_name_without_exposing_value(tmp_path: Path, monkeypatch) -> None:
    secret_value = "test-key-another-secret-value-that-must-not-appear"
    monkeypatch.setenv("OPENAI_API_KEY", secret_value)
    _seed_minimal_vault(tmp_path, secret_target="OPENAI_API_KEY")

    payload = build_mvp_readiness_gate(tmp_path)
    serialized = json.dumps(payload, sort_keys=True)

    assert payload["checks"]["provider_credentials"]["secret_reference_target"] == "OPENAI_API_KEY"
    assert payload["checks"]["provider_credentials"]["secret_reference_env_name_present"] is True
    assert payload["checks"]["provider_credentials"]["secret_reference_resolvable"] is True
    assert payload["checks"]["provider_credentials"]["secret_reference_probe_source"] == "env-var"
    assert payload["checks"]["provider_credentials"]["secret_reference_probe_error"] is None
    assert payload["checks"]["provider_credentials"]["blockers"] == []
    assert secret_value not in serialized


def test_mvp_readiness_gate_checks_local_reference_without_reading_secret_value(
    tmp_path: Path, monkeypatch
) -> None:
    secret_marker = "not-a-real-secret-marker-that-must-not-appear"
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    _seed_minimal_vault(tmp_path, secret_target="runtime/secrets/openai.ref")
    secret_ref = tmp_path / "runtime" / "secrets" / "openai.ref"
    secret_ref.parent.mkdir(parents=True, exist_ok=True)
    secret_ref.write_text(secret_marker, encoding="utf-8")

    payload = build_mvp_readiness_gate(tmp_path)
    serialized = json.dumps(payload, sort_keys=True)

    assert payload["checks"]["provider_credentials"]["secret_reference_target"] == "runtime/secrets/openai.ref"
    assert payload["checks"]["provider_credentials"]["secret_reference_env_name_present"] is False
    assert payload["checks"]["provider_credentials"]["secret_reference_resolvable"] is True
    assert payload["checks"]["provider_credentials"]["secret_reference_probe_source"] == "local-path"
    assert payload["checks"]["provider_credentials"]["secret_reference_probe_error"] is None
    assert payload["checks"]["provider_credentials"]["blockers"] == []
    assert secret_marker not in serialized


def test_mvp_readiness_gate_cli_uses_json_envelope(tmp_path: Path, capsys, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    _seed_minimal_vault(tmp_path)

    exit_code = cli.main(["mvp", "readiness-gate", "--vault-root", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "mvp.readiness-gate"
    assert payload["result"]["surface"] == "chaseos_mvp_readiness_gate"
    assert payload["result"]["readiness_status"] == "blocked_operator_input_required"
    assert payload["result"]["safe_to_call_update_goal_complete"] is False
    assert payload["result"]["operator_input_ids"] == [
        "openai_secret_reference",
        "ventureops_real_client_scope",
        "pending_chat_approval_decision",
    ]
    assert payload["result"]["completion_decision"]["operator_input_ids"] == payload["result"][
        "operator_input_ids"
    ]
    assert payload["result"]["no_safe_autonomous_completion_pass_available"] is True
    assert payload["result"]["update_goal_allowed"] is False
    assert payload["result"]["next_operator_action_id"] == "openai_secret_reference"
    assert payload["result"]["next_recommended_pass"] == "operator-provide-openai-secret-reference"
    assert payload["result"]["canonical_operator_handoff"]["path"] == (
        "07_LOGS/Operator-Briefs/2026-05-13-mvp-next-action-card.md"
    )
    assert payload["result"]["canonical_operator_handoff"]["execution_authority_granted"] is False
    assert payload["result"]["operator_input_template_artifact"]["path"] == (
        "07_LOGS/Operator-Briefs/2026-05-13-mvp-operator-input-template.json"
    )
    assert payload["result"]["operator_input_template_artifact"]["exists"] is False
    assert payload["result"]["operator_input_template_artifact"]["contains_secret_values"] is False


def test_mvp_readiness_gate_current_repo_cli_survives_ventureops_import_graph(
    capsys, monkeypatch
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    exit_code = cli.main(["mvp", "readiness-gate", "--vault-root", str(ROOT), "--json"])
    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "mvp.readiness-gate"
    assert result["surface"] == "chaseos_mvp_readiness_gate"
    assert result["readiness_status"] == "blocked_operator_input_required"
    assert result["safe_to_call_update_goal_complete"] is False
    assert result["completion_decision"]["operator_input_ids"] == result["operator_input_ids"]
    assert result["no_safe_autonomous_completion_pass_available"] is True
    assert result["update_goal_allowed"] is False
    assert result["next_operator_action_id"] == "openai_secret_reference"
    assert result["next_recommended_pass"] == "operator-provide-openai-secret-reference"
    assert result["canonical_operator_handoff"]["path"] == (
        "07_LOGS/Operator-Briefs/2026-05-13-mvp-next-action-card.md"
    )
    assert result["operator_input_template_artifact"]["path"] == (
        "07_LOGS/Operator-Briefs/2026-05-13-mvp-operator-input-template.json"
    )
    assert result["operator_input_template_artifact"]["exists"] is True
    assert result["operator_input_template_artifact"]["contains_secret_values"] is False
    assert result["setup_scope_boundary"]["status"] == (
        "setup_wide_validation_expected_to_fail_mvp_blocker_and_non_mvp_gaps"
    )
    assert result["setup_scope_boundary"]["setup_wide_invalid_provider_ids"] == [
        "claude",
        "openai",
        "local_oss",
        "n8n",
    ]
    assert result["setup_scope_boundary"]["setup_wide_invalid_integration_ids"] == [
        "telegram",
        "slack",
    ]
    assert result["setup_scope_boundary"]["non_mvp_setup_gap_ids"] == [
        "provider:claude",
        "provider:local_oss",
        "provider:n8n",
        "integration:telegram",
        "integration:slack",
    ]
    assert (
        result["setup_scope_boundary"]["non_mvp_setup_gaps_are_current_mvp_blockers"]
        is False
    )
    assert result["overall_goal_complete"] is False
    approvals = result["checks"]["studio_approvals"]
    assert approvals["tracked_chat_approval_is_current_mvp_decision"] is False
    assert approvals["untracked_pending_approvals_are_current_mvp_blockers"] is False
    assert approvals["untracked_pending_approval_count"] >= 0
    assert approvals["untracked_pending_approval_boundary"].startswith(
        "Visible in Studio approval queues"
    )
    assert result["p1_decision_ids"] == []
    assert result["authority"]["secret_values_read"] is False
    assert result["authority"]["provider_calls_performed"] is False


def test_mvp_primary_status_text_outputs_show_completion_barrier(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    _seed_minimal_vault(tmp_path)

    for command in (
        ["mvp", "readiness-gate", "--vault-root", str(tmp_path)],
        ["mvp", "completion-audit", "--vault-root", str(tmp_path)],
    ):
        exit_code = cli.main(command)
        output = capsys.readouterr().out
        assert exit_code == 0
        assert "objective_achieved: False" in output
        assert "safe_to_call_update_goal_complete: False" in output
        assert "autonomous_completion_barrier:" in output
        assert "completion_safety_contract:" in output
        assert "update_goal_allowed=False" in output
        if command[1] == "completion-audit":
            assert "completion_safety_contract:" in output
            assert "checklist_coverage_is_not_completion=" in output
        assert "setup_scope: status=setup_wide_validation_expected_to_fail_current_mvp_blocker" in output
        assert "non_mvp_are_mvp_blockers=False" in output


def test_mvp_completion_audit_builds_prompt_to_artifact_checklist_without_secrets(
    tmp_path: Path, monkeypatch
) -> None:
    secret_value = "FAKE_COMPLETION_AUDIT_SECRET_THAT_MUST_NOT_APPEAR"
    monkeypatch.setenv("OPENAI_API_KEY", secret_value)
    _seed_minimal_vault(tmp_path)
    brief = tmp_path / "06_AGENTS" / "ChaseOS-MVP-Current-Goal-and-Pass-Plan.md"
    brief.parent.mkdir(parents=True, exist_ok=True)
    brief.write_text("# ChaseOS MVP Current Goal and Pass Plan\n", encoding="utf-8")
    dashboard = tmp_path / "runtime" / "studio" / "dashboard.py"
    dashboard.parent.mkdir(parents=True, exist_ok=True)
    dashboard.write_text("# studio dashboard\n", encoding="utf-8")
    dashboard_app = tmp_path / "runtime" / "studio" / "dashboard_app.py"
    dashboard_app.write_text("# studio dashboard app\n", encoding="utf-8")
    runtime_startup = tmp_path / "runtime" / "studio" / "runtime_startup_controls.py"
    runtime_startup.write_text("# runtime startup controls\n", encoding="utf-8")
    readiness_gate = tmp_path / "runtime" / "mvp_readiness_gate.py"
    readiness_gate.write_text("# mvp readiness gate\n", encoding="utf-8")
    _seed_agent_bus_lifecycle_proof(tmp_path)

    payload = build_mvp_completion_audit(tmp_path)
    serialized = json.dumps(payload, sort_keys=True)

    assert payload["surface"] == "chaseos_mvp_completion_audit"
    assert payload["read_only"] is True
    assert payload["deliverable_count"] == 10
    assert payload["checklist_count"] == 10
    assert payload["covered_checklist_count"] <= payload["checklist_count"]
    assert payload["next_operator_action_id"] == payload["autonomous_completion_barrier"][
        "next_operator_action_id"
    ]
    assert payload["next_recommended_pass"] == payload["autonomous_completion_barrier"][
        "next_recommended_pass"
    ]
    assert payload["update_goal_allowed"] is False
    assert payload["no_safe_autonomous_completion_pass_available"] is True
    assert payload["completion_safety_contract"] == {
        "status": "blocked_do_not_call_update_goal_complete",
        "update_goal_allowed": False,
        "safe_to_call_update_goal_complete": False,
        "checklist_coverage_is_not_completion": False,
        "covered_checklist_count": payload["covered_checklist_count"],
        "checklist_count": payload["checklist_count"],
        "operator_input_ids": [
            "openai_secret_reference",
            "ventureops_real_client_scope",
            "pending_chat_approval_decision",
        ],
        "p0_blocker_ids": [
            "openai_secret_reference",
            "ventureops_real_client_scope",
        ],
        "p1_decision_ids": ["pending_chat_approval_decision"],
        "next_operator_action_id": payload["next_operator_action_id"],
        "next_recommended_pass": payload["next_recommended_pass"],
        "required_before_update_goal_complete": [
            "resolve_operator_inputs",
            "rerun_completion_audit",
            "require_safe_to_call_update_goal_complete_true",
        ],
        "reason": payload["completion_decision"]["reason"],
    }
    assert len(payload["prompt_to_artifact_checklist"]) == 10
    assert payload["canonical_operator_handoff"]["path"] == (
        "07_LOGS/Operator-Briefs/2026-05-13-mvp-next-action-card.md"
    )
    assert payload["canonical_operator_handoff"]["contains_secret_values"] is False
    assert payload["canonical_operator_handoff"]["execution_authority_granted"] is False
    assert payload["operator_input_template_artifact"] == {
        "path": "07_LOGS/Operator-Briefs/2026-05-13-mvp-operator-input-template.json",
        "exists": False,
        "contains_secret_values": False,
        "validation_command": "python -m runtime.cli.main mvp validate-operator-input --input 07_LOGS/Operator-Briefs/2026-05-13-mvp-operator-input-template.json --json",
        "write_command": "python -m runtime.cli.main mvp operator-input-template --write-template 07_LOGS/Operator-Briefs/2026-05-13-mvp-operator-input-template.json --json",
    }
    assert payload["setup_scope_boundary"]["mvp_current_setup_blocker_ids"] == [
        "openai_secret_reference"
    ]
    assert payload["setup_scope_boundary"]["non_mvp_setup_gap_ids"] == []
    assert (
        payload["setup_scope_boundary"]["non_mvp_setup_gaps_are_current_mvp_blockers"]
        is False
    )
    assert payload["completion_decision"]["objective_achieved"] is False
    assert payload["completion_decision"]["safe_to_call_update_goal_complete"] is False
    assert payload["objective_achieved"] == payload["completion_decision"]["objective_achieved"]
    assert payload["safe_to_call_update_goal_complete"] == payload["completion_decision"][
        "safe_to_call_update_goal_complete"
    ]
    assert payload["operator_input_ids"] == payload["completion_decision"]["operator_input_ids"]
    assert payload["p0_blocker_ids"] == payload["completion_decision"]["p0_blocker_ids"]
    assert payload["p1_decision_ids"] == payload["completion_decision"]["p1_decision_ids"]
    assert payload["blocked_requirement_ids"] == payload["completion_decision"][
        "blocked_requirement_ids"
    ]
    assert payload["incomplete_or_operator_blocked_requirements"] == payload[
        "completion_decision"
    ]["incomplete_or_operator_blocked_requirements"]
    assert payload["completion_decision"]["p0_blocker_ids"] == [
        "openai_secret_reference",
        "ventureops_real_client_scope",
    ]
    assert {
        "ventureops_real_use",
    } <= set(payload["completion_decision"]["incomplete_or_operator_blocked_requirements"])
    assert "credential_readiness" not in set(
        payload["completion_decision"]["incomplete_or_operator_blocked_requirements"]
    )
    checklist_by_id = {item["id"]: item for item in payload["prompt_to_artifact_checklist"]}
    assert "07_LOGS/Build-Logs/Build-Logs-Index.md" in checklist_by_id[
        "repo_truth_consolidation"
    ]["evidence_refs"]
    assert (
        "07_LOGS/Build-Logs/2026-05-14-ChaseOS-mvp-current-state-rollover-audit.md"
        in checklist_by_id["repo_truth_consolidation"]["evidence_refs"]
    )
    assert (
        "99_ARCHIVE/Documentation-History/2026-05-14_mvp-current-state-rollover-audit.md"
        in checklist_by_id["repo_truth_consolidation"]["evidence_refs"]
    )
    assert "07_LOGS/Daily/2026-05-14.md" in checklist_by_id[
        "repo_truth_consolidation"
    ]["evidence_refs"]
    assert (
        "07_LOGS/Agent-Activity/2026-05-14-codex-mvp-current-state-rollover-audit.md"
        in checklist_by_id["repo_truth_consolidation"]["evidence_refs"]
    )
    assert "06_AGENTS/ChaseOS-MVP-Current-Goal-and-Pass-Plan.md" in checklist_by_id[
        "repo_truth_consolidation"
    ]["evidence_refs"]
    assert "runtime/studio/dashboard.py" in checklist_by_id["repo_truth_consolidation"][
        "evidence_refs"
    ]
    assert "python -m runtime.cli.main mvp current-state --json" in checklist_by_id[
        "repo_truth_consolidation"
    ]["inspection_commands"]
    assert "roadmap and Now truth surfaces" in checklist_by_id["repo_truth_consolidation"][
        "required_artifacts_or_evidence"
    ]
    assert (
        "Agent Bus, Studio, Chat, VentureOps, and provider setup checks"
        in checklist_by_id["repo_truth_consolidation"]["required_artifacts_or_evidence"]
    )
    assert "writeback logs and latest build records" in checklist_by_id[
        "repo_truth_consolidation"
    ]["required_artifacts_or_evidence"]
    assert "06_AGENTS/ChaseOS-MVP-Current-Goal-and-Pass-Plan.md" in checklist_by_id[
        "mvp_scope_lock"
    ]["evidence_refs"]
    assert "P0 current blocker ids" in checklist_by_id["mvp_scope_lock"][
        "required_artifacts_or_evidence"
    ]
    assert "P1 pending decision ids" in checklist_by_id["mvp_scope_lock"][
        "required_artifacts_or_evidence"
    ]
    assert "P1 next-after-MVP lanes" in checklist_by_id["mvp_scope_lock"][
        "required_artifacts_or_evidence"
    ]
    assert "P2 parked/gated lanes" in checklist_by_id["mvp_scope_lock"][
        "required_artifacts_or_evidence"
    ]
    assert "runtime/studio/dashboard_app.py" in checklist_by_id["studio_cockpit"]["evidence_refs"]
    assert "runtime/studio/runtime_startup_controls.py" in checklist_by_id["studio_cockpit"][
        "evidence_refs"
    ]
    assert "python -m runtime.cli.main mvp current-state --json" in checklist_by_id[
        "studio_cockpit"
    ]["inspection_commands"]
    assert "status visibility" in checklist_by_id["studio_cockpit"][
        "required_artifacts_or_evidence"
    ]
    assert "approval visibility" in checklist_by_id["studio_cockpit"][
        "required_artifacts_or_evidence"
    ]
    assert "runtime health visibility" in checklist_by_id["studio_cockpit"][
        "required_artifacts_or_evidence"
    ]
    assert "blocker visibility" in checklist_by_id["studio_cockpit"][
        "required_artifacts_or_evidence"
    ]
    assert checklist_by_id["credential_readiness"]["covered_by_current_evidence"] is True
    assert "credential-only handoff" in checklist_by_id["credential_readiness"][
        "required_artifacts_or_evidence"
    ]
    assert "setup-wide validation" in checklist_by_id["credential_readiness"][
        "required_artifacts_or_evidence"
    ]
    assert "provider inventory" in checklist_by_id["credential_readiness"][
        "required_artifacts_or_evidence"
    ]
    assert "provider live-smoke readiness" in checklist_by_id["credential_readiness"][
        "required_artifacts_or_evidence"
    ]
    assert "python -m runtime.cli.main mvp credential-handoff --json" in checklist_by_id[
        "credential_readiness"
    ]["inspection_commands"]
    assert "python -m runtime.cli.main setup validate --json" in checklist_by_id[
        "credential_readiness"
    ]["inspection_commands"]
    assert "python -m runtime.cli.main setup provider validate openai --json" in checklist_by_id[
        "credential_readiness"
    ]["inspection_commands"]
    assert "python -m runtime.cli.main runtime providers --json" in checklist_by_id[
        "credential_readiness"
    ]["inspection_commands"]
    assert (
        "python -m runtime.cli.main runtime provider live-smoke-readiness --json"
        in checklist_by_id["credential_readiness"]["inspection_commands"]
    )
    assert (
        "06_AGENTS/ChaseOS-MVP-Credential-Readiness-Checklist.md"
        in checklist_by_id["credential_readiness"]["evidence_refs"]
    )
    assert (
        "07_LOGS/Operator-Briefs/2026-05-13-mvp-openai-secret-reference-handoff-card.md"
        in checklist_by_id["credential_readiness"]["evidence_refs"]
    )
    assert (
        "07_LOGS/Operator-Briefs/2026-05-14-openai-api-key-later-guide.md"
        in checklist_by_id["credential_readiness"]["evidence_refs"]
    )
    assert (
        "07_LOGS/Operator-Briefs/2026-05-13-mvp-operator-input-template.json"
        in checklist_by_id["credential_readiness"]["evidence_refs"]
    )
    assert checklist_by_id["credential_readiness"]["missing_incomplete_or_unverified"] == []
    assert any(
        "operator supplies resolvable local OpenAI" in item
        for item in checklist_by_id["credential_readiness"]["operator_followups"]
    )
    assert checklist_by_id["chat_to_approval"]["covered_by_current_evidence"] is True
    assert "tracked Chat approval artifact" in checklist_by_id["chat_to_approval"][
        "required_artifacts_or_evidence"
    ]
    assert "approval id and lifecycle status" in checklist_by_id["chat_to_approval"][
        "required_artifacts_or_evidence"
    ]
    assert "action type and target preview" in checklist_by_id["chat_to_approval"][
        "required_artifacts_or_evidence"
    ]
    assert "Studio/Chat submitted-by metadata" in checklist_by_id["chat_to_approval"][
        "required_artifacts_or_evidence"
    ]
    assert "Approval Center visibility" in checklist_by_id["chat_to_approval"][
        "required_artifacts_or_evidence"
    ]
    assert "governed approval lifecycle state" in checklist_by_id["chat_to_approval"][
        "required_artifacts_or_evidence"
    ]
    assert (
        f"runtime/studio/approvals/{PENDING_CHAT_APPROVAL_ID}.json"
        in checklist_by_id["chat_to_approval"]["evidence_refs"]
    )
    assert checklist_by_id["approval_to_action"]["covered_by_current_evidence"] is True
    assert "executed approval artifact" in checklist_by_id["approval_to_action"][
        "required_artifacts_or_evidence"
    ]
    assert "exact-once marker" in checklist_by_id["approval_to_action"][
        "required_artifacts_or_evidence"
    ]
    assert "approved target action id" in checklist_by_id["approval_to_action"][
        "required_artifacts_or_evidence"
    ]
    assert "approved target action performed" in checklist_by_id["approval_to_action"][
        "required_artifacts_or_evidence"
    ]
    assert (
        "provider/browser/workflow/canonical side effects false"
        in checklist_by_id["approval_to_action"]["required_artifacts_or_evidence"]
    )
    assert (
        "operator follow-up separated when a Chat approval remains pending"
        in checklist_by_id["approval_to_action"]["required_artifacts_or_evidence"]
    )
    assert "runtime/studio/approvals/executed-example.json" in checklist_by_id[
        "approval_to_action"
    ]["evidence_refs"]
    assert (
        "runtime/studio/approvals/_runtime_dispatch_markers/executed-example.json"
        in checklist_by_id["approval_to_action"]["evidence_refs"]
    )
    assert checklist_by_id["approval_to_action"]["missing_incomplete_or_unverified"] == []
    assert checklist_by_id["approval_to_action"]["operator_followups"] == [
        f"operator decision on pending Chat approval {PENDING_CHAT_APPROVAL_ID}"
    ]
    assert "task created event" in checklist_by_id["agent_bus_lifecycle"][
        "required_artifacts_or_evidence"
    ]
    assert "task claimed by Codex" in checklist_by_id["agent_bus_lifecycle"][
        "required_artifacts_or_evidence"
    ]
    assert "task started" in checklist_by_id["agent_bus_lifecycle"][
        "required_artifacts_or_evidence"
    ]
    assert "task completed or safely blocked" in checklist_by_id["agent_bus_lifecycle"][
        "required_artifacts_or_evidence"
    ]
    assert "result artifact written" in checklist_by_id["agent_bus_lifecycle"][
        "required_artifacts_or_evidence"
    ]
    assert "result logged" in checklist_by_id["agent_bus_lifecycle"][
        "required_artifacts_or_evidence"
    ]
    assert (
        "runtime/adapters/codex/runs/20260513T104717Z-task-e417a38df4d0/codex-adapter-result.json"
        in checklist_by_id["agent_bus_lifecycle"]["evidence_refs"]
    )
    assert (
        "runtime/adapters/codex/runs/20260513T104717Z-task-e417a38df4d0/codex-stdout.md"
        in checklist_by_id["agent_bus_lifecycle"]["evidence_refs"]
    )
    assert (
        "runtime/adapters/codex/runs/20260513T104717Z-task-e417a38df4d0/codex-stderr.log"
        in checklist_by_id["agent_bus_lifecycle"]["evidence_refs"]
    )
    assert "not synthetic/demo evidence" in checklist_by_id["ventureops_real_use"][
        "required_artifacts_or_evidence"
    ]
    assert "external/provider/browser/revenue side effects false" in checklist_by_id[
        "ventureops_real_use"
    ]["required_artifacts_or_evidence"]
    assert "source package refs" in checklist_by_id["graph_source_intelligence"][
        "required_artifacts_or_evidence"
    ]
    assert "graph context refs" in checklist_by_id["graph_source_intelligence"][
        "required_artifacts_or_evidence"
    ]
    assert "workflow context reference" in checklist_by_id["graph_source_intelligence"][
        "required_artifacts_or_evidence"
    ]
    assert "context/navigation only" in checklist_by_id["graph_source_intelligence"][
        "required_artifacts_or_evidence"
    ]
    assert "mutation authority false" in checklist_by_id["graph_source_intelligence"][
        "required_artifacts_or_evidence"
    ]
    assert "browser/system automation gated" in checklist_by_id["full_system_control_boundary"][
        "required_artifacts_or_evidence"
    ]
    assert "host mutation false" in checklist_by_id["full_system_control_boundary"][
        "required_artifacts_or_evidence"
    ]
    assert "workflow replay gated" in checklist_by_id["full_system_control_boundary"][
        "required_artifacts_or_evidence"
    ]
    assert (
        "approval/provider/Agent Bus execution blocked"
        in checklist_by_id["full_system_control_boundary"]["required_artifacts_or_evidence"]
    )
    assert (
        "credential/session/profile access blocked"
        in checklist_by_id["full_system_control_boundary"]["required_artifacts_or_evidence"]
    )
    assert "CDP no-execution proof" in checklist_by_id["full_system_control_boundary"][
        "required_artifacts_or_evidence"
    ]
    assert (
        "future local proof requires separate approval"
        in checklist_by_id["full_system_control_boundary"]["required_artifacts_or_evidence"]
    )
    assert checklist_by_id["full_system_control_boundary"]["covered_by_current_evidence"] is True
    assert payload["provider_secret_reference_state"]["secret_reference_resolvable"] is False
    assert payload["authority"]["secret_values_read"] is False
    assert payload["authority"]["provider_calls_performed"] is False
    assert secret_value not in serialized


def test_mvp_completion_audit_cli_uses_json_envelope(tmp_path: Path, capsys, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    _seed_minimal_vault(tmp_path)

    exit_code = cli.main(["mvp", "completion-audit", "--vault-root", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "mvp.completion-audit"
    assert payload["result"]["surface"] == "chaseos_mvp_completion_audit"
    assert payload["result"]["canonical_operator_handoff"]["path"] == (
        "07_LOGS/Operator-Briefs/2026-05-13-mvp-next-action-card.md"
    )
    assert payload["result"]["canonical_operator_handoff"]["execution_authority_granted"] is False
    assert payload["result"]["operator_input_template_artifact"]["path"] == (
        "07_LOGS/Operator-Briefs/2026-05-13-mvp-operator-input-template.json"
    )
    assert payload["result"]["operator_input_template_artifact"]["exists"] is False
    assert payload["result"]["operator_input_template_artifact"]["contains_secret_values"] is False
    assert payload["result"]["setup_scope_boundary"]["mvp_current_setup_blocker_ids"] == [
        "openai_secret_reference"
    ]
    assert (
        payload["result"]["setup_scope_boundary"][
            "non_mvp_setup_gaps_are_current_mvp_blockers"
        ]
        is False
    )
    assert payload["result"]["safe_to_call_update_goal_complete"] is False
    assert payload["result"]["operator_input_ids"] == payload["result"]["completion_decision"][
        "operator_input_ids"
    ]
    assert payload["result"]["completion_decision"]["safe_to_call_update_goal_complete"] is False
    assert payload["result"]["autonomous_completion_barrier"]["active"] is True
    assert payload["result"]["autonomous_completion_barrier"]["update_goal_allowed"] is False
    assert payload["result"]["completion_safety_contract"]["status"] == (
        "blocked_do_not_call_update_goal_complete"
    )
    assert payload["result"]["completion_safety_contract"]["update_goal_allowed"] is False


def test_mvp_completion_audit_current_repo_cli_survives_ventureops_import_graph(
    capsys, monkeypatch
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    exit_code = cli.main(["mvp", "completion-audit", "--vault-root", str(ROOT), "--json"])
    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "mvp.completion-audit"
    assert result["surface"] == "chaseos_mvp_completion_audit"
    assert result["deliverable_count"] == 10
    assert result["checklist_count"] == 10
    assert result["covered_checklist_count"] == 10
    assert len(result["prompt_to_artifact_checklist"]) == 10
    assert result["operator_input_template_artifact"]["path"] == (
        "07_LOGS/Operator-Briefs/2026-05-13-mvp-operator-input-template.json"
    )
    assert result["operator_input_template_artifact"]["exists"] is True
    assert result["setup_scope_boundary"]["status"] == (
        "setup_wide_validation_expected_to_fail_mvp_blocker_and_non_mvp_gaps"
    )
    assert result["setup_scope_boundary"]["non_mvp_setup_gap_ids"] == [
        "provider:claude",
        "provider:local_oss",
        "provider:n8n",
        "integration:telegram",
        "integration:slack",
    ]
    assert (
        result["setup_scope_boundary"]["non_mvp_setup_gaps_are_current_mvp_blockers"]
        is False
    )
    assert result["safe_to_call_update_goal_complete"] is False
    assert result["operator_input_ids"] == result["completion_decision"]["operator_input_ids"]
    assert result["p0_blocker_ids"] == result["completion_decision"]["p0_blocker_ids"]
    assert result["p1_decision_ids"] == result["completion_decision"]["p1_decision_ids"]
    assert result["autonomous_completion_barrier"] == {
        "active": True,
        "all_numbered_mvp_rows_covered": True,
        "covered_numbered_mvp_row_count": 10,
        "numbered_mvp_row_count": 10,
        "no_safe_autonomous_completion_pass_available": True,
        "blocked_by_operator_input": True,
        "update_goal_allowed": False,
        "operator_input_ids": result["operator_input_ids"],
        "p0_blocker_ids": result["p0_blocker_ids"],
        "p1_decision_ids": result["p1_decision_ids"],
        "next_operator_action_id": "openai_secret_reference",
        "next_recommended_pass": "operator-provide-openai-secret-reference",
        "reason": "All numbered MVP rows are covered, but operator-owned input still blocks safe goal completion.",
    }
    assert result["next_operator_action_id"] == "openai_secret_reference"
    assert result["next_recommended_pass"] == "operator-provide-openai-secret-reference"
    assert result["next_operator_action_id"] == result["autonomous_completion_barrier"][
        "next_operator_action_id"
    ]
    assert result["next_recommended_pass"] == result["autonomous_completion_barrier"][
        "next_recommended_pass"
    ]
    assert result["update_goal_allowed"] is False
    assert result["no_safe_autonomous_completion_pass_available"] is True
    assert result["completion_safety_contract"] == {
        "status": "blocked_do_not_call_update_goal_complete",
        "update_goal_allowed": False,
        "safe_to_call_update_goal_complete": False,
        "checklist_coverage_is_not_completion": True,
        "covered_checklist_count": 10,
        "checklist_count": 10,
        "operator_input_ids": ["openai_secret_reference"],
        "p0_blocker_ids": ["openai_secret_reference"],
        "p1_decision_ids": [],
        "next_operator_action_id": "openai_secret_reference",
        "next_recommended_pass": "operator-provide-openai-secret-reference",
        "required_before_update_goal_complete": [
            "resolve_operator_inputs",
            "rerun_completion_audit",
            "require_safe_to_call_update_goal_complete_true",
        ],
        "reason": result["completion_decision"]["reason"],
    }
    checklist_by_id = {item["id"]: item for item in result["prompt_to_artifact_checklist"]}
    assert "07_LOGS/Operator-Briefs/2026-05-13-mvp-operator-input-template.json" in checklist_by_id[
        "credential_readiness"
    ]["evidence_refs"]
    assert "07_LOGS/Operator-Briefs/2026-05-14-openai-api-key-later-guide.md" in checklist_by_id[
        "credential_readiness"
    ]["evidence_refs"]
    assert result["completion_decision"]["safe_to_call_update_goal_complete"] is False
    assert result["authority"]["secret_values_read"] is False
    assert result["authority"]["provider_calls_performed"] is False


def test_mvp_completion_audit_current_proof_state_links_canonical_handoff(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    _seed_minimal_vault(tmp_path)
    _seed_ventureops_live_client_workflow_proof(tmp_path)
    _seed_source_context_fixture(tmp_path)
    _seed_current_mvp_truth_surfaces(tmp_path)
    _seed_agent_bus_lifecycle_proof(tmp_path)

    payload = build_mvp_completion_audit(tmp_path)

    assert payload["canonical_operator_handoff"] == {
        "id": "mvp_next_action_card",
        "label": "MVP Next Action Card",
        "path": "07_LOGS/Operator-Briefs/2026-05-13-mvp-next-action-card.md",
        "exists": True,
        "purpose": "Canonical current MVP handoff for goal, sector, 10-pass scope, P0 OpenAI reference, and tracked Chat approval state.",
        "contains_secret_values": False,
        "execution_authority_granted": False,
        "covers": [
            "current_goal",
            "current_sector",
            "ten_pass_scope",
            "openai_secret_reference",
            "pending_chat_approval_decision",
        ],
    }
    assert payload["completion_decision"]["operator_input_ids"] == [
        "openai_secret_reference",
        "pending_chat_approval_decision",
    ]
    assert payload["completion_decision"]["blocked_requirement_ids"] == []
    assert payload["completion_decision"]["incomplete_or_operator_blocked_requirements"] == []
    checklist_by_id = {item["id"]: item for item in payload["prompt_to_artifact_checklist"]}
    assert (
        "runtime/source_intelligence/workspaces/phase7-test/sources/demo.json"
        in checklist_by_id["graph_source_intelligence"]["evidence_refs"]
    )
    assert "06_AGENTS/Agent-Control-Plane.md" in checklist_by_id[
        "graph_source_intelligence"
    ]["evidence_refs"]


def test_mvp_operator_action_required_reports_operator_owned_blockers_without_secrets(
    tmp_path: Path, monkeypatch
) -> None:
    secret_value = "test-key-operator-action-secret-that-must-not-appear"
    monkeypatch.setenv("OPENAI_API_KEY", secret_value)
    _seed_minimal_vault(tmp_path)
    _seed_operator_input_template(tmp_path)

    payload = build_mvp_operator_action_required(tmp_path)
    serialized = json.dumps(payload, sort_keys=True)

    assert payload["surface"] == "chaseos_mvp_operator_action_required"
    assert payload["objective_achieved"] is False
    assert payload["safe_to_call_update_goal_complete"] is False
    assert payload["operator_input_ids"] == payload["completion_decision"]["operator_input_ids"]
    assert payload["p0_blocker_ids"] == payload["completion_decision"]["p0_blocker_ids"]
    assert payload["p1_decision_ids"] == payload["completion_decision"]["p1_decision_ids"]
    assert payload["operator_action_required"] is True
    assert payload["required"] is True
    assert payload["no_safe_autonomous_completion_pass_available"] is True
    assert payload["next_operator_action_id"] == payload["autonomous_completion_barrier"][
        "next_operator_action_id"
    ]
    assert payload["next_recommended_pass"] == payload["autonomous_completion_barrier"][
        "next_recommended_pass"
    ]
    assert payload["update_goal_allowed"] is False
    assert payload["autonomous_completion_barrier"]["active"] is True
    assert payload["autonomous_completion_barrier"]["update_goal_allowed"] is False
    assert payload["autonomous_completion_barrier"]["operator_input_ids"] == payload[
        "operator_input_ids"
    ]
    assert payload["setup_scope_boundary"]["status"] == (
        "setup_wide_validation_expected_to_fail_current_mvp_blocker"
    )
    assert payload["setup_scope_boundary"]["mvp_current_setup_blocker_ids"] == [
        "openai_secret_reference"
    ]
    assert payload["setup_scope_boundary"]["setup_wide_invalid_provider_ids"] == [
        "openai"
    ]
    assert payload["setup_scope_boundary"]["non_mvp_setup_gap_ids"] == []
    assert (
        payload["setup_scope_boundary"]["non_mvp_setup_gaps_are_current_mvp_blockers"]
        is False
    )
    assert payload["required_actions"] == payload["required_operator_actions"]
    assert payload["canonical_operator_handoff"]["path"] == (
        "07_LOGS/Operator-Briefs/2026-05-13-mvp-next-action-card.md"
    )
    assert payload["canonical_operator_handoff"]["contains_secret_values"] is False
    assert payload["canonical_operator_handoff"]["execution_authority_granted"] is False
    assert payload["operator_input_template_artifact"]["exists"] is True
    assert {
        "openai_secret_reference",
        "ventureops_real_client_scope",
        "pending_chat_approval_decision",
    } >= {item["id"] for item in payload["required_operator_actions"]}
    openai_action = next(
        item for item in payload["required_operator_actions"] if item["id"] == "openai_secret_reference"
    )
    assert openai_action["owner"] == "operator"
    assert openai_action["handoff_guide_path"] == (
        "07_LOGS/Operator-Briefs/2026-05-14-openai-api-key-later-guide.md"
    )
    assert openai_action["current_secret_reference_target"] == "SET_OPENAI_SECRET_REF"
    assert openai_action["current_secret_reference_target_is_placeholder"] is True
    assert openai_action["current_secret_reference_resolvable"] is False
    assert openai_action["secret_reference_probe_source"] == "env-var-or-local-secret-ref"
    assert openai_action["secret_reference_probe_error"] == "reference_not_found"
    assert openai_action["setup_provider_validation_command"] == (
        "python -m runtime.cli.main setup provider validate openai --json"
    )
    assert openai_action["setup_wide_validation_command"] == (
        "python -m runtime.cli.main setup validate --json"
    )
    assert openai_action["provider_live_smoke_readiness_command"] == (
        "python -m runtime.cli.main runtime provider live-smoke-readiness --json"
    )
    assert openai_action["reference_presence_check_commands"] == [
        '[bool][Environment]::GetEnvironmentVariable("OPENAI_API_KEY", "User")',
        '[bool][Environment]::GetEnvironmentVariable("OPENAI_API_KEY", "Process")',
    ]
    assert openai_action["reference_presence_check_outputs_secret_value"] is False
    assert openai_action["secret_value_read"] is False
    assert openai_action["live_network_call_attempted"] is False
    assert openai_action["files_modified"] is False
    assert openai_action["codex_can_perform_now"] is False
    assert openai_action["secret_value_allowed_in_repo_or_chat"] is False
    pending_action = next(
        item
        for item in payload["required_operator_actions"]
        if item["id"] == "pending_chat_approval_decision"
    )
    assert pending_action["approval_id"] == PENDING_CHAT_APPROVAL_ID
    assert pending_action["approval_consumption_readiness_command"] == (
        "python -m runtime.cli.main studio phase11-chat-approval-consumption-readiness-contract "
        f"--approval-id {PENDING_CHAT_APPROVAL_ID} --json"
    )
    assert pending_action["approval_consumption_executor_command_template"] == (
        "python -m runtime.cli.main studio phase11-chat-approval-consumption-executor "
        f"--approval-id {PENDING_CHAT_APPROVAL_ID} "
        "--expected-consumption-digest <digest_from_readiness> --json"
    )
    assert pending_action["approval_consumption_allowed_now"] is False
    assert payload["authority"]["secret_values_read"] is False
    assert payload["authority"]["provider_calls_performed"] is False
    assert payload["authority"]["setup_metadata_write_performed"] is False
    assert secret_value not in serialized


def test_mvp_operator_action_required_current_proof_state_lists_only_openai_and_pending_approval(
    tmp_path: Path, monkeypatch
) -> None:
    secret_value = "test-key-current-proof-state-secret-that-must-not-appear"
    monkeypatch.setenv("OPENAI_API_KEY", secret_value)
    _seed_minimal_vault(tmp_path)
    _seed_ventureops_live_client_workflow_proof(tmp_path)
    _seed_source_context_fixture(tmp_path)
    _seed_current_mvp_truth_surfaces(tmp_path)
    _seed_agent_bus_lifecycle_proof(tmp_path)
    _seed_operator_input_template(tmp_path)

    payload = build_mvp_operator_action_required(tmp_path)
    serialized = json.dumps(payload, sort_keys=True)

    assert payload["surface"] == "chaseos_mvp_operator_action_required"
    assert payload["operator_action_required"] is True
    assert payload["required"] is True
    assert payload["safe_to_call_update_goal_complete"] is False
    assert payload["operator_input_ids"] == payload["completion_decision"]["operator_input_ids"]
    assert payload["p0_blocker_ids"] == payload["completion_decision"]["p0_blocker_ids"]
    assert payload["p1_decision_ids"] == payload["completion_decision"]["p1_decision_ids"]
    assert payload["autonomous_completion_barrier"] == {
        "active": True,
        "all_numbered_mvp_rows_covered": True,
        "covered_numbered_mvp_row_count": 10,
        "numbered_mvp_row_count": 10,
        "no_safe_autonomous_completion_pass_available": True,
        "blocked_by_operator_input": True,
        "update_goal_allowed": False,
        "operator_input_ids": payload["operator_input_ids"],
        "p0_blocker_ids": payload["p0_blocker_ids"],
        "p1_decision_ids": payload["p1_decision_ids"],
        "next_operator_action_id": "openai_secret_reference",
        "next_recommended_pass": "operator-provide-openai-secret-reference",
        "reason": "All numbered MVP rows are covered, but operator-owned input still blocks safe goal completion.",
    }
    assert payload["next_operator_action_id"] == "openai_secret_reference"
    assert payload["next_recommended_pass"] == "operator-provide-openai-secret-reference"
    assert payload["setup_scope_boundary"]["mvp_current_setup_blocker_ids"] == [
        "openai_secret_reference"
    ]
    assert (
        payload["setup_scope_boundary"]["non_mvp_setup_gaps_are_current_mvp_blockers"]
        is False
    )
    assert payload["canonical_operator_handoff"] == {
        "id": "mvp_next_action_card",
        "label": "MVP Next Action Card",
        "path": "07_LOGS/Operator-Briefs/2026-05-13-mvp-next-action-card.md",
        "exists": True,
        "purpose": "Canonical current MVP handoff for goal, sector, 10-pass scope, P0 OpenAI reference, and tracked Chat approval state.",
        "contains_secret_values": False,
        "execution_authority_granted": False,
        "covers": [
            "current_goal",
            "current_sector",
            "ten_pass_scope",
            "openai_secret_reference",
            "pending_chat_approval_decision",
        ],
    }
    assert payload["operator_input_template_artifact"]["exists"] is True
    assert [item["id"] for item in payload["required_operator_actions"]] == [
        "openai_secret_reference",
        "pending_chat_approval_decision",
    ]
    assert payload["required_operator_actions"][0]["handoff_guide_path"] == (
        "07_LOGS/Operator-Briefs/2026-05-14-openai-api-key-later-guide.md"
    )
    assert payload["required_operator_actions"][0]["current_secret_reference_target"] == (
        "SET_OPENAI_SECRET_REF"
    )
    assert (
        payload["required_operator_actions"][0][
            "current_secret_reference_target_is_placeholder"
        ]
        is True
    )
    assert payload["required_operator_actions"][0][
        "provider_live_smoke_readiness_command"
    ] == "python -m runtime.cli.main runtime provider live-smoke-readiness --json"
    assert payload["required_operator_actions"][1]["approval_id"] == PENDING_CHAT_APPROVAL_ID
    assert payload["required_operator_actions"][1][
        "approval_consumption_readiness_command"
    ] == (
        "python -m runtime.cli.main studio phase11-chat-approval-consumption-readiness-contract "
        f"--approval-id {PENDING_CHAT_APPROVAL_ID} --json"
    )
    assert payload["required_operator_actions"][1][
        "approval_consumption_executor_command_template"
    ] == (
        "python -m runtime.cli.main studio phase11-chat-approval-consumption-executor "
        f"--approval-id {PENDING_CHAT_APPROVAL_ID} "
        "--expected-consumption-digest <digest_from_readiness> --json"
    )
    assert payload["completion_decision"]["operator_input_ids"] == [
        "openai_secret_reference",
        "pending_chat_approval_decision",
    ]
    assert payload["completion_decision"]["incomplete_or_operator_blocked_requirements"] == []
    assert payload["completion_decision"]["blocked_requirement_ids"] == []
    assert "ventureops_real_client_scope" not in {
        item["id"] for item in payload["required_operator_actions"]
    }
    assert payload["authority"]["secret_values_read"] is False
    assert payload["authority"]["provider_calls_performed"] is False
    assert payload["authority"]["approval_consumption_performed"] is False
    assert secret_value not in serialized


def test_mvp_operator_action_required_cli_current_proof_state_lists_only_openai_and_pending_approval(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    secret_value = "test-key-current-proof-cli-secret-that-must-not-appear"
    monkeypatch.setenv("OPENAI_API_KEY", secret_value)
    _seed_minimal_vault(tmp_path)
    _seed_ventureops_live_client_workflow_proof(tmp_path)
    _seed_source_context_fixture(tmp_path)
    _seed_current_mvp_truth_surfaces(tmp_path)
    _seed_agent_bus_lifecycle_proof(tmp_path)
    _seed_operator_input_template(tmp_path)

    exit_code = cli.main(["mvp", "operator-action-required", "--vault-root", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]
    serialized = json.dumps(payload, sort_keys=True)

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "mvp.operator-action-required"
    assert result["surface"] == "chaseos_mvp_operator_action_required"
    assert result["operator_action_required"] is True
    assert result["required"] is True
    assert result["safe_to_call_update_goal_complete"] is False
    assert result["next_operator_action_id"] == "openai_secret_reference"
    assert result["next_recommended_pass"] == "operator-provide-openai-secret-reference"
    assert result["canonical_operator_handoff"]["path"] == (
        "07_LOGS/Operator-Briefs/2026-05-13-mvp-next-action-card.md"
    )
    assert result["canonical_operator_handoff"]["exists"] is True
    assert result["canonical_operator_handoff"]["execution_authority_granted"] is False
    assert [item["id"] for item in result["required_operator_actions"]] == [
        "openai_secret_reference",
        "pending_chat_approval_decision",
    ]
    assert result["required_operator_actions"][0]["current_secret_reference_target"] == (
        "SET_OPENAI_SECRET_REF"
    )
    assert (
        result["required_operator_actions"][0][
            "current_secret_reference_target_is_placeholder"
        ]
        is True
    )
    assert result["required_operator_actions"][0][
        "current_secret_reference_resolvable"
    ] is False
    assert result["required_operator_actions"][0]["secret_reference_probe_error"] == (
        "reference_not_found"
    )
    assert result["required_operator_actions"][0][
        "provider_live_smoke_readiness_command"
    ] == "python -m runtime.cli.main runtime provider live-smoke-readiness --json"
    assert result["required_operator_actions"][0]["secret_value_read"] is False
    assert result["required_operator_actions"][1]["approval_id"] == PENDING_CHAT_APPROVAL_ID
    assert result["required_operator_actions"][1][
        "approval_consumption_readiness_command"
    ] == (
        "python -m runtime.cli.main studio phase11-chat-approval-consumption-readiness-contract "
        f"--approval-id {PENDING_CHAT_APPROVAL_ID} --json"
    )
    assert result["required_operator_actions"][1][
        "approval_consumption_executor_command_template"
    ] == (
        "python -m runtime.cli.main studio phase11-chat-approval-consumption-executor "
        f"--approval-id {PENDING_CHAT_APPROVAL_ID} "
        "--expected-consumption-digest <digest_from_readiness> --json"
    )
    assert result["completion_decision"]["operator_input_ids"] == [
        "openai_secret_reference",
        "pending_chat_approval_decision",
    ]
    assert result["completion_decision"]["blocked_requirement_ids"] == []
    assert result["completion_decision"]["incomplete_or_operator_blocked_requirements"] == []
    assert result["autonomous_completion_barrier"]["active"] is True
    assert result["autonomous_completion_barrier"]["update_goal_allowed"] is False
    assert result["autonomous_completion_barrier"]["operator_input_ids"] == result[
        "operator_input_ids"
    ]
    assert result["completion_safety_contract"]["status"] == (
        "blocked_do_not_call_update_goal_complete"
    )
    assert result["completion_safety_contract"]["update_goal_allowed"] is False
    assert result["completion_safety_contract"]["operator_input_ids"] == result[
        "operator_input_ids"
    ]
    assert result["setup_scope_boundary"]["mvp_current_setup_blocker_ids"] == [
        "openai_secret_reference"
    ]
    assert (
        result["setup_scope_boundary"]["non_mvp_setup_gaps_are_current_mvp_blockers"]
        is False
    )
    assert "ventureops_real_client_scope" not in {
        item["id"] for item in result["required_operator_actions"]
    }
    assert result["operator_input_template_artifact"]["exists"] is True
    assert result["authority"]["secret_values_read"] is False
    assert result["authority"]["provider_calls_performed"] is False
    assert result["authority"]["approval_consumption_performed"] is False
    assert secret_value not in serialized


def test_mvp_operator_action_required_cli_uses_json_envelope(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    _seed_minimal_vault(tmp_path)

    exit_code = cli.main(["mvp", "operator-action-required", "--vault-root", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "mvp.operator-action-required"
    assert payload["result"]["surface"] == "chaseos_mvp_operator_action_required"
    assert payload["result"]["operator_action_required"] is True
    assert payload["result"]["required"] is True
    assert payload["result"]["safe_to_call_update_goal_complete"] is False
    assert payload["result"]["next_operator_action_id"] == payload["result"][
        "autonomous_completion_barrier"
    ]["next_operator_action_id"]
    assert payload["result"]["next_recommended_pass"] == payload["result"][
        "autonomous_completion_barrier"
    ]["next_recommended_pass"]
    assert payload["result"]["update_goal_allowed"] is False
    assert payload["result"]["operator_input_ids"] == payload["result"]["completion_decision"][
        "operator_input_ids"
    ]
    assert payload["result"]["autonomous_completion_barrier"]["active"] is True
    assert payload["result"]["autonomous_completion_barrier"]["update_goal_allowed"] is False
    assert payload["result"]["completion_safety_contract"]["status"] == (
        "blocked_do_not_call_update_goal_complete"
    )
    assert payload["result"]["completion_safety_contract"]["update_goal_allowed"] is False
    assert payload["result"]["setup_scope_boundary"]["mvp_current_setup_blocker_ids"] == [
        "openai_secret_reference"
    ]
    assert (
        payload["result"]["setup_scope_boundary"][
            "non_mvp_setup_gaps_are_current_mvp_blockers"
        ]
        is False
    )
    assert payload["result"]["required_actions"] == payload["result"][
        "required_operator_actions"
    ]


def test_mvp_operator_action_required_current_repo_cli_survives_ventureops_import_graph(
    capsys, monkeypatch
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    exit_code = cli.main(["mvp", "operator-action-required", "--vault-root", str(ROOT), "--json"])
    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "mvp.operator-action-required"
    assert result["surface"] == "chaseos_mvp_operator_action_required"
    assert result["operator_action_required"] is True
    assert result["required"] is True
    assert result["no_safe_autonomous_completion_pass_available"] is True
    assert result["safe_to_call_update_goal_complete"] is False
    assert result["next_operator_action_id"] == "openai_secret_reference"
    assert result["next_recommended_pass"] == "operator-provide-openai-secret-reference"
    assert result["update_goal_allowed"] is False
    assert result["operator_input_ids"] == result["completion_decision"]["operator_input_ids"]
    assert result["required_operator_actions"][0]["handoff_guide_path"] == (
        "07_LOGS/Operator-Briefs/2026-05-14-openai-api-key-later-guide.md"
    )
    assert result["required_operator_actions"][0]["reference_presence_check_commands"] == [
        '[bool][Environment]::GetEnvironmentVariable("OPENAI_API_KEY", "User")',
        '[bool][Environment]::GetEnvironmentVariable("OPENAI_API_KEY", "Process")',
    ]
    assert (
        result["required_operator_actions"][0][
            "reference_presence_check_outputs_secret_value"
        ]
        is False
    )
    assert result["p0_blocker_ids"] == result["completion_decision"]["p0_blocker_ids"]
    assert result["p1_decision_ids"] == result["completion_decision"]["p1_decision_ids"]
    assert result["autonomous_completion_barrier"]["update_goal_allowed"] is False
    assert result["autonomous_completion_barrier"]["next_operator_action_id"] == (
        "openai_secret_reference"
    )
    assert result["completion_safety_contract"] == {
        "status": "blocked_do_not_call_update_goal_complete",
        "update_goal_allowed": False,
        "safe_to_call_update_goal_complete": False,
        "checklist_coverage_is_not_completion": True,
        "covered_checklist_count": 10,
        "checklist_count": 10,
        "operator_input_ids": ["openai_secret_reference"],
        "p0_blocker_ids": ["openai_secret_reference"],
        "p1_decision_ids": [],
        "next_operator_action_id": "openai_secret_reference",
        "next_recommended_pass": "operator-provide-openai-secret-reference",
        "required_before_update_goal_complete": [
            "resolve_operator_inputs",
            "rerun_completion_audit",
            "require_safe_to_call_update_goal_complete_true",
        ],
        "reason": result["completion_decision"]["reason"],
    }
    assert result["setup_scope_boundary"]["status"] == (
        "setup_wide_validation_expected_to_fail_mvp_blocker_and_non_mvp_gaps"
    )
    assert result["setup_scope_boundary"]["setup_wide_invalid_provider_ids"] == [
        "claude",
        "openai",
        "local_oss",
        "n8n",
    ]
    assert result["setup_scope_boundary"]["setup_wide_invalid_integration_ids"] == [
        "telegram",
        "slack",
    ]
    assert result["setup_scope_boundary"]["non_mvp_setup_gap_ids"] == [
        "provider:claude",
        "provider:local_oss",
        "provider:n8n",
        "integration:telegram",
        "integration:slack",
    ]
    assert (
        result["setup_scope_boundary"]["non_mvp_setup_gaps_are_current_mvp_blockers"]
        is False
    )
    assert result["required_actions"] == result["required_operator_actions"]
    assert [item["id"] for item in result["required_operator_actions"]] == [
        "openai_secret_reference"
    ]
    assert result["p1_decision_ids"] == []
    assert result["canonical_operator_handoff"]["path"] == (
        "07_LOGS/Operator-Briefs/2026-05-13-mvp-next-action-card.md"
    )
    assert "resolved_chat_approval_consumption" in result["canonical_operator_handoff"]["covers"]
    assert result["authority"]["secret_values_read"] is False
    assert result["authority"]["provider_calls_performed"] is False
    assert result["authority"]["approval_consumption_performed"] is False


def test_mvp_operator_action_required_text_surfaces_provider_blocker_without_secrets(
    capsys, monkeypatch
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    exit_code = cli.main(["mvp", "operator-action-required", "--vault-root", str(ROOT)])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "safe_to_call_update_goal_complete: False" in output
    assert "completion_safety_contract:" in output
    assert "checklist_coverage_is_not_completion=True" in output
    assert "next_operator_action: openai_secret_reference" in output
    assert "setup_scope: status=setup_wide_validation_expected_to_fail_mvp_blocker_and_non_mvp_gaps" in output
    assert "non_mvp_are_mvp_blockers=False" in output
    assert "current_secret_reference: target=OPENAI_API_KEY" in output
    assert "placeholder=False" in output
    assert "resolvable=False" in output
    assert "error=reference_not_found" in output
    assert (
        "provider_live_smoke_readiness: "
        "python -m runtime.cli.main runtime provider live-smoke-readiness --json"
    ) in output
    assert (
        'presence_check: [bool][Environment]::GetEnvironmentVariable("OPENAI_API_KEY", "User")'
        in output
    )
    assert '[bool][Environment]::GetEnvironmentVariable("OPENAI_API_KEY", "Process")' in output
    assert "secret_value_read" not in output
    assert "sk-" not in output


def test_mvp_credential_handoff_lists_only_reference_requirements_without_secrets(
    tmp_path: Path, monkeypatch
) -> None:
    secret_value = "FAKE_CREDENTIAL_HANDOFF_SECRET_THAT_MUST_NOT_APPEAR"
    monkeypatch.setenv("OPENAI_API_KEY", secret_value)
    _seed_minimal_vault(tmp_path)

    payload = build_mvp_credential_handoff(tmp_path)
    serialized = json.dumps(payload, sort_keys=True)

    assert payload["surface"] == "chaseos_mvp_credential_handoff"
    assert payload["read_only"] is True
    assert payload["readiness_status"] == "blocked_operator_input_required"
    assert payload["safe_to_call_update_goal_complete"] is False
    assert payload["operator_input_ids"] == payload["completion_decision"]["operator_input_ids"]
    assert payload["p0_blocker_ids"] == payload["completion_decision"]["p0_blocker_ids"]
    assert payload["p1_decision_ids"] == payload["completion_decision"]["p1_decision_ids"]
    assert payload["current_secret_reference_kind"] == "env-var-or-local-secret-ref"
    assert payload["current_secret_reference_target"] == "SET_OPENAI_SECRET_REF"
    assert payload["current_secret_reference_target_is_placeholder"] is True
    assert payload["current_secret_reference_resolvable"] is False
    assert payload["secret_reference_probe_error"] == "reference_not_found"
    assert payload["recommended_reference_name"] == "OPENAI_API_KEY"
    assert payload["autonomous_completion_barrier"]["active"] is True
    assert payload["autonomous_completion_barrier"]["update_goal_allowed"] is False
    assert payload["completion_safety_contract"]["status"] == (
        "blocked_do_not_call_update_goal_complete"
    )
    assert payload["completion_safety_contract"]["update_goal_allowed"] is False
    assert "checklist_coverage_is_not_completion" in payload["completion_safety_contract"]
    assert payload["completion_safety_contract"]["operator_input_ids"] == payload[
        "operator_input_ids"
    ]
    assert payload["no_safe_autonomous_completion_pass_available"] is True
    assert payload["update_goal_allowed"] is False
    assert payload["next_operator_action_id"] == "openai_secret_reference"
    assert payload["next_recommended_pass"] == "operator-provide-openai-secret-reference"
    assert payload["required_operator_inputs"]
    openai_required = next(
        item for item in payload["required_operator_inputs"] if item["id"] == "openai_secret_reference"
    )
    assert openai_required["reference_presence_check_commands"] == [
        '[bool][Environment]::GetEnvironmentVariable("OPENAI_API_KEY", "User")',
        '[bool][Environment]::GetEnvironmentVariable("OPENAI_API_KEY", "Process")',
    ]
    assert openai_required["reference_presence_check_outputs_secret_value"] is False
    assert payload["p0_required_now"][0]["id"] == "openai_secret_reference"
    assert payload["p0_required_now"][0]["current_secret_reference_target"] == "SET_OPENAI_SECRET_REF"
    assert payload["p0_required_now"][0]["current_secret_reference_target_is_placeholder"] is True
    assert payload["p0_required_now"][0]["reference_presence_check_commands"] == [
        '[bool][Environment]::GetEnvironmentVariable("OPENAI_API_KEY", "User")',
        '[bool][Environment]::GetEnvironmentVariable("OPENAI_API_KEY", "Process")',
    ]
    assert payload["p0_required_now"][0]["reference_presence_check_outputs_secret_value"] is False
    assert payload["p0_required_now"][0]["secret_value_allowed_in_repo_or_chat"] is False
    assert payload["p0_required_now"][0]["codex_can_perform_now"] is False
    assert "n8n_connector_credentials" in {
        item["id"] for item in payload["p2_parked_or_out_of_scope"]
    }
    assert "wallet_exchange_or_seed_credentials" in {
        item["id"] for item in payload["p2_parked_or_out_of_scope"]
    }
    assert "07_LOGS/Operator-Briefs/2026-05-14-openai-api-key-later-guide.md" in payload[
        "source_docs"
    ]
    assert payload["operator_input_template_artifact"] == {
        "path": "07_LOGS/Operator-Briefs/2026-05-13-mvp-operator-input-template.json",
        "exists": False,
        "contains_secret_values": False,
        "validation_command": "python -m runtime.cli.main mvp validate-operator-input --input 07_LOGS/Operator-Briefs/2026-05-13-mvp-operator-input-template.json --json",
        "write_command": "python -m runtime.cli.main mvp operator-input-template --write-template 07_LOGS/Operator-Briefs/2026-05-13-mvp-operator-input-template.json --json",
    }
    assert payload["safe_commands"]["check_reference_presence_user"] == (
        '[bool][Environment]::GetEnvironmentVariable("OPENAI_API_KEY", "User")'
    )
    assert payload["safe_commands"]["check_reference_presence_process"] == (
        '[bool][Environment]::GetEnvironmentVariable("OPENAI_API_KEY", "Process")'
    )
    assert payload["safe_commands"]["preview_setup_metadata"].endswith("--dry-run --json")
    assert payload["source_commands"]["setup_wide_validation"] == (
        "python -m runtime.cli.main setup validate --json"
    )
    assert payload["boundary"]["secret_values_read"] is False
    assert payload["boundary"]["secret_values_visible"] is False
    assert payload["boundary"]["provider_calls_performed"] is False
    assert payload["boundary"]["setup_metadata_write_performed"] is False
    assert secret_value not in serialized


def test_mvp_credential_handoff_cli_uses_json_envelope(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    _seed_minimal_vault(tmp_path)

    exit_code = cli.main(["mvp", "credential-handoff", "--vault-root", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "mvp.credential-handoff"
    assert payload["result"]["surface"] == "chaseos_mvp_credential_handoff"
    assert payload["result"]["safe_to_call_update_goal_complete"] is False
    assert payload["result"]["operator_input_ids"] == payload["result"]["completion_decision"][
        "operator_input_ids"
    ]
    assert payload["result"]["autonomous_completion_barrier"]["active"] is True
    assert payload["result"]["autonomous_completion_barrier"]["update_goal_allowed"] is False
    assert payload["result"]["completion_safety_contract"]["status"] == (
        "blocked_do_not_call_update_goal_complete"
    )
    assert payload["result"]["completion_safety_contract"]["update_goal_allowed"] is False
    assert payload["result"]["completion_safety_contract"]["operator_input_ids"] == payload[
        "result"
    ]["operator_input_ids"]
    assert payload["result"]["setup_scope_boundary"]["mvp_current_setup_blocker_ids"] == [
        "openai_secret_reference"
    ]
    assert (
        payload["result"]["setup_scope_boundary"][
            "non_mvp_setup_gaps_are_current_mvp_blockers"
        ]
        is False
    )
    assert payload["result"]["no_safe_autonomous_completion_pass_available"] is True
    assert payload["result"]["update_goal_allowed"] is False
    assert payload["result"]["next_operator_action_id"] == "openai_secret_reference"
    assert payload["result"]["next_recommended_pass"] == "operator-provide-openai-secret-reference"
    assert payload["result"]["current_secret_reference_kind"] == "env-var-or-local-secret-ref"
    assert payload["result"]["current_secret_reference_target"] == "SET_OPENAI_SECRET_REF"
    assert payload["result"]["current_secret_reference_target_is_placeholder"] is True
    assert payload["result"]["current_secret_reference_resolvable"] is False
    assert payload["result"]["secret_reference_probe_error"] == "reference_not_found"
    assert payload["result"]["recommended_reference_name"] == "OPENAI_API_KEY"
    assert payload["result"]["required_operator_inputs"]
    assert payload["result"]["required_operator_inputs"][0][
        "reference_presence_check_outputs_secret_value"
    ] is False
    assert payload["result"]["p0_required_now"][0]["id"] == "openai_secret_reference"
    assert payload["result"]["p0_required_now"][0]["reference_presence_check_commands"] == [
        '[bool][Environment]::GetEnvironmentVariable("OPENAI_API_KEY", "User")',
        '[bool][Environment]::GetEnvironmentVariable("OPENAI_API_KEY", "Process")',
    ]
    assert payload["result"]["safe_commands"]["check_reference_presence_user"] == (
        '[bool][Environment]::GetEnvironmentVariable("OPENAI_API_KEY", "User")'
    )
    assert "07_LOGS/Operator-Briefs/2026-05-14-openai-api-key-later-guide.md" in payload[
        "result"
    ]["source_docs"]
    assert payload["result"]["operator_input_template_artifact"]["path"] == (
        "07_LOGS/Operator-Briefs/2026-05-13-mvp-operator-input-template.json"
    )
    assert payload["result"]["operator_input_template_artifact"]["exists"] is False
    assert payload["result"]["operator_input_template_artifact"]["contains_secret_values"] is False
    assert payload["result"]["boundary"]["secret_values_visible"] is False


def test_mvp_credential_handoff_text_surfaces_provider_blocker_without_secrets(
    capsys, monkeypatch
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    exit_code = cli.main(["mvp", "credential-handoff", "--vault-root", str(ROOT)])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "safe_to_call_update_goal_complete: False" in output
    assert "completion_safety_contract:" in output
    assert "checklist_coverage_is_not_completion=True" in output
    assert "setup_scope: status=setup_wide_validation_expected_to_fail_mvp_blocker_and_non_mvp_gaps" in output
    assert "non_mvp_are_mvp_blockers=False" in output
    assert "openai_secret_reference: target=OPENAI_API_KEY" in output
    assert "placeholder=False" in output
    assert "resolvable=False" in output
    assert "error=reference_not_found" in output
    assert (
        "provider_live_smoke_readiness: "
        "python -m runtime.cli.main runtime provider live-smoke-readiness --json"
    ) in output
    assert (
        'presence_check: [bool][Environment]::GetEnvironmentVariable("OPENAI_API_KEY", "User")'
        in output
    )
    assert '[bool][Environment]::GetEnvironmentVariable("OPENAI_API_KEY", "Process")' in output
    assert "sk-" not in output


def test_mvp_no_secret_handoff_text_outputs_show_completion_barrier(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    _seed_minimal_vault(tmp_path)
    template_path = _seed_operator_input_template(tmp_path)

    commands = [
        ["mvp", "credential-handoff", "--vault-root", str(tmp_path)],
        ["mvp", "operator-unblock-packet", "--vault-root", str(tmp_path)],
        ["mvp", "operator-input-template", "--vault-root", str(tmp_path)],
        [
            "mvp",
            "validate-operator-input",
            "--vault-root",
            str(tmp_path),
            "--input",
            str(template_path),
        ],
    ]

    for command in commands:
        exit_code = cli.main(command)
        output = capsys.readouterr().out
        assert exit_code == 0
        assert "autonomous_completion_barrier:" in output
        assert "update_goal_allowed=False" in output
        if command[1] in {
            "credential-handoff",
            "operator-unblock-packet",
            "operator-input-template",
            "validate-operator-input",
        }:
            assert "completion_safety_contract:" in output
        if command[1] in {
            "credential-handoff",
            "operator-unblock-packet",
            "operator-input-template",
            "validate-operator-input",
        }:
            assert "setup_scope: status=setup_wide_validation_expected_to_fail_current_mvp_blocker" in output
            assert "non_mvp_are_mvp_blockers=False" in output


def test_mvp_readiness_gate_reports_source_graph_context_bridge(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    _seed_minimal_vault(tmp_path)
    _seed_source_context_fixture(tmp_path)

    payload = build_mvp_readiness_gate(tmp_path)
    graph = payload["checks"]["graph_source_intelligence"]

    assert graph["status"] == "ready_for_read_only_workflow_context_reference"
    assert graph["source_context_available"] is True
    assert graph["source_package_reference_count"] == 1
    assert graph["graph_context_available"] is True
    assert graph["graph_context_reference_count"] == 4
    assert graph["workflow_context_reference_present"] is True
    assert graph["workflow_can_reference_context_without_mutation"] is True
    assert graph["context_navigation_only"] is True
    assert graph["mutation_authority_false"] is True
    assert graph["autonomous_mutation_allowed"] is False
    assert graph["context_bridge"]["authority"]["graph_mutation_allowed"] is False
    assert (
        "runtime/source_intelligence/workspaces/phase7-test/sources/demo.json"
        in graph["evidence_refs"]
    )
    assert "06_AGENTS/Agent-Control-Plane.md" in graph["evidence_refs"]


def test_mvp_readiness_gate_reports_machine_checked_system_control_boundary(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    _seed_minimal_vault(tmp_path)
    _seed_source_context_fixture(tmp_path)
    for relative in [
        "runtime/browser_runtime/cdp_executor_spec.py",
        "runtime/browser_runtime/workflow_replay_execution_readiness.py",
        "06_AGENTS/ChaseOS-MVP-Operator-Unblock-Packet.md",
    ]:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# {path.stem}\n", encoding="utf-8")

    payload = build_mvp_readiness_gate(tmp_path)
    system_control = payload["checks"]["full_system_control"]
    boundary = system_control["boundary"]
    cdp = boundary["cdp_read_only_boundary"]

    assert system_control["status"] == "parked_and_gated_until_mvp_proven"
    assert system_control["browser_system_automation_allowed_now"] is False
    assert system_control["host_mutation_allowed_now"] is False
    assert system_control["browser_system_automation_gated"] is True
    assert system_control["host_mutation_false"] is True
    assert system_control["workflow_replay_gated"] is True
    assert system_control["approval_provider_agent_bus_blocked"] is True
    assert system_control["credential_session_profile_access_blocked"] is True
    assert system_control["cdp_no_execution_proof"] is True
    assert system_control["future_local_proof_requires_separate_approval"] is True
    assert boundary["authority"]["broad_system_control_allowed"] is False
    assert boundary["authority"]["host_mutation_allowed_now"] is False
    assert boundary["authority"]["approval_consumption_allowed"] is False
    assert cdp["execution_enabled"] is False
    assert cdp["browser_launch_attempted"] is False
    assert cdp["credential_value_read"] is False
    assert cdp["cookie_or_session_read"] is False
    assert cdp["real_profile_used"] is False
    pass_10 = next(row for row in payload["passes"] if row["pass"] == 10)
    assert pass_10["status"] == "parked_and_gated_until_mvp_proven"
    assert pass_10["blockers"] == []
