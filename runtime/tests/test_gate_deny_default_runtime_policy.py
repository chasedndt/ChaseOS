"""Deny-by-default runtime operation policy tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path


_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[2]
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

import runtime.cli.agent_bus_commands as agent_bus_cli  # noqa: E402
import runtime.cli.main as cli  # noqa: E402
import runtime.setup_cli as setup_cli  # noqa: E402
from runtime.chaseos_gate import (  # noqa: E402
    BROWSER_CDP_READ_ONLY_PROOF_APPROVAL_SCHEMA_ID,
    BROWSER_CDP_READ_ONLY_PROOF_OPERATION,
    RUNTIME_PROVIDER_CONFIG_APPLY_APPROVAL_SCHEMA_ID,
    RUNTIME_PROVIDER_CONFIG_APPLY_OPERATION,
    RUNTIME_PROVIDER_LIVE_PROBE_APPROVAL_SCHEMA_ID,
    RUNTIME_PROVIDER_LIVE_PROBE_OPERATION,
    check_runtime_operation,
    get_runtime_operation_approval_schema,
)


def test_unknown_runtime_operation_is_denied() -> None:
    allowed, reason = check_runtime_operation("gateway.magic.write")

    assert allowed is False
    assert "not allowlisted" in reason


def test_agent_bus_task_create_operation_allows_active_bus_runtimes() -> None:
    allowed, reason = check_runtime_operation(
        "agent_bus.task.create",
        actor_adapter_id="Hermes",
        target_runtime="OpenClaw",
    )

    assert allowed is True
    assert "allowed" in reason


def test_agent_bus_task_create_operation_blocks_advisory_actor() -> None:
    allowed, reason = check_runtime_operation(
        "agent_bus.task.create",
        actor_adapter_id="openai-chat",
        target_runtime="OpenClaw",
    )

    assert allowed is False
    assert "not approved for coordination-sensitive runtime work" in reason


def test_agent_bus_discord_ingress_operation_allows_active_target() -> None:
    allowed, reason = check_runtime_operation(
        "agent_bus.ingress.discord",
        target_runtime="OpenClaw",
    )

    assert allowed is True
    assert "allowed" in reason


def test_setup_provider_apply_operation_is_allowlisted() -> None:
    allowed, reason = check_runtime_operation("setup.provider.apply")

    assert allowed is True
    assert "allowed" in reason


def test_runtime_provider_live_probe_operation_is_declared_but_approval_blocked() -> None:
    schema = get_runtime_operation_approval_schema(
        RUNTIME_PROVIDER_LIVE_PROBE_OPERATION,
        provider_id="openai",
        model="gpt-5.5",
        runtime="openclaw",
        external_api="provider.openai",
    )
    assert schema is not None
    assert schema["approval_schema_id"] == RUNTIME_PROVIDER_LIVE_PROBE_APPROVAL_SCHEMA_ID
    assert schema["approval_request_written"] is False
    assert schema["live_network_call_attempted"] is False

    allowed, reason = check_runtime_operation(
        RUNTIME_PROVIDER_LIVE_PROBE_OPERATION,
        external_api="provider.openai",
    )
    assert allowed is False
    assert RUNTIME_PROVIDER_LIVE_PROBE_APPROVAL_SCHEMA_ID in reason


def test_runtime_provider_config_apply_operation_is_declared_but_approval_blocked() -> None:
    schema = get_runtime_operation_approval_schema(
        RUNTIME_PROVIDER_CONFIG_APPLY_OPERATION,
        provider_id="openai",
        model="gpt-5.5",
        runtime="cli",
    )
    assert schema is not None
    assert schema["approval_schema_id"] == RUNTIME_PROVIDER_CONFIG_APPLY_APPROVAL_SCHEMA_ID
    assert schema["approval_request_written"] is False
    assert schema["apply_executor_implemented"] is False
    assert schema["provider_config_mutated"] is False
    assert schema["setup_state_mutated"] is False
    assert schema["provider_state_mutated"] is False

    allowed, reason = check_runtime_operation(
        RUNTIME_PROVIDER_CONFIG_APPLY_OPERATION,
        write_targets=[
            "runtime/openclaw/model_config.yaml",
            "runtime/setup_state.json",
        ],
    )
    assert allowed is False
    assert RUNTIME_PROVIDER_CONFIG_APPLY_APPROVAL_SCHEMA_ID in reason


def test_browser_cdp_read_only_proof_operation_is_declared_but_approval_blocked() -> None:
    schema = get_runtime_operation_approval_schema(
        BROWSER_CDP_READ_ONLY_PROOF_OPERATION,
        runtime="Codex",
        external_api="browser.navigation",
    )

    assert schema is not None
    assert schema["approval_schema_id"] == BROWSER_CDP_READ_ONLY_PROOF_APPROVAL_SCHEMA_ID
    assert schema["approval_request_written"] is False
    assert schema["browser_launch_attempted"] is False
    assert schema["cdp_connection_attempted"] is False
    assert schema["real_profile_used"] is False
    assert schema["credential_value_read"] is False
    assert schema["cookie_or_session_read"] is False
    assert schema["trusted_skill_written"] is False
    assert schema["canonical_files_mutated"] is False
    template = schema["approval_request_template"]
    assert template["operation"] == BROWSER_CDP_READ_ONLY_PROOF_OPERATION
    assert template["secret_policy"]["credentials_allowed"] is False
    assert template["secret_policy"]["cookies_allowed"] is False
    assert template["secret_policy"]["raw_cdp_allowed"] is False

    allowed, reason = check_runtime_operation(
        BROWSER_CDP_READ_ONLY_PROOF_OPERATION,
        external_api="browser.navigation",
        write_targets=[
            "07_LOGS/Browser-Runs/example.json",
            "07_LOGS/Agent-Activity/example.md",
            "03_INPUTS/Browser-Skill-Candidates/example/example.md",
        ],
    )
    assert allowed is False
    assert BROWSER_CDP_READ_ONLY_PROOF_APPROVAL_SCHEMA_ID in reason


def test_gate_check_operation_cli_surfaces_browser_cdp_approval_schema(capsys) -> None:
    exit_code = cli.main(
        [
            "gate",
            "check-operation",
            BROWSER_CDP_READ_ONLY_PROOF_OPERATION,
            "--external-api",
            "browser.navigation",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]
    assert exit_code == 1
    assert result["allowed"] is False
    assert result["operation"] == BROWSER_CDP_READ_ONLY_PROOF_OPERATION
    assert result["approval_schema"]["approval_schema_id"] == BROWSER_CDP_READ_ONLY_PROOF_APPROVAL_SCHEMA_ID
    assert result["approval_schema"]["approval_request_written"] is False
    assert result["approval_schema"]["cdp_connection_attempted"] is False
    assert result["approval_schema"]["browser_launch_attempted"] is False


def test_gate_check_operation_cli_surfaces_live_probe_approval_schema(capsys) -> None:
    exit_code = cli.main(
        [
            "gate",
            "check-operation",
            RUNTIME_PROVIDER_LIVE_PROBE_OPERATION,
            "--external-api",
            "provider.openai",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]
    assert exit_code == 1
    assert result["allowed"] is False
    assert result["operation"] == RUNTIME_PROVIDER_LIVE_PROBE_OPERATION
    assert result["approval_schema"]["approval_schema_id"] == RUNTIME_PROVIDER_LIVE_PROBE_APPROVAL_SCHEMA_ID
    assert result["approval_schema"]["approval_request_written"] is False
    assert result["approval_schema"]["live_network_call_attempted"] is False


def test_gate_check_operation_cli_surfaces_provider_config_apply_schema(capsys) -> None:
    exit_code = cli.main(
        [
            "gate",
            "check-operation",
            RUNTIME_PROVIDER_CONFIG_APPLY_OPERATION,
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]
    assert exit_code == 1
    assert result["allowed"] is False
    assert result["operation"] == RUNTIME_PROVIDER_CONFIG_APPLY_OPERATION
    assert result["approval_schema"]["approval_schema_id"] == RUNTIME_PROVIDER_CONFIG_APPLY_APPROVAL_SCHEMA_ID
    assert result["approval_schema"]["approval_request_written"] is False
    assert result["approval_schema"]["provider_config_mutated"] is False
    assert result["approval_schema"]["setup_state_mutated"] is False


def test_gate_check_operation_cli_blocks_unknown_operation(capsys) -> None:
    exit_code = cli.main(["gate", "check-operation", "gateway.magic.write", "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert payload["ok"] is False
    assert payload["action"] == "gate.check-operation"
    assert payload["result"]["allowed"] is False
    assert payload["result"]["operation"] == "gateway.magic.write"


def test_agent_bus_task_create_policy_blocks_before_bus_write(monkeypatch, capsys) -> None:
    called = {"create": False}

    def fake_create_task(*args, **kwargs):
        called["create"] = True
        return {"created": True, "task_id": "task-should-not-exist"}

    monkeypatch.setattr(agent_bus_cli, "agent_bus_create_task", fake_create_task)

    exit_code = cli.main(
        [
            "agent-bus",
            "task",
            "create",
            "--sender",
            "openai-chat",
            "--to",
            "OpenClaw",
            "--request",
            "Do unsafe work",
            "--expected-output",
            "Should be blocked",
            "--vault-root",
            str(_VAULT_ROOT),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert called["create"] is False
    assert payload["ok"] is False
    assert payload["action"] == "agent-bus.task.create"
    assert payload["result"]["allowed"] is False
    assert payload["result"]["operation"] == "agent_bus.task.create"


def test_config_set_operation_allows_cli_operator_write_target() -> None:
    allowed, reason = check_runtime_operation(
        "config.set",
        write_targets=[".chaseos/config.yaml"],
    )

    assert allowed is True
    assert "allowed" in reason



def test_schedule_enable_operation_allows_cli_operator_write_targets() -> None:
    allowed, reason = check_runtime_operation(
        "schedule.enable",
        write_targets=[
            "runtime/schedules/sch-example.yaml",
            "runtime/schedules/index.yaml",
            "07_LOGS/Schedule-State/schedule_state_log.jsonl",
        ],
    )

    assert allowed is True
    assert "allowed" in reason


def test_gateway_workflow_dispatch_allows_openclaw_scheduled_briefing_targets() -> None:
    allowed, reason = check_runtime_operation(
        "gateway.workflow.dispatch",
        actor_adapter_id="openclaw",
        task_type="scheduled-briefing",
        write_targets=[
            "07_LOGS/SBP-Runs/",
            "07_LOGS/Agent-Activity/",
        ],
    )

    assert allowed is True
    assert "allowed" in reason


def test_gateway_workflow_dispatch_blocks_non_actor_write_target() -> None:
    allowed, reason = check_runtime_operation(
        "gateway.workflow.dispatch",
        actor_adapter_id="openclaw",
        task_type="scheduled-briefing",
        write_targets=["02_KNOWLEDGE/unsafe.md"],
    )

    assert allowed is False
    assert "outside explicit allowlists" in reason or "explicitly denied" in reason


def test_gateway_workflow_invoke_bounded_allows_openclaw_brief_targets() -> None:
    allowed, reason = check_runtime_operation(
        "gateway.workflow.invoke_bounded",
        actor_adapter_id="openclaw",
        task_type="operator-briefing",
        write_targets=[
            "07_LOGS/Operator-Briefs/",
            "07_LOGS/Agent-Activity/",
        ],
    )

    assert allowed is True
    assert "allowed" in reason


def test_sbp_discord_delivery_operation_allows_declared_external_api() -> None:
    allowed, reason = check_runtime_operation(
        "sbp.delivery.discord.webhook_send",
        external_api="delivery.discord_webhook",
        external_side_effect=True,
    )

    assert allowed is True
    assert "allowed" in reason


def test_sbp_whop_delivery_operation_allows_declared_external_api() -> None:
    allowed, reason = check_runtime_operation(
        "sbp.delivery.whop.post",
        external_api="delivery.whop_api",
        external_side_effect=True,
    )

    assert allowed is True
    assert "allowed" in reason


def test_sbp_delivery_operation_requires_matching_external_api() -> None:
    allowed, reason = check_runtime_operation(
        "sbp.delivery.discord.webhook_send",
        external_api="delivery.whop_api",
        external_side_effect=True,
    )

    assert allowed is False
    assert "delivery.discord_webhook" in reason


def test_osril_approval_response_operation_allows_response_and_session_state_targets() -> None:
    allowed, reason = check_runtime_operation(
        "osril.approval_response",
        write_targets=[
            "runtime/osril/approvals/appr-1.response.json",
            "runtime/osril/approvals/appr-1.application.json",
            "runtime/osril/run/",
        ],
    )

    assert allowed is True
    assert "allowed" in reason


def test_osril_approval_resume_operation_allows_resume_and_session_state_targets() -> None:
    allowed, reason = check_runtime_operation(
        "osril.approval_resume",
        write_targets=[
            "runtime/osril/approvals/appr-1.resume.json",
            "runtime/osril/run/",
        ],
    )

    assert allowed is True
    assert "allowed" in reason



def test_config_set_policy_blocks_before_write(monkeypatch, capsys) -> None:
    called = {"set": False}

    def fake_set_config_value(*args, **kwargs):
        called["set"] = True
        return {}, Path("/tmp/should-not-write")

    monkeypatch.setattr(cli, "set_config_value", fake_set_config_value)
    monkeypatch.setattr(
        cli,
        "check_runtime_operation",
        lambda *args, **kwargs: (False, "blocked-by-test"),
    )

    exit_code = cli.main(
        [
            "config",
            "set",
            "default_provider",
            "openai",
            "--vault-root",
            str(_VAULT_ROOT),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert called["set"] is False
    assert payload["ok"] is False
    assert payload["action"] == "config.set"
    assert payload["result"]["allowed"] is False
    assert payload["result"]["operation"] == "config.set"



def test_schedule_enable_policy_blocks_before_state_mutation(monkeypatch, capsys) -> None:
    called = {"enable": False}

    def fake_enable_schedule(*args, **kwargs):
        called["enable"] = True
        return True

    monkeypatch.setattr(cli, "enable_schedule", fake_enable_schedule)
    monkeypatch.setattr(
        cli,
        "check_runtime_operation",
        lambda *args, **kwargs: (False, "blocked-by-test"),
    )

    exit_code = cli.main(
        [
            "schedule",
            "enable",
            "sch-example",
            "--vault-root",
            str(_VAULT_ROOT),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert called["enable"] is False
    assert payload["ok"] is False
    assert payload["action"] == "schedule.enable"
    assert payload["result"]["allowed"] is False
    assert payload["result"]["operation"] == "schedule.enable"


def test_setup_provider_apply_policy_blocks_before_setup_state_write(monkeypatch, capsys) -> None:
    called = {"write": False}

    monkeypatch.setattr(
        setup_cli,
        "check_runtime_operation",
        lambda *args, **kwargs: (False, "blocked by setup policy"),
        raising=False,
    )
    monkeypatch.setattr(setup_cli, "ensure_setup_state", lambda: Path("runtime/setup_state.json"))

    def fake_update_provider_state(*args, **kwargs):
        called["write"] = True
        return Path("runtime/setup_state.json")

    monkeypatch.setattr(setup_cli, "update_provider_state", fake_update_provider_state)

    exit_code = cli.main(["setup", "provider", "wizard", "openai", "--apply", "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert called["write"] is False
    assert payload["ok"] is False
    assert payload["action"] == "setup.provider.wizard"
    assert "blocked by setup policy" in payload["errors"]
    assert payload["result"]["error"] == "blocked by setup policy"


def test_scaffold_project_generate_operation_allows_draft_output_target() -> None:
    allowed, reason = check_runtime_operation(
        "scaffold.project.generate",
        write_targets=["runtime/scaffold/generated/project-alpha-core/scaffold_request.json"],
    )

    assert allowed is True
    assert "allowed" in reason


def test_scaffold_workspace_generate_operation_allows_draft_output_target() -> None:
    allowed, reason = check_runtime_operation(
        "scaffold.workspace.generate",
        write_targets=["runtime/scaffold/generated/workspace-signal-lab/scaffold_request.json"],
    )

    assert allowed is True
    assert "allowed" in reason


def test_scaffold_brain_generate_operation_allows_draft_output_target() -> None:
    allowed, reason = check_runtime_operation(
        "scaffold.brain.generate",
        write_targets=["runtime/scaffold/generated/brain-demo-brain/scaffold_request.json"],
    )

    assert allowed is True
    assert "allowed" in reason


def test_scaffold_project_policy_blocks_before_generator_write(monkeypatch, capsys) -> None:
    called = {"generate": False}

    def fake_generate_scaffold(*args, **kwargs):
        called["generate"] = True
        return {"should": "not run"}

    monkeypatch.setattr(cli, "generate_scaffold", fake_generate_scaffold)
    monkeypatch.setattr(
        cli,
        "check_runtime_operation",
        lambda *args, **kwargs: (False, "blocked-by-scaffold-policy"),
    )

    exit_code = cli.main(
        [
            "scaffold",
            "project",
            "Alpha Core",
            "--vault-root",
            str(_VAULT_ROOT),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert called["generate"] is False
    assert payload["ok"] is False
    assert payload["action"] == "scaffold.project"
    assert payload["result"]["allowed"] is False
    assert payload["result"]["operation"] == "scaffold.project.generate"


def test_browser_open_operation_allows_audit_write_target() -> None:
    allowed, reason = check_runtime_operation(
        "browser.open",
        write_targets=["07_LOGS/Agent-Activity/browser-open-test.json"],
    )

    assert allowed is True
    assert "allowed" in reason


def test_browser_operation_requires_declared_navigation_api() -> None:
    allowed, reason = check_runtime_operation(
        "browser.open",
        write_targets=["07_LOGS/Agent-Activity/browser-open-test.json"],
        external_api="capture.rss",
        external_side_effect=True,
    )

    assert allowed is False
    assert "browser.navigation" in reason


def test_browser_operation_blocks_unknown_explicit_external_api() -> None:
    allowed, reason = check_runtime_operation(
        "browser.screenshot",
        write_targets=["07_LOGS/Agent-Activity/browser-screenshot-test.json"],
        external_api="browser.magic",
        external_side_effect=True,
    )

    assert allowed is False
    assert "browser.navigation" in reason


def test_browser_screenshot_operation_allows_activity_artifact_target() -> None:
    allowed, reason = check_runtime_operation(
        "browser.screenshot",
        write_targets=["07_LOGS/Agent-Activity/browser-screenshot-test.json"],
    )

    assert allowed is True
    assert "allowed" in reason


def test_browser_open_policy_blocks_before_navigation(monkeypatch, capsys) -> None:
    called = {"open": False}

    def fake_run_open(*args, **kwargs):
        called["open"] = True
        return 0

    monkeypatch.setattr(cli, "run_open", fake_run_open)
    monkeypatch.setattr(
        cli,
        "check_runtime_operation",
        lambda *args, **kwargs: (False, "blocked-by-browser-policy"),
    )

    exit_code = cli.main(
        [
            "operate",
            "browser",
            "open",
            "https://example.com",
            "--vault-root",
            str(_VAULT_ROOT),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert called["open"] is False
    assert payload["ok"] is False
    assert payload["action"] == "operate.browser.open"
    assert payload["result"]["allowed"] is False
    assert payload["result"]["operation"] == "browser.open"


def test_browser_screenshot_policy_blocks_before_browser_write(monkeypatch, capsys) -> None:
    called = {"screenshot": False}

    def fake_run_screenshot(*args, **kwargs):
        called["screenshot"] = True
        return 0

    monkeypatch.setattr(cli, "run_screenshot", fake_run_screenshot)
    monkeypatch.setattr(
        cli,
        "check_runtime_operation",
        lambda *args, **kwargs: (False, "blocked-by-browser-policy"),
    )

    exit_code = cli.main(
        [
            "operate",
            "browser",
            "screenshot",
            "https://example.com",
            "--vault-root",
            str(_VAULT_ROOT),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert called["screenshot"] is False
    assert payload["ok"] is False
    assert payload["action"] == "operate.browser.screenshot"
    assert payload["result"]["allowed"] is False
    assert payload["result"]["operation"] == "browser.screenshot"


def test_runtime_registry_operations_allow_registry_targets() -> None:
    allowed, reason = check_runtime_operation(
        "agent.register",
        write_targets=[
            "runtime/aor/runtime_registry/custom-local/registry_entry.yaml",
            "runtime/aor/runtime_registry/custom-local/audit/lifecycle_log.jsonl",
        ],
    )

    assert allowed is True
    assert "allowed" in reason


def test_runtime_registry_operations_block_path_escape() -> None:
    allowed, reason = check_runtime_operation(
        "agent.register",
        write_targets=[
            "runtime/aor/runtime_registry/../../runtime/policy/protected_files.yaml",
        ],
    )

    assert allowed is False
    assert "outside explicit allowlists" in reason


def test_agent_register_policy_blocks_before_registry_write(monkeypatch, capsys) -> None:
    called = {"register": False}

    def fake_register_runtime(*args, **kwargs):
        called["register"] = True
        return {"entry": {}, "path": Path("runtime/aor/runtime_registry/blocked/registry_entry.yaml")}

    monkeypatch.setattr(cli, "register_runtime", fake_register_runtime)
    monkeypatch.setattr(
        cli,
        "check_runtime_operation",
        lambda *args, **kwargs: (False, "blocked-by-runtime-registry-policy"),
    )

    exit_code = cli.main(
        [
            "agent",
            "register",
            "custom-provider",
            "local-runner",
            "--runtime-id",
            "blocked-runtime",
            "--vault-root",
            str(_VAULT_ROOT),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert called["register"] is False
    assert payload["ok"] is False
    assert payload["result"]["operation"] == "agent.register"


def test_graph_store_write_operations_allow_only_declared_store_roots() -> None:
    allowed_targets = {
        "graph_store.snapshot.write": [
            "runtime/graph/store/manifests/current.json",
            "runtime/graph/store/manifests/snapshots/graph-snap-1.json",
            "runtime/graph/store/snapshots/graph-snap-1.json",
        ],
        "graph_store.identity.write": [
            "runtime/graph/store/identity/node_identity_registry.json",
            "runtime/graph/store/identity/aliases.json",
        ],
        "graph_store.migration.write": [
            "runtime/graph/store/migrations/migration-1.json",
        ],
    }

    for operation, write_targets in allowed_targets.items():
        allowed, reason = check_runtime_operation(operation, write_targets=write_targets)

        assert allowed is True, f"{operation}: {reason}"
        assert "allowed" in reason


def test_graph_store_write_operations_block_canonical_protected_source_and_ambient_paths() -> None:
    blocked_targets = [
        "02_KNOWLEDGE/graph-store-leak.md",
        "06_AGENTS/Permission-Matrix.md",
        "06_AGENTS/HERMES.md",
        "runtime/graph/artifact.py",
        "runtime/graph/store/../artifact.py",
        "/tmp/graph-snap-1.json",
    ]

    for operation in (
        "graph_store.snapshot.write",
        "graph_store.identity.write",
        "graph_store.migration.write",
    ):
        for write_target in blocked_targets:
            allowed, reason = check_runtime_operation(operation, write_targets=[write_target])

            assert allowed is False, f"{operation} unexpectedly allowed {write_target}"
            assert "outside explicit allowlists" in reason


def test_agent_lifecycle_policy_blocks_before_registry_write(monkeypatch, capsys) -> None:
    called = {"transition": False}

    def fake_transition_lifecycle_state(*args, **kwargs):
        called["transition"] = True
        return {"entry": {}, "changed": True, "audit_path": None}

    monkeypatch.setattr(cli, "transition_lifecycle_state", fake_transition_lifecycle_state)
    monkeypatch.setattr(
        cli,
        "check_runtime_operation",
        lambda *args, **kwargs: (False, "blocked-by-runtime-registry-policy"),
    )

    exit_code = cli.main(
        [
            "agent",
            "lifecycle",
            "openclaw",
            "sandboxed",
            "--decision-ref",
            "test-decision",
            "--vault-root",
            str(_VAULT_ROOT),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert called["transition"] is False
    assert payload["ok"] is False
    assert payload["result"]["operation"] == "agent.lifecycle.transition"


def test_lifecycle_coordination_watch_run_operation_allows_agent_bus_transport() -> None:
    allowed, reason = check_runtime_operation("lifecycle.coordination_watch.run")

    assert allowed is True
    assert "allowed" in reason


def test_lifecycle_supervisor_start_operation_allows_host_process_and_lifecycle_targets() -> None:
    allowed, reason = check_runtime_operation(
        "lifecycle.coordination_watch_supervisor.start",
        write_targets=[
            "runtime/lifecycle/run/openclaw-coordination-watch.json",
            "runtime/lifecycle/run/openclaw-coordination-watch.log",
        ],
        external_api="host.process",
        external_side_effect=True,
    )

    assert allowed is True
    assert "allowed" in reason


def test_lifecycle_bootstrap_apply_operation_allows_host_scheduler_and_lifecycle_targets() -> None:
    allowed, reason = check_runtime_operation(
        "lifecycle.coordination_watch_bootstrap.apply",
        write_targets=[
            "runtime/lifecycle/bootstrap/openclaw-coordination-watch-launcher.bat",
            "runtime/lifecycle/bootstrap/openclaw-coordination-watch-registration.json",
            "runtime/lifecycle/run/openclaw-coordination-watch-bootstrap-events.jsonl",
        ],
        external_api="host.scheduler",
        external_side_effect=True,
    )

    assert allowed is True
    assert "allowed" in reason


def test_lifecycle_bootstrap_verify_requires_declared_scheduler_api() -> None:
    allowed, reason = check_runtime_operation(
        "lifecycle.coordination_watch_bootstrap.verify",
        write_targets=["runtime/lifecycle/run/openclaw-coordination-watch-bootstrap-events.jsonl"],
        external_api="browser.navigation",
    )

    assert allowed is False
    assert "host.scheduler" in reason


def test_lifecycle_bootstrap_activation_checklist_allows_scheduler_query_only() -> None:
    allowed, reason = check_runtime_operation(
        "lifecycle.coordination_watch_bootstrap.activation_checklist",
        external_api="host.scheduler",
    )

    assert allowed is True
    assert "allowed" in reason


def test_runtime_coordination_watch_supervisor_start_policy_blocks_before_process(monkeypatch, capsys) -> None:
    called = {"start": False}

    def fake_start_supervised_coordination_watch(*args, **kwargs):
        called["start"] = True
        return {"started": True}

    monkeypatch.setattr(cli, "start_supervised_coordination_watch", fake_start_supervised_coordination_watch)
    monkeypatch.setattr(
        cli,
        "check_runtime_operation",
        lambda *args, **kwargs: (False, "blocked-by-lifecycle-policy"),
    )

    exit_code = cli.main(
        [
            "runtime",
            "coordination-watch-supervisor",
            "--runtime",
            "openclaw",
            "--action",
            "start",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert called["start"] is False
    assert payload["ok"] is False
    assert payload["action"] == "runtime.coordination-watch-supervisor"
    assert payload["result"]["allowed"] is False
    assert payload["result"]["operation"] == "lifecycle.coordination_watch_supervisor.start"


def test_runtime_coordination_watch_bootstrap_apply_policy_blocks_before_host_mutation(monkeypatch, capsys) -> None:
    called = {"apply": False}

    def fake_apply_coordination_watch_bootstrap(*args, **kwargs):
        called["apply"] = True
        return {"applied": True}

    monkeypatch.setattr(cli, "apply_coordination_watch_bootstrap", fake_apply_coordination_watch_bootstrap)
    monkeypatch.setattr(
        cli,
        "check_runtime_operation",
        lambda *args, **kwargs: (False, "blocked-by-lifecycle-policy"),
    )

    exit_code = cli.main(
        [
            "runtime",
            "coordination-watch-bootstrap",
            "--runtime",
            "openclaw",
            "--action",
            "apply",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert called["apply"] is False
    assert payload["ok"] is False
    assert payload["action"] == "runtime.coordination-watch-bootstrap"
    assert payload["result"]["allowed"] is False
    assert payload["result"]["operation"] == "lifecycle.coordination_watch_bootstrap.apply"
