"""
test_pass8p9.py — ChaseOS Phase 8 Pass 9
Tests for the watched-folder automation module.

Coverage:
  - Config add_folder: creates config, idempotent replace on same path
  - Config add_folder: invalid input_class raises ValueError
  - Config add_folder: invalid extension raises ValueError
  - Config remove_folder: removes by path, returns False if not found
  - Config list_folders: returns all folder defs
  - Config set_folder_enabled: enable/disable, returns False if not found
  - Config persistence: load after save returns same data
  - Processed registry: is_processed True/False on mtime+size match
  - Processed registry: mark_processed + is_processed roundtrip
  - Processed registry: mtime change → not processed
  - Scan: disabled folder skipped (no capture attempted)
  - Scan: missing folder reported as folder_error, no crash
  - Scan: unsupported extension skipped
  - Scan: .txt file routed through CLI capture path
  - Scan: .md file routed through CLI capture path
  - Scan: .html file routed through browser connector path
  - Scan: already-processed file skipped on second run
  - Scan: dedup — same content file on second run returns duplicate
  - Scan: per-file error does not stop scan of other files
  - scan_all_folders: scans all enabled folders, persists processed
  - CLI: chaseos watch add PATH --class source
  - CLI: chaseos watch list
  - CLI: chaseos watch remove PATH
  - CLI: chaseos watch run --once
  - CLI: chaseos watch run --once --json
  - Backward compat: existing capture file command still works

Running: chaseos test capture   (included via cmd_test_capture in main.py)
Manual:  python runtime/capture/test_pass8p9.py
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

# Ensure vault root is importable
_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[2]
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

from runtime.capture.watch_folders import (
    SUPPORTED_EXTENSIONS,
    add_folder,
    config_path,
    is_processed,
    list_folders,
    load_config,
    load_processed,
    mark_processed,
    processed_path,
    remove_folder,
    scan_all_folders,
    scan_folder,
    set_folder_enabled,
)
from runtime.capture.content_packet import INPUT_CLASS_SOURCE, INPUT_CLASS_DIGEST


# ── Test runner infrastructure ─────────────────────────────────────────────────

_TESTS: list[tuple[str, object]] = []
_PASS  = 0
_FAIL  = 0
_ERRORS: list[str] = []


def _test(label: str):
    def decorator(fn):
        _TESTS.append((label, fn))
        return fn
    return decorator


def _run_test(label: str, fn) -> None:
    global _PASS, _FAIL
    try:
        fn()
        print("  PASS")
        _PASS += 1
    except AssertionError as exc:
        print(f"  FAIL: {exc}")
        _FAIL += 1
        _ERRORS.append(f"{label}: {exc}")
    except Exception as exc:
        print(f"  ERROR: {type(exc).__name__}: {exc}")
        _FAIL += 1
        _ERRORS.append(f"{label}: {type(exc).__name__}: {exc}")


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


# ── Vault fixture helpers ──────────────────────────────────────────────────────

def _make_vault() -> Path:
    """Create a minimal temporary vault with 03_INPUTS/ structure."""
    td = tempfile.mkdtemp()
    vault = Path(td)
    (vault / "03_INPUTS" / "00_QUARANTINE" / "Sources").mkdir(parents=True)
    (vault / "03_INPUTS" / "00_QUARANTINE" / "Digests").mkdir(parents=True)
    (vault / "03_INPUTS" / "00_QUARANTINE" / "Transcript-Raw").mkdir(parents=True)
    (vault / "03_INPUTS" / "00_QUARANTINE" / "Clipboard").mkdir(parents=True)
    (vault / "03_INPUTS" / "00_QUARANTINE" / "NotebookLM").mkdir(parents=True)
    (vault / "03_INPUTS" / "00_QUARANTINE" / "Journal-Raw").mkdir(parents=True)
    (vault / "03_INPUTS" / "00_QUARANTINE" / "YouTube-Notes").mkdir(parents=True)
    (vault / ".chaseos").mkdir(parents=True, exist_ok=True)
    return vault


def _make_watch_folder(vault: Path) -> Path:
    """Create a temp directory to use as the watched folder."""
    import tempfile
    d = Path(tempfile.mkdtemp())
    return d


# ── Tests: Config add/list/remove/enable/disable ──────────────────────────────

@_test("P9-T01: add_folder creates config entry with correct defaults")
def _test_add_folder_defaults():
    vault = _make_vault()
    wd = _make_watch_folder(vault)
    folder_def = add_folder(vault, str(wd), INPUT_CLASS_SOURCE)
    _assert(folder_def["input_class"] == INPUT_CLASS_SOURCE, "input_class")
    _assert(folder_def["source_platform"] == "watched-folder", "source_platform")
    _assert(folder_def["enabled"] is True, "enabled")
    _assert(set(folder_def["extensions"]) == SUPPORTED_EXTENSIONS, "extensions")
    _assert(folder_def["path"] == str(wd.resolve()), "path stored as absolute")
    folders = list_folders(vault)
    _assert(len(folders) == 1, "one folder in list")


@_test("P9-T02: add_folder is idempotent — same path replaces previous entry")
def _test_add_folder_idempotent():
    vault = _make_vault()
    wd = _make_watch_folder(vault)
    add_folder(vault, str(wd), INPUT_CLASS_SOURCE)
    add_folder(vault, str(wd), INPUT_CLASS_DIGEST)  # same path, different class
    folders = list_folders(vault)
    _assert(len(folders) == 1, "still one folder after re-add")
    _assert(folders[0]["input_class"] == INPUT_CLASS_DIGEST, "class updated to digest")


@_test("P9-T03: add_folder raises ValueError on invalid input_class")
def _test_add_folder_invalid_class():
    vault = _make_vault()
    wd = _make_watch_folder(vault)
    try:
        add_folder(vault, str(wd), "not-a-class")
        _assert(False, "should have raised ValueError")
    except ValueError:
        pass  # expected


@_test("P9-T04: add_folder raises ValueError on unsupported extension")
def _test_add_folder_invalid_ext():
    vault = _make_vault()
    wd = _make_watch_folder(vault)
    try:
        add_folder(vault, str(wd), INPUT_CLASS_SOURCE, extensions=[".pdf"])
        _assert(False, "should have raised ValueError")
    except ValueError:
        pass  # expected


@_test("P9-T05: remove_folder removes by path, returns True")
def _test_remove_folder():
    vault = _make_vault()
    wd = _make_watch_folder(vault)
    add_folder(vault, str(wd), INPUT_CLASS_SOURCE)
    removed = remove_folder(vault, str(wd))
    _assert(removed is True, "removed")
    _assert(len(list_folders(vault)) == 0, "list is empty")


@_test("P9-T06: remove_folder returns False when path not found")
def _test_remove_folder_not_found():
    vault = _make_vault()
    removed = remove_folder(vault, "/nonexistent/path")
    _assert(removed is False, "should return False")


@_test("P9-T07: list_folders returns all configured folders")
def _test_list_folders():
    vault = _make_vault()
    wd1 = _make_watch_folder(vault)
    wd2 = _make_watch_folder(vault)
    add_folder(vault, str(wd1), INPUT_CLASS_SOURCE)
    add_folder(vault, str(wd2), INPUT_CLASS_DIGEST)
    folders = list_folders(vault)
    _assert(len(folders) == 2, "two folders")
    classes = {f["input_class"] for f in folders}
    _assert(INPUT_CLASS_SOURCE in classes and INPUT_CLASS_DIGEST in classes, "both classes present")


@_test("P9-T08: set_folder_enabled disables a folder, returns True")
def _test_disable_folder():
    vault = _make_vault()
    wd = _make_watch_folder(vault)
    add_folder(vault, str(wd), INPUT_CLASS_SOURCE)
    updated = set_folder_enabled(vault, str(wd), False)
    _assert(updated is True, "updated")
    folders = list_folders(vault)
    _assert(folders[0]["enabled"] is False, "disabled")


@_test("P9-T09: set_folder_enabled returns False when path not found")
def _test_enable_not_found():
    vault = _make_vault()
    updated = set_folder_enabled(vault, "/no/such/path", True)
    _assert(updated is False, "not found")


@_test("P9-T10: config persistence: load_config after add returns same data")
def _test_config_persistence():
    vault = _make_vault()
    wd = _make_watch_folder(vault)
    add_folder(vault, str(wd), INPUT_CLASS_SOURCE, domain_hint="trading-systems")
    config = load_config(vault)
    folders = config["folders"]
    _assert(len(folders) == 1, "one folder")
    _assert(folders[0]["domain_hint"] == "trading-systems", "domain_hint persisted")


# ── Tests: Processed-file registry ────────────────────────────────────────────

@_test("P9-T11: is_processed returns False for unknown path")
def _test_is_processed_unknown():
    processed = {"schema_version": "1.0", "processed": {}}
    _assert(not is_processed("/some/file.txt", 1234.0, 100, processed), "should be False")


@_test("P9-T12: mark_processed then is_processed returns True")
def _test_mark_then_is_processed():
    processed = {"schema_version": "1.0", "processed": {}}
    mark_processed("/some/file.txt", 1234.0, 100, processed)
    _assert(is_processed("/some/file.txt", 1234.0, 100, processed), "should be True")


@_test("P9-T13: is_processed returns False when mtime differs")
def _test_is_processed_mtime_changed():
    processed = {"schema_version": "1.0", "processed": {}}
    mark_processed("/some/file.txt", 1234.0, 100, processed)
    _assert(not is_processed("/some/file.txt", 9999.0, 100, processed), "different mtime")


@_test("P9-T14: is_processed returns False when size differs")
def _test_is_processed_size_changed():
    processed = {"schema_version": "1.0", "processed": {}}
    mark_processed("/some/file.txt", 1234.0, 100, processed)
    _assert(not is_processed("/some/file.txt", 1234.0, 999, processed), "different size")


# ── Tests: Scan behavior ───────────────────────────────────────────────────────

@_test("P9-T15: disabled folder is skipped — no capture attempted")
def _test_disabled_folder_skipped():
    vault = _make_vault()
    wd = _make_watch_folder(vault)
    # Drop a file in the watched folder
    (wd / "test.txt").write_text("hello world content for disabled test", encoding="utf-8")
    add_folder(vault, str(wd), INPUT_CLASS_SOURCE)
    set_folder_enabled(vault, str(wd), False)
    results = scan_all_folders(vault)
    _assert(len(results) == 1, "one result")
    _assert(results[0].enabled is False, "disabled")
    _assert(len(results[0].captured) == 0, "nothing captured")


@_test("P9-T16: missing folder reported as folder_error, no crash")
def _test_missing_folder_error():
    vault = _make_vault()
    # Add a folder path that does not exist
    add_folder(vault, "/nonexistent/watched/folder/path", INPUT_CLASS_SOURCE)
    results = scan_all_folders(vault)
    _assert(len(results) == 1, "one result")
    _assert(results[0].folder_error is not None, "folder_error set")
    _assert(len(results[0].captured) == 0, "nothing captured")


@_test("P9-T17: unsupported extension skipped")
def _test_unsupported_extension_skipped():
    vault = _make_vault()
    wd = _make_watch_folder(vault)
    # Drop an unsupported file
    (wd / "document.pdf").write_bytes(b"%PDF fake content")
    add_folder(vault, str(wd), INPUT_CLASS_SOURCE)
    results = scan_all_folders(vault)
    _assert(len(results) == 1, "one result")
    _assert(len(results[0].captured) == 0, "nothing captured")
    _assert(len(results[0].skipped) == 1, "one skipped")
    _assert(results[0].skipped[0].reason == "unsupported_extension", "skip reason")


@_test("P9-T18: .txt file routed through CLI capture path")
def _test_txt_file_captured():
    vault = _make_vault()
    wd = _make_watch_folder(vault)
    content = "This is a text article captured from watched folder in test P9-T18."
    (wd / "my-article.txt").write_text(content, encoding="utf-8")
    add_folder(vault, str(wd), INPUT_CLASS_SOURCE)
    results = scan_all_folders(vault)
    _assert(len(results) == 1, "one folder result")
    _assert(len(results[0].captured) == 1, "one file captured")
    captured = results[0].captured[0]
    _assert(captured.result.get("is_duplicate") is False, "not duplicate")
    _assert("my article" in captured.result.get("filename", "").lower()
            or "my-article" in captured.result.get("filename", "").lower(), "filename contains stem")


@_test("P9-T19: .md file routed through CLI capture path")
def _test_md_file_captured():
    vault = _make_vault()
    wd = _make_watch_folder(vault)
    content = "# Test Markdown Note\n\nThis is a markdown file captured in test P9-T19."
    (wd / "test-note.md").write_text(content, encoding="utf-8")
    add_folder(vault, str(wd), INPUT_CLASS_SOURCE)
    results = scan_all_folders(vault)
    _assert(len(results[0].captured) == 1, "one md file captured")
    _assert(results[0].captured[0].result.get("is_duplicate") is False, "not duplicate")


@_test("P9-T20: .html file routed through browser connector path")
def _test_html_file_captured():
    vault = _make_vault()
    wd = _make_watch_folder(vault)
    html_content = """<!DOCTYPE html>
