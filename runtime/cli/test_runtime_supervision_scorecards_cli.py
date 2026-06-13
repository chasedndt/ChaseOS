from __future__ import annotations

import json
import sys
from pathlib import Path

VAULT_ROOT = Path(__file__).resolve().parents[2]
if str(VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(VAULT_ROOT))

import runtime.cli.main as cli  # noqa: E402


def test_runtime_supervision_cli_reports_visibility_only_scorecards(tmp_path: Path, capsys) -> None:
    audit_dir = tmp_path / "07_LOGS" / "Agent-Activity"
    audit_dir.mkdir(parents=True)
    (audit_dir / "20260606-120000__operator_today__hermes.json").write_text(
        json.dumps(
            {
                "audit_id": "audit-hermes",
                "runtime_id": "hermes",
                "workflow_id": "operator_today",
                "timestamp_utc": "2026-06-06T12:00:00Z",
                "status": "success",
            }
        ),
        encoding="utf-8",
    )
    before = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*") if path.is_file())

    exit_code = cli.main(["runtime", "supervision", "--vault-root", str(tmp_path), "--json"])

    payload = json.loads(capsys.readouterr().out)
    after = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*") if path.is_file())
    result = payload["result"]
    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "runtime.supervision"
    assert result["surface"] == "runtime_supervision_scorecards"
    assert result["scorecards"][0]["runtime_id"] == "hermes"
    assert result["authority"]["visibility_only"] is True
    assert result["authority"]["runtime_dispatch_performed"] is False
    assert result["authority"]["canonical_state_written"] is False
    assert after == before
