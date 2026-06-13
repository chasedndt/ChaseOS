"""Tests for Phase 11 Chat Live E2E pass.

Covers:
  - run_chat_probe() send+poll cycle
  - Bus round-trip: send → simulate runtime claim+respond → poll → verify result
  - build_phase11_chat_live_e2e_verification() orchestration
  - api.py get_chat_live_e2e_verification() envelope
  - panel_registry flags
"""
from __future__ import annotations

import sqlite3
import tempfile
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "00_HOME").mkdir()
    (vault / "00_HOME" / "Now.md").write_text("# Now\n", encoding="utf-8")
    bus_dir = vault / "runtime" / "agent_bus"
    bus_dir.mkdir(parents=True)
    return vault


def _init_bus(vault: Path) -> Path:
    """Create the agent_bus SQLite schema in the vault."""
    from runtime.agent_bus.bus import init_db
    init_db(vault)
    return vault / "runtime" / "agent_bus" / "agent_bus.sqlite"


def _seed_heartbeat(vault: Path, runtime: str = "Hermes", age_s: float = 30.0) -> None:
    """Insert a recent heartbeat row for a runtime via the bus public API."""
    from runtime.agent_bus.bus import upsert_heartbeat
    now = datetime.now(timezone.utc)
    ts = (now - timedelta(seconds=age_s)).isoformat().replace("+00:00", "Z")
    upsert_heartbeat(
        vault,
        runtime=runtime,
        status="idle",
        health="ok",
        now_iso=ts,
    )


def _bus_simulator(vault: Path, runtime: str, response_text: str,
                   *, max_wait_s: float = 10.0) -> None:
    """Background thread: watches for a task addressed to `runtime`, claims and responds."""
    from runtime.agent_bus.bus import list_tasks, claim_task, update_task_status

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


# ── run_chat_probe ────────────────────────────────────────────────────────────

class TestRunChatProbe:
    def _vault_with_bus(self, tmp_path):
        vault = _make_vault(tmp_path)
        _init_bus(vault)
        _seed_heartbeat(vault, "Hermes", age_s=30)
        return vault

    def test_send_creates_task_on_bus(self, tmp_path):
        from runtime.studio.phase11_chat_live_e2e import run_chat_probe
        from runtime.agent_bus.bus import list_tasks

        vault = self._vault_with_bus(tmp_path)
        sim = threading.Thread(
            target=_bus_simulator,
            args=(vault, "Hermes", "[Hermes ack] hi received"),
            daemon=True,
        )
        sim.start()
        result = run_chat_probe(vault, "hi", runtime_id="hermes", max_wait_s=8.0, poll_interval_s=0.2)
        sim.join(timeout=2)

        assert result["task_id"] is not None
        assert result["recipient"] == "Hermes"

    def test_round_trip_complete(self, tmp_path):
        from runtime.studio.phase11_chat_live_e2e import run_chat_probe

        vault = self._vault_with_bus(tmp_path)
        response = "[Hermes bounded ack] Chat message received: hi"
        sim = threading.Thread(
            target=_bus_simulator,
            args=(vault, "Hermes", response),
            daemon=True,
        )
        sim.start()
        result = run_chat_probe(vault, "hi", runtime_id="hermes", max_wait_s=8.0, poll_interval_s=0.2)
        sim.join(timeout=2)

        assert result["ok"] is True
        assert result["probe_outcome"] == "complete"
        assert result["result_text"] is not None
        assert "hi" in result["result_text"] or "ack" in result["result_text"].lower()

    def test_probe_timeout_when_no_runtime(self, tmp_path):
        from runtime.studio.phase11_chat_live_e2e import run_chat_probe

        vault = self._vault_with_bus(tmp_path)
        # No simulator thread — no one claims the task
        result = run_chat_probe(vault, "hi", runtime_id="hermes", max_wait_s=1.0, poll_interval_s=0.2)

        assert result["ok"] is False
        assert result["probe_outcome"] == "timeout"
        assert result["task_id"] is not None  # task WAS created, just not answered

    def test_probe_normalizes_empty_message(self, tmp_path):
        # run_chat_probe normalizes "" → "hi" before calling send_chat_message,
        # so an empty string still creates a task (no send_failed).
        from runtime.studio.phase11_chat_live_e2e import run_chat_probe

        vault = self._vault_with_bus(tmp_path)
        sim = threading.Thread(
            target=_bus_simulator,
            args=(vault, "Hermes", "[Hermes ack] normalized"),
            daemon=True,
        )
        sim.start()
        result = run_chat_probe(vault, "", runtime_id="hermes", max_wait_s=8.0, poll_interval_s=0.2)
        sim.join(timeout=2)

        assert result["task_id"] is not None  # normalized to "hi", task created
        assert result["ok"] is True

    def test_probe_returns_elapsed_s(self, tmp_path):
        from runtime.studio.phase11_chat_live_e2e import run_chat_probe

        vault = self._vault_with_bus(tmp_path)
        sim = threading.Thread(
            target=_bus_simulator,
            args=(vault, "Hermes", "ack"),
            daemon=True,
        )
        sim.start()
        result = run_chat_probe(vault, "hi", runtime_id="hermes", max_wait_s=8.0, poll_interval_s=0.2)
        sim.join(timeout=2)

        assert isinstance(result["elapsed_s"], float)
        assert result["elapsed_s"] >= 0.0

    def test_probe_openclaw_runtime(self, tmp_path):
        from runtime.studio.phase11_chat_live_e2e import run_chat_probe

        vault = self._vault_with_bus(tmp_path)
        _seed_heartbeat(vault, "OpenClaw", age_s=30)
        sim = threading.Thread(
            target=_bus_simulator,
            args=(vault, "OpenClaw", "[OpenClaw ack] received"),
            daemon=True,
        )
        sim.start()
        result = run_chat_probe(vault, "hi", runtime_id="openclaw", max_wait_s=8.0, poll_interval_s=0.2)
        sim.join(timeout=2)

        assert result["recipient"] == "OpenClaw"
        assert result["ok"] is True

    def test_probe_result_text_present(self, tmp_path):
        from runtime.studio.phase11_chat_live_e2e import run_chat_probe

        vault = self._vault_with_bus(tmp_path)
        expected = "hello from hermes runtime"
        sim = threading.Thread(
            target=_bus_simulator,
            args=(vault, "Hermes", expected),
            daemon=True,
        )
        sim.start()
        result = run_chat_probe(vault, "hi", runtime_id="hermes", max_wait_s=8.0, poll_interval_s=0.2)
        sim.join(timeout=2)

        assert result["result_text"] == expected


