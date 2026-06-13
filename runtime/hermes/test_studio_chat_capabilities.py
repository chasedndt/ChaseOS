from __future__ import annotations

from pathlib import Path


def test_capability_command_returns_bounded_command_map(tmp_path: Path) -> None:
    from runtime.hermes.studio_chat_capabilities import try_handle_studio_chat_capability

    result = try_handle_studio_chat_capability("/capabilities", session_id="s1", vault_root=tmp_path)

    assert result is not None
    assert result["ok"] is True
    assert result["runtime"] == "Hermes"
    assert result["session_id"] == "s1"
    assert result["bridge"] == "hermes_studio_capability_layer"
    assert result["capability_action"] == "capabilities"
    assert "/status" in result["text"]
    assert "Proposal and action preview" in result["text"]
    assert result["authority"]["provider_call_performed"] is False
    assert result["authority"]["shell_command_performed"] is False
    assert result["authority"]["approval_consumed"] is False
    assert result["authority"]["agent_bus_task_created"] is False


def test_readiness_command_reports_agent_bus_without_effects(tmp_path: Path) -> None:
    from runtime.agent_bus.bus import create_task
    from runtime.hermes.studio_chat_capabilities import try_handle_studio_chat_capability

    create_task(
        tmp_path,
        sender="Studio",
        recipient="Hermes",
        intent="TASK",
        request="ping",
        expected_output="chat-response",
        notes="task_type: chat",
    )

    result = try_handle_studio_chat_capability("/readiness", session_id="s2", vault_root=tmp_path)

    assert result is not None
    assert result["capability_action"] == "readiness"
    assert "Studio Chat route" in result["text"]
    assert "Agent Bus task statuses" in result["text"]
    assert "Hermes" in result["text"]
    assert "direct provider call from Studio: `false`" in result["text"]
    assert result["authority"]["preview_only"] is True


def test_model_call_readiness_command_exposes_narrow_contract_without_provider_call(
    tmp_path: Path, monkeypatch
) -> None:
    from runtime.hermes.studio_chat_capabilities import try_handle_studio_chat_capability

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    result = try_handle_studio_chat_capability("/model-call", session_id="s-model", vault_root=tmp_path)

    assert result is not None
    assert result["capability_action"] == "model-call"
    assert "Studio Provider/Model Call Readiness" in result["text"]
    assert "studio_read_only_model_call_v1" in result["text"]
    assert "what_can_be_done_now" in result["text"]
    assert "what_approval_unlocks" in result["text"]
    assert "proof_appears_in" in result["text"]
    assert "provider_calls_allowed=false" in result["text"]
    assert result["authority"]["provider_call_performed"] is False
    assert result["authority"]["approval_consumed"] is False


def test_proposal_and_handoff_are_preview_only(tmp_path: Path) -> None:
    from runtime.hermes.studio_chat_capabilities import try_handle_studio_chat_capability

    proposal = try_handle_studio_chat_capability(
        "/proposal create a runtime status panel", session_id="s3", vault_root=tmp_path
    )
    handoff = try_handle_studio_chat_capability(
        "/handoff OpenClaw: review the Studio Chat UI", session_id="s4", vault_root=tmp_path
    )

    assert proposal is not None
    assert "writes_performed: `false`" in proposal["text"]
    assert "approval_consumed: `false`" in proposal["text"]
    assert handoff is not None
    assert "recipient: `OpenClaw`" in handoff["text"]
    assert "No Agent Bus task was created" in handoff["text"]
    assert handoff["authority"]["agent_bus_task_created"] is False


def test_normal_chat_falls_through_to_live_bridge(monkeypatch, tmp_path: Path) -> None:
    import shutil
    import subprocess

    from runtime.hermes.chat_bridge import call_hermes_chat_bridge

    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, stdout="hello\n", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(shutil, "which", lambda name: name if name == "hermes" else None)

    result = call_hermes_chat_bridge("hi. Reply exactly: hello", vault_root=tmp_path)

    assert result["ok"] is True
    assert result["text"] == "hello"
    assert result["bridge"] == "hermes_cli_z"
    assert calls