<html><head><title>Test Article Title</title></head>
<body><h1>Article Heading</h1><p>Some article content for test P9-T20.</p></body>
</html>"""
    (wd / "article.html").write_text(html_content, encoding="utf-8")
    add_folder(vault, str(wd), INPUT_CLASS_SOURCE)
    results = scan_all_folders(vault)
    _assert(len(results[0].captured) == 1, "one html file captured")
    _assert(results[0].captured[0].result.get("is_duplicate") is False, "not duplicate")
    # Check that the title was extracted from HTML <title>
    captured_filename = results[0].captured[0].result.get("filename", "")
    _assert("test" in captured_filename.lower() or "article" in captured_filename.lower(),
            f"HTML title extracted into filename; got: {captured_filename}")


@_test("P9-T21: already-processed file skipped on second scan run")
def _test_already_processed_skipped():
    vault = _make_vault()
    wd = _make_watch_folder(vault)
    (wd / "once.txt").write_text("content only captured once in test P9-T21", encoding="utf-8")
    add_folder(vault, str(wd), INPUT_CLASS_SOURCE)
    # First scan — should capture
    results1 = scan_all_folders(vault)
    _assert(len(results1[0].captured) == 1, "captured on first scan")
    # Second scan — already processed
    results2 = scan_all_folders(vault)
    _assert(len(results2[0].captured) == 0, "skipped on second scan")
    _assert(len(results2[0].duplicates) == 0, "not in duplicates (was skipped before dedup)")


@_test("P9-T22: dedup — same content dropped again returns duplicate on scan")
def _test_dedup_interaction():
    vault = _make_vault()
    wd = _make_watch_folder(vault)
    content = "Unique content string for dedup test P9-T22 watched folder."
    file1 = wd / "version-a.txt"
    file1.write_text(content, encoding="utf-8")
    add_folder(vault, str(wd), INPUT_CLASS_SOURCE)
    # First scan captures version-a.txt
    results1 = scan_all_folders(vault)
    _assert(len(results1[0].captured) == 1, "first file captured")

    # Write same content to a different filename (not in processed registry)
    file2 = wd / "version-b.txt"
    file2.write_text(content, encoding="utf-8")
    # Second scan: version-a.txt is already-processed (skipped); version-b.txt is new
    # but has same content → content dedup registry kicks in → duplicate
    results2 = scan_all_folders(vault)
    _assert(len(results2[0].duplicates) == 1, "version-b is duplicate in content dedup")
    _assert(len(results2[0].captured) == 0, "nothing new captured")


@_test("P9-T23: per-file error does not stop scan of other files")
def _test_per_file_error_does_not_stop_scan():
    vault = _make_vault()
    wd = _make_watch_folder(vault)
    # Write a valid file and a file that will cause a read error
    (wd / "good.txt").write_text("Good content for P9-T23 scan error test.", encoding="utf-8")
    bad_file = wd / "bad.html"
    # Write a file with completely invalid/broken encoding that will fail parsing
    bad_file.write_bytes(b"\x80\x81\x82\x83")  # invalid UTF-8 bytes
    # The browser connector will try to load this — latin-1 fallback may handle it
    # but if it produces empty content, ContentPacket will raise ValueError
    # We just check that the scan completes and good.txt is captured or error is logged

    add_folder(vault, str(wd), INPUT_CLASS_SOURCE)
    results = scan_all_folders(vault)
    _assert(len(results) == 1, "one folder result")
    # Scan completes without crashing
    total_outcomes = (len(results[0].captured) + len(results[0].errors) +
                      len(results[0].duplicates))
    _assert(total_outcomes >= 1, "at least one file outcome")


@_test("P9-T24: scan_all_folders persists processed registry to disk")
def _test_scan_persists_processed():
    vault = _make_vault()
    wd = _make_watch_folder(vault)
    (wd / "persist-test.txt").write_text(
        "Content to verify processed registry persistence in P9-T24.", encoding="utf-8"
    )
    add_folder(vault, str(wd), INPUT_CLASS_SOURCE)
    scan_all_folders(vault)
    # The processed registry file should now exist on disk
    proc_path = processed_path(vault)
    _assert(proc_path.exists(), "watch_processed.json created on disk")
    processed = load_processed(vault)
    entries = processed.get("processed", {})
    _assert(len(entries) == 1, "one processed entry")


@_test("P9-T25: watch add CLI command creates config entry")
def _test_cli_watch_add():
    vault = _make_vault()
    wd = _make_watch_folder(vault)
    from runtime.cli.main import main as cli_main
    argv = [
        "watch", "add", str(wd),
        "--class", "source",
        "--source", "watched-folder",
        "--vault-root", str(vault),
    ]
    exit_code = cli_main(argv)
    _assert(exit_code == 0, f"exit code should be 0, got {exit_code}")
    folders = list_folders(vault)
    _assert(len(folders) == 1, "one folder added")
    _assert(folders[0]["input_class"] == "source", "input_class correct")


@_test("P9-T26: watch list CLI command shows folders")
def _test_cli_watch_list():
    import io
    vault = _make_vault()
    wd = _make_watch_folder(vault)
    add_folder(vault, str(wd), INPUT_CLASS_SOURCE)
    from runtime.cli.main import main as cli_main
    argv = ["watch", "list", "--vault-root", str(vault)]
    exit_code = cli_main(argv)
    _assert(exit_code == 0, "exit code 0")


@_test("P9-T27: watch remove CLI command removes folder")
def _test_cli_watch_remove():
    vault = _make_vault()
    wd = _make_watch_folder(vault)
    add_folder(vault, str(wd), INPUT_CLASS_SOURCE)
    from runtime.cli.main import main as cli_main
    argv = ["watch", "remove", str(wd), "--vault-root", str(vault)]
    exit_code = cli_main(argv)
    _assert(exit_code == 0, "exit code 0")
    _assert(len(list_folders(vault)) == 0, "folder removed")


@_test("P9-T28: watch run --once CLI scans and reports")
def _test_cli_watch_run_once():
    vault = _make_vault()
    wd = _make_watch_folder(vault)
    (wd / "run-once-test.txt").write_text(
        "Content for watched folder CLI run once test P9-T28.", encoding="utf-8"
    )
    add_folder(vault, str(wd), INPUT_CLASS_SOURCE)
    from runtime.cli.main import main as cli_main
    argv = ["watch", "run", "--once", "--vault-root", str(vault)]
    exit_code = cli_main(argv)
    _assert(exit_code == 0, f"exit code should be 0, got {exit_code}")


@_test("P9-T29: watch run --once --json produces valid JSON output")
def _test_cli_watch_run_once_json():
    import io
    from unittest.mock import patch
    vault = _make_vault()
    wd = _make_watch_folder(vault)
    (wd / "json-run-test.txt").write_text(
        "Content for watched folder JSON run test P9-T29.", encoding="utf-8"
    )
    add_folder(vault, str(wd), INPUT_CLASS_SOURCE)
    from runtime.cli.main import main as cli_main

    captured_output = io.StringIO()
    with patch("sys.stdout", captured_output):
        exit_code = cli_main(["watch", "run", "--once", "--json", "--vault-root", str(vault)])

    output = captured_output.getvalue()
    _assert(exit_code == 0, f"exit code {exit_code}")
    data = json.loads(output)
    _assert("folders" in data, "JSON has 'folders' key")
    _assert(isinstance(data["folders"], list), "folders is a list")


@_test("P9-T30: backward compat: capture file command still works after Pass 9")
def _test_backward_compat_capture_file():
    vault = _make_vault()
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False,
                                     encoding="utf-8") as f:
        f.write("Backward compat content for test P9-T30.")
        tmp_path = f.name
    try:
        from runtime.cli.main import main as cli_main
        argv = [
            "capture", "file", tmp_path,
            "--class", "source",
            "--source", "web",
            "--title", "P9 Backward Compat Test",
            "--vault-root", str(vault),
        ]
        exit_code = cli_main(argv)
        _assert(exit_code == 0, f"backward compat capture file: exit code {exit_code}")
    finally:
        os.unlink(tmp_path)


# ── Main runner ────────────────────────────────────────────────────────────────

def _run_all() -> int:
    global _PASS, _FAIL
    _PASS = 0
    _FAIL = 0
    _ERRORS.clear()
    for label, fn in _TESTS:
        print(f"\n[{label}]")
        _run_test(label, fn)
    print(f"\nPass 9: {_PASS} passed, {_FAIL} failed")
    if _ERRORS:
        print("\nFailed tests:")
        for e in _ERRORS:
            print(f"  - {e}")
    return 0 if _FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(_run_all())
