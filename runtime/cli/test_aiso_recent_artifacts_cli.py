from __future__ import annotations

import json
import os
import sys
from pathlib import Path

VAULT_ROOT = Path(__file__).resolve().parents[2]
if str(VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(VAULT_ROOT))

import runtime.cli.main as cli  # noqa: E402


def test_aiso_recent_artifacts_cli_json_is_read_only(tmp_path: Path, capsys) -> None:
    target = tmp_path / "03_INPUTS" / "00_QUARANTINE" / "media" / "clip.mp4"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"video")
    os.utime(target, (1_700_000_000, 1_700_000_000))
    before = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*") if path.is_file())

    exit_code = cli.main([
        "aiso",
        "recent-artifacts",
        "--vault-root",
        str(tmp_path),
        "--root",
        "03_INPUTS/00_QUARANTINE",
        "--suffix",
        ".mp4",
        "--json",
    ])

    payload = json.loads(capsys.readouterr().out)
    after = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*") if path.is_file())
    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "aiso.recent-artifacts"
    assert payload["result"]["surface"] == "aiso_recent_artifact_locator"
    assert payload["result"]["authority"]["read_only"] is True
    assert payload["result"]["authority"]["write_performed"] is False
    assert payload["result"]["authority"]["email_or_external_send_allowed"] is False
    assert payload["result"]["artifacts"][0]["relative_path"] == "03_INPUTS/00_QUARANTINE/media/clip.mp4"
    assert after == before