def test_agent_control_plane_phrase_does_not_trigger_proposal_preview(tmp_path: Path) -> None:
    from runtime.hermes.studio_chat_capabilities import try_handle_studio_chat_capability

    result = try_handle_studio_chat_capability(
        "Hello Hermes from Agent Control Plane verification. Reply in one short natural sentence.",
        session_id="s-control-plane-normal",
        vault_root=tmp_path,
    )

    assert result is None


def test_bridge_retries_when_normal_chat_gets_unrequested_proposal_preview(monkeypatch, tmp_path: Path) -> None:
    import shutil
    import subprocess

    from runtime.hermes.chat_bridge import call_hermes_chat_bridge

    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        if len(calls) == 1:
            return subprocess.CompletedProcess(cmd, 0, stdout="## Proposal preview — no effects performed\n", stderr="")
        return subprocess.CompletedProcess(cmd, 0, stdout="Hermes received the live Agent Control Plane test.\n", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(shutil, "which", lambda name: name if name == "hermes" else None)

    result = call_hermes_chat_bridge(
        "Hermes, this is a live Agent Control Plane test. Reply in one short natural sentence confirming you received it.",
        vault_root=tmp_path,
    )

    assert result["ok"] is True
    assert result["text"] == "Hermes received the live Agent Control Plane test."
    assert result["bridge"].endswith(":retry_direct_chat")
    assert len(calls) == 2


def test_bridge_sanitizes_repeated_unrequested_proposal_preview(monkeypatch, tmp_path: Path) -> None:
    import shutil
    import subprocess

    from runtime.hermes.chat_bridge import call_hermes_chat_bridge

    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, stdout="## Proposal preview — no effects performed\n", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(shutil, "which", lambda name: name if name == "hermes" else None)

    result = call_hermes_chat_bridge(
        "Hermes, this is a live Agent Control Plane test. Reply in one short natural sentence confirming you received it.",
        vault_root=tmp_path,
    )

    assert result["ok"] is True
    assert result["text"] == "Received loud and clear — Hermes is live on the Agent Control Plane."
    assert result["bridge"].endswith(":sanitized_unrequested_proposal")
    assert len(calls) == 3


def test_authority_catalog_exposes_requested_control_plane_classes_without_effects(tmp_path: Path) -> None:
    from runtime.hermes.studio_chat_capabilities import try_handle_studio_chat_capability

    result = try_handle_studio_chat_capability("/authority", session_id="s5", vault_root=tmp_path)

    assert result is not None
    assert result["ok"] is True
    assert result["capability_action"] == "authority"
    for capability in (
        "shell/runtime execution",
        "approval consumption",
        "protected-file mutation",
        "canonical knowledge promotion",
        "external connector sends",
        "granting new runtime authority",
    ):
        assert capability in result["text"]
    assert "effects_performed_now: `false`" in result["text"]
    assert "aor_governance_required: `true`" in result["text"]
    assert "chaseos_gate_required_for_gated_effects: `true`" in result["text"]
    assert "runtime_self_authorization_allowed: `false`" in result["text"]
    assert "None of the six requested capability classes are inherently invalid" in result["text"]
    assert result["authority"]["shell_command_performed"] is False
    assert result["authority"]["approval_consumed"] is False
    assert result["authority"]["protected_file_mutation_performed"] is False
    assert result["authority"]["canonical_mutation_performed"] is False


def test_natural_language_main_control_plane_routes_to_authority_catalog(tmp_path: Path) -> None:
    from runtime.hermes.studio_chat_capabilities import try_handle_studio_chat_capability

    result = try_handle_studio_chat_capability(
        "ChaseOS is the main control plane for shell/runtime execution and approval consumption",
        session_id="s6",
        vault_root=tmp_path,
    )

    assert result is not None
    assert result["capability_action"] == "authority"
    assert "ChaseOS main control-plane authority catalog" in result["text"]


def test_capability_request_does_not_spawn_hermes_cli(monkeypatch, tmp_path: Path) -> None:
    import subprocess

    from runtime.hermes.chat_bridge import call_hermes_chat_bridge

    def fail_run(*args, **kwargs):  # pragma: no cover - should never be reached
        raise AssertionError("capability command should not invoke subprocess")

    monkeypatch.setattr(subprocess, "run", fail_run)

    result = call_hermes_chat_bridge("/blockers", vault_root=tmp_path)

    assert result["ok"] is True
    assert result["bridge"] == "hermes_studio_capability_layer"
    assert "Blocker report" in result["text"]


def test_shell_action_envelope_is_preview_only_and_requires_aor(tmp_path: Path) -> None:
    from runtime.hermes.studio_chat_capabilities import try_handle_studio_chat_capability

    result = try_handle_studio_chat_capability(
        "/shell run python -m runtime.cli.main runtime status --runtime all --json",
        session_id="s7",
        vault_root=tmp_path,
    )

    assert result is not None
    assert result["capability_action"] == "shell"
    assert "## Action envelope preview — shell/runtime execution" in result["text"]
    assert "target_effect_allowed_now: `false`" in result["text"]
    assert "agent_bus_task_created: `false`" in result["text"]
    assert "required_executor: `AOR workflow manifest + runtime-owned executor`" in result["text"]
    assert "requested_payload" in result["text"]
    assert result["authority"]["shell_command_performed"] is False
    assert result["authority"]["agent_bus_task_created"] is False


def test_approval_and_promotion_envelopes_do_not_consume_or_mutate(tmp_path: Path) -> None:
    from runtime.hermes.studio_chat_capabilities import try_handle_studio_chat_capability

    approval = try_handle_studio_chat_capability(
        "/approve proposal fingerprint abc123 for graph hygiene run",
        session_id="s8",
        vault_root=tmp_path,
    )
    promotion = try_handle_studio_chat_capability(
        "/promote 03_INPUTS/example.md into 02_KNOWLEDGE/example.md",
        session_id="s9",
        vault_root=tmp_path,
    )

    assert approval is not None
    assert approval["capability_action"] == "approve"
    assert "## Action envelope preview — approval consumption" in approval["text"]
    assert "approval_consumed_now: `false`" in approval["text"]
    assert "exact_once_marker_required: `true`" in approval["text"]
    assert approval["authority"]["approval_consumed"] is False

    assert promotion is not None
    assert promotion["capability_action"] == "promote"
    assert "## Action envelope preview — canonical knowledge promotion" in promotion["text"]
    assert "canonical_mutation_performed_now: `false`" in promotion["text"]
    assert "chaseos_gate_required: `true`" in promotion["text"]
    assert promotion["authority"]["canonical_mutation_performed"] is False


def test_external_send_and_authority_grant_envelopes_are_gated_previews(tmp_path: Path) -> None:
    from runtime.hermes.studio_chat_capabilities import try_handle_studio_chat_capability

    send = try_handle_studio_chat_capability(
        "/send discord:#updates announce the runtime proof is ready",
        session_id="s10",
        vault_root=tmp_path,
    )
    grant = try_handle_studio_chat_capability(
        "/grant-runtime-authority Hermes browser access for Studio QA",
        session_id="s11",
        vault_root=tmp_path,
    )

    assert send is not None
    assert send["capability_action"] == "send"
    assert "## Action envelope preview — external connector sends" in send["text"]
    assert "external_delivery_performed_now: `false`" in send["text"]
    assert "destination_allowlist_required: `true`" in send["text"]

    assert grant is not None
    assert grant["capability_action"] == "grant-runtime-authority"
    assert "## Action envelope preview — granting new runtime authority" in grant["text"]
    assert "runtime_self_authorization_allowed: `false`" in grant["text"]
    assert "governance_patch_required: `true`" in grant["text"]
    assert grant["authority"]["preview_only"] is True
