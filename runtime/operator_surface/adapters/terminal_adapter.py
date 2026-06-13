"""
runtime.operator_surface.adapters.terminal_adapter

Terminal Operator Surface Adapter.

Status: PARTIAL.
This implementation is a narrow read-only command foothold for Terminal
Workbench planning. It does not provide an interactive PTY, command writeback,
network operations, or destructive/elevated execution.

See:
  - 06_AGENTS/Full-System-Operator-Surface.md Section 8.2
  - 06_AGENTS/Terminal-Workbench-Architecture.md
"""

from __future__ import annotations

import os
import re
import shlex
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable

from runtime.operator_surface.adapters.base import OperatorSurfaceAdapterBase
from runtime.operator_surface.capabilities import OperatorCapability, SurfaceType
from runtime.operator_surface.contracts import OperatorScope, OperatorSession, RecoveryResult, StepResult
from runtime.operator_surface.events import OperatorEvent, OperatorEventType


UNTRUSTED_TERMINAL_TIER = "Tier 4"


@dataclass(frozen=True)
class CommandClassification:
    """Policy decision for a single terminal command string."""

    action_class: str
    allowed: bool
    approval_required: bool
    reason: str
    tokens: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "action_class": self.action_class,
            "allowed": self.allowed,
            "approval_required": self.approval_required,
            "reason": self.reason,
            "tokens": list(self.tokens),
            "untrusted_output": True,
        }


