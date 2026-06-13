"""
test_openclaw_promotion_preactivation_failures.py — ChaseOS Phase 9

Focused pre-activation failure-path checks for the OpenClaw draft promotion contract.

Covers:
  - approval-linkage failure posture is explicitly declared
  - exact target-scope failure posture is explicitly declared
  - audit-survival expectations remain declared for blocked runs

Running:
  .venv/Scripts/python.exe -m pytest runtime/aor/test_openclaw_promotion_preactivation_failures.py -q
"""

from __future__ import annotations

import sys
from pathlib import Path


_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[2]
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

from runtime.aor.promotion_readiness import collect_openclaw_preactivation_failure_signals


def test_openclaw_preactivation_declares_approval_linkage_failure_posture() -> None:
    signals = collect_openclaw_preactivation_failure_signals(vault_root=_VAULT_ROOT)

    assert signals["operator_approval_ref_required"] is True
    assert signals["approval_linkage_declared"] is True


def test_openclaw_preactivation_declares_exact_target_scope_failure_posture() -> None:
    signals = collect_openclaw_preactivation_failure_signals(vault_root=_VAULT_ROOT)

    assert signals["target_scope_failure_declared"] is True


def test_openclaw_preactivation_declares_audit_survival_expectations() -> None:
    signals = collect_openclaw_preactivation_failure_signals(vault_root=_VAULT_ROOT)

    assert signals["audit_survival_declared"] is True
    assert signals["blocking_gaps"] == []
