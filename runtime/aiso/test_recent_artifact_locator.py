from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from runtime.aiso.recent_artifact_locator import locate_recent_artifacts


def _touch(path: Path, *, mtime: int, content: bytes = b"x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    os.utime(path, (mtime, mtime))


def test_locator_returns_recent_video_artifacts_sorted_and_read_only(tmp_path: Path) -> None:
    vault = tmp_path
    root = vault / "03_INPUTS" / "00_QUARANTINE" / "media"
    older = root / "older.mp4"
    newer = root / "newer.mov"
    ignored = root / "notes.md"
    _touch(older, mtime=1_700_000_000, content=b"old")
    _touch(newer, mtime=1_700_000_500, content=b"new")
    _touch(ignored, mtime=1_700_001_000, content=b"# notes")
    before = sorted(p.relative_to(vault).as_posix() for p in vault.rglob("*") if p.is_file())

    result = locate_recent_artifacts(
        vault_root=vault,
        roots=["03_INPUTS/00_QUARANTINE"],
        suffixes=[".mp4", ".mov"],
        limit=10,
    )

    after = sorted(p.relative_to(vault).as_posix() for p in vault.rglob("*") if p.is_file())
    assert result["ok"] is True
    assert result["authority"]["read_only"] is True
    assert result["authority"]["write_performed"] is False
    assert result["authority"]["provider_call_performed"] is False
    assert result["authority"]["browser_access_performed"] is False
    assert [item["relative_path"] for item in result["artifacts"]] == [
        "03_INPUTS/00_QUARANTINE/media/newer.mov",
        "03_INPUTS/00_QUARANTINE/media/older.mp4",
    ]
    assert result["artifacts"][0]["suffix"] == ".mov"
    assert result["artifacts"][0]["size_bytes"] == 3
    assert result["artifacts"][0]["modified_at_utc"].endswith("Z")
    datetime.fromisoformat(result["artifacts"][0]["modified_at_utc"].replace("Z", "+00:00"))
    assert after == before


def test_locator_blocks_outside_vault_and_credential_like_roots(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    outside = tmp_path / "outside"
    vault.mkdir()
    outside.mkdir()
    _touch(outside / "leak.mp4", mtime=1_700_000_000)
    _touch(vault / ".env" / "secret.mp4", mtime=1_700_000_000)

    result = locate_recent_artifacts(
        vault_root=vault,
        roots=[str(outside), ".env"],
        suffixes=[".mp4"],
        limit=10,
    )

    assert result["ok"] is True
    assert result["artifacts"] == []
    assert {item["reason"] for item in result["blocked_roots"]} == {
        "root_outside_vault",
        "credential_or_browser_profile_root_blocked",
    }


def test_locator_respects_since_and_limit(tmp_path: Path) -> None:
    vault = tmp_path
    root = vault / "runtime" / "acquisition" / "packs"
    _touch(root / "old.mp4", mtime=1_600_000_000)
    _touch(root / "mid.mp4", mtime=1_700_000_000)
    _touch(root / "new.mp4", mtime=1_800_000_000)

    result = locate_recent_artifacts(
        vault_root=vault,
        roots=["runtime/acquisition/packs"],
        suffixes=[".mp4"],
        since="2023-11-14T22:13:20Z",  # 1_700_000_000
        limit=1,
    )

    assert [item["relative_path"] for item in result["artifacts"]] == [
        "runtime/acquisition/packs/new.mp4"
    ]
    assert result["candidate_count_before_limit"] == 2
