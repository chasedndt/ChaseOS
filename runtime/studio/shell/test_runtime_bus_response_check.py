"""Tests for runtime_bus_response_check — full-stack liveness verification framework."""
from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Any

import pytest


# ---------------------------------------------------------------------------
# Helpers (mirrors pattern from test_phase11_chat_live_e2e.py)
# ---------------------------------------------------------------------------

def _make_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "00_HOME").mkdir()
    (vault / "00_HOME" / "Now.md").write_text("# Now\n", encoding="utf-8")
    bus_dir = vault / "runtime" / "agent_bus"
    bus_dir.mkdir(parents=True)
    return vault


def _init_bus(vault: Path) -> None:
    from runtime.agent_bus.bus import init_db
    init_db(vault)


def _seed_heartbeat(vault: Path, runtime: str = "Hermes", age_s: float = 30.0) -> None:
    from datetime import datetime, timedelta, timezone
    from runtime.agent_bus.bus import upsert_heartbeat
    now = datetime.now(timezone.utc)
    ts = (now - timedelta(seconds=age_s)).isoformat().replace("+00:00", "Z")
    upsert_heartbeat(vault, runtime=runtime, status="idle", health="ok", now_iso=ts)


def _bus_simulator(vault: Path, runtime: str, response_text: str, *, max_wait_s: float = 15.0) -> threading.Thread:
    """Background thread: claims open tasks for `runtime` and attaches a result."""
    from runtime.agent_bus.bus import list_tasks, claim_task, update_task_status

    def _run() -> None:
        deadline = time.monotonic() + max_wait_s
        while time.monotonic() < deadline:
            try:
                tasks = list_tasks(vault, recipient=runtime) or []
                pending = [t for t in tasks if str(t.get("status", "")).lower() in ("open", "pending")]
                for task in pending:
                    task_id = task["task_id"]
                    claimed = claim_task(vault, task_id=task_id, runtime=runtime)
                    if claimed.get("claimed"):
                        update_task_status(
                            vault,
                            task_id=task_id,
                            runtime=runtime,
                            status="done",
                            event_type="result_attached",
                            message=response_text,
                        )
                        return
            except Exception:
                pass
            time.sleep(0.2)

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return t


def _force_ports_offline(monkeypatch: pytest.MonkeyPatch) -> None:
    """Force all gateway port probes to report offline (for tests that need clean state)."""
    import runtime.studio.phase11_chat_runtime_dispatch_verification as _disp
    monkeypatch.setattr(
        _disp, "_check_gateway_ports",
        lambda _a: {"gateway_port_online": False, "gateway_port_listening": None, "gateway_ports_checked": []},
    )


def _force_ports_online(monkeypatch: pytest.MonkeyPatch, port: int = 18790) -> None:
    """Force all gateway port probes to report online."""
    import runtime.studio.phase11_chat_runtime_dispatch_verification as _disp
    monkeypatch.setattr(
        _disp, "_check_gateway_ports",
        lambda _a: {"gateway_port_online": True, "gateway_port_listening": port, "gateway_ports_checked": [port]},
    )


# ---------------------------------------------------------------------------
# check_runtime tests
# ---------------------------------------------------------------------------

