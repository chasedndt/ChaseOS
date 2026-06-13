"""No-browser availability probe for a declared VincisOS product UI target.

This module validates the VincisOS full UI target contract, then performs only
a local HTTP reachability check. It does not launch a browser, connect to CDP,
inspect DOM state, capture screenshots, click UI, write artifacts, or promote
skills.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from runtime.browser_runtime.vincisos_full_ui_target_contract import (
    evaluate_vincisos_full_ui_target_contract,
    evaluate_vincisos_full_ui_target_contract_file,
)
from runtime.browser_runtime.vincisos_preflight import LOCAL_BROWSER_HOSTS


PROBE_VERSION = "vincisos.product_ui_target_probe.v1"


@dataclass(frozen=True)
class VincisOSProductUITargetProbeResult:
    """Machine-readable result for the product UI target availability probe."""

    ok: bool
    status: str
    probe_version: str
    target_name: str | None
    target_url: str | None
    blockers: list[dict[str, str]]
    contract_validation: dict[str, Any]
    checks: dict[str, Any]
    next_allowed_step: str | None
    browser_launch_attempted: bool = False
    cdp_connection_attempted: bool = False
    browser_harness_used: bool = False
    browser_use_cli_live_used: bool = False
    screenshot_attempted: bool = False
    profile_access_attempted: bool = False
    credentials_read: bool = False
    cookie_or_session_read: bool = False
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


def _local_url_allowed(target_url: str | None) -> bool:
    if not target_url:
        return False
    parsed = urlparse(target_url)
    host = (parsed.hostname or "").lower()
    return parsed.scheme in {"http", "https"} and host in {item.lower() for item in LOCAL_BROWSER_HOSTS}


def _http_probe(target_url: str, timeout_seconds: float) -> dict[str, Any]:
    request = Request(
        target_url,
        method="GET",
        headers={"User-Agent": "ChaseOS-BrowserRuntime-TargetProbe/1.0"},
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            content = response.read(1024)
            return {
                "http_probe_attempted": True,
                "http_reachable": True,
                "http_status": int(response.status),
                "content_sample_bytes": len(content),
                "content_type": response.headers.get("content-type"),
            }
    except HTTPError as exc:
        return {
            "http_probe_attempted": True,
            "http_reachable": True,
            "http_status": int(exc.code),
            "http_error": str(exc),
        }
    except (OSError, URLError) as exc:
        reason = getattr(exc, "reason", exc)
        return {
            "http_probe_attempted": True,
            "http_reachable": False,
            "http_error": str(reason),
        }


def probe_vincisos_product_ui_target(
    contract: Mapping[str, Any] | None,
    *,
    timeout_seconds: float = 2.0,
) -> VincisOSProductUITargetProbeResult:
    """Validate and locally probe a VincisOS product UI target without browser execution."""
    validation = evaluate_vincisos_full_ui_target_contract(contract)
    validation_dict = validation.as_dict()
    blockers = list(validation.blockers)
    checks: dict[str, Any] = {
        "contract_ready": validation.ok,
        "local_http_probe_only": True,
        "browser_execution_allowed_by_this_probe": False,
        "timeout_seconds": timeout_seconds,
        "http_probe_attempted": False,
        "http_reachable": False,
    }

    target_url = validation.target_url
    if not validation.ok:
        blockers.insert(
            0,
            _blocker(
                "target_contract_not_ready",
                "The VincisOS product UI target contract is not ready; availability probe is blocked.",
            ),
        )
    elif not _local_url_allowed(target_url):
        blockers.append(
            _blocker("target_url_not_local", "The product UI target probe is restricted to local HTTP targets.")
        )
    elif target_url:
        checks.update(_http_probe(target_url, timeout_seconds))
        if not checks["http_reachable"]:
            blockers.append(
                _blocker(
                    "local_product_ui_target_unreachable",
                    "The declared local VincisOS product UI target did not answer an HTTP request.",
                )
            )

    ok = not blockers
    status = (
        "vincisos_product_ui_target_available_no_browser"
        if ok
        else "blocked_vincisos_product_ui_target_availability"
    )
    next_step = (
        "A later pass may run the isolated browser proof against this local target and write draft/log artifacts."
        if ok
        else None
    )
    return VincisOSProductUITargetProbeResult(
        ok=ok,
        status=status,
        probe_version=PROBE_VERSION,
        target_name=validation.target_name,
        target_url=target_url,
        blockers=blockers,
        contract_validation=validation_dict,
        checks=checks,
        next_allowed_step=next_step,
    )


def probe_vincisos_product_ui_target_file(
    path: Path | str,
    *,
    timeout_seconds: float = 2.0,
) -> VincisOSProductUITargetProbeResult:
    """Load a contract file and probe the declared local target without browser execution."""
    validation = evaluate_vincisos_full_ui_target_contract_file(path)
    if not validation.ok:
        blockers = [
            _blocker(
                "target_contract_not_ready",
                "The VincisOS product UI target contract is not ready; availability probe is blocked.",
            ),
            *validation.blockers,
        ]
        return VincisOSProductUITargetProbeResult(
            ok=False,
            status="blocked_vincisos_product_ui_target_availability",
            probe_version=PROBE_VERSION,
            target_name=validation.target_name,
            target_url=validation.target_url,
            blockers=blockers,
            contract_validation=validation.as_dict(),
            checks={
                "contract_ready": False,
                "local_http_probe_only": True,
                "browser_execution_allowed_by_this_probe": False,
                "timeout_seconds": timeout_seconds,
                "http_probe_attempted": False,
                "http_reachable": False,
            },
            next_allowed_step=None,
        )
    return probe_vincisos_product_ui_target(
        {
            "contract_version": validation.contract_version,
            "target_name": validation.target_name,
            "target_url": validation.target_url,
            "target_kind": validation.checks.get("target_kind"),
            "mode": validation.checks.get("mode"),
            "safe_mode_asserted": validation.checks.get("safe_mode_asserted"),
            "safe_mode_evidence": "validated by contract file",
            "allowed_hosts": validation.checks.get("allowed_hosts"),
            "allowed_actions": validation.checks.get("allowed_actions"),
            "expected_artifacts": validation.checks.get("expected_artifacts"),
            "draft_only": validation.checks.get("draft_only"),
            "require_running_target": False,
            "probe_reachability": False,
            "forbidden_authority": validation.checks.get("forbidden_authority"),
        },
        timeout_seconds=timeout_seconds,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Probe a VincisOS product UI target without launching a browser."
    )
    parser.add_argument("--contract-json", required=True, help="Path to a JSON target contract.")
    parser.add_argument("--timeout-seconds", type=float, default=2.0)
    parser.add_argument("--json", action="store_true", help="Print JSON output. Text output is not implemented.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    result = probe_vincisos_product_ui_target_file(
        Path(args.contract_json),
        timeout_seconds=args.timeout_seconds,
    )
    print(json.dumps(result.as_dict(), indent=2))
    return 0 if result.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
