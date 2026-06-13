"""
test_hermes_promotion_activation_readiness.py — ChaseOS Phase 9

Focused readiness checks for the Hermes bounded promotion path.

Covers:
  - Hermes adapter posture remains fail-closed for knowledge promotion
  - Hermes draft contract preserves control-plane approval linkage and direct-authority denial
  - Promotion-record routing is declared in the still-draft Hermes contract
  - Activation readiness remains blocked while draft/adapter activation switches stay closed

Running:
  .venv/Scripts/python.exe -m pytest runtime/aor/test_hermes_promotion_activation_readiness.py -q
"""

from __future__ import annotations

import sys
from pathlib import Path


_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[2]
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

from runtime.aor.promotion_readiness import assess_hermes_promotion_activation_readiness
from runtime.chaseos_gate import load_adapter_manifest



def test_hermes_adapter_manifest_stays_fail_closed_for_promotion() -> None:
    manifest = load_adapter_manifest("hermes")

    assert manifest["promotion_behavior"]["may_promote_to_knowledge"] == "no"
    assert manifest["promotion_behavior"]["gate_conditions_required"] is False
    assert "02_KNOWLEDGE/**" in manifest["explicitly_denied_write_targets"]



def test_hermes_draft_contract_declares_control_plane_linkage_and_direct_authority_denial() -> None:
    readiness = assess_hermes_promotion_activation_readiness(vault_root=_VAULT_ROOT)

    assert readiness["control_plane_linkage_declared"] is True
    assert readiness["direct_authority_guard_declared"] is True



def test_hermes_draft_contract_now_declares_promotion_record_routing() -> None:
    readiness = assess_hermes_promotion_activation_readiness(vault_root=_VAULT_ROOT)

    assert readiness["promotion_record_lane_seeded"] is True
    assert readiness["promotion_record_lane_declared"] is True



def test_hermes_activation_readiness_stays_blocked_while_draft_activation_switches_remain_closed() -> None:
    readiness = assess_hermes_promotion_activation_readiness(vault_root=_VAULT_ROOT)

    assert readiness["ready"] is False
    assert readiness["adapter_posture_ok"] is True
    assert readiness["provenance_gate_seam_present"] is True
    assert readiness["control_plane_linkage_declared"] is True
    assert readiness["direct_authority_guard_declared"] is True
    assert readiness["promotion_record_lane_declared"] is True
    assert readiness["workflow_still_draft"] is True
    assert readiness["adapter_still_fail_closed"] is True
    assert any("draft" in issue.lower() for issue in readiness["blocking_issues"])
    assert any("fail-closed" in issue.lower() or "may_promote_to_knowledge" in issue for issue in readiness["blocking_issues"])