class TestCheckRuntime:
    def test_gateway_and_bus_ok(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """ok=True when port is live and bus round-trip completes."""
        vault = _make_vault(tmp_path)
        _init_bus(vault)
        _seed_heartbeat(vault, "Hermes", age_s=30.0)
        _force_ports_online(monkeypatch, port=18790)
        _bus_simulator(vault, "Hermes", "pong from hermes")

        from runtime.studio.runtime_bus_response_check import check_runtime
        result = check_runtime(vault, "hermes", max_wait_s=12.0)

        assert result["ok"] is True
        assert result["gateway_ok"] is True
        assert result["bus_ok"] is True
        assert result["bus_outcome"] == "complete"
        assert result["result_text"] is not None
        assert "pong from hermes" in (result["result_text"] or "")
        assert result["error"] is None

    def test_gateway_down_bus_fail(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """ok=False when gateway port is offline, even if bus would respond."""
        vault = _make_vault(tmp_path)
        _init_bus(vault)
        _seed_heartbeat(vault, "Hermes", age_s=30.0)
        _force_ports_offline(monkeypatch)
        _bus_simulator(vault, "Hermes", "pong")

        from runtime.studio.runtime_bus_response_check import check_runtime
        result = check_runtime(vault, "hermes", max_wait_s=12.0)

        assert result["ok"] is False
        assert result["gateway_ok"] is False
        assert result["runtime_id"] == "hermes"
        assert result["error"] is not None

    def test_bus_timeout_no_runtime(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """bus_ok=False when no runtime responds within max_wait_s."""
        vault = _make_vault(tmp_path)
        _init_bus(vault)
        _seed_heartbeat(vault, "Hermes", age_s=30.0)
        _force_ports_online(monkeypatch, port=18790)
        # No simulator — task will time out

        from runtime.studio.runtime_bus_response_check import check_runtime
        result = check_runtime(vault, "hermes", max_wait_s=2.0)

        assert result["ok"] is False
        assert result["gateway_ok"] is True
        assert result["bus_ok"] is False
        assert result["bus_outcome"] in ("timeout", "probe_exception", "send_failed")
        assert result["error"] is not None

    def test_result_dict_shape(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Result dict always has all required keys regardless of outcome."""
        vault = _make_vault(tmp_path)
        _init_bus(vault)
        _force_ports_offline(monkeypatch)

        from runtime.studio.runtime_bus_response_check import check_runtime
        result = check_runtime(vault, "hermes", max_wait_s=2.0)

        for key in ("ok", "runtime_id", "gateway_ok", "gateway_port", "bus_ok",
                    "bus_outcome", "bus_elapsed_s", "result_text", "error"):
            assert key in result, f"missing key: {key}"

    def test_runtime_id_preserved(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        vault = _make_vault(tmp_path)
        _init_bus(vault)
        _force_ports_offline(monkeypatch)

        from runtime.studio.runtime_bus_response_check import check_runtime
        result = check_runtime(vault, "openclaw", max_wait_s=2.0)
        assert result["runtime_id"] == "openclaw"

    def test_gateway_port_in_result(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """gateway_port field reflects the port returned by _check_gateway_ports."""
        vault = _make_vault(tmp_path)
        _init_bus(vault)
        _seed_heartbeat(vault, "OpenClaw", age_s=30.0)
        _force_ports_online(monkeypatch, port=18789)
        _bus_simulator(vault, "OpenClaw", "openclaw pong")

        from runtime.studio.runtime_bus_response_check import check_runtime
        result = check_runtime(vault, "openclaw", max_wait_s=12.0)

        assert result["gateway_port"] == 18789

    def test_error_none_on_success(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        vault = _make_vault(tmp_path)
        _init_bus(vault)
        _seed_heartbeat(vault, "Hermes", age_s=30.0)
        _force_ports_online(monkeypatch)
        _bus_simulator(vault, "Hermes", "ack")

        from runtime.studio.runtime_bus_response_check import check_runtime
        result = check_runtime(vault, "hermes", max_wait_s=12.0)
        assert result["ok"] is True
        assert result["error"] is None

    def test_elapsed_s_populated(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """bus_elapsed_s is a non-negative float on completion."""
        vault = _make_vault(tmp_path)
        _init_bus(vault)
        _seed_heartbeat(vault, "Hermes", age_s=30.0)
        _force_ports_online(monkeypatch)
        _bus_simulator(vault, "Hermes", "ack")

        from runtime.studio.runtime_bus_response_check import check_runtime
        result = check_runtime(vault, "hermes", max_wait_s=12.0)
        assert result["bus_elapsed_s"] is not None
        assert isinstance(result["bus_elapsed_s"], (int, float))
        assert result["bus_elapsed_s"] >= 0


# ---------------------------------------------------------------------------
# run_runtime_bus_response_check tests
# ---------------------------------------------------------------------------

class TestRunRuntimeBusResponseCheck:
    def test_all_ok(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """ok=True when all runtimes pass gateway + bus checks."""
        vault = _make_vault(tmp_path)
        _init_bus(vault)
        _seed_heartbeat(vault, "Hermes", age_s=30.0)
        _seed_heartbeat(vault, "OpenClaw", age_s=30.0)
        _force_ports_online(monkeypatch, port=18790)
        _bus_simulator(vault, "Hermes", "hi back from hermes")
        _bus_simulator(vault, "OpenClaw", "hi back from openclaw")

        from runtime.studio.runtime_bus_response_check import run_runtime_bus_response_check
        report = run_runtime_bus_response_check(vault, max_wait_s=15.0)

        assert report["ok"] is True
        assert report["any_ok"] is True
        assert report["summary"]["responding_bus"] == 2
        assert "ALL RUNTIMES LIVE" in report["status"]

    def test_partial_ok(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """any_ok=True, ok=False when one runtime passes and one fails gateway."""
        call_count: dict[str, int] = {}

        def _fake_gateway(adapter_id: str) -> dict:
            call_count[adapter_id] = call_count.get(adapter_id, 0) + 1
            if adapter_id == "hermes":
                return {"gateway_port_online": True, "gateway_port_listening": 18790, "gateway_ports_checked": [18790]}
            return {"gateway_port_online": False, "gateway_port_listening": None, "gateway_ports_checked": []}

        import runtime.studio.phase11_chat_runtime_dispatch_verification as _disp
        monkeypatch.setattr(_disp, "_check_gateway_ports", _fake_gateway)

        vault = _make_vault(tmp_path)
        _init_bus(vault)
        _seed_heartbeat(vault, "Hermes", age_s=30.0)
        _bus_simulator(vault, "Hermes", "hermes pong")

        from runtime.studio.runtime_bus_response_check import run_runtime_bus_response_check
        report = run_runtime_bus_response_check(vault, max_wait_s=15.0)

        assert report["ok"] is False
        assert report["any_ok"] is True
        assert "PARTIAL" in report["status"] or "hermes" in report["status"].lower()

    def test_none_ok(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """ok=False, any_ok=False when all runtimes fail gateway check."""
        vault = _make_vault(tmp_path)
        _init_bus(vault)
        _force_ports_offline(monkeypatch)

        from runtime.studio.runtime_bus_response_check import run_runtime_bus_response_check
        report = run_runtime_bus_response_check(vault, runtimes=["hermes", "openclaw"], max_wait_s=2.0)

        assert report["ok"] is False
        assert report["summary"]["online_gateway"] == 0

    def test_single_runtime(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Passing runtimes=['hermes'] checks only hermes."""
        vault = _make_vault(tmp_path)
        _init_bus(vault)
        _seed_heartbeat(vault, "Hermes", age_s=30.0)
        _force_ports_online(monkeypatch)
        _bus_simulator(vault, "Hermes", "hermes only")

        from runtime.studio.runtime_bus_response_check import run_runtime_bus_response_check
        report = run_runtime_bus_response_check(vault, runtimes=["hermes"], max_wait_s=15.0)

        assert report["summary"]["total"] == 1
        assert report["results"][0]["runtime_id"] == "hermes"

    def test_report_shape(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Report dict has all required top-level keys."""
        vault = _make_vault(tmp_path)
        _init_bus(vault)
        _force_ports_offline(monkeypatch)

        from runtime.studio.runtime_bus_response_check import run_runtime_bus_response_check
        report = run_runtime_bus_response_check(vault, runtimes=["hermes"], max_wait_s=2.0)

        for key in ("ok", "any_ok", "surface", "model_version", "generated_at_utc",
                    "status", "runtimes_checked", "results", "summary", "authority"):
            assert key in report, f"missing key: {key}"

    def test_summary_shape(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Summary dict has all required keys."""
        vault = _make_vault(tmp_path)
        _init_bus(vault)
        _force_ports_offline(monkeypatch)

        from runtime.studio.runtime_bus_response_check import run_runtime_bus_response_check
        report = run_runtime_bus_response_check(vault, runtimes=["hermes"], max_wait_s=2.0)
        summary = report["summary"]

        for key in ("total", "online_gateway", "responding_bus", "all_ok"):
            assert key in summary, f"missing summary key: {key}"

    def test_authority_flags(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Authority block marks agent_bus_task_write_performed=True."""
        vault = _make_vault(tmp_path)
        _init_bus(vault)
        _force_ports_offline(monkeypatch)

        from runtime.studio.runtime_bus_response_check import run_runtime_bus_response_check
        report = run_runtime_bus_response_check(vault, runtimes=["hermes"], max_wait_s=2.0)
        auth = report["authority"]

        assert auth["agent_bus_task_write_performed"] is True
        assert auth["canonical_mutation_performed"] is False
        assert auth["approval_consumed"] is False

    def test_parallel_and_sequential_same_count(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """parallel=True and parallel=False both produce the same runtime count."""
        (tmp_path / "par").mkdir()
        (tmp_path / "seq").mkdir()
        vault_par = _make_vault(tmp_path / "par")
        vault_seq = _make_vault(tmp_path / "seq")
        for v in (vault_par, vault_seq):
            _init_bus(v)
        _force_ports_offline(monkeypatch)

        from runtime.studio.runtime_bus_response_check import run_runtime_bus_response_check
        r_par = run_runtime_bus_response_check(vault_par, runtimes=["hermes", "openclaw"], max_wait_s=2.0, parallel=True)
        r_seq = run_runtime_bus_response_check(vault_seq, runtimes=["hermes", "openclaw"], max_wait_s=2.0, parallel=False)

        assert r_par["summary"]["total"] == r_seq["summary"]["total"] == 2

    def test_generated_at_utc(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        vault = _make_vault(tmp_path)
        _init_bus(vault)
        _force_ports_offline(monkeypatch)

        from runtime.studio.runtime_bus_response_check import run_runtime_bus_response_check
        report = run_runtime_bus_response_check(vault, runtimes=["hermes"], max_wait_s=2.0)
        assert report["generated_at_utc"].endswith("Z")

    def test_gateway_up_bus_unresponsive_status(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """GATEWAY UP / BUS UNRESPONSIVE when ports live but no runtime responds."""
        vault = _make_vault(tmp_path)
        _init_bus(vault)
        _seed_heartbeat(vault, "Hermes", age_s=30.0)
        _seed_heartbeat(vault, "OpenClaw", age_s=30.0)
        _force_ports_online(monkeypatch)
        # No simulator — both time out on bus

        from runtime.studio.runtime_bus_response_check import run_runtime_bus_response_check
        report = run_runtime_bus_response_check(vault, runtimes=["hermes", "openclaw"], max_wait_s=2.0)

        assert report["ok"] is False
        assert report["summary"]["online_gateway"] == 2
        assert report["summary"]["responding_bus"] == 0

    def test_runtimes_checked_in_report(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        vault = _make_vault(tmp_path)
        _init_bus(vault)
        _force_ports_offline(monkeypatch)

        from runtime.studio.runtime_bus_response_check import run_runtime_bus_response_check
        report = run_runtime_bus_response_check(vault, runtimes=["hermes", "openclaw"], max_wait_s=2.0)
        assert set(report["runtimes_checked"]) == {"hermes", "openclaw"}

    def test_default_runtimes_hermes_and_openclaw(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        vault = _make_vault(tmp_path)
        _init_bus(vault)
        _force_ports_offline(monkeypatch)

        from runtime.studio.runtime_bus_response_check import run_runtime_bus_response_check
        report = run_runtime_bus_response_check(vault, max_wait_s=2.0)
        assert set(report["runtimes_checked"]) == {"hermes", "openclaw"}

    def test_no_runtimes_reachable_status(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        vault = _make_vault(tmp_path)
        _init_bus(vault)
        _force_ports_offline(monkeypatch)

        from runtime.studio.runtime_bus_response_check import run_runtime_bus_response_check
        report = run_runtime_bus_response_check(vault, max_wait_s=2.0)
        assert "NO RUNTIMES REACHABLE" in report["status"]

    def test_openclaw_responds(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """OpenClaw runtime round-trip succeeds when gateway+bus are both OK."""
        vault = _make_vault(tmp_path)
        _init_bus(vault)
        _seed_heartbeat(vault, "OpenClaw", age_s=30.0)
        _force_ports_online(monkeypatch, port=18789)
        _bus_simulator(vault, "OpenClaw", "openclaw ack")

        from runtime.studio.runtime_bus_response_check import run_runtime_bus_response_check
        report = run_runtime_bus_response_check(vault, runtimes=["openclaw"], max_wait_s=12.0)

        assert report["ok"] is True
        oc = report["results"][0]
        assert oc["runtime_id"] == "openclaw"
        assert oc["bus_ok"] is True
        assert oc["result_text"] is not None


# ---------------------------------------------------------------------------
# API method tests
# ---------------------------------------------------------------------------

class TestApiMethod:
    def test_envelope_shape(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """StudioAPI.get_runtime_bus_response_check returns ok/status/data envelope."""
        vault = _make_vault(tmp_path)
        _init_bus(vault)
        _force_ports_offline(monkeypatch)

        from runtime.studio.shell.api import StudioAPI
        api = StudioAPI(str(vault))
        result = api.get_runtime_bus_response_check(max_wait_s=2.0)

        assert "ok" in result
        assert "status" in result
        assert "data" in result

    def test_single_runtime_via_api(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Passing runtimes=['hermes'] checks only hermes."""
        vault = _make_vault(tmp_path)
        _init_bus(vault)
        _force_ports_offline(monkeypatch)

        from runtime.studio.shell.api import StudioAPI
        api = StudioAPI(str(vault))
        result = api.get_runtime_bus_response_check(runtimes=["hermes"], max_wait_s=2.0)

        data = result.get("data") or {}
        assert data.get("summary", {}).get("total") == 1

    def test_api_ok_when_runtime_responds(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """API method returns ok=True in data when runtime responds on bus."""
        vault = _make_vault(tmp_path)
        _init_bus(vault)
        _seed_heartbeat(vault, "Hermes", age_s=30.0)
        _force_ports_online(monkeypatch)
        _bus_simulator(vault, "Hermes", "api ack")

        from runtime.studio.shell.api import StudioAPI
        api = StudioAPI(str(vault))
        result = api.get_runtime_bus_response_check(runtimes=["hermes"], max_wait_s=12.0)

        data = result.get("data") or {}
        assert data.get("ok") is True
