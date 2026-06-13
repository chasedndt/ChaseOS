"""
test_hermes_promotion_preactivation_failures.py — ChaseOS Phase 9

Focused pre-activation failure-path checks for the Hermes draft promotion contract.

Covers:
  - control-plane approval-linkage failure posture is explicitly declared
  - exact target-scope failure posture is explicitly declared
  - audit-survival expectations remain declared for blocked runs
  - direct-authority denial for Discord/control-plane input remains declared

Running:
  .venv/Scripts/python.exe -m pytest runtime/aor/test_hermes_promotion_preactivation_failures.py -q
"""

from __future__ import annotations

import sys
from pathlib import Path


_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[2]
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

from runtime.aor.promotion_readiness import collect_hermes_preactivation_failure_signals


def test_hermes_preactivation_failure_signals_are_declared() -> None:
    signals = collect_hermes_preactivation_failure_signals(vault_root=_VAULT_ROOT)

    assert signals["approval_linkage_declared"] is True
    assert signals["control_plane_linkage_declared"] is True
    assert signals["direct_authority_guard_declared"] is True
    assert signals["target_scope_failure_declared"] is True
    assert signals["audit_survival_declared"] is True
    assert signals["operator_approval_ref_required"] is True
    assert signals["control_plane_request_ref_required"] is True
    assert signals["blocking_gaps"] == []