# ── build_phase11_chat_live_e2e_verification ──────────────────────────────────

class TestBuildLiveE2EVerification:
    def _vault_no_bus(self, tmp_path):
        return _make_vault(tmp_path)

    def _vault_with_bus_no_hb(self, tmp_path):
        vault = _make_vault(tmp_path)
        _init_bus(vault)
        return vault

    def _vault_with_bus_and_hb(self, tmp_path):
        vault = _make_vault(tmp_path)
        _init_bus(vault)
        _seed_heartbeat(vault, "Hermes", age_s=30)
        return vault

    def test_no_bus_blocked(self, tmp_path):
        from runtime.studio.phase11_chat_live_e2e import build_phase11_chat_live_e2e_verification
        vault = self._vault_no_bus(tmp_path)
        result = build_phase11_chat_live_e2e_verification(vault, probe_timeout_s=1.0)

        assert result["ok"] is False
        assert "agent_bus_storage_not_present" in result["blocked_reasons"]
        assert result["checks"]["agent_bus_storage_accessible"] is False

    def test_no_heartbeat_blocked(self, tmp_path, monkeypatch):
        # Monkeypatch port probe so no gateway port appears live in this isolated vault.
        # Without this the test would depend on whether the real gateway is running.
        import runtime.studio.phase11_chat_runtime_dispatch_verification as _disp
        monkeypatch.setattr(
            _disp, "_check_gateway_ports",
            lambda adapter_id: {"gateway_port_online": False, "gateway_port_listening": None, "gateway_ports_checked": []},
        )
        from runtime.studio.phase11_chat_live_e2e import build_phase11_chat_live_e2e_verification
        vault = self._vault_with_bus_no_hb(tmp_path)
        result = build_phase11_chat_live_e2e_verification(vault, probe_timeout_s=1.0)

        assert result["ok"] is False
        assert "no_runtime_daemon_heartbeat_present" in result["blocked_reasons"]
        assert result["checks"]["any_runtime_online"] is False

    def test_imports_always_wired(self, tmp_path):
        from runtime.studio.phase11_chat_live_e2e import build_phase11_chat_live_e2e_verification
        vault = self._vault_no_bus(tmp_path)
        result = build_phase11_chat_live_e2e_verification(vault, probe_timeout_s=1.0)

        assert result["checks"]["send_chat_message_importable"] is True
        assert result["checks"]["poll_chat_result_importable"] is True

    def test_full_round_trip_ok(self, tmp_path):
        from runtime.studio.phase11_chat_live_e2e import build_phase11_chat_live_e2e_verification

        vault = self._vault_with_bus_and_hb(tmp_path)
        sim = threading.Thread(
            target=_bus_simulator,
            args=(vault, "Hermes", "[Hermes bounded ack] Chat message received: hi"),
            daemon=True,
        )
        sim.start()
        result = build_phase11_chat_live_e2e_verification(
            vault, probe_timeout_s=10.0, probe_message="hi"
        )
        sim.join(timeout=2)

        assert result["ok"] is True
        assert result["checks"]["probe_round_trip_ok"] is True
        assert result["checks"]["probe_result_received"] is True
        assert "COMPLETE" in result["status"]

    def test_probe_timeout_produces_blocked_reason(self, tmp_path):
        from runtime.studio.phase11_chat_live_e2e import build_phase11_chat_live_e2e_verification

        vault = self._vault_with_bus_and_hb(tmp_path)
        # No simulator — probe will time out
        result = build_phase11_chat_live_e2e_verification(vault, probe_timeout_s=1.0)

        assert result["ok"] is False
        assert any("probe_" in r for r in result["blocked_reasons"])

    def test_status_awaiting_runtime_when_no_heartbeat(self, tmp_path, monkeypatch):
        import runtime.studio.phase11_chat_runtime_dispatch_verification as _disp
        monkeypatch.setattr(
            _disp, "_check_gateway_ports",
            lambda adapter_id: {"gateway_port_online": False, "gateway_port_listening": None, "gateway_ports_checked": []},
        )
        from runtime.studio.phase11_chat_live_e2e import build_phase11_chat_live_e2e_verification
        vault = self._vault_with_bus_no_hb(tmp_path)
        result = build_phase11_chat_live_e2e_verification(vault, probe_timeout_s=1.0)

        assert "AWAITING" in result["status"]

    def test_pass_id_and_surface(self, tmp_path):
        from runtime.studio.phase11_chat_live_e2e import (
            build_phase11_chat_live_e2e_verification,
            PASS_ID,
            SURFACE_ID,
        )
        vault = self._vault_no_bus(tmp_path)
        result = build_phase11_chat_live_e2e_verification(vault, probe_timeout_s=1.0)

        assert result["pass"] == PASS_ID
        assert result["surface"] == SURFACE_ID

    def test_authority_flags(self, tmp_path):
        from runtime.studio.phase11_chat_live_e2e import build_phase11_chat_live_e2e_verification
        vault = self._vault_with_bus_and_hb(tmp_path)
        sim = threading.Thread(
            target=_bus_simulator,
            args=(vault, "Hermes", "ack"),
            daemon=True,
        )
        sim.start()
        result = build_phase11_chat_live_e2e_verification(vault, probe_timeout_s=10.0)
        sim.join(timeout=2)

        auth = result["authority"]
        assert auth["read_only"] is False
        assert auth["approval_consumed"] is False
        assert auth["canonical_mutation_performed"] is False

    def test_authority_write_performed_when_probe_runs(self, tmp_path):
        from runtime.studio.phase11_chat_live_e2e import build_phase11_chat_live_e2e_verification
        vault = self._vault_with_bus_and_hb(tmp_path)
        sim = threading.Thread(
            target=_bus_simulator,
            args=(vault, "Hermes", "ack"),
            daemon=True,
        )
        sim.start()
        result = build_phase11_chat_live_e2e_verification(vault, probe_timeout_s=10.0)
        sim.join(timeout=2)

        assert result["authority"]["agent_bus_task_write_performed"] is True

    def test_summary_has_probe_outcome(self, tmp_path):
        from runtime.studio.phase11_chat_live_e2e import build_phase11_chat_live_e2e_verification
        vault = self._vault_with_bus_and_hb(tmp_path)
        sim = threading.Thread(
            target=_bus_simulator,
            args=(vault, "Hermes", "summary ack"),
            daemon=True,
        )
        sim.start()
        result = build_phase11_chat_live_e2e_verification(vault, probe_timeout_s=10.0)
        sim.join(timeout=2)

        assert result["summary"]["probe_outcome"] == "complete"
        assert result["summary"]["result_text_preview"] != ""


