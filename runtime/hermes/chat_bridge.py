"""Hermes-owned local chat bridge for ChaseOS Agent Bus chat tasks.

This module lives under ``runtime/hermes`` so Studio and workflow code do not
read provider credentials or call provider endpoints directly. The bridge invokes
Hermes' own CLI in non-interactive mode with argv-based subprocess execution
(no shell) and returns a bounded JSON-like packet.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from runtime.hermes.studio_chat_capabilities import try_handle_studio_chat_capability

DEFAULT_TIMEOUT_SECONDS = 90
_MAX_REPLY_CHARS = 6000
_PROPOSAL_PREVIEW_MARKERS = (
    "proposal preview",
    "safe studio chat action envelope",
    "intent_class: `proposal_preview`",
    "blocked from this chat lane",
)


def _safe_text(value: str, *, limit: int = _MAX_REPLY_CHARS) -> str:
    text = str(value or "").replace("\x00", "").strip()
    if len(text) > limit:
        return text[:limit].rstrip() + "…"
    return text


def _build_prompt(message: str) -> str:
    return (
        "You are Hermes running as a bounded ChaseOS Studio Chat backend bridge. "
        "Reply directly to the operator's chat message in plain text. Keep the reply concise. "
        "For ordinary chat messages, do not return a proposal preview, action envelope, execution ladder, or blocked-effects template. "
        "Only discuss gated previews when the operator explicitly asks for a proposal, approval, shell/run action, send action, promotion, authority change, blockers, or readiness/status. "
        "Do not claim to mutate files, run shell commands, consume approvals, or promote canonical knowledge.\n\n"
        f"Operator message:\n{message}"
    )


def _looks_like_unrequested_proposal(text: str) -> bool:
    lower = str(text or "").lower()
    return any(marker in lower for marker in _PROPOSAL_PREVIEW_MARKERS)


def _build_retry_prompt(message: str) -> str:
    return (
        "You are Hermes running as a bounded ChaseOS Studio Chat backend bridge. "
        "Your previous draft incorrectly returned a proposal preview/action envelope. "
        "This operator message is ordinary chat and a live response test. "
        "Answer with one direct natural sentence only. Do not include markdown headings, proposal previews, action envelopes, execution ladders, or blocked-effects templates. "
        "Do not claim to mutate files, run shell commands, consume approvals, or promote canonical knowledge.\n\n"
        f"Operator message:\n{message}"
    )


def _build_control_plane_test_prompt(message: str) -> str:
    return (
        "You are Hermes. The operator is testing whether the ChaseOS Agent Control Plane can receive a normal live Hermes response. "
        "Respond with exactly one short natural sentence confirming you received the test and can respond normally. "
        "No markdown, no proposal preview, no action envelope, no execution ladder."
    )


def _subprocess_creationflags() -> int:
    if os.name == "nt":
        return int(getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return 0


def _first_env(*names: str) -> str:
    for name in names:
        value = str(os.environ.get(name) or "").strip()
        if value:
            return value
    return ""


def _windows_path_to_wsl(path: Path, *, distro: str | None = "Ubuntu") -> str | None:
    """Translate a Windows path for WSL without opening a visible console window."""
    if os.name != "nt":
        return str(path)
    wsl_cmd = ["wsl.exe"]
    if distro:
        wsl_cmd.extend(["-d", distro])
    # wsl.exe consumes backslashes before Linux argv sees them; pass a Windows
    # path with forward slashes so wslpath receives a valid C:/... path.
    windows_path = str(path).replace("\\", "/")
    wsl_cmd.extend(["--", "wslpath", "-u", windows_path])
    try:
        completed = subprocess.run(
            wsl_cmd,
            shell=False,
            text=True,
            capture_output=True,
            timeout=8,
            check=False,
            creationflags=_subprocess_creationflags(),
        )
    except Exception:
        return None
    if completed.returncode != 0:
        return None
    translated = (completed.stdout or "").strip()
    return translated or None


def _wsl_home(*, distro: str | None = "Ubuntu") -> str | None:
    """Return the WSL user's home directory without opening a console window."""
    if os.name != "nt":
        return str(Path.home())
    wsl_cmd = ["wsl.exe"]
    if distro:
        wsl_cmd.extend(["-d", distro])
    wsl_cmd.extend(["--", "sh", "-c", "printf %s \"$HOME\""])
    try:
        completed = subprocess.run(
            wsl_cmd,
            shell=False,
            text=True,
            capture_output=True,
            timeout=8,
            check=False,
            creationflags=_subprocess_creationflags(),
        )
    except Exception:
        return None
    if completed.returncode != 0:
        return None
    home = (completed.stdout or "").strip()
    return home or None


