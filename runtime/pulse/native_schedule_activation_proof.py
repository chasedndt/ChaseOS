"""Bounded ChaseOS Pulse native schedule activation/catch-up proof.

This proof exercises the ChaseOS-owned Pulse catch-up artifact path without
starting a schedule daemon, installing cron, enabling the manifest, calling
providers/connectors, or mutating canonical ChaseOS state.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - fallback path for minimal environments
    yaml = None

from runtime.pulse.card_schema import now_utc
from runtime.pulse.minimal_deck import generate_and_write_minimal_user_deck

PULSE_NATIVE_SCHEDULE_MANIFEST_PATH = (
    "runtime/schedules/manifests/chaseos_pulse_daily.yaml"
)
NATIVE_SCHEDULE_ACTIVATION_PROOF_PATH = (
    "06_AGENTS/ChaseOS-Pulse-Native-Schedule-Activation-Catchup-Proof.md"
)
NATIVE_SCHEDULE_PROOF_RECORD_DIR = (
    Path("07_LOGS") / "Pulse-Decks" / "native-schedule-proof"
)


@dataclass(frozen=True)
class PulseNativeScheduleActivationProof:
    generated_at: str
    proof_status: str
    dry_run: bool
    schedule_id: str
    manifest_path: str
    manifest_status: str
    manifest_activation_state: str
    schedule_manifest_enabled: bool
    catchup_policy: str
    catchup_deck_written: bool
    proof_written: bool
    schedule_manifest_written: bool
    schedule_daemon_started: bool
    deck_artifact: dict[str, Any] | None
    proof_path: str | None
    record_path: str | None
    writes: list[str]
    schedule_activation_allowed: bool = False
    provider_or_connector_call_allowed: bool = False
    canonical_writeback_allowed: bool = False
    mutates_canonical_state: bool = False
    rd_workbook_update_allowed: bool = False
    agent_bus_task_written: bool = False

    def validate(self) -> None:
        if self.proof_status not in {"ready", "complete"}:
            raise ValueError("invalid proof_status")
        if self.dry_run and self.writes:
            raise ValueError("dry-run native schedule proof cannot write artifacts")
        if self.schedule_manifest_written:
            raise ValueError("native schedule proof cannot mutate the schedule manifest")
        if self.schedule_daemon_started:
            raise ValueError("native schedule proof cannot start a schedule daemon")
        if self.schedule_activation_allowed:
            raise ValueError("native schedule proof cannot grant schedule activation authority")
        if self.provider_or_connector_call_allowed:
            raise ValueError("native schedule proof cannot call providers/connectors")
        if self.canonical_writeback_allowed or self.mutates_canonical_state:
            raise ValueError("native schedule proof cannot mutate canonical state")
        if self.rd_workbook_update_allowed:
            raise ValueError("native schedule proof cannot update the R&D workbook")
        if self.agent_bus_task_written:
            raise ValueError("native schedule proof cannot write Agent Bus tasks")
        if self.proof_status == "complete" and not self.catchup_deck_written:
            raise ValueError("complete proof requires a catch-up deck artifact")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _relative_to_vault(vault: Path, path: Path) -> str:
    return path.resolve().relative_to(vault).as_posix()


def _load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValueError(f"Pulse native schedule manifest missing: {path}")
    text = path.read_text(encoding="utf-8")
    if yaml is not None:
        parsed = yaml.safe_load(text) or {}
    else:
        parsed = _parse_simple_yaml(text)
    if not isinstance(parsed, dict):
        raise ValueError("Pulse native schedule manifest must be a mapping")
    return parsed


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    # Narrow fallback sufficient for the flat/nested scalar fields this proof reads.
    parsed: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, parsed)]
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#") or ":" not in raw:
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        key, value = raw.strip().split(":", 1)
        value = value.strip().strip('"')
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if value == "":
            child: dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            if value.lower() == "true":
                parent[key] = True
            elif value.lower() == "false":
                parent[key] = False
            else:
                parent[key] = value
    return parsed


def _date_slug(generated_at: str) -> str:
    date = generated_at[:10]
    if len(date) != 10:
        date = now_utc()[:10]
    return date


def _render_proof_markdown(result: PulseNativeScheduleActivationProof) -> str:
    deck_json = result.deck_artifact.get("json_path") if result.deck_artifact else "(none)"
    deck_md = result.deck_artifact.get("markdown_path") if result.deck_artifact else "(none)"
    return "\n".join(
        [
            "# ChaseOS Pulse Native Schedule Activation / Catch-Up Proof",
            "",
            f"Generated: {result.generated_at}",
            "Status: PASS",
            "Runtime lane: Hermes / Optimus",
            "",
            "## Scope",
            "",
            "This proof exercises the ChaseOS-owned Pulse catch-up artifact path from the native schedule manifest intent. It does not enable a persistent scheduler.",
            "",
            "## Evidence",
            "",
            f"- schedule_id: `{result.schedule_id}`",
            f"- manifest: `{result.manifest_path}`",
            f"- manifest status: `{result.manifest_status}`",
            f"- manifest activation_state: `{result.manifest_activation_state}`",
            f"- manifest enabled: `{result.schedule_manifest_enabled}`",
            f"- missed-run policy if_machine_off: `{result.catchup_policy}`",
            f"- catch-up deck JSON: `{deck_json}`",
            f"- catch-up deck Markdown: `{deck_md}`",
            "",
            "## Boundary Proof",
            "",
            "- No schedule daemon was started.",
            "- No cron/Windows Task Scheduler/OpenClaw scheduler ownership was installed.",
            "- The schedule manifest was not mutated or enabled by this proof.",
            "- No provider/connector call occurred.",
            "- No Agent Bus task was written.",
            "- No candidate apply or memory approval occurred.",
            "- No canonical writeback or `02_KNOWLEDGE/` mutation occurred.",
            "- No R&D workbook update occurred.",
            "",
            "## ChaseOS OS Alignment",
            "",
            "Pulse remains a native ChaseOS proactive-intelligence subsystem. This proof validates the local artifact/catch-up path as an OS-owned scheduled-workflow lane while keeping runtime instances as bounded executors, not schedule owners or canonical truth engines.",
            "",
        ]
    )


def build_native_schedule_activation_catchup_proof(
    vault_root: str | Path,
    *,
    generated_at: str | None = None,
    live: bool = False,
) -> PulseNativeScheduleActivationProof:
    """Build or write the bounded native schedule/catch-up proof.

    ``live=False`` previews the proof and writes nothing. ``live=True`` writes a
    deterministic catch-up deck artifact and proof record, while preserving the
    native schedule manifest and daemon state unchanged.
    """
    vault = _vault_path(vault_root)
    timestamp = generated_at or now_utc()
    manifest = _load_manifest(vault / PULSE_NATIVE_SCHEDULE_MANIFEST_PATH)
    schedule_id = str(manifest.get("schedule_id") or "")
    if schedule_id != "chaseos_pulse_daily":
        raise ValueError("Pulse native schedule proof requires chaseos_pulse_daily")
    missed_run_policy = manifest.get("missed_run_policy") or {}
    if not isinstance(missed_run_policy, dict):
        raise ValueError("Pulse native schedule manifest missed_run_policy must be a mapping")
    catchup_policy = str(missed_run_policy.get("if_machine_off") or "")
    if catchup_policy != "catch_up_once":
        raise ValueError("Pulse native schedule proof requires catch_up_once missed-run policy")
    if bool((manifest.get("source_policy") or {}).get("external_connectors_enabled", False)):
        raise ValueError("Pulse native schedule proof requires external connectors disabled")
    if bool((manifest.get("deck") or {}).get("canonical_writeback_enabled", False)):
        raise ValueError("Pulse native schedule proof requires canonical writeback disabled")

    deck_artifact: dict[str, Any] | None = None
    writes: list[str] = []
    proof_path: str | None = None
    record_path: str | None = None
    proof_written = False
    catchup_deck_written = False

    if live:
        slug_date = _date_slug(timestamp)
        artifact = generate_and_write_minimal_user_deck(
            vault,
            deck_id=f"pulse-user-{slug_date}-native-schedule-catchup",
            slug=f"{slug_date}-native-schedule-catchup-pulse",
            generated_at=timestamp,
        )
        deck_artifact = artifact.to_dict()
        catchup_deck_written = True
        writes.extend([artifact.markdown_path, artifact.json_path])

    result = PulseNativeScheduleActivationProof(
        generated_at=timestamp,
        proof_status="complete" if live else "ready",
        dry_run=not live,
        schedule_id=schedule_id,
        manifest_path=PULSE_NATIVE_SCHEDULE_MANIFEST_PATH,
        manifest_status=str(manifest.get("status") or "unknown"),
        manifest_activation_state=str(manifest.get("activation_state") or "unknown"),
        schedule_manifest_enabled=bool(manifest.get("enabled", False)),
        catchup_policy=catchup_policy,
        catchup_deck_written=catchup_deck_written,
        proof_written=False,
        schedule_manifest_written=False,
        schedule_daemon_started=False,
        deck_artifact=deck_artifact,
        proof_path=None,
        record_path=None,
        writes=writes,
    )
    result.validate()

    if live:
        proof_file = vault / NATIVE_SCHEDULE_ACTIVATION_PROOF_PATH
        proof_file.parent.mkdir(parents=True, exist_ok=True)
        record_file = vault / NATIVE_SCHEDULE_PROOF_RECORD_DIR / f"{_date_slug(timestamp)}-native-schedule-catchup-proof.json"
        record_file.parent.mkdir(parents=True, exist_ok=True)
        proof_path = _relative_to_vault(vault, proof_file)
        record_path = _relative_to_vault(vault, record_file)
        result = PulseNativeScheduleActivationProof(
            **{
                **result.to_dict(),
                "proof_written": True,
                "proof_path": proof_path,
                "record_path": record_path,
                "writes": [*writes, proof_path, record_path],
            }
        )
        proof_file.write_text(_render_proof_markdown(result), encoding="utf-8")
        record_file.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")
        proof_written = True

    if proof_written:
        result.validate()
    return result