# ── pick_probe_runtime ────────────────────────────────────────────────────────

class TestPickProbeRuntime:
    def test_prefers_hermes_when_online(self, tmp_path):
        from runtime.studio.phase11_chat_live_e2e import _pick_probe_runtime
        avail = {
            "runtime_by_adapter": {
                "hermes": {"online": True, "is_bus_runtime": True},
                "openclaw": {"online": True, "is_bus_runtime": True},
            }
        }
        assert _pick_probe_runtime(avail) == "hermes"

    def test_falls_back_to_openclaw(self, tmp_path):
        from runtime.studio.phase11_chat_live_e2e import _pick_probe_runtime
        avail = {
            "runtime_by_adapter": {
                "hermes": {"online": False, "is_bus_runtime": True},
                "openclaw": {"online": True, "is_bus_runtime": True},
            }
        }
        assert _pick_probe_runtime(avail) == "openclaw"

    def test_falls_back_to_hermes_when_all_offline(self, tmp_path):
        from runtime.studio.phase11_chat_live_e2e import _pick_probe_runtime
        avail = {"runtime_by_adapter": {}}
        assert _pick_probe_runtime(avail) == "hermes"


# ── api.py envelope ───────────────────────────────────────────────────────────

class TestApiGetChatLiveE2EVerification:
    def _api(self, tmp_path):
        vault = _make_vault(tmp_path)
        _init_bus(vault)
        from runtime.studio.shell.api import StudioAPI
        return StudioAPI(str(vault)), vault

    def test_returns_ok_envelope(self, tmp_path):
        api, _ = self._api(tmp_path)
        result = api.get_chat_live_e2e_verification()
        assert "ok" in result
        assert "data" in result

    def test_data_has_pass_id(self, tmp_path):
        api, _ = self._api(tmp_path)
        result = api.get_chat_live_e2e_verification()
        data = result["data"]
        assert data["pass"] == "phase11-chat-live-e2e-with-active-runtime"

    def test_data_has_checks(self, tmp_path):
        api, _ = self._api(tmp_path)
        result = api.get_chat_live_e2e_verification()
        assert "checks" in result["data"]
        assert "send_chat_message_importable" in result["data"]["checks"]

    def test_data_has_authority(self, tmp_path):
        api, _ = self._api(tmp_path)
        result = api.get_chat_live_e2e_verification()
        assert "authority" in result["data"]

    def test_data_has_summary(self, tmp_path):
        api, _ = self._api(tmp_path)
        result = api.get_chat_live_e2e_verification()
        assert "summary" in result["data"]
        assert "dispatch_chain_complete" in result["data"]["summary"]

    def test_no_bus_ok_false(self, tmp_path):
        vault = _make_vault(tmp_path)
        from runtime.studio.shell.api import StudioAPI
        api = StudioAPI(str(vault))
        result = api.get_chat_live_e2e_verification()
        assert result["data"]["ok"] is False