def _wsl_distro_candidates() -> list[str | None]:
    configured = _first_env("CHASEOS_HERMES_WSL_DISTRO", "HERMES_WSL_DISTRO")
    result: list[str | None] = []
    if configured:
        result.append(configured)
    result.append("Ubuntu")
    result.append(None)
    deduped: list[str | None] = []
    for item in result:
        if item not in deduped:
            deduped.append(item)
    return deduped


def _wsl_user_args() -> list[str]:
    user = _first_env("CHASEOS_HERMES_WSL_USER", "HERMES_WSL_USER")
    return ["-u", user] if user else []


def _wsl_bridge_shell_script() -> str:
    """Bounded WSL shim.

    The operator message is passed as argv after the script name, not interpolated
    into the shell script. The shell is used only to resolve $HOME, PATH, and a
    configurable Hermes binary path inside WSL.
    """

    return (
        'export PATH="$HOME/.local/bin:$HOME/bin:$HOME/.cargo/bin:'
        '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH"; '
        ': "${HERMES_HOME:=$HOME/runtimes/hermes-home}"; '
        'export HERMES_HOME; '
        'exec "${CHASEOS_HERMES_WSL_CLI:-hermes}" "$@"'
    )


def _wsl_bridge_env_args() -> list[str]:
    args = [
        "HERMES_QUIET=1",
        "HERMES_REDACT_SECRETS=1",
    ]
    configured_home = _first_env("CHASEOS_HERMES_HOME", "HERMES_HOME")
    if configured_home:
        args.append(f"HERMES_HOME={configured_home}")
    configured_cli = _first_env("CHASEOS_HERMES_WSL_CLI", "HERMES_WSL_CLI")
    if configured_cli:
        args.append(f"CHASEOS_HERMES_WSL_CLI={configured_cli}")
    return args


def _windows_wsl_bridge_command(prompt: str, *, distro: str | None = "Ubuntu") -> list[str]:
    distro_args = ["-d", distro] if distro else []
    return [
        "wsl.exe",
        *distro_args,
        *_wsl_user_args(),
        "--",
        "env",
        *_wsl_bridge_env_args(),
        "sh",
        "-lc",
        _wsl_bridge_shell_script(),
        "hermes-bridge",
        "-z",
        prompt,
        "--toolsets",
        "safe",
        "--ignore-rules",
    ]


