"""Runtime Bus Response Check — full-stack liveness verification.

Checks two independent layers per runtime:
  1. Gateway liveness  — HTTP/TCP probe (is the process running?)
  2. Bus round-trip    — send a chat task, wait for the runtime to claim and respond

Together these answer: "Is this runtime alive AND ready to process Agent Bus tasks?"

This is the canonical startup + on-demand runtime verification surface. It is the
right thing to run when ChaseOS starts, when a new runtime is integrated, or when
you want to confirm the control plane is functioning before dispatch.

All probes are fail-open. A timeout is a FAIL result, not an exception.
"""

from __future__ import annotations

import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MODEL_VERSION = "studio.runtime_bus_response_check.v1"
SURFACE_ID = "runtime_bus_response_check"

# Bus runtimes to check by default. Ordered by preference.
_DEFAULT_RUNTIMES = ["hermes", "openclaw"]

_DEFAULT_MAX_WAIT_S = 30.0


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def check_runtime(
    vault_root: str | Path,
    runtime_id: str,
    *,
    max_wait_s: float = _DEFAULT_MAX_WAIT_S,
) -> dict[str, Any]:
    """Run a full-stack liveness check for a single runtime.

    Returns a result dict:
      ok              — True only if both gateway and bus round-trip succeed
      runtime_id      — the adapter id (hermes, openclaw, ...)
      gateway_ok      — TCP port probe succeeded
      gateway_port    — which port responded (int or None)
      bus_ok          — Agent Bus round-trip returned a result
      bus_outcome     — complete / timeout / send_failed / poll_error
      bus_elapsed_s   — seconds for the bus round-trip
      result_text     — the runtime's response (bounded ack or LLM reply)
      error           — human-readable failure description (or None)
    """
    from runtime.studio.phase11_chat_runtime_dispatch_verification import (
        _check_gateway_ports,
    )
    from runtime.studio.phase11_chat_live_e2e import run_chat_probe

    vault = Path(vault_root).resolve()
    start = time.monotonic()

    # Layer 1: gateway port probe
    try:
        port_info = _check_gateway_ports(runtime_id)
        gateway_ok = port_info.get("gateway_port_online", False)
        gateway_port = port_info.get("gateway_port_listening")
    except Exception:
        gateway_ok = False
        gateway_port = None

    # Layer 2: bus round-trip probe
    try:
        probe = run_chat_probe(
            vault,
            "ping",
            runtime_id=runtime_id,
            max_wait_s=max_wait_s,
            auto_trigger_daemon=True,
        )
        bus_ok = probe.get("ok") is True
        bus_outcome = probe.get("probe_outcome", "unknown")
        bus_elapsed_s = probe.get("elapsed_s")
        result_text = probe.get("result_text")
    except Exception as exc:
        bus_ok = False
        bus_outcome = "probe_exception"
        bus_elapsed_s = round(time.monotonic() - start, 2)
        result_text = None
        probe = {"error": str(exc)[:120]}

    ok = gateway_ok and bus_ok

    error: str | None = None
    if not gateway_ok:
        error = f"Gateway not reachable (no process on declared ports)"
    elif not bus_ok:
        error = f"Bus round-trip failed: {bus_outcome}"

    return {
        "ok": ok,
        "runtime_id": runtime_id,
        "gateway_ok": gateway_ok,
        "gateway_port": gateway_port,
        "bus_ok": bus_ok,
        "bus_outcome": bus_outcome,
        "bus_elapsed_s": bus_elapsed_s,
        "result_text": result_text,
        "error": error,
    }


def run_runtime_bus_response_check(
    vault_root: str | Path,
    runtimes: list[str] | None = None,
    *,
    max_wait_s: float = _DEFAULT_MAX_WAIT_S,
    parallel: bool = True,
) -> dict[str, Any]:
    """Run full-stack liveness checks for all requested runtimes.

    Runs in parallel by default (one thread per runtime) so the total time is
    bounded by the slowest runtime, not the sum.

    Args:
        vault_root: Vault root directory.
        runtimes: List of runtime adapter IDs to check. Defaults to hermes + openclaw.
        max_wait_s: Seconds to wait for each bus round-trip before declaring timeout.
        parallel: Run checks concurrently (default True).

    Returns a report dict with overall ok, per-runtime results, and a summary.
    """
    vault = Path(vault_root).resolve()
    runtime_ids = runtimes or list(_DEFAULT_RUNTIMES)
    results: list[dict[str, Any]] = [{}] * len(runtime_ids)

    if parallel and len(runtime_ids) > 1:
        threads = []
        for i, rid in enumerate(runtime_ids):
            def _run(idx: int, runtime_id: str) -> None:
                results[idx] = check_runtime(vault, runtime_id, max_wait_s=max_wait_s)
            t = threading.Thread(target=_run, args=(i, rid), daemon=True)
            threads.append(t)
            t.start()
        for t in threads:
            t.join(timeout=max_wait_s + 5)
        # Fill any thread that didn't complete
        for i, r in enumerate(results):
            if not r:
                results[i] = {
                    "ok": False, "runtime_id": runtime_ids[i],
                    "gateway_ok": False, "gateway_port": None,
                    "bus_ok": False, "bus_outcome": "thread_timeout",
                    "bus_elapsed_s": None, "result_text": None,
                    "error": "Check thread did not complete in time",
                }
    else:
        for i, rid in enumerate(runtime_ids):
            results[i] = check_runtime(vault, rid, max_wait_s=max_wait_s)

    all_ok = all(r.get("ok") for r in results)
    any_ok = any(r.get("ok") for r in results)
    online_count = sum(1 for r in results if r.get("gateway_ok"))
    responding_count = sum(1 for r in results if r.get("bus_ok"))

    if all_ok:
        status = f"ALL RUNTIMES LIVE — {responding_count}/{len(results)} responding on bus"
    elif any_ok:
        ok_ids = [r["runtime_id"] for r in results if r.get("ok")]
        status = f"PARTIAL — {', '.join(ok_ids)} responding; others failed"
    elif online_count > 0:
        status = f"GATEWAY UP / BUS UNRESPONSIVE — {online_count}/{len(results)} gateway live, 0 bus responding"
    else:
        status = "NO RUNTIMES REACHABLE"

    return {
        "ok": all_ok,
        "any_ok": any_ok,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at_utc": _now_utc(),
        "status": status,
        "runtimes_checked": runtime_ids,
        "results": results,
        "summary": {
            "total": len(results),
            "online_gateway": online_count,
            "responding_bus": responding_count,
            "all_ok": all_ok,
        },
        "authority": {
            "read_only": False,
            "agent_bus_task_write_performed": True,
            "approval_consumed": False,
            "canonical_mutation_performed": False,
        },
    }