# ── panel_registry flags ──────────────────────────────────────────────────────

class TestPanelRegistryLiveE2EFlags:
    def _registry(self):
        from runtime.studio.shell.panel_registry import build_native_shell_panel_registry
        with tempfile.TemporaryDirectory() as td:
            vault = Path(td)
            (vault / "runtime" / "agent_bus").mkdir(parents=True)
            return build_native_shell_panel_registry(str(vault))

    def test_probe_wired(self):
        r = self._registry()
        assert r["readiness"]["phase11_chat_live_e2e_probe_wired"] is True

    def test_round_trip_verified(self):
        r = self._registry()
        assert r["readiness"]["phase11_chat_live_e2e_round_trip_verified"] is True

    def test_bus_write_confirmed(self):
        r = self._registry()
        assert r["readiness"]["phase11_chat_live_e2e_bus_write_confirmed"] is True

    def test_runtime_ack_confirmed(self):
        r = self._registry()
        assert r["readiness"]["phase11_chat_live_e2e_runtime_ack_confirmed"] is True

    def test_phase11_next_pass_advanced(self):
        r = self._registry()
        assert r["readiness"]["phase11_next_recommended_pass"] == "phase11-chat-post-e2e-hardening"

    def test_global_next_pass_advanced(self):
        r = self._registry()
        assert r["readiness"]["next_recommended_pass"] == "ventureops-operator-readiness-gate"
