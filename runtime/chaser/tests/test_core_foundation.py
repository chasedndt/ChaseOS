from __future__ import annotations

from pathlib import Path

from runtime.chaser.agent import ChaserAgent, preview_chaser_task
from runtime.chaser.artifacts import build_artifact_manifest_item, build_manifest
from runtime.chaser.board import create_board_card, validate_board_card
from runtime.chaser.memory import build_memory_boundary, validate_memory_reference
from runtime.chaser.policies import assert_no_authority_change, build_policy_snapshot
from runtime.chaser.profiles import get_profile, list_profiles, validate_profile_view
from runtime.chaser.toolsets import get_toolset, list_toolsets, validate_toolset_view


def _files(root: Path) -> set[str]:
    return {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}


def test_policy_snapshot_is_no_authority() -> None:
    snapshot = build_policy_snapshot()
    assert snapshot["available_for_runtime_activation"] is False
    assert snapshot["read_only"] is True
    assert all(value is False for value in snapshot["authority"].values())
    assert assert_no_authority_change()["ok"] is True
    blocked = assert_no_authority_change({"provider_called": True})
    assert blocked["ok"] is False
    assert "authority_change_forbidden:provider_called" in blocked["blocked_reasons"]


def test_profiles_are_descriptive_only() -> None:
    profiles = list_profiles()
    assert {profile["profile_id"] for profile in profiles} >= {"default", "research", "ops", "local", "builder"}
    for profile in profiles:
        assert validate_profile_view(profile)["ok"] is True
        assert profile["grants_permission"] is False
        assert profile["activates_runtime"] is False


def test_toolsets_do_not_execute_or_write() -> None:
    toolsets = list_toolsets()
    assert {toolset["toolset_id"] for toolset in toolsets} >= {"none", "terminal-preview", "gateway-diagnostic"}
    for toolset in toolsets:
        assert validate_toolset_view(toolset)["ok"] is True
        assert toolset["executes_now"] is False
        assert toolset["writes_now"] is False


def test_memory_boundary_and_candidate_are_no_write(tmp_path: Path) -> None:
    before = _files(tmp_path)
    boundary = build_memory_boundary(tmp_path)
    after = _files(tmp_path)
    assert before == after
    assert boundary["memory_writes_allowed_now"] is False
    valid = validate_memory_reference(
        {"reference_class": "profile_reference", "target": "06_AGENTS/ChaserAgent-Runtime-Profile.md"}
    )
    assert valid["ok"] is True
    assert valid["write_allowed_now"] is False
    denied = validate_memory_reference({"reference_class": "credential", "target": "secret", "secret": True})
    assert denied["ok"] is False


def test_board_card_contract_validates() -> None:
    card = create_board_card(operator_intent="Prepare a Chaser runtime plan", result_shape="proposal")
    assert card["task_id"].startswith("chaser-")
    assert card["valid"] is True
    assert validate_board_card(card)["ok"] is True
    invalid = create_board_card(operator_intent="Bad shape", result_shape="execute")
    assert invalid["valid"] is False
    assert "invalid_result_shape" in invalid["validation"]["errors"]


def test_artifact_manifest_is_untrusted_and_no_authority() -> None:
    item = build_artifact_manifest_item(artifact_type="proposal", title="Plan", source="test")
    manifest = build_manifest([item])
    assert item["trust_tier"] == "Tier 4"
    assert item["valid"] is True
    assert manifest["ok"] is True
    assert all(value is False for value in item["authority"].values())


def test_preview_chaser_task_is_in_memory_only(tmp_path: Path) -> None:
    before = _files(tmp_path)
    preview = preview_chaser_task(
        operator_intent="Draft task board card",
        vault_root=str(tmp_path),
        profile_id="ops",
        toolset_id="gateway-diagnostic",
    )
    after = _files(tmp_path)
    assert before == after
    assert preview["ok"] is True
    assert preview["status"] == "preview_only_not_live"
    assert preview["external_effects_performed"] is False
    assert preview["authority_ok"] is True
    assert all(value is False for value in preview["authority"].values())


def test_chaser_agent_facade_preview(tmp_path: Path) -> None:
    agent = ChaserAgent(vault_root=str(tmp_path))
    preview = agent.preview_task(operator_intent="Summarize board readiness", toolset_id="none")
    assert preview["ok"] is True
    assert preview["board_card"]["proposed_runtime"] == "chaser"
    assert get_profile("missing")["profile_id"] == "default"
    assert get_toolset("missing")["toolset_id"] == "none"
