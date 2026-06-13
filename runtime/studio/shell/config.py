"""ChaseOS Studio shell configuration — app paths and dev/prod mode."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _looks_like_vault_root(path: Path) -> bool:
    return path.is_dir() and ((path / "CLAUDE.md").exists() or (path / "runtime").is_dir())


def _default_vault_root() -> Path | None:
    env_default = os.environ.get("CHASEOS_VAULT_ROOT") or os.environ.get("CHASEOS_STUDIO_VAULT_ROOT")
    if env_default:
        candidate = Path(env_default).expanduser()
        if _looks_like_vault_root(candidate):
            return candidate.resolve()

    state = _studio_state_dir() / "window-state.json"
    if state.exists():
        import json
        try:
            data = json.loads(state.read_text(encoding="utf-8"))
            last = data.get("last_vault_root")
            if last and Path(last).is_dir():
                return Path(last)
        except Exception:
            pass

    home = Path.home()
    for candidate in (
        home / "Documents" / "ChaseOS",
        home / "ChaseOS",
    ):
        if _looks_like_vault_root(candidate):
            return candidate.resolve()
    return None


def resolve_vault_root(cli_arg: str | None = None) -> Path:
    if cli_arg:
        p = Path(cli_arg).resolve()
        if not p.is_dir():
            raise ValueError(f"vault_root does not exist: {p}")
        return p
    from_state = _default_vault_root()
    if from_state:
        return from_state
    cwd = Path.cwd()
    if (cwd / "CLAUDE.md").exists() or (cwd / "runtime").is_dir():
        return cwd
    raise ValueError(
        "No vault root found. Pass --vault-root PATH or open a vault first."
    )


def _studio_state_dir() -> Path:
    override = os.environ.get("CHASEOS_STUDIO_STATE_DIR")
    candidates = []
    if override:
        candidates.append(Path(override))
    candidates.append(Path.home() / ".chaseos" / "studio")
    candidates.append(Path.cwd() / ".pytest_tmp_env" / "chaseos-studio-state")
    candidates.append(Path(os.environ.get("CHASEOS_STUDIO_FALLBACK_STATE_DIR", "C:/tmp/chaseos-studio")))

    last_error: Exception | None = None
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write-probe"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            return candidate
        except Exception as exc:
            last_error = exc
            continue
    raise OSError(f"no writable Studio state directory found: {last_error}")


def studio_state_dir() -> Path:
    return _studio_state_dir()


def is_dev_mode() -> bool:
    return bool(os.environ.get("CHASEOS_DEV")) or "--dev" in sys.argv


def frontend_dir() -> Path:
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        bundled_root = Path(meipass)
        for candidate in (
            bundled_root / "studio_frontend",
            bundled_root / "runtime" / "studio" / "shell" / "frontend",
        ):
            if (candidate / "index.html").is_file():
                return candidate
    return Path(__file__).parent / "frontend"


def save_window_state(vault_root: Path, width: int, height: int, x: int, y: int) -> None:
    import json
    state_file = _studio_state_dir() / "window-state.json"
    try:
        state_file.write_text(
            json.dumps(
                {
                    "last_vault_root": str(vault_root),
                    "width": width,
                    "height": height,
                    "x": x,
                    "y": y,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    except Exception:
        pass
