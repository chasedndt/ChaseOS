"""Portability tests for the runtime chat-consumer --vault-root resolution.

Core-readiness: the daemon must open the SAME Agent Bus file Studio writes to,
on ANY user's machine — never a path hardcoded to one operator.
"""

from __future__ import annotations

import runtime.lifecycle.coordination_watch_supervisor as sup


def test_windows_to_wsl_translation_is_generic():
    assert sup._windows_to_wsl_vault_path(r"<WINDOWS_USER_HOME>\<path>") == "<WINDOWS_USER_HOME_WSL>/<path>"
    assert sup._windows_to_wsl_vault_path(r"D:\vaults\chaseos_obsidian") == "/mnt/d/vaults/chaseos_obsidian"
    # different user, different drive — still derived, never hardcoded
    assert sup._windows_to_wsl_vault_path(r"E:\bob\notes") == "/mnt/e/bob/notes"


def test_posix_and_non_drive_paths_pass_through():
    assert sup._windows_to_wsl_vault_path("/home/bob/chaseos") == "/home/bob/chaseos"
    assert sup._windows_to_wsl_vault_path("/mnt/c/x") == "/mnt/c/x"
    assert sup._windows_to_wsl_vault_path("") == ""


def test_explicit_override_always_wins():
    # Override wins even with launch_via_wsl set — the user's declared path is truth.
    cfg = {"vault_root": "/home/bob/shared/chaseos", "launch_via_wsl": True}
    assert sup._resolve_consumer_vault_root(cfg) == "/home/bob/shared/chaseos"


def test_wsl_launch_gets_translated_root():
    # Only when the command actually runs inside WSL do we hand it a /mnt path.
    cfg = {"vault_root": None, "launch_via_wsl": True, "supervisor_host": "windows"}
    resolved = sup._resolve_consumer_vault_root(cfg)
    assert resolved.startswith("/mnt/"), resolved


def test_host_launch_uses_root_even_for_wsl_runtime():
    # The bug guard: a host-launched (Windows) process must NOT get a /mnt path.
    cfg = {"vault_root": None, "launch_via_wsl": False,
           "runtime_platform": "wsl-ubuntu", "supervisor_host": "windows"}
    assert sup._resolve_consumer_vault_root(cfg) == str(sup.ROOT)


def test_same_host_uses_root():
    cfg = {"vault_root": None, "supervisor_host": "windows"}
    assert sup._resolve_consumer_vault_root(cfg) == str(sup.ROOT)
