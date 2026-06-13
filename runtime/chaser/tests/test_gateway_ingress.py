from __future__ import annotations

from pathlib import Path

from runtime.chaser.gateway import (
    build_gateway_ingress_contract,
    handle_gateway_ingress,
)
from runtime.studio.service import StudioService


def _auth(**overrides) -> dict:
    data = {
        "mode": "local_operator",
        "operator_confirmed": True,
        "approval_queue_write_confirmed": False,
        "operator_approved_terminal_write": False,
    }
    data.update(overrides)
    return data


def test_gateway_ingress_contract_preserves_control_plane_boundaries(tmp_path: Path) -> None:
    contract = build_gateway_ingress_contract(tmp_path)

    assert contract["ok"] is True
    assert contract["surface"] == "chaser_gateway_ingress"
    assert contract["mode"] == "internal_structured_ingress"
    assert contract["authority"]["gateway_network_server_now"] is False
    assert contract["authority"]["studio_execution_now"] is False
    assert contract["authority"]["agent_bus_write_now"] is False
    assert contract["authority"]["provider_call_now"] is False
    assert contract["authority"]["canonical_writeback_now"] is False
    assert contract["studio_contract"]["studio_ingress_execution_api"] is False
    assert {item["intent"] for item in contract["supported_intents"]} >= {
        "terminal.propose",
        "terminal.approval_request_write",
        "terminal.execute_approval",
    }


def test_gateway_ingress_rejects_unsafe_ids_and_missing_auth(tmp_path: Path) -> None:
    unsafe = handle_gateway_ingress(
        tmp_path,
        {
            "request_id": "../bad",
            "session_id": "../session",
            "intent": "terminal.propose",
            "payload": {"command": "pwd", "cwd": str(tmp_path)},
            "auth": _auth(),
        },
    )
    missing_auth = handle_gateway_ingress(
        tmp_path,
        {
            "request_id": "safe-request",
            "intent": "terminal.propose",
            "payload": {"command": "pwd", "cwd": str(tmp_path)},
            "auth": {},
        },
    )

    assert unsafe["ok"] is False
    assert "unsafe_request_id" in unsafe["blockers"]
    assert "unsafe_session_id" in unsafe["blockers"]
    assert missing_auth["ok"] is False
    assert "auth_mode_not_local_operator" in missing_auth["blockers"]
    assert "local_operator_confirmation_required" in missing_auth["blockers"]
    assert unsafe["authority"]["agent_bus_write_now"] is False
    assert missing_auth["authority"]["provider_call_now"] is False


def test_gateway_terminal_propose_is_preview_only(tmp_path: Path) -> None:
    result = handle_gateway_ingress(
        tmp_path,
        {
            "request_id": "gateway-propose",
            "intent": "terminal.propose",
            "payload": {"command": "mkdir example", "cwd": str(tmp_path)},
            "auth": _auth(),
        },
    )

    assert result["ok"] is True
    assert result["intent"] == "terminal.propose"
    assert result["result"]["status"] == "approval_required_future_n6"
    assert result["authority"]["terminal_execution_now"] is False
    assert result["authority"]["approval_queue_write_now"] is False
    assert result["authority"]["agent_bus_write_now"] is False
    assert not (tmp_path / "example").exists()
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_gateway_approval_request_write_requires_separate_confirmation(tmp_path: Path) -> None:
    blocked = handle_gateway_ingress(
        tmp_path,
        {
            "request_id": "gateway-approval-block",
            "intent": "terminal.approval_request_write",
            "payload": {"command": "mkdir example", "cwd": str(tmp_path)},
            "auth": _auth(),
        },
    )
    written = handle_gateway_ingress(
        tmp_path,
        {
            "request_id": "gateway-approval-write",
            "intent": "terminal.approval_request_write",
            "payload": {"command": "mkdir example", "cwd": str(tmp_path)},
            "auth": _auth(approval_queue_write_confirmed=True),
        },
    )

    assert blocked["ok"] is False
    assert "approval_queue_write_confirmation_required" in blocked["blockers"]
    assert written["ok"] is True
    assert written["result"]["approval_request_written"] is True
    assert written["authority"]["approval_queue_write_now"] is True
    assert written["authority"]["terminal_execution_now"] is False
    assert written["authority"]["agent_bus_write_now"] is False
    assert (tmp_path / written["result"]["approval_path"]).exists()
    assert not (tmp_path / "example").exists()
    assert not (tmp_path / "runtime" / "agent_bus").exists()


