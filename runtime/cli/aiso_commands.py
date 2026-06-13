from __future__ import annotations

import argparse
import json
from pathlib import Path

from runtime.aiso.recent_artifact_locator import DEFAULT_SAFE_ROOTS, locate_recent_artifacts


def cmd_aiso_recent_artifacts(args: argparse.Namespace) -> int:
    vault_root = Path(getattr(args, "vault_root", None) or ".").resolve()
    roots = getattr(args, "roots", None) or list(DEFAULT_SAFE_ROOTS)
    suffixes = getattr(args, "suffixes", None) or None
    payload = locate_recent_artifacts(
        vault_root=vault_root,
        roots=roots,
        suffixes=suffixes,
        limit=int(getattr(args, "limit", 25)),
        since=getattr(args, "since", None),
    )
    if getattr(args, "output_json", False):
        print(json.dumps(payload, indent=2, default=str))
        return 0

    print("AISO recent artifact locator (read-only):")
    print(f"  scanned_roots: {len(payload['scanned_roots'])}")
    print(f"  blocked_roots: {len(payload['blocked_roots'])}")
    print(f"  artifacts: {payload['artifact_count']}")
    for item in payload["artifacts"]:
        print(f"  - {item['relative_path']} ({item['size_bytes']} bytes, {item['modified_at_utc']})")
    print("  authority: read-only; no rename/package/email/browser/provider/submission performed")
    return 0
