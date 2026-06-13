"""Tests for Core export sanitizer rewrite and template preview modes."""

from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[2]
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))


def test_sanitized_rewrite_mode_scans_rendered_output_not_private_source(tmp_path: Path) -> None:
    from runtime.core_export.exporter import build_dry_run_report

    source = tmp_path / "live-vault"
    source.mkdir()
    (source / "README.md").write_text(
        "# ChaseOS\n\n"
        "Private source path: <VAULT_ROOT>\n\n"
        "Operational truth lives in 00_HOME/ and 07_LOGS/.\n"
        "Runtime binding notes mention runtime/agent_bus/ and discord_instance_bindings.yaml.\n",
        encoding="utf-8",
    )
    target = tmp_path / "chaseos-core"
    manifest = source / "export_manifest.yaml"
    manifest.write_text(
        "\n".join(
            [
                "version: 0.1",
                "source_root_mode: live-personal-instance",
                f"default_target: {target.as_posix()}",
                "mode: allowlist-only",
                "include:",
                "  - source: README.md",
                "    target: README.md",
                "    mode: sanitized_rewrite",
                "    sanitizer: framework_docs_v1",
                "exclude_always:",
                "  - 00_HOME/",
                "  - 07_LOGS/",
            ]
        ),
        encoding="utf-8",
    )

    report = build_dry_run_report(source_root=source, target_root=target, manifest_path=manifest)

    assert report["ok"] is True
    assert report["scanner"]["blocking_count"] == 0
    candidate = report["candidates"][0]
    assert candidate["mode"] == "sanitized_rewrite"
    assert candidate["sanitizer"] == "framework_docs_v1"
    assert candidate["rewrite_applied"] is True
    assert candidate["preview_sha256"]
    assert "<WINDOWS_USER_HOME_WSL>" not in candidate["preview_text"]
    assert "00_HOME/" not in candidate["preview_text"]
    assert "07_LOGS/" not in candidate["preview_text"]
    assert "runtime/agent_bus/" not in candidate["preview_text"]
    assert "discord_instance_bindings" not in candidate["preview_text"]
    assert "[LOCAL_PATH_REDACTED]" in candidate["preview_text"]
    assert "docs/framework-home/" in candidate["preview_text"]
    assert not target.exists()


def test_core_template_mode_uses_curated_template_instead_of_live_private_source(tmp_path: Path) -> None:
    from runtime.core_export.exporter import build_dry_run_report

    source = tmp_path / "live-vault"
    source.mkdir()
    (source / "README.md").write_text(
        "# Live Private README\n\n<VAULT_ROOT> and 00_HOME/\n",
        encoding="utf-8",
    )
    templates = source / "core_export" / "templates"
    templates.mkdir(parents=True)
    (templates / "README.core.md").write_text(
        "# ChaseOS Core\n\nPublic framework template only.\n",
        encoding="utf-8",
    )
    target = tmp_path / "chaseos-core"
    manifest = source / "export_manifest.yaml"
    manifest.write_text(
        "\n".join(
            [
                "version: 0.1",
                "source_root_mode: live-personal-instance",
                f"default_target: {target.as_posix()}",
                "mode: allowlist-only",
                "include:",
                "  - source: README.md",
                "    target: README.md",
                "    mode: core_template",
                "    template: core_export/templates/README.core.md",
                "exclude_always:",
                "  - 00_HOME/",
            ]
        ),
        encoding="utf-8",
    )

    report = build_dry_run_report(source_root=source, target_root=target, manifest_path=manifest)

    assert report["ok"] is True
    candidate = report["candidates"][0]
    assert candidate["mode"] == "core_template"
    assert candidate["template"] == "core_export/templates/README.core.md"
    assert candidate["preview_text"] == "# ChaseOS Core\n\nPublic framework template only.\n"
    assert report["scanner"]["blocking_count"] == 0
    assert not target.exists()


def test_live_core_manifest_switches_blocked_docs_to_curated_templates() -> None:
    import tempfile
    import yaml

    from runtime.core_export.exporter import build_dry_run_report

    manifest_path = _VAULT_ROOT / "core_export" / "export_manifest.yaml"
    _tmp = tempfile.TemporaryDirectory()
    dry_run_target = Path(_tmp.name) / "chaseos-core"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    include_by_target = {item["target"]: item for item in manifest["include"]}

    for target in ("CORE_MANIFEST.md", "README.md", "PROJECT_FOUNDATION.md"):
        item = include_by_target[target]
        assert item["mode"] == "core_template"
        template = item["template"]
        assert template == f"core_export/templates/{target.removesuffix('.md')}.core.md"
        assert (_VAULT_ROOT / template).is_file()

    report = build_dry_run_report(
        source_root=_VAULT_ROOT,
        target_root=dry_run_target,
        manifest_path=manifest_path,
    )

    assert report["ok"] is True
    assert report["scanner"]["blocking_count"] == 0
    candidates = {candidate["target"]: candidate for candidate in report["candidates"]}
    for target in ("CORE_MANIFEST.md", "README.md", "PROJECT_FOUNDATION.md"):
        candidate = candidates[target]
        assert candidate["mode"] == "core_template"
        assert candidate["template"].endswith(f"/{target.removesuffix('.md')}.core.md")
        preview = candidate["preview_text"]
        assert "TradeSync" not in preview
        assert "StrikeZone" not in preview
        assert "OpenClaw" not in preview
        assert "Hermes" not in preview
        assert "Discord" not in preview
        assert "[LOCAL_PATH_REDACTED]" not in preview
        assert "Owner label" not in preview
        assert "Refactor note" not in preview
        assert "Codex GPT" not in preview
        assert "â" not in preview
        assert not dry_run_target.exists()


def test_sanitized_rewrite_unknown_sanitizer_fails_closed(tmp_path: Path) -> None:
    from runtime.core_export.exporter import build_dry_run_report

    source = tmp_path / "live-vault"
    source.mkdir()
    (source / "README.md").write_text("# Core\n", encoding="utf-8")
    target = tmp_path / "chaseos-core"
    manifest = source / "export_manifest.yaml"
    manifest.write_text(
        "\n".join(
            [
                "version: 0.1",
                "source_root_mode: live-personal-instance",
                f"default_target: {target.as_posix()}",
                "mode: allowlist-only",
                "include:",
                "  - source: README.md",
                "    target: README.md",
                "    mode: sanitized_rewrite",
                "    sanitizer: missing_sanitizer",
            ]
        ),
        encoding="utf-8",
    )

    report = build_dry_run_report(source_root=source, target_root=target, manifest_path=manifest)

    assert report["ok"] is False
    assert any("unknown sanitizer" in issue for issue in report["blocking_issues"])
    assert report["writes_performed"] is False
    assert not target.exists()
