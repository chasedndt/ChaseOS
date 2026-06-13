"""Canonical CLI handlers for ChaseOS Core export dry-run planning."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from runtime.capture.capture import _detect_vault_root
from runtime.core_export.exporter import (
    build_core_export_next_step,
    build_core_export_public_repo_gates,
    build_core_export_readiness,
    build_core_export_request,
    build_dry_run_report,
    export_verified_core_tree,
    verify_dry_run_review_artifacts,
    verify_exported_core_tree,
    write_dry_run_review_artifacts,
)
from runtime.core_export.manifest import load_manifest


def _resolve_source(source_root: str | None) -> Path:
    if source_root:
        return Path(source_root)
    return _detect_vault_root()


def _resolve_manifest(source_root: Path, manifest: str | None) -> Path:
    if manifest:
        return Path(manifest)
    return source_root / "core_export" / "export_manifest.yaml"


def _resolve_target(
    target: str | None,
    *,
    source_root: Path,
    manifest_path: Path,
    manifest_target: str | None = None,
) -> Path:
    if target:
        return Path(target)
    env_target = os.environ.get("CHASEOS_CORE_EXPORT_TARGET")
    if env_target:
        return Path(env_target)
    if manifest_target:
        manifest_default = Path(manifest_target).expanduser()
        if manifest_default.is_absolute():
            return manifest_default
        return (manifest_path.parent / manifest_default).resolve()
    return source_root.parent / "chaseos-core"


def _resolve_target_from_manifest(source_root: Path, manifest_path: Path, target: str | None) -> Path:
    manifest = load_manifest(manifest_path)
    manifest_target = manifest.get("default_target")
    return _resolve_target(
        target,
        source_root=source_root,
        manifest_path=manifest_path,
        manifest_target=str(manifest_target) if manifest_target else None,
    )


def _resolve_report_dir(source_root: Path, report_dir: str | None) -> Path:
    if report_dir:
        return Path(report_dir)
    return source_root / "core_export" / "reports" / "latest"


def cmd_core_export_verify_export(args: argparse.Namespace) -> int:
    source_root = _resolve_source(getattr(args, "source_root", None))
    manifest_path = _resolve_manifest(source_root, getattr(args, "manifest", None))
    target_root = _resolve_target_from_manifest(source_root, manifest_path, getattr(args, "target", None))
    result = verify_exported_core_tree(
        source_root=source_root,
        target_root=target_root,
        manifest_path=manifest_path,
        report_dir=_resolve_report_dir(source_root, getattr(args, "report_dir", None)),
        manual_review_path=getattr(args, "manual_review", None),
    )
    print(json.dumps(result, indent=2))
    return 0 if result.get("ok") else 1


def cmd_core_export_next_step(args: argparse.Namespace) -> int:
    source_root = _resolve_source(getattr(args, "source_root", None))
    manifest_path = _resolve_manifest(source_root, getattr(args, "manifest", None))
    target_root = _resolve_target_from_manifest(source_root, manifest_path, getattr(args, "target", None))
    result = build_core_export_next_step(
        source_root=source_root,
        target_root=target_root,
        manifest_path=manifest_path,
        report_dir=_resolve_report_dir(source_root, getattr(args, "report_dir", None)),
        manual_review_path=getattr(args, "manual_review", None),
        requested_by=getattr(args, "requested_by", None),
    )
    print(json.dumps(result, indent=2))
    return 0 if result.get("ok") else 1


def cmd_core_export_request_export(args: argparse.Namespace) -> int:
    source_root = _resolve_source(getattr(args, "source_root", None))
    manifest_path = _resolve_manifest(source_root, getattr(args, "manifest", None))
    target_root = _resolve_target_from_manifest(source_root, manifest_path, getattr(args, "target", None))
    result = build_core_export_request(
        source_root=source_root,
        target_root=target_root,
        manifest_path=manifest_path,
        report_dir=_resolve_report_dir(source_root, getattr(args, "report_dir", None)),
        manual_review_path=getattr(args, "manual_review", None),
        requested_by=getattr(args, "requested_by", None),
    )
    print(json.dumps(result, indent=2))
    return 0 if result.get("ok") else 1


def cmd_core_export_export(args: argparse.Namespace) -> int:
    source_root = _resolve_source(getattr(args, "source_root", None))
    manifest_path = _resolve_manifest(source_root, getattr(args, "manifest", None))
    target_root = _resolve_target_from_manifest(source_root, manifest_path, getattr(args, "target", None))
    result = export_verified_core_tree(
        source_root=source_root,
        target_root=target_root,
        manifest_path=manifest_path,
        report_dir=_resolve_report_dir(source_root, getattr(args, "report_dir", None)),
        manual_review_path=getattr(args, "manual_review", None),
        operator_approval_ref=getattr(args, "operator_approval_ref", None),
        confirm=getattr(args, "confirm", False),
        update_existing=getattr(args, "update_existing", False),
    )
    print(json.dumps(result, indent=2))
    return 0 if result.get("ok") else 1


def cmd_core_export_readiness(args: argparse.Namespace) -> int:
    source_root = _resolve_source(getattr(args, "source_root", None))
    manifest_path = _resolve_manifest(source_root, getattr(args, "manifest", None))
    target_root = _resolve_target_from_manifest(source_root, manifest_path, getattr(args, "target", None))
    result = build_core_export_readiness(
        source_root=source_root,
        target_root=target_root,
        manifest_path=manifest_path,
        report_dir=_resolve_report_dir(source_root, getattr(args, "report_dir", None)),
        manual_review_path=getattr(args, "manual_review", None),
    )
    print(json.dumps(result, indent=2))
    return 0 if result.get("ok") else 1


def cmd_core_export_public_repo_gates(args: argparse.Namespace) -> int:
    source_root = _resolve_source(getattr(args, "source_root", None))
    manifest_path = _resolve_manifest(source_root, getattr(args, "manifest", None))
    target_root = _resolve_target_from_manifest(source_root, manifest_path, getattr(args, "target", None))
    result = build_core_export_public_repo_gates(
        source_root=source_root,
        target_root=target_root,
        manifest_path=manifest_path,
        report_dir=_resolve_report_dir(source_root, getattr(args, "report_dir", None)),
        manual_review_path=getattr(args, "manual_review", None),
        requested_by=getattr(args, "requested_by", None),
    )
    print(json.dumps(result, indent=2))
    return 0 if result.get("ok") else 1


def cmd_core_export_verify_report(args: argparse.Namespace) -> int:
    source_root = _resolve_source(getattr(args, "source_root", None))
    manifest_path = _resolve_manifest(source_root, getattr(args, "manifest", None))
    target_root = _resolve_target_from_manifest(source_root, manifest_path, getattr(args, "target", None))
    result = verify_dry_run_review_artifacts(
        source_root=source_root,
        target_root=target_root,
        manifest_path=manifest_path,
        report_dir=_resolve_report_dir(source_root, getattr(args, "report_dir", None)),
    )
    print(json.dumps(result, indent=2))
    return 0 if result.get("ok") else 1


def cmd_core_export_build(args: argparse.Namespace) -> int:
    if not getattr(args, "dry_run", False):
        payload = {
            "ok": False,
            "dry_run": False,
            "writes_performed": False,
            "blocking_issues": ["core-export build is currently dry-run only; pass --dry-run"],
        }
        print(json.dumps(payload, indent=2))
        return 1

    source_root = _resolve_source(getattr(args, "source_root", None))
    manifest_path = _resolve_manifest(source_root, getattr(args, "manifest", None))
    target_root = _resolve_target_from_manifest(source_root, manifest_path, getattr(args, "target", None))
    report = build_dry_run_report(
        source_root=source_root,
        target_root=target_root,
        manifest_path=manifest_path,
    )
    if getattr(args, "write_report", False):
        try:
            report["report_artifacts"] = write_dry_run_review_artifacts(
                report,
                _resolve_report_dir(source_root, getattr(args, "report_dir", None)),
            )
        except ValueError as exc:
            report["ok"] = False
            report.setdefault("blocking_issues", []).append(str(exc))
    print(json.dumps(report, indent=2))
    return 0 if report.get("ok") else 1
