from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from runtime.repo_secret_audit import audit_repo_secrets
from runtime.cli.main import main


def test_repo_secret_audit_classifies_placeholders_and_known_sentinels_without_leaking_values(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "provider.md").write_text(
        "Use pplx-YOUR_KEY_HERE in examples only.\n"
        "Webhook placeholder: https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN\n"
        "Known sentinel: secret-token\n",
        encoding="utf-8",
    )

    report = audit_repo_secrets(tmp_path)

    assert report["summary"]["high_confidence_secret_count"] == 0
    assert report["summary"]["placeholder_or_doc_reference_count"] == 3
    assert report["ok"] is True
    classes = {finding["classification"] for finding in report["findings"]}
    assert "placeholder_or_doc_reference" in classes
    assert "allowlisted_sentinel" in classes
    rendered = json.dumps(report)
    assert "pplx-YOUR_KEY_HERE" not in rendered
    assert "YOUR_WEBHOOK_TOKEN" not in rendered
    assert "secret-token" not in rendered


def test_repo_secret_audit_flags_high_confidence_live_secret_without_emitting_secret(tmp_path: Path) -> None:
    secret = "pplx-" + "a" * 48
    (tmp_path / "runtime").mkdir()
    (tmp_path / "runtime" / "config.py").write_text(f'API_KEY = "{secret}"\n', encoding="utf-8")

    report = audit_repo_secrets(tmp_path)

    assert report["ok"] is False
    assert report["summary"]["high_confidence_secret_count"] == 1
    finding = report["findings"][0]
    assert finding["classification"] == "high_confidence_secret"
    assert finding["provider"] == "perplexity"
    assert "redacted_preview" in finding
    assert secret not in json.dumps(report)


def test_repo_secret_audit_skips_private_env_files_without_reading_values(tmp_path: Path) -> None:
    private_secret = "pplx-" + "b" * 48
    (tmp_path / ".env").write_text(f"PPLX_API_KEY={private_secret}\n", encoding="utf-8")
    (tmp_path / ".env.example").write_text("PPLX_API_KEY=pplx-YOUR_KEY_HERE\n", encoding="utf-8")

    report = audit_repo_secrets(tmp_path)

    assert report["summary"]["high_confidence_secret_count"] == 0
    assert report["summary"]["private_file_skipped_count"] == 1
    assert report["summary"]["placeholder_or_doc_reference_count"] == 1
    rendered = json.dumps(report)
    assert private_secret not in rendered
    assert "pplx-YOUR_KEY_HERE" not in rendered


def test_repo_secret_audit_skips_symlink_alias_to_private_env_without_reading_value(tmp_path: Path) -> None:
    private_secret = "pplx-" + "c" * 48
    (tmp_path / ".env").write_text(f"PPLX_API_KEY={private_secret}\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "env-link.md").symlink_to(Path("../.env"))

    report = audit_repo_secrets(tmp_path)

    assert report["summary"]["high_confidence_secret_count"] == 0
    assert report["summary"]["private_file_skipped_count"] == 2
    assert report["summary"]["scanned_file_count"] == 0
    assert "docs/env-link.md" in report["skipped_private_files"]
    assert private_secret not in json.dumps(report)


def test_repo_secret_audit_skips_hardlink_alias_to_private_env_without_reading_value(tmp_path: Path) -> None:
    private_secret = "pplx-" + "d" * 48
    private_env = tmp_path / ".env"
    hardlink_alias = tmp_path / "docs" / "env-hardlink.md"
    private_env.write_text(f"PPLX_API_KEY={private_secret}\n", encoding="utf-8")
    hardlink_alias.parent.mkdir()
    try:
        os.link(private_env, hardlink_alias)
    except OSError as exc:
        pytest.skip(f"filesystem does not support hardlinks: {exc}")

    report = audit_repo_secrets(tmp_path)

    assert report["summary"]["high_confidence_secret_count"] == 0
    assert report["summary"]["private_file_skipped_count"] == 2
    assert report["summary"]["scanned_file_count"] == 0
    assert "docs/env-hardlink.md" in report["skipped_private_files"]
    assert private_secret not in json.dumps(report)


def test_repo_secret_audit_cli_json_contract(tmp_path: Path, capsys) -> None:
    (tmp_path / "README.md").write_text("pplx-YOUR_KEY_HERE\n", encoding="utf-8")

    exit_code = main(["audit", "secrets", "--vault-root", str(tmp_path), "--json"])

    assert exit_code == 0
    envelope = json.loads(capsys.readouterr().out)
    assert envelope["action"] == "audit.secrets"
    assert envelope["ok"] is True
    result = envelope["result"]
    assert result["surface"] == "repo_safe_secret_audit"
    assert result["summary"]["placeholder_or_doc_reference_count"] == 1
