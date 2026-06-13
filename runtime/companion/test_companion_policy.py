from __future__ import annotations

from pathlib import Path

from runtime.companion.policy import FORBIDDEN_EFFECTS, classify_companion_comment
from runtime.companion.roster import get_companion, list_companions, validate_roster
from runtime.companion.schema import validate_companion_profile
from runtime.companion.selection import (
    SELECTION_TARGET_PATH,
    SWITCH_LEDGER_PATH,
    get_active_companion,
    preview_companion_switch,
    select_companion,
)


def test_roster_contains_initial_companions() -> None:
    ids = [profile["companion_id"] for profile in list_companions()]
    assert ids == ["hermes", "openclaw", "claude-code", "chaser"]


def test_profiles_validate() -> None:
    report = validate_roster()
    assert report["valid"] is True
    for profile in list_companions():
        assert validate_companion_profile(profile)["valid"] is True


def test_invalid_companion_ids_fail_cleanly(tmp_path: Path) -> None:
    preview = preview_companion_switch(tmp_path, "unknown")
    assert preview["ok"] is False
    assert preview["selection_written"] is False
    assert "invalid_companion_id" in preview["blocked_reasons"]
    try:
        get_companion("unknown")
    except ValueError as exc:
        assert "invalid companion id" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("invalid companion id did not fail")


def test_chaser_is_profiled_but_not_selectable(tmp_path: Path) -> None:
    profile = get_companion("chaser")
    assert profile["current_status"] == "planned"
    preview = preview_companion_switch(tmp_path, "chaser", session_id="chat-1")
    assert preview["ok"] is False
    assert preview["selection_written"] is False
    assert preview["ledger_written"] is False
    assert "companion_unavailable" in preview["blocked_reasons"]


def test_preview_does_not_mutate_state(tmp_path: Path) -> None:
    before = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))
    preview = preview_companion_switch(tmp_path, "openclaw", session_id="chat-1")
    after = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))
    assert preview["ok"] is True
    assert preview["read_only"] is True
    assert preview["selection_written"] is False
    assert preview["ledger_written"] is False
    assert before == after
    assert get_active_companion(tmp_path)["selected_companion_id"] == "hermes"


def test_selection_without_approval_is_blocked(tmp_path: Path) -> None:
    result = select_companion(tmp_path, "openclaw", approved=False, session_id="chat-1")
    assert result["ok"] is False
    assert result["selection_written"] is False
    assert result["ledger_written"] is False
    assert "approval_required" in result["blocked_reasons"]
    assert not (tmp_path / SELECTION_TARGET_PATH).exists()


def test_selection_with_approval_succeeds_and_writes_ledger(tmp_path: Path) -> None:
    result = select_companion(
        tmp_path,
        "openclaw",
        approved=True,
        approved_by="operator",
        session_id="chat-1",
        notes="approved companion switch",
    )
    assert result["ok"] is True
    assert result["selection_written"] is True
    assert result["ledger_written"] is True
    assert (tmp_path / SELECTION_TARGET_PATH).is_file()
    assert (tmp_path / SWITCH_LEDGER_PATH).is_file()
    active = get_active_companion(tmp_path, session_id="chat-1")
    assert active["selected_companion_id"] == "openclaw"
    assert result["ledger_entry"]["previous_companion"] == "hermes"
    assert result["ledger_entry"]["new_companion"] == "openclaw"


def test_selection_never_changes_routing_memory_or_permissions(tmp_path: Path) -> None:
    result = select_companion(tmp_path, "claude-code", approved=True, session_id="chat-2")
    assert result["selection_payload"]["routing_changed"] is False
    assert result["selection_payload"]["memory_changed"] is False
    assert result["selection_payload"]["permissions_changed"] is False
    assert result["authority"]["routing_changed"] is False
    assert result["authority"]["memory_changed"] is False
    assert result["authority"]["permissions_changed"] is False


def test_stats_and_rarity_do_not_change_capability() -> None:
    for profile in list_companions():
        assert profile["rarity"]["cosmetic_only"] is True
        assert profile["rarity"]["changes_capability"] is False
        for stat in profile["stats"].values():
            assert stat["cosmetic_only"] is True
            assert stat["changes_capability"] is False


def test_forbidden_effects_include_authority_boundaries() -> None:
    profile = get_companion("hermes")
    assert set(FORBIDDEN_EFFECTS).issubset(set(profile["forbidden_effects"]))
    assert "runtime_routing_changes" in profile["forbidden_effects"]
    assert "canonical_state_mutation" in profile["forbidden_effects"]


def test_companion_commentary_is_non_authoritative() -> None:
    comment = classify_companion_comment("Keep this gated.", companion_id="openclaw")
    assert comment["classification"] == "non_authoritative_commentary"
    assert comment["is_executable_instruction"] is False
    assert comment["grants_permission"] is False
    assert comment["changes_routing"] is False
    assert comment["writes_memory"] is False
    assert comment["mutates_canonical_state"] is False
