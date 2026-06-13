"""Tests for Phase 11 Chat runtime dispatch verification surface."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.studio.phase11_chat_runtime_dispatch_verification import (
    NEXT_RECOMMENDED_PASS,
    PASS_ID,
    SURFACE_ID,
    build_phase11_chat_runtime_dispatch_verification,
    build_chat_runtime_availability,
)


def test_verification_returns_ok_when_chain_intact(tmp_path: Path) -> None:
    result = build_phase11_chat_runtime_dispatch_verification(tmp_path)
    assert result["ok"] is True


def test_verification_correct_pass_id(tmp_path: Path) -> None:
    result = build_phase11_chat_runtime_dispatch_verification(tmp_path)
    assert result["pass"] == PASS_ID
    assert PASS_ID == "phase11-chat-runtime-dispatch-verification"


def test_verification_correct_surface_id(tmp_path: Path) -> None:
    result = build_phase11_chat_runtime_dispatch_verification(tmp_path)
    assert result["surface"] == SURFACE_ID
    assert SURFACE_ID == "phase11_chat_runtime_dispatch_verification"


def test_verification_is_read_only(tmp_path: Path) -> None:
    result = build_phase11_chat_runtime_dispatch_verification(tmp_path)
    assert result["read_only"] is True
    auth = result["authority"]
    assert auth["read_only"] is True
    assert auth["provider_call_performed"] is False
    assert auth["agent_bus_task_write_performed"] is False
    assert auth["approval_consumed"] is False
    assert auth["canonical_mutation_performed"] is False


def test_verification_correct_next_recommended_pass(tmp_path: Path) -> None:
    result = build_phase11_chat_runtime_dispatch_verification(tmp_path)
    assert result["summary"]["next_recommended_pass"] == NEXT_RECOMMENDED_PASS
    assert NEXT_RECOMMENDED_PASS == "agent-bus-or-canonical-writeback-readiness"


def test_verification_summary_keys_present(tmp_path: Path) -> None:
    result = build_phase11_chat_runtime_dispatch_verification(tmp_path)
    summary = result["summary"]
    assert "dispatch_chain_wired" in summary
    assert "send_message_wired" in summary
    assert "poll_result_wired" in summary
    assert "agent_bus_storage_accessible" in summary
    assert "any_runtime_online" in summary
    assert "next_recommended_pass" in summary
    assert "next_step" in summary


def test_verification_dispatch_checks_present(tmp_path: Path) -> None:
    result = build_phase11_chat_runtime_dispatch_verification(tmp_path)
    checks = result["dispatch_checks"]
    assert "send_chat_message_importable" in checks
    assert "poll_chat_result_importable" in checks
    assert "send_chat_message_callable" in checks
    assert "poll_chat_result_callable" in checks


def test_verification_reports_send_and_poll_callable(tmp_path: Path) -> None:
    result = build_phase11_chat_runtime_dispatch_verification(tmp_path)
    checks = result["dispatch_checks"]
    assert checks["send_chat_message_callable"] is True
    assert checks["poll_chat_result_callable"] is True


def test_verification_is_json_serializable(tmp_path: Path) -> None:
    result = build_phase11_chat_runtime_dispatch_verification(tmp_path)
    json.dumps(result, default=str)


def test_verification_contains_runtime_availability(tmp_path: Path) -> None:
    result = build_phase11_chat_runtime_dispatch_verification(tmp_path)
    avail = result["runtime_availability"]
    assert avail["ok"] is True
    assert "runtimes" in avail
    assert isinstance(avail["runtimes"], list)
    adapter_ids = {r["adapter_id"] for r in avail["runtimes"]}
    assert "hermes" in adapter_ids
    assert "openclaw" in adapter_ids
    assert "claude-code" in adapter_ids


def test_chat_runtime_availability_all_adapters(tmp_path: Path) -> None:
    avail = build_chat_runtime_availability(tmp_path)
    assert avail["ok"] is True
    adapter_ids = {r["adapter_id"] for r in avail["runtimes"]}
    assert {"hermes", "openclaw", "claude-code", "direct-provider"}.issubset(adapter_ids)
    for runtime in avail["runtimes"]:
        if runtime.get("is_bus_runtime"):
            assert "freshness" in runtime
            assert "pip_class" in runtime


def test_chat_runtime_availability_is_passive_for_chat_page_load(tmp_path: Path, monkeypatch) -> None:
    import runtime.studio.phase11_chat_runtime_dispatch_verification as _m
    import runtime.studio.runtime_live_status as _live

    monkeypatch.setattr(
        _m,
        "_check_gateway_ports",
        lambda _adapter: {
            "gateway_port_online": False,
            "gateway_port_listening": None,
            "gateway_ports_checked": [],
        },
    )
    monkeypatch.setattr(
        _live,
        "_wsl_process_status",
        lambda _runtime: (_ for _ in ()).throw(
            AssertionError("Chat availability must not invoke wsl.exe process probes")
        ),
    )
    (tmp_path / "runtime" / "lifecycle").mkdir(parents=True)

    avail = build_chat_runtime_availability(tmp_path)
    assert avail["runtime_by_adapter"]["hermes"]["wsl_process_probe_enabled"] is False


def test_verification_api_method_returns_ok(tmp_path: Path) -> None:
    from runtime.studio.shell.api import StudioAPI
    api = StudioAPI(tmp_path)
    result = api.get_phase11_chat_runtime_dispatch_verification()
    assert result["ok"] is True
    assert result["data"]["pass"] == PASS_ID


def test_verification_cli_produces_json(tmp_path: Path) -> None:
    import subprocess, sys
    proc = subprocess.run(
        [sys.executable, "-m", "runtime.cli.main", "studio",
         "phase11-chat-runtime-dispatch-verification", "--json",
         "--vault-root", str(tmp_path)],
        capture_output=True, text=True, cwd=str(tmp_path.parent),
    )
    assert proc.returncode == 0
    data = json.loads(proc.stdout)
    assert data["result"]["pass"] == PASS_ID
    assert data["result"]["summary"]["next_recommended_pass"] == NEXT_RECOMMENDED_PASS


def test_verification_no_files_written(tmp_path: Path) -> None:
    before = set(tmp_path.rglob("*"))
    build_phase11_chat_runtime_dispatch_verification(tmp_path)
    after = set(tmp_path.rglob("*"))
    assert before == after