def test_gateway_execute_approval_wraps_n6_confirmation_and_duplicates(tmp_path: Path) -> None:
    write_request = handle_gateway_ingress(
        tmp_path,
        {
            "request_id": "gateway-exec-request",
            "intent": "terminal.approval_request_write",
            "payload": {"command": "mkdir example", "cwd": str(tmp_path)},
            "auth": _auth(approval_queue_write_confirmed=True),
        },
    )["result"]
    StudioService(tmp_path).approve(write_request["approval_id"], reviewed_by="operator")

    blocked = handle_gateway_ingress(
        tmp_path,
        {
            "request_id": "gateway-exec-blocked",
            "intent": "terminal.execute_approval",
            "payload": {
                "approval_id": write_request["approval_id"],
                "expected_proposal_id": write_request["proposal_id"],
            },
            "auth": _auth(operator_approved_terminal_write=True),
        },
    )
    assert blocked["ok"] is False
    assert "payload_confirm_approved_terminal_write_required" in blocked["blockers"]
    assert not (tmp_path / "example").exists()

    executed = handle_gateway_ingress(
        tmp_path,
        {
            "request_id": "gateway-exec-confirmed",
            "intent": "terminal.execute_approval",
            "payload": {
                "approval_id": write_request["approval_id"],
                "expected_proposal_id": write_request["proposal_id"],
                "confirm_approved_terminal_write": True,
            },
            "auth": _auth(operator_approved_terminal_write=True),
        },
    )
    duplicate = handle_gateway_ingress(
        tmp_path,
        {
            "request_id": "gateway-exec-duplicate",
            "intent": "terminal.execute_approval",
            "payload": {
                "approval_id": write_request["approval_id"],
                "expected_proposal_id": write_request["proposal_id"],
                "confirm_approved_terminal_write": True,
            },
            "auth": _auth(operator_approved_terminal_write=True),
        },
    )

    assert executed["ok"] is True
    assert executed["authority"]["terminal_execution_now"] is True
    assert executed["authority"]["approval_consumption_now"] is True
    assert executed["authority"]["exact_once_marker_write_now"] is True
    assert executed["authority"]["agent_bus_write_now"] is False
    assert executed["authority"]["provider_call_now"] is False
    assert executed["authority"]["canonical_writeback_now"] is False
    assert (tmp_path / "example").is_dir()
    assert duplicate["ok"] is False
    assert duplicate["authority"]["terminal_execution_now"] is False


def test_gateway_execute_approval_wraps_approved_touch(tmp_path: Path) -> None:
    write_request = handle_gateway_ingress(
        tmp_path,
        {
            "request_id": "gateway-touch-request",
            "intent": "terminal.approval_request_write",
            "payload": {"command": "touch example.txt", "cwd": str(tmp_path)},
            "auth": _auth(approval_queue_write_confirmed=True),
        },
    )["result"]
    StudioService(tmp_path).approve(write_request["approval_id"], reviewed_by="operator")

    executed = handle_gateway_ingress(
        tmp_path,
        {
            "request_id": "gateway-touch-confirmed",
            "intent": "terminal.execute_approval",
            "payload": {
                "approval_id": write_request["approval_id"],
                "expected_proposal_id": write_request["proposal_id"],
                "confirm_approved_terminal_write": True,
            },
            "auth": _auth(operator_approved_terminal_write=True),
        },
    )

    assert executed["ok"] is True
    assert executed["result"]["supported_write_executable"] == "touch"
    assert executed["authority"]["terminal_execution_now"] is True
    assert executed["authority"]["approval_consumption_now"] is True
    assert executed["authority"]["exact_once_marker_write_now"] is True
    assert executed["authority"]["agent_bus_write_now"] is False
    assert executed["authority"]["provider_call_now"] is False
    assert executed["authority"]["canonical_writeback_now"] is False
    assert (tmp_path / "example.txt").is_file()


def test_gateway_execute_approval_wraps_approved_cp_alias(tmp_path: Path) -> None:
    (tmp_path / "source.txt").write_text("copied through gateway\n", encoding="utf-8")
    write_request = handle_gateway_ingress(
        tmp_path,
        {
            "request_id": "gateway-cp-request",
            "intent": "terminal.approval_request_write",
            "payload": {"command": "cp source.txt copied.txt", "cwd": str(tmp_path)},
            "auth": _auth(approval_queue_write_confirmed=True),
        },
    )["result"]
    StudioService(tmp_path).approve(write_request["approval_id"], reviewed_by="operator")

    executed = handle_gateway_ingress(
        tmp_path,
        {
            "request_id": "gateway-cp-confirmed",
            "intent": "terminal.execute_approval",
            "payload": {
                "approval_id": write_request["approval_id"],
                "expected_proposal_id": write_request["proposal_id"],
                "confirm_approved_terminal_write": True,
            },
            "auth": _auth(operator_approved_terminal_write=True),
        },
    )

    assert executed["ok"] is True
    assert executed["result"]["supported_write_executable"] == "cp"
    assert executed["result"]["source_path"] == "source.txt"
    assert executed["result"]["target_path"] == "copied.txt"
    assert executed["authority"]["terminal_execution_now"] is True
    assert executed["authority"]["approval_consumption_now"] is True
    assert executed["authority"]["exact_once_marker_write_now"] is True
    assert executed["authority"]["agent_bus_write_now"] is False
    assert executed["authority"]["provider_call_now"] is False
    assert executed["authority"]["canonical_writeback_now"] is False
    assert (tmp_path / "source.txt").read_text(encoding="utf-8") == "copied through gateway\n"
    assert (tmp_path / "copied.txt").read_text(encoding="utf-8") == "copied through gateway\n"