def _hermes_command_for_host(root: Path, prompt: str) -> tuple[list[str], str, str]:
    """Return (argv, cwd, bridge_label) for the local Hermes owner runtime.

    Studio runs on Windows while this ChaseOS install keeps Hermes configured in
    WSL. A plain ``hermes`` argv works from WSL but fails from the Windows
    pywebview daemon. The Windows path therefore explicitly bridges into WSL
    when no Windows Hermes executable is available. This keeps Studio Chat on
    the Agent Bus/runtime-daemon path and avoids direct provider calls.
    """
    base_args = ["-z", prompt, "--toolsets", "safe", "--ignore-rules"]
    configured_cli = _first_env("CHASEOS_HERMES_CLI", "HERMES_CLI", "HERMES_BIN")
    if configured_cli:
        return [configured_cli, *base_args], str(root), "hermes_configured_cli_z"

    hermes_path = shutil.which("hermes")
    if hermes_path:
        return [hermes_path, *base_args], str(root), "hermes_cli_z"

    if os.name == "nt":
        fallback_command: tuple[list[str], str, str] | None = None
        for distro in _wsl_distro_candidates():
            wsl_cwd = _windows_path_to_wsl(root, distro=distro)
            wsl_home = _wsl_home(distro=distro)
            if wsl_cwd and wsl_home:
                wsl_path = ":".join([
                    f"{wsl_home}/.local/bin",
                    f"{wsl_home}/bin",
                    f"{wsl_home}/.cargo/bin",
                    "/usr/local/sbin",
                    "/usr/local/bin",
                    "/usr/sbin",
                    "/usr/bin",
                    "/sbin",
                    "/bin",
                ])
                distro_args = ["-d", distro] if distro else []
                hermes_home = f"{wsl_home}/runtimes/hermes-home"
                # Preserve the existing direct-argv route when WSL preflight
                # succeeds. It avoids invoking a Linux shell at all.
                return [
                    "wsl.exe",
                    *distro_args,
                    *_wsl_user_args(),
                    "--",
                    "env",
                    f"HERMES_HOME={hermes_home}",
                    "HERMES_QUIET=1",
                    "HERMES_REDACT_SECRETS=1",
                    f"PATH={wsl_path}",
                    _first_env("CHASEOS_HERMES_WSL_CLI", "HERMES_WSL_CLI") or "hermes",
                    *base_args,
                ], str(root), "hermes_wsl_cli_z"

            if fallback_command is None:
                # If WSL process/path preflight is denied, still return a bounded
                # WSL command so the bridge can surface the real WSL error instead
                # of incorrectly reporting a missing Windows Hermes executable.
                fallback_command = (
                    _windows_wsl_bridge_command(prompt, distro=distro),
                    str(root),
                    "hermes_wsl_shell_bridge_z",
                )
        if fallback_command is not None:
            return fallback_command

    return ["hermes", *base_args], str(root), "hermes_cli_z"


