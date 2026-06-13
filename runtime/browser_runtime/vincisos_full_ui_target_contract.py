"""Contract gate for a future full VincisOS product UI browser proof.

This module does not launch a browser, inspect a page, connect to CDP, take a
screenshot, or write skill artifacts. It validates that a future VincisOS target
has been declared as a local safe-mode product UI before a separate browser
proof is allowed to proceed.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from runtime.browser_runtime.vincisos_full_ui_preflight import (
    VincisOSFullUISafeModePreflightRequest,
    evaluate_vincisos_full_ui_safe_mode_preflight,
)
from runtime.browser_runtime.vincisos_preflight import LOCAL_BROWSER_HOSTS


CONTRACT_VERSION = "vincisos.full_ui_target.v1"

ALLOWED_CONTRACT_ACTIONS = frozenset(
    {
        "open",
        "read_state",
        "capture_screenshot",
        "harmless_click",
        "close",
    }
)
MINIMUM_REQUIRED_ACTIONS = frozenset({"open", "read_state", "capture_screenshot"})

REQUIRED_EXPECTED_ARTIFACTS = frozenset(
    {
        "browser_run_log",
        "agent_activity_log",
        "screenshot",
        "draft_skill_candidate",
    }
)

FORBIDDEN_AUTHORITY_FLAGS = {
    "allow_real_profile": "Real browser profile use is forbidden.",
    "allow_credentials": "Credential and saved-login access is forbidden.",
    "allow_cdp": "CDP execution is not authorized for this target contract.",
    "allow_browser_harness": "Browser Harness is not authorized for this target contract.",
    "allow_browser_use_cli_live": "Browser Use live CLI execution is not authorized for this target contract.",
    "allow_trusted_skill_write": "Trusted Browser Skill or SiteOps Skill Card writes are forbidden.",
    "allow_skill_activation": "Skill activation is forbidden.",
    "allow_agent_bus_enqueue": "Agent Bus enqueue is forbidden.",
    "allow_provider_call": "Provider/API calls are forbidden.",
    "allow_gate_mutation": "Gate mutation is forbidden.",
    "allow_canonical_writeback": "Canonical ChaseOS writeback is forbidden.",
}


@dataclass(frozen=True)
class VincisOSFullUITargetContractResult:
    """Machine-readable result for the target contract gate."""

    ok: bool
    status: str
    contract_version: str | None
    target_name: str | None
    target_url: str | None
    blockers: list[dict[str, str]]
    checks: dict[str, Any]
    preflight: dict[str, Any]
    future_full_ui_shadow_proof_ready: bool
    next_allowed_step: str | None
    browser_launch_attempted: bool = False
    cdp_connection_attempted: bool = False
    browser_harness_used: bool = False
    browser_use_cli_live_used: bool = False
    screenshot_attempted: bool = False
    profile_access_attempted: bool = False
    credentials_read: bool = False
    trusted_skill_write_attempted: bool = False
    skill_activation_attempted: bool = False
    agent_bus_enqueue_attempted: bool = False
    provider_call_attempted: bool = False
    gate_mutation_attempted: bool = False
    canonical_writeback_attempted: bool = False
    files_modified: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _blocker(blocker_id: str, message: str) -> dict[str, str]:
    return {"blocker_id": blocker_id, "message": message}


def _as_bool(value: Any) -> bool:
    return value is True


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return []


def _safe_mode_evidence_present(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return any(isinstance(item, str) and item.strip() for item in value)
    return False


def _contract_value(contract: Mapping[str, Any], key: str, default: Any = None) -> Any:
    return contract[key] if key in contract else default


def evaluate_vincisos_full_ui_target_contract(
    contract: Mapping[str, Any] | None,
) -> VincisOSFullUITargetContractResult:
    """Validate a declared future VincisOS full product UI target.

    The result may become `ok=True` only for a local, safe-mode, product-UI
    contract. `ok=True` still means no browser has run; it only allows a later
    bounded proof pass to use this target declaration.
    """
    blockers: list[dict[str, str]] = []
    checks: dict[str, Any] = {
        "contract_version_expected": CONTRACT_VERSION,
        "allowed_contract_actions": sorted(ALLOWED_CONTRACT_ACTIONS),
        "minimum_required_actions": sorted(MINIMUM_REQUIRED_ACTIONS),
        "required_expected_artifacts": sorted(REQUIRED_EXPECTED_ARTIFACTS),
        "required_forbidden_authority_flags": sorted(FORBIDDEN_AUTHORITY_FLAGS),
        "browser_execution_allowed_by_this_contract": False,
        "files_modified": False,
    }

    if contract is None:
        contract = {}
        blockers.append(_blocker("target_contract_missing", "No VincisOS full UI target contract was supplied."))
    elif not isinstance(contract, Mapping):
        contract = {}
        blockers.append(_blocker("target_contract_not_object", "Target contract must be a JSON object."))

    contract_version = _contract_value(contract, "contract_version")
    target_name = _contract_value(contract, "target_name")
    target_url = _contract_value(contract, "target_url")
    target_kind = _contract_value(contract, "target_kind", "product_ui")
    mode = _contract_value(contract, "mode", "shadow")
    safe_mode_asserted = _as_bool(_contract_value(contract, "safe_mode_asserted"))
    safe_mode_evidence = _contract_value(contract, "safe_mode_evidence")
    allowed_hosts = _as_list(_contract_value(contract, "allowed_hosts"))
    allowed_actions = _as_list(_contract_value(contract, "allowed_actions"))
    expected_artifacts = _as_list(_contract_value(contract, "expected_artifacts"))
    forbidden_authority = _contract_value(contract, "forbidden_authority")
    draft_only = _as_bool(_contract_value(contract, "draft_only"))
    require_running_target = _as_bool(_contract_value(contract, "require_running_target", False))
    probe_reachability = _as_bool(_contract_value(contract, "probe_reachability", False))

    local_hosts = {item.lower() for item in LOCAL_BROWSER_HOSTS}
    declared_hosts = {str(item).lower() for item in allowed_hosts if isinstance(item, str)}
    declared_actions = {str(item) for item in allowed_actions if isinstance(item, str)}
    declared_artifacts = {str(item) for item in expected_artifacts if isinstance(item, str)}

    checks.update(
        {
            "contract_version": contract_version,
            "target_name": target_name,
            "target_url_declared": bool(target_url),
            "target_kind": target_kind,
            "mode": mode,
            "safe_mode_asserted": safe_mode_asserted,
            "safe_mode_evidence_present": _safe_mode_evidence_present(safe_mode_evidence),
            "allowed_hosts": sorted(declared_hosts),
            "allowed_hosts_local_only": bool(declared_hosts) and declared_hosts.issubset(local_hosts),
            "allowed_actions": sorted(declared_actions),
            "expected_artifacts": sorted(declared_artifacts),
            "draft_only": draft_only,
            "require_running_target": require_running_target,
            "probe_reachability": probe_reachability,
        }
    )

    if contract_version != CONTRACT_VERSION:
        blockers.append(_blocker("contract_version_invalid", f"Contract version must be {CONTRACT_VERSION}."))
    if not isinstance(target_name, str) or not target_name.strip():
        blockers.append(_blocker("target_name_missing", "Target contract must name the local VincisOS target."))
    if not isinstance(target_url, str) or not target_url.strip():
        blockers.append(_blocker("target_url_missing", "Target contract must declare a local target_url."))
    if target_kind != "product_ui":
        blockers.append(_blocker("target_kind_not_product_ui", "Target contract must declare target_kind=product_ui."))
    if mode != "shadow":
        blockers.append(_blocker("mode_not_shadow", "Target contract must remain in shadow mode."))
    if not safe_mode_asserted:
        blockers.append(_blocker("safe_mode_not_asserted", "Target contract must assert safe/test mode."))
    if not _safe_mode_evidence_present(safe_mode_evidence):
        blockers.append(
            _blocker("safe_mode_evidence_missing", "Target contract must include non-empty safe-mode evidence.")
        )
    if not declared_hosts:
        blockers.append(_blocker("allowed_hosts_missing", "Target contract must declare local allowed_hosts."))
    elif not declared_hosts.issubset(local_hosts):
        blockers.append(_blocker("allowed_hosts_not_local_only", "Allowed hosts must stay within local browser hosts."))

    unknown_actions = declared_actions - ALLOWED_CONTRACT_ACTIONS
    missing_actions = MINIMUM_REQUIRED_ACTIONS - declared_actions
    if not declared_actions:
        blockers.append(_blocker("allowed_actions_missing", "Target contract must declare allowed browser actions."))
    if unknown_actions:
        blockers.append(
            _blocker(
                "allowed_actions_unknown",
                "Target contract requested unsupported browser actions: " + ", ".join(sorted(unknown_actions)),
            )
        )
    if missing_actions:
        blockers.append(
            _blocker(
                "allowed_actions_minimum_missing",
                "Target contract is missing required actions: " + ", ".join(sorted(missing_actions)),
            )
        )

    missing_artifacts = REQUIRED_EXPECTED_ARTIFACTS - declared_artifacts
    if missing_artifacts:
        blockers.append(
            _blocker(
                "expected_artifacts_missing",
                "Target contract must expect these artifacts: " + ", ".join(sorted(missing_artifacts)),
            )
        )

    if not draft_only:
        blockers.append(_blocker("draft_only_not_asserted", "Target contract must declare draft_only=true."))

    if not isinstance(forbidden_authority, Mapping):
        blockers.append(
            _blocker(
                "forbidden_authority_missing",
                "Target contract must declare forbidden_authority flags and keep every flag false.",
            )
        )
        forbidden_authority = {}

    forbidden_authority_status: dict[str, Any] = {}
    for flag, message in FORBIDDEN_AUTHORITY_FLAGS.items():
        value = forbidden_authority.get(flag)
        forbidden_authority_status[flag] = value
        if flag not in forbidden_authority:
            blockers.append(_blocker(f"{flag}_not_declared", f"forbidden_authority.{flag} must be declared false."))
        elif value is not False:
            blockers.append(_blocker(f"{flag}_forbidden", message))
    checks["forbidden_authority"] = forbidden_authority_status

    preflight = evaluate_vincisos_full_ui_safe_mode_preflight(
        VincisOSFullUISafeModePreflightRequest(
            target_url=target_url if isinstance(target_url, str) else None,
            target_name=target_name if isinstance(target_name, str) else "VincisOS product UI",
            target_kind=target_kind if isinstance(target_kind, str) else "product_ui",
            mode=mode if isinstance(mode, str) else "shadow",
            safe_mode_asserted=safe_mode_asserted,
            allowed_hosts=list(declared_hosts) if declared_hosts else list(LOCAL_BROWSER_HOSTS),
            require_running_target=require_running_target,
            probe_reachability=probe_reachability,
            allow_real_profile=forbidden_authority.get("allow_real_profile") is True,
            allow_credentials=forbidden_authority.get("allow_credentials") is True,
            allow_cdp=forbidden_authority.get("allow_cdp") is True,
            allow_browser_harness=forbidden_authority.get("allow_browser_harness") is True,
            allow_browser_use_cli_live=forbidden_authority.get("allow_browser_use_cli_live") is True,
            allow_trusted_skill_write=forbidden_authority.get("allow_trusted_skill_write") is True,
            allow_skill_activation=forbidden_authority.get("allow_skill_activation") is True,
            allow_agent_bus_enqueue=forbidden_authority.get("allow_agent_bus_enqueue") is True,
            allow_provider_call=forbidden_authority.get("allow_provider_call") is True,
            allow_gate_mutation=forbidden_authority.get("allow_gate_mutation") is True,
            allow_canonical_writeback=forbidden_authority.get("allow_canonical_writeback") is True,
        )
    )
    preflight_dict = preflight.as_dict()
    for item in preflight.blockers:
        if item not in blockers:
            blockers.append(item)

    ok = not blockers
    status = "vincisos_full_ui_target_contract_ready_no_execution" if ok else "blocked_vincisos_full_ui_target_contract"
    next_step = (
        "A later pass may run the contract-backed local full UI shadow proof with isolated browser state."
        if ok
        else None
    )

    return VincisOSFullUITargetContractResult(
        ok=ok,
        status=status,
        contract_version=contract_version if isinstance(contract_version, str) else None,
        target_name=target_name if isinstance(target_name, str) else None,
        target_url=target_url if isinstance(target_url, str) else None,
        blockers=blockers,
        checks=checks,
        preflight=preflight_dict,
        future_full_ui_shadow_proof_ready=ok,
        next_allowed_step=next_step,
    )


def evaluate_vincisos_full_ui_target_contract_file(path: Path | str) -> VincisOSFullUITargetContractResult:
    """Read and evaluate a JSON target contract file, failing closed on errors."""
    contract_path = Path(path)
    try:
        payload = json.loads(contract_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        result = evaluate_vincisos_full_ui_target_contract(None)
        blockers = list(result.blockers)
        blockers.append(_blocker("target_contract_file_missing", f"Contract file not found: {contract_path}"))
        return VincisOSFullUITargetContractResult(
            **{**result.as_dict(), "blockers": blockers, "status": "blocked_vincisos_full_ui_target_contract"}
        )
    except json.JSONDecodeError as exc:
        result = evaluate_vincisos_full_ui_target_contract({})
        blockers = list(result.blockers)
        blockers.append(_blocker("target_contract_json_invalid", f"Invalid JSON: {exc}"))
        return VincisOSFullUITargetContractResult(
            **{**result.as_dict(), "blockers": blockers, "status": "blocked_vincisos_full_ui_target_contract"}
        )
    return evaluate_vincisos_full_ui_target_contract(payload)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate a VincisOS full UI target contract without execution.")
    parser.add_argument("--contract-json", required=True, help="Path to a JSON target contract.")
    parser.add_argument("--json", action="store_true", help="Print JSON output. Text output is not implemented.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    result = evaluate_vincisos_full_ui_target_contract_file(Path(args.contract_json))
    print(json.dumps(result.as_dict(), indent=2))
    return 0 if result.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
