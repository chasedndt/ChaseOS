"""VentureOps AI runtime security audit workflow alias.

This wrapper preserves the exact early VentureOps workflow id while reusing the
hardened agent runtime governance audit implementation. The wrapper does not
add authority; it only changes the AOR workflow identity used in proof outputs.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from runtime.workflows import agent_runtime_governance_audit as _governance_audit


WORKFLOW_ID = "ventureops_ai_runtime_security_audit"


def build_ventureops_ai_runtime_security_audit(
    *,
    inputs: dict[str, Any] | None = None,
    vault_root: str | Path | None = None,
) -> dict[str, Any]:
    previous_workflow_id = _governance_audit.WORKFLOW_ID
    try:
        _governance_audit.WORKFLOW_ID = WORKFLOW_ID
        result = _governance_audit.build_agent_runtime_governance_audit(
            inputs=inputs,
            vault_root=vault_root,
        )
    finally:
        _governance_audit.WORKFLOW_ID = previous_workflow_id

    result["alias_of"] = previous_workflow_id
    result["workflow_family"] = "AI Runtime Security Audit"
    return result


def run_ventureops_ai_runtime_security_audit(
    *,
    inputs: dict[str, Any] | None = None,
    vault_root: str | Path | None = None,
) -> dict[str, Any]:
    return build_ventureops_ai_runtime_security_audit(inputs=inputs, vault_root=vault_root)