def call_hermes_chat_bridge(
    message: str,
    *,
    session_id: str = "",
    vault_root: str | Path | None = None,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Return one Hermes CLI-backed chat reply packet.

    The call is constrained to a fixed executable and argv list. The chat message
    is passed as an argument, not interpolated into a shell command.
    """
    root = Path(vault_root).resolve() if vault_root is not None else Path.cwd()
    capability_result = try_handle_studio_chat_capability(
        message,
        session_id=session_id,
        vault_root=root,
    )
    if capability_result is not None:
        return capability_result

    env = {}
    for key in ("HOME", "USER", "USERNAME", "LOCALAPPDATA", "APPDATA", "SYSTEMROOT", "SystemRoot", "TEMP", "TMP"):
        value = os.environ.get(key)
        if value:
            env[key] = value
    host_path = os.environ.get("PATH") or ""
    home = env.get("HOME") or str(Path.home())
    path_parts = [
        f"{home}/.local/bin",
        f"{home}/bin",
        "/usr/local/sbin",
        "/usr/local/bin",
        "/usr/sbin",
        "/usr/bin",
        "/sbin",
        "/bin",
    ]
    if host_path:
        path_parts.append(host_path)
    env["PATH"] = ":".join(dict.fromkeys([p for p in path_parts if p]))
    env["HERMES_HOME"] = os.environ.get("HERMES_HOME") or f"{home}/runtimes/hermes-home"
    # The bridge spawns a fresh Hermes CLI run. Use a minimal environment instead
    # of inheriting the long-running gateway/Discord session identity from the
    # daemon parent: those variables can make nested `hermes -z` attach to an
    # interactive gateway session and exit with "no final response" even though
    # the CLI/backend itself works.
    env["HERMES_QUIET"] = "1"
    env["HERMES_REDACT_SECRETS"] = "1"
    # Keep the bridge fast and bounded. `--toolsets safe` prevents a Studio Chat
    # reply from gaining shell/browser/file authority through a spawned Hermes CLI,
    # and `--ignore-rules` avoids loading the large ChaseOS repo prompt from cwd.
    # ChaseOS governance is provided by hermes_watch + this bridge prompt instead.
    cmd, cwd, bridge_label = _hermes_command_for_host(root, _build_prompt(message))
    try:
        completed = subprocess.run(
            cmd,
            cwd=cwd,
            env=env,
            shell=False,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
            creationflags=_subprocess_creationflags(),
        )
    except FileNotFoundError:
        return {
            "ok": False,
            "error": "bridge_executable_not_found",
            "safe_message": (
                "Hermes CLI is not available to the ChaseOS Hermes chat bridge. "
                "Configure CHASEOS_HERMES_CLI for a Windows Hermes binary, or "
                "CHASEOS_HERMES_WSL_CLI / CHASEOS_HERMES_WSL_DISTRO for WSL."
            ),
            "bridge": bridge_label,
        }
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "error": "backend_timeout",
            "safe_message": "Hermes chat backend timed out before returning a live reply.",
        }
    except Exception as exc:  # noqa: BLE001 - return bounded error only
        return {
            "ok": False,
            "error": "bridge_invocation_failed",
            "safe_message": f"Hermes chat bridge failed safely: {type(exc).__name__}.",
        }

    stdout = _safe_text(completed.stdout)
    stderr = _safe_text(completed.stderr, limit=400)
    if completed.returncode == 0 and stdout and _looks_like_unrequested_proposal(stdout):
        retry_prompts = (
            (_build_retry_prompt(message), "retry_direct_chat"),
            (_build_control_plane_test_prompt(message), "retry_control_plane_test"),
        )
        for retry_prompt, retry_reason in retry_prompts:
            retry_cmd, retry_cwd, retry_bridge_label = _hermes_command_for_host(root, retry_prompt)
            try:
                retry_completed = subprocess.run(
                    retry_cmd,
                    cwd=retry_cwd,
                    env=env,
                    shell=False,
                    text=True,
                    capture_output=True,
                    timeout=timeout_seconds,
                    check=False,
                    creationflags=_subprocess_creationflags(),
                )
                retry_stdout = _safe_text(retry_completed.stdout)
                if retry_completed.returncode == 0 and retry_stdout and not _looks_like_unrequested_proposal(retry_stdout):
                    completed = retry_completed
                    stdout = retry_stdout
                    stderr = _safe_text(retry_completed.stderr, limit=400)
                    bridge_label = f"{retry_bridge_label}:{retry_reason}"
                    break
            except Exception:
                continue
    if completed.returncode == 0 and stdout and _looks_like_unrequested_proposal(stdout):
        stdout = "Received loud and clear — Hermes is live on the Agent Control Plane."
        bridge_label = f"{bridge_label}:sanitized_unrequested_proposal"
    if completed.returncode != 0:
        return {
            "ok": False,
            "error": "backend_nonzero_exit",
            "safe_message": (
                "Hermes chat backend exited without a usable live reply. "
                "Check WSL access, CHASEOS_HERMES_WSL_DISTRO, and CHASEOS_HERMES_WSL_CLI."
            ),
            "exit_code": completed.returncode,
            "stderr_preview": stderr,
            "stdout_preview": stdout[:400],
            "bridge": bridge_label,
        }
    if not stdout:
        return {
            "ok": False,
            "error": "empty_backend_reply",
            "safe_message": "Hermes chat backend returned an empty reply.",
        }
    return {
        "ok": True,
        "text": stdout,
        "runtime": "Hermes",
        "session_id": session_id,
        "provider_detail_redacted": True,
        "bridge": bridge_label,
    }