class TerminalAdapter(OperatorSurfaceAdapterBase):
    """
    Partial Terminal Operator Surface Adapter.

    The adapter only runs commands classified as read-only and scoped to an
    explicitly allowed working directory. All output is treated as untrusted
    terminal data and must not be promoted to canonical memory without a
    separate review/writeback path.
    """

    ADAPTER_ID = "terminal-subprocess-v1"
    SURFACE_TYPE = SurfaceType.TERMINAL
    ADAPTER_VERSION = "0.1.0"
    ADAPTER_STATUS = "partial"
    DESCRIPTION = "Terminal Operator Surface via bounded read-only subprocess execution"
    CAPABILITIES = frozenset({
        OperatorCapability.TERMINAL_READ,
        OperatorCapability.TERMINAL_EXECUTE,
        OperatorCapability.TERMINAL_SPAWN,
        OperatorCapability.TERMINAL_MONITOR,
    })
    REQUIRED_SCOPE_FIELDS = frozenset({"target_uris"})
    FORBIDDEN_SCOPE_PROPERTIES = frozenset({"credential_access"})
    MIN_TRUST_TIER = 2
    APPROVAL_REQUIRED_ACTIONS = frozenset({
        "destructive_command",
        "write_command",
        "network_command",
    })
    GROUNDING_MODES = []

    SAFE_EXECUTABLES = frozenset({
        "cat",
        "dir",
        "git",
        "ls",
        "node",
        "npm",
        "npx",
        "pip",
        "pip3",
        "pwsh",
        "pwd",
        "py",
        "pytest",
        "python",
        "python3",
        "rg",
        "type",
        "where",
        "whoami",
    })
    SAFE_GIT_SUBCOMMANDS = frozenset({
        "branch",
        "diff",
        "log",
        "show",
        "status",
    })
    DESTRUCTIVE_EXECUTABLES = frozenset({
        "del",
        "erase",
        "format",
        "move",
        "rd",
        "rm",
        "rmdir",
    })
    WRITE_EXECUTABLES = frozenset({
        "cp",
        "copy",
        "mkdir",
        "mv",
        "ni",
        "new-item",
        "npm",
        "npx",
        "out-file",
        "pip",
        "pip3",
        "rename-item",
        "set-content",
        "tee",
        "touch",
        "write-output",
    })
    NETWORK_EXECUTABLES = frozenset({
        "curl",
        "ftp",
        "gh",
        "iwr",
        "invoke-restmethod",
        "invoke-webrequest",
        "ssh",
        "wget",
    })
    ELEVATED_EXECUTABLES = frozenset({
        "runas",
        "su",
        "sudo",
    })
    SHELL_CONTROL_TOKENS = (
        "&&",
        "||",
        "|",
        ";",
        ">",
        "<",
        "`",
        "$(",
    )
    DEFAULT_TIMEOUT_SECONDS = 15
    DEFAULT_MAX_OUTPUT_CHARS = 4000
    SECRET_PATTERNS = (
        re.compile(r"(?i)(api[_-]?key|token|password|secret)\s*=\s*['\"]?[^'\"\s]+"),
        re.compile(r"sk-[A-Za-z0-9_\-]{12,}"),
        re.compile(r"AKIA[0-9A-Z]{16}"),
    )

    def __init__(self) -> None:
        self.scope: OperatorScope | None = None
        self.session: OperatorSession | None = None
        self.allowed_roots: list[Path] = []
        self.commands_attempted = 0
        self.commands_executed = 0
        self.commands_blocked = 0
        self.steps_completed = 0
        self.steps_failed = 0
        self.last_classifications: list[dict] = []

    def initialize(self, scope: OperatorScope, session: OperatorSession) -> None:
        errors = self.validate_scope(scope)
        if scope.surface != self.SURFACE_TYPE:
            errors.append("TerminalAdapter requires SurfaceType.TERMINAL scope")
        if errors:
            raise ValueError("; ".join(errors))

        self.scope = scope
        self.session = session
        self.allowed_roots = self._resolve_allowed_roots(scope)
        if not self.allowed_roots:
            raise ValueError("TerminalAdapter requires at least one allowed path")

    def plan(self, goal: str, context: dict) -> list[dict]:
        command = context.get("command") if context else None
        if not command:
            raise NotImplementedError(
                "TerminalAdapter dynamic planning is not implemented; provide explicit command steps."
            )
        classification = self.classify_command(command)
        return [{
            "step_index": 0,
            "action_type": classification["action_class"],
            "target": command,
            "command": command,
            "description": f"Run bounded terminal command for goal: {goal}",
            "classification": classification,
        }]

    def execute_step(self, step: dict, emit_event: Callable[[OperatorEvent], None]) -> StepResult:
        if self.scope is None or self.session is None:
            raise RuntimeError("TerminalAdapter must be initialized before execute_step")

        command = str(step.get("command") or step.get("target") or "").strip()
        step_index = int(step.get("step_index", 0))
        if not command:
            raise ValueError("Terminal step requires a command or target")

        classification = self.classify_command(command)
        self.commands_attempted += 1
        self.last_classifications.append(classification)

        cwd = self.validate_cwd(step.get("cwd"))
        action_class = classification["action_class"]
        emit_event(self._event(OperatorEventType.STEP_STARTED, step_index, action_class, {
            "command": command,
            "cwd": str(cwd),
            "classification": classification,
        }))

        if not classification["allowed"]:
            self.commands_blocked += 1
            self.steps_failed += 1
            payload = {
                "blocked": True,
                "reason": classification["reason"],
                "classification": classification,
                "untrusted_tier": UNTRUSTED_TERMINAL_TIER,
                "terminal_output_trusted": False,
            }
            emit_event(self._event(OperatorEventType.STEP_FAILED, step_index, action_class, payload))
            return StepResult(
                step_index=step_index,
                success=False,
                action_type=action_class,
                target=command,
                output=payload,
                error=classification["reason"],
                grounding_mode_used="terminal_text_untrusted",
                requires_approval=classification["approval_required"],
            )

        timeout_seconds = int(step.get("timeout_seconds", self.DEFAULT_TIMEOUT_SECONDS))
        max_output_chars = int(step.get("max_output_chars", self.DEFAULT_MAX_OUTPUT_CHARS))
        tokens = classification["tokens"]

        try:
            self.validate_command_paths(tokens, cwd)
        except ValueError as exc:
            self.commands_blocked += 1
            self.steps_failed += 1
            action_class = "path_outside_scope"
            payload = {
                "blocked": True,
                "reason": str(exc),
                "classification": {**classification, "action_class": action_class, "allowed": False},
                "untrusted_tier": UNTRUSTED_TERMINAL_TIER,
                "terminal_output_trusted": False,
            }
            emit_event(self._event(OperatorEventType.STEP_FAILED, step_index, action_class, payload))
            return StepResult(
                step_index=step_index,
                success=False,
                action_type=action_class,
                target=command,
                output=payload,
                error=str(exc),
                grounding_mode_used="terminal_text_untrusted",
                requires_approval=True,
            )

        try:
            completed = subprocess.run(
                tokens,
                cwd=str(cwd),
                capture_output=True,
                check=False,
                text=True,
                timeout=timeout_seconds,
                shell=False,
                env=self._safe_environment(),
            )
        except subprocess.TimeoutExpired as exc:
            self.steps_failed += 1
            payload = {
                "blocked": False,
                "timeout": True,
                "timeout_seconds": timeout_seconds,
                "stdout": self._redact_and_truncate(exc.stdout or "", max_output_chars),
                "stderr": self._redact_and_truncate(exc.stderr or "", max_output_chars),
                "untrusted_tier": UNTRUSTED_TERMINAL_TIER,
                "terminal_output_trusted": False,
                "classification": classification,
            }
            emit_event(self._event(OperatorEventType.STEP_FAILED, step_index, action_class, payload))
            return StepResult(
                step_index=step_index,
                success=False,
                action_type=action_class,
                target=command,
                output=payload,
                error=f"Command timed out after {timeout_seconds}s",
                grounding_mode_used="terminal_text_untrusted",
            )

        self.commands_executed += 1
        success = completed.returncode == 0
        stdout, stdout_truncated = self._redact_and_truncate_with_flag(completed.stdout, max_output_chars)
        stderr, stderr_truncated = self._redact_and_truncate_with_flag(completed.stderr, max_output_chars)
        payload = {
            "blocked": False,
            "command": command,
            "cwd": str(cwd),
            "returncode": completed.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "stdout_truncated": stdout_truncated,
            "stderr_truncated": stderr_truncated,
            "classification": classification,
            "untrusted_tier": UNTRUSTED_TERMINAL_TIER,
            "terminal_output_trusted": False,
        }
        if success:
            self.steps_completed += 1
            event_type = OperatorEventType.STEP_COMPLETE
        else:
            self.steps_failed += 1
            event_type = OperatorEventType.STEP_FAILED
        emit_event(self._event(event_type, step_index, action_class, payload))
        return StepResult(
            step_index=step_index,
            success=success,
            action_type=action_class,
            target=command,
            output=payload,
            error=None if success else f"Command exited with {completed.returncode}",
            grounding_mode_used="terminal_text_untrusted",
        )

    def recover(self, failed_step: dict, emit_event: Callable[[OperatorEvent], None]) -> RecoveryResult:
        step_index = int(failed_step.get("step_index", 0))
        emit_event(self._event(OperatorEventType.RECOVERY_STARTED, step_index, "terminal_recovery", {
            "strategy": "no_process_state_retained",
        }))
        emit_event(self._event(OperatorEventType.RECOVERY_COMPLETE, step_index, "terminal_recovery", {
            "final_surface_state": "clean",
        }))
        return RecoveryResult(
            attempted=True,
            success=True,
            recovery_actions=["no retained process state; command boundary already closed"],
            final_surface_state="clean",
        )

    def teardown(self, outcome: str, emit_event: Callable[[OperatorEvent], None]) -> None:
        event_type = (
            OperatorEventType.SESSION_COMPLETE
            if outcome.upper() == "COMPLETE"
            else OperatorEventType.SESSION_FAILED
        )
        emit_event(self._event(event_type, self.steps_completed + self.steps_failed, "terminal_teardown", {
            "outcome": outcome,
            "process_state": "none_retained",
        }))

    def build_audit_payload(self) -> dict:
        return {
            "adapter_id": self.ADAPTER_ID,
            "surface_type": self.SURFACE_TYPE.value,
            "adapter_status": self.ADAPTER_STATUS,
            "adapter_version": self.ADAPTER_VERSION,
            "implementation_note": "PARTIAL read-only subprocess foothold; no interactive PTY.",
            "commands_attempted": self.commands_attempted,
            "commands_executed": self.commands_executed,
            "commands_blocked": self.commands_blocked,
            "steps_completed": self.steps_completed,
            "steps_failed": self.steps_failed,
            "terminal_output_trust_tier": UNTRUSTED_TERMINAL_TIER,
            "terminal_output_trusted": False,
            "last_classifications": self.last_classifications[-10:],
        }

    @classmethod
    def classify_command(cls, command: str) -> dict:
        command = command.strip()
        if not command:
            return CommandClassification("invalid_command", False, False, "empty command", ()).to_dict()
        if cls._contains_shell_control(command):
            return CommandClassification(
                action_class="blocked_shell_control_command",
                allowed=False,
                approval_required=True,
                reason="shell control operators are blocked by terminal policy",
                tokens=(),
            ).to_dict()

        try:
            tokens = tuple(shlex.split(command, posix=True))
        except ValueError as exc:
            return CommandClassification(
                action_class="invalid_command",
                allowed=False,
                approval_required=False,
                reason=f"unable to parse command: {exc}",
                tokens=(),
            ).to_dict()
        if not tokens:
            return CommandClassification("invalid_command", False, False, "empty command", tokens).to_dict()

        executable = cls._normalize_executable(tokens[0])
        token_set = {token.lower() for token in tokens[1:]}
        if executable in cls.ELEVATED_EXECUTABLES or ("-verb" in token_set and "runas" in token_set):
            return CommandClassification(
                "elevated_command",
                False,
                True,
                "elevated terminal commands are blocked",
                tokens,
            ).to_dict()
        if executable in cls.DESTRUCTIVE_EXECUTABLES or cls._has_destructive_flags(executable, tokens):
            return CommandClassification(
                "destructive_command",
                False,
                True,
                "destructive terminal commands are blocked",
                tokens,
            ).to_dict()
        if executable in cls.NETWORK_EXECUTABLES:
            return CommandClassification(
                "network_command",
                False,
                True,
                "network terminal commands are blocked in this foothold",
                tokens,
            ).to_dict()
        if executable in cls.WRITE_EXECUTABLES:
            return CommandClassification(
                "write_command",
                False,
                True,
                "write terminal commands require the dedicated approval-gated N6 executor",
                tokens,
            ).to_dict()
        if executable == "git" and len(tokens) > 1:
            subcommand = tokens[1].lower()
            if subcommand not in cls.SAFE_GIT_SUBCOMMANDS:
                return CommandClassification(
                    "write_command",
                    False,
                    True,
                    f"git {subcommand} is not in the read-only allowlist",
                    tokens,
                ).to_dict()
        if executable not in cls.SAFE_EXECUTABLES:
            return CommandClassification(
                "unknown_command",
                False,
                True,
                f"command '{executable}' is not in the read-only allowlist",
                tokens,
            ).to_dict()
        return CommandClassification(
            "read_only_command",
            True,
            False,
            "command is allowed by read-only terminal policy",
            tokens,
        ).to_dict()

    def validate_cwd(self, cwd: str | os.PathLike[str] | None) -> Path:
        requested = Path(cwd).resolve() if cwd else self.allowed_roots[0]
        for root in self.allowed_roots:
            try:
                requested.relative_to(root)
                return requested
            except ValueError:
                continue
        raise ValueError(f"cwd '{requested}' is outside allowed terminal scope")

    def validate_command_paths(self, tokens: Iterable[str], cwd: Path) -> None:
        """Reject explicit command path arguments that escape the allowed roots."""
        for token in tuple(tokens)[1:]:
            if token.startswith("-") or not self._looks_like_path_argument(token):
                continue
            candidate = Path(token)
            if not candidate.is_absolute():
                candidate = cwd / candidate
            resolved = candidate.resolve(strict=False)
            for root in self.allowed_roots:
                try:
                    resolved.relative_to(root)
                    break
                except ValueError:
                    continue
            else:
                raise ValueError(f"path argument '{token}' is outside allowed terminal scope")

    @classmethod
    def _looks_like_path_argument(cls, token: str) -> bool:
        return (
            token.startswith(("/", "./", "../", "~"))
            or "/" in token
            or "\\" in token
            or re.match(r"^[A-Za-z]:", token) is not None
        )

    @classmethod
    def _contains_shell_control(cls, command: str) -> bool:
        return any(token in command for token in cls.SHELL_CONTROL_TOKENS)

    @classmethod
    def _normalize_executable(cls, executable: str) -> str:
        name = Path(executable).name.lower()
        if name.endswith(".exe"):
            name = name[:-4]
        return name

    @classmethod
    def _has_destructive_flags(cls, executable: str, tokens: Iterable[str]) -> bool:
        lowered = [token.lower() for token in tokens]
        if executable == "rm" and any(
            token in {"-rf", "-fr"} or ("r" in token and "f" in token and token.startswith("-"))
            for token in lowered
        ):
            return True
        if executable == "git" and len(lowered) > 1 and lowered[1] in {"clean", "reset", "checkout"}:
            return True
        return False

    @classmethod
    def _redact_and_truncate(cls, text: str | bytes | None, max_chars: int) -> str:
        return cls._redact_and_truncate_with_flag(text, max_chars)[0]

    @classmethod
    def _redact_and_truncate_with_flag(cls, text: str | bytes | None, max_chars: int) -> tuple[str, bool]:
        if text is None:
            text = ""
        if isinstance(text, bytes):
            text = text.decode(errors="replace")
        for pattern in cls.SECRET_PATTERNS:
            text = pattern.sub("[REDACTED]", text)
        truncated = len(text) > max_chars
        if truncated:
            text = text[:max_chars] + "\n[TRUNCATED]"
        return text, truncated

    def _resolve_allowed_roots(self, scope: OperatorScope) -> list[Path]:
        roots: list[Path] = []
        for raw_path in scope.allowed_paths:
            roots.append(Path(raw_path).resolve())
        for uri in scope.target_uris:
            if uri.startswith("file://"):
                raw = uri.removeprefix("file://")
                if raw:
                    try:
                        roots.append(Path(raw).resolve())
                    except OSError:
                        pass

        deduped: list[Path] = []
        seen: set[str] = set()
        for root in roots:
            key = str(root).casefold()
            if key not in seen:
                seen.add(key)
                deduped.append(root)
        return deduped

    def _event(
        self,
        event_type: OperatorEventType,
        step_index: int,
        action_class: str,
        payload: dict,
    ) -> OperatorEvent:
        return OperatorEvent(
            run_id=self.session.run_id if self.session else "",
            surface=self.SURFACE_TYPE.value,
            event_type=event_type,
            timestamp=datetime.now(timezone.utc).isoformat(),
            step_index=step_index,
            action_class=action_class,
            description=payload.get("reason", action_class),
            payload=payload,
            grounding_mode="terminal_text_untrusted",
        )

    def _safe_environment(self) -> dict[str, str]:
        allowed_keys = {
            "PATH",
            "PATHEXT",
            "SYSTEMROOT",
            "TEMP",
            "TMP",
            "USERPROFILE",
            "WINDIR",
        }
        return {key: value for key, value in os.environ.items() if key.upper() in allowed_keys}
