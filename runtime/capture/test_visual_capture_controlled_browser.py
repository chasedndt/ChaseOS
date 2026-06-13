from __future__ import annotations

from pathlib import Path

import pytest

from runtime.capture.visual_capture import capture_from_controlled_browser_artifact


def _write_browser_artifact(vault: Path, relative_path: str, html: str) -> Path:
    path = vault / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    return path


def test_controlled_browser_artifact_extracts_local_page_without_writes(tmp_path: Path) -> None:
    artifact = _write_browser_artifact(
        tmp_path,
        "07_LOGS/Browser-Runs/local/default/example-page.html",
        (
            "<html><head><title>Controlled Page</title></head>"
            "<body><nav>Skip nav</nav><h1>Controlled Heading</h1>"
            "<p>Useful controlled paragraph.</p></body></html>"
        ),
    )

    packet = capture_from_controlled_browser_artifact(
        file_path=artifact,
        vault_root=tmp_path,
        declared_url="https://example.com/research/page",
        allowed_origin="https://example.com",
        title="Controlled Browser Clip",
        captured_at="2026-05-20T12:34:56Z",
        capture_id="vcmi_20260520123456_ctrl001",
    )

    assert packet.routing.status == "preview_only"
    assert packet.capture_method == "controlled_browser_dom"
    assert packet.source.source_app == "browser-runtime-controlled-artifact"
    assert packet.source.source_url == "https://example.com/research/page"
    assert packet.source.declared_source == "07_LOGS/Browser-Runs/local/default/example-page.html"
    assert "Useful controlled paragraph." in packet.content.raw_extracted_text
    assert "Skip nav" not in packet.content.raw_extracted_text
    assert "controlled_browser_artifact_confined" in packet.quality.extraction_warnings
    assert any(
        step["step"] == "controlled_browser_artifact_validate"
        for step in packet.provenance["transformation_chain"]
    )
    assert not (tmp_path / "03_INPUTS").exists()


def test_controlled_browser_artifact_can_use_studio_webview_selector(tmp_path: Path) -> None:
    artifact = _write_browser_artifact(
        tmp_path,
        "runtime/studio/webview_artifacts/owned-webview.html",
        "<html><head><title>Owned Webview</title></head><body><p>Owned DOM text.</p></body></html>",
    )

    packet = capture_from_controlled_browser_artifact(
        file_path=artifact,
        vault_root=tmp_path,
        declared_url="https://docs.example.test/page",
        source_selector="studio_webview_export",
        title="Owned Webview Clip",
    )

    assert packet.source.source_app == "studio-controlled-webview"
    assert packet.source.declared_source == "runtime/studio/webview_artifacts/owned-webview.html"
    assert "Owned DOM text." in packet.content.raw_extracted_text


def test_controlled_browser_artifact_blocks_outside_allowed_dirs(tmp_path: Path) -> None:
    artifact = _write_browser_artifact(
        tmp_path,
        "downloads/page.html",
        "<html><body><p>Not an allowed browser artifact.</p></body></html>",
    )

    with pytest.raises(ValueError, match="allowed browser evidence directory|allowed browser"):
        capture_from_controlled_browser_artifact(
            file_path=artifact,
            vault_root=tmp_path,
            declared_url="https://example.com/page",
        )


def test_controlled_browser_artifact_blocks_outside_vault_root(tmp_path: Path) -> None:
    outside = tmp_path.parent / f"{tmp_path.name}-outside.html"
    outside.write_text("<html><body><p>Outside vault.</p></body></html>", encoding="utf-8")

    with pytest.raises(ValueError, match="outside the vault root"):
        capture_from_controlled_browser_artifact(
            file_path=outside,
            vault_root=tmp_path,
            declared_url="https://example.com/page",
        )


@pytest.mark.parametrize(
    ("html", "match"),
    [
        ("<html><body><form><input name='q'></form></body></html>", "forms_not_allowed"),
        ("<html><body><input type='password' name='pw'></body></html>", "password_inputs_not_allowed"),
        ("<html><body><input type='file' name='upload'></body></html>", "file_inputs_not_allowed"),
        ("<html><body><a href='report.pdf' download>download</a></body></html>", "downloads_not_allowed"),
        ("<html><body><p>chrome://history export</p></body></html>", "browser_history_not_allowed"),
        ("<html><body><script>document.cookie = 'x'</script></body></html>", "browser_session_storage_not_allowed"),
    ],
)
def test_controlled_browser_artifact_blocks_forms_downloads_history_and_storage(
    tmp_path: Path,
    html: str,
    match: str,
) -> None:
    artifact = _write_browser_artifact(tmp_path, "07_LOGS/Browser-Runs/local/default/blocked.html", html)

    with pytest.raises(ValueError, match=match):
        capture_from_controlled_browser_artifact(
            file_path=artifact,
            vault_root=tmp_path,
            declared_url="https://example.com/page",
        )


def test_controlled_browser_artifact_blocks_history_or_cookie_artifact_paths(tmp_path: Path) -> None:
    artifact = _write_browser_artifact(
        tmp_path,
        "07_LOGS/Browser-Runs/browser-history/export.html",
        "<html><body><p>History export path.</p></body></html>",
    )

    with pytest.raises(ValueError, match="history, cookies, sessions"):
        capture_from_controlled_browser_artifact(
            file_path=artifact,
            vault_root=tmp_path,
            declared_url="https://example.com/page",
        )


@pytest.mark.parametrize(
    "declared_url",
    [
        "file:///tmp/page.html",
        "https://user:password@example.com/page",
        "https://example.com/page?access_token=abc123",
    ],
)
def test_controlled_browser_artifact_requires_safe_declared_url(tmp_path: Path, declared_url: str) -> None:
    artifact = _write_browser_artifact(
        tmp_path,
        "07_LOGS/Browser-Runs/local/default/url-check.html",
        "<html><body><p>URL check.</p></body></html>",
    )

    with pytest.raises(ValueError):
        capture_from_controlled_browser_artifact(
            file_path=artifact,
            vault_root=tmp_path,
            declared_url=declared_url,
        )


def test_controlled_browser_artifact_blocks_origin_mismatch(tmp_path: Path) -> None:
    artifact = _write_browser_artifact(
        tmp_path,
        "07_LOGS/Browser-Runs/local/default/origin-check.html",
        "<html><body><p>Origin check.</p></body></html>",
    )

    with pytest.raises(ValueError, match="does not match allowed_origin"):
        capture_from_controlled_browser_artifact(
            file_path=artifact,
            vault_root=tmp_path,
            declared_url="https://example.com/page",
            allowed_origin="https://other.example",
        )
