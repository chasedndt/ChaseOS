"""Read-only connector/source-scanner readiness for ChaseOS Pulse.

This module defines the governed bridge between Pulse and source acquisition
surfaces. It inventories declared local paths and connector code posture only;
it does not read secrets, make network calls, browse, fetch feeds, scan browser
history, activate schedules, or promote outputs.
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from runtime.pulse.card_schema import now_utc


READINESS_STATUS_READY_BLOCKED = "contract_ready_live_execution_blocked"
READINESS_STATUS_PARTIAL = "partial"
READINESS_STATUS_MISSING = "missing"
READINESS_STATUSES = {
    READINESS_STATUS_READY_BLOCKED,
    READINESS_STATUS_PARTIAL,
    READINESS_STATUS_MISSING,
}

CONNECTOR_STATUS_LOCAL_READY = "local_ready"
CONNECTOR_STATUS_AVAILABLE_INACTIVE = "available_inactive"
CONNECTOR_STATUS_PLANNED = "planned"
CONNECTOR_STATUS_MISSING = "missing"
CONNECTOR_STATUSES = {
    CONNECTOR_STATUS_LOCAL_READY,
    CONNECTOR_STATUS_AVAILABLE_INACTIVE,
    CONNECTOR_STATUS_PLANNED,
    CONNECTOR_STATUS_MISSING,
}

SOURCE_SURFACE_STATUS_READY = "ready"
SOURCE_SURFACE_STATUS_PARTIAL = "partial"
SOURCE_SURFACE_STATUS_MISSING = "missing"
SOURCE_SURFACE_STATUSES = {
    SOURCE_SURFACE_STATUS_READY,
    SOURCE_SURFACE_STATUS_PARTIAL,
    SOURCE_SURFACE_STATUS_MISSING,
}

BLOCKED_EFFECTS = (
    "agent_bus_task_write",
    "approval_execution",
    "autonomous_promotion",
    "browser_history_ingest",
    "canonical_writeback",
    "credential_or_secret_read",
    "external_connector_call",
    "memory_approval",
    "provider_call",
    "schedule_activation",
    "unrestricted_web_scan",
)

DENIED_SOURCE_CLASSES = (
    "browser_history",
    "cookies",
    "credential_stores",
    "password_managers",
    "private_email_without_connector_approval",
    "private_calendar_without_connector_approval",
    "unbounded_filesystem_scan",
)

LOCAL_SOURCE_SURFACES = (
    (
        "pulse_decks",
        "07_LOGS/Pulse-Decks",
        "Existing Pulse deck artifacts and review lanes",
    ),
    (
        "source_intelligence",
        "runtime/source_intelligence",
        "Source Intelligence Core packages, outputs, indexes, and workspaces",
    ),
    (
        "capture_inputs",
        "03_INPUTS",
        "Governed capture and quarantine folders",
    ),
    (
        "build_logs",
        "07_LOGS/Build-Logs",
        "Build logs for repo/runtime signal extraction",
    ),
    (
        "agent_activity",
        "07_LOGS/Agent-Activity",
        "Agent activity logs and runtime execution traces",
    ),
    (
        "acquisition_runtime",
        "runtime/acquisition",
        "Acquisition/normalization adapters and source-pack substrate",
    ),
)

CONNECTOR_CONTRACTS = (
    {
        "connector_id": "capture_file",
        "label": "Capture File",
        "adapter_path": "runtime/capture/capture.py",
        "source_class": "local_file",
        "execution_mode": "local_declared_input",
        "status_if_present": CONNECTOR_STATUS_LOCAL_READY,
        "external_call": False,
        "approval_required_for_live": False,
    },
    {
        "connector_id": "capture_browser_file",
        "label": "Browser HTML File Import",
        "adapter_path": "runtime/capture/connectors/browser_connector.py",
        "source_class": "operator_supplied_html_file",
        "execution_mode": "local_file_only",
        "status_if_present": CONNECTOR_STATUS_LOCAL_READY,
        "external_call": False,
        "approval_required_for_live": False,
    },
    {
        "connector_id": "rss_capture",
        "label": "RSS / Atom Capture",
        "adapter_path": "runtime/capture/connectors/rss_connector.py",
        "source_class": "rss_atom_feed",
        "execution_mode": "external_opt_in",
        "status_if_present": CONNECTOR_STATUS_AVAILABLE_INACTIVE,
        "external_call": True,
        "approval_required_for_live": True,
    },
    {
        "connector_id": "perplexity_capture",
        "label": "Perplexity Capture",
        "adapter_path": "runtime/capture/connectors/perplexity_connector.py",
        "source_class": "external_ai_synthesis",
        "execution_mode": "external_opt_in",
        "status_if_present": CONNECTOR_STATUS_AVAILABLE_INACTIVE,
        "external_call": True,
        "approval_required_for_live": True,
    },
    {
        "connector_id": "grok_capture",
        "label": "Grok / xAI Capture",
        "adapter_path": "runtime/capture/connectors/grok_connector.py",
        "source_class": "external_ai_synthesis",
        "execution_mode": "external_opt_in",
        "status_if_present": CONNECTOR_STATUS_AVAILABLE_INACTIVE,
        "external_call": True,
        "approval_required_for_live": True,
    },
    {
        "connector_id": "acquisition_rss_live",
        "label": "Acquisition RSS Live Adapter",
        "adapter_path": "runtime/acquisition/adapters/rss_live_adapter.py",
        "source_class": "rss_atom_feed",
        "execution_mode": "external_opt_in",
        "status_if_present": CONNECTOR_STATUS_AVAILABLE_INACTIVE,
        "external_call": True,
        "approval_required_for_live": True,
    },
    {
        "connector_id": "acquisition_web_scrape",
        "label": "Acquisition Web Scrape Adapter",
        "adapter_path": "runtime/acquisition/adapters/web_scrape_adapter.py",
        "source_class": "web_page",
        "execution_mode": "external_opt_in",
        "status_if_present": CONNECTOR_STATUS_AVAILABLE_INACTIVE,
        "external_call": True,
        "approval_required_for_live": True,
    },
    {
        "connector_id": "email_imap",
        "label": "Email IMAP Acquisition Adapter",
        "adapter_path": "runtime/acquisition/adapters/email_adapter.py",
        "source_class": "private_email",
        "execution_mode": "connector_approval_required",
        "status_if_present": CONNECTOR_STATUS_AVAILABLE_INACTIVE,
        "external_call": True,
        "approval_required_for_live": True,
    },
    {
        "connector_id": "google_docs_drive",
        "label": "Google Docs / Drive Acquisition Adapter",
        "adapter_path": "runtime/acquisition/adapters/google_adapter.py",
        "source_class": "cloud_document",
        "execution_mode": "connector_approval_required",
        "status_if_present": CONNECTOR_STATUS_AVAILABLE_INACTIVE,
        "external_call": True,
        "approval_required_for_live": True,
    },
)


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _count_files_bounded(root: Path, *, max_files: int = 200) -> int:
    if not root.exists():
        return 0
    count = 0
    skip_dirs = {"__pycache__", ".pytest_cache", "_tmp_pytest", "_tmp_cli_test"}
    for current, dirs, files in os.walk(root, onerror=lambda _error: None):
        dirs[:] = [name for name in dirs if name not in skip_dirs and not name.startswith("tmp")]
        count += len(files)
        if count >= max_files:
            return max_files
    return count


@dataclass(frozen=True)
class PulseSourceSurface:
    surface_id: str
    path: str
    label: str
    status: str
    file_count_bounded: int = 0
    reads_content: bool = False

    def validate(self) -> None:
        if not self.surface_id:
            raise ValueError("source surface_id is required")
        if not self.path:
            raise ValueError("source surface path is required")
        if self.status not in SOURCE_SURFACE_STATUSES:
            raise ValueError("invalid source surface status")
        if self.file_count_bounded < 0:
            raise ValueError("file_count_bounded cannot be negative")
        if self.reads_content:
            raise ValueError("readiness source surface cannot read content")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class PulseConnectorContract:
    connector_id: str
    label: str
    adapter_path: str
    source_class: str
    execution_mode: str
    status: str
    external_call: bool
    approval_required_for_live: bool
    live_execution_enabled: bool = False
    secrets_read: bool = False
    hidden_history_ingest_allowed: bool = False

    def validate(self) -> None:
        if not self.connector_id:
            raise ValueError("connector_id is required")
        if self.status not in CONNECTOR_STATUSES:
            raise ValueError("invalid connector status")
        if self.live_execution_enabled:
            raise ValueError("readiness contract cannot enable live connector execution")
        if self.secrets_read:
            raise ValueError("readiness contract cannot read secrets")
        if self.hidden_history_ingest_allowed:
            raise ValueError("readiness contract cannot allow hidden history ingest")
        if self.external_call and not self.approval_required_for_live:
            raise ValueError("external connector calls require live approval")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class PulseConnectorSourceScannerReadiness:
    generated_at: str
    readiness_status: str
    local_source_surfaces: tuple[PulseSourceSurface, ...]
    connector_contracts: tuple[PulseConnectorContract, ...]
    allowed_source_classes: tuple[str, ...]
    denied_source_classes: tuple[str, ...] = DENIED_SOURCE_CLASSES
    next_recommended_pass: str = "chaseos-pulse-connector-source-scanner-local-preview"
    read_only: bool = True
    local_inventory_only: bool = True
    reads_source_content: bool = False
    writes_artifacts: bool = False
    live_connector_execution_enabled: bool = False
    provider_or_connector_call_allowed: bool = False
    unrestricted_web_scan_allowed: bool = False
    browser_history_ingest_allowed: bool = False
    credential_or_secret_read_allowed: bool = False
    schedule_activation_allowed: bool = False
    agent_bus_task_write_allowed: bool = False
    approval_execution_allowed: bool = False
    memory_approval_allowed: bool = False
    autonomous_promotion_allowed: bool = False
    canonical_writeback_allowed: bool = False
    blocked_effects: tuple[str, ...] = BLOCKED_EFFECTS

    @property
    def source_surface_count(self) -> int:
        return len(self.local_source_surfaces)

    @property
    def ready_source_surface_count(self) -> int:
        return sum(1 for surface in self.local_source_surfaces if surface.status == SOURCE_SURFACE_STATUS_READY)

    @property
    def connector_count(self) -> int:
        return len(self.connector_contracts)

    @property
    def external_connector_count(self) -> int:
        return sum(1 for connector in self.connector_contracts if connector.external_call)

    @property
    def live_enabled_connector_count(self) -> int:
        return sum(1 for connector in self.connector_contracts if connector.live_execution_enabled)

    def validate(self) -> None:
        if self.readiness_status not in READINESS_STATUSES:
            raise ValueError("invalid connector/source scanner readiness_status")
        for surface in self.local_source_surfaces:
            surface.validate()
        for connector in self.connector_contracts:
            connector.validate()
        if not self.read_only or not self.local_inventory_only:
            raise ValueError("connector/source scanner readiness must be read-only local inventory")
        if self.reads_source_content:
            raise ValueError("readiness contract cannot read source content")
        if self.writes_artifacts:
            raise ValueError("readiness contract cannot write artifacts")
        if self.live_connector_execution_enabled or self.live_enabled_connector_count:
            raise ValueError("readiness contract cannot enable live connector execution")
        if self.provider_or_connector_call_allowed:
            raise ValueError("readiness contract cannot call providers/connectors")
        if self.unrestricted_web_scan_allowed:
            raise ValueError("readiness contract cannot allow unrestricted web scan")
        if self.browser_history_ingest_allowed:
            raise ValueError("readiness contract cannot ingest browser history")
        if self.credential_or_secret_read_allowed:
            raise ValueError("readiness contract cannot read credentials or secrets")
        if self.schedule_activation_allowed:
            raise ValueError("readiness contract cannot activate schedules")
        if self.agent_bus_task_write_allowed:
            raise ValueError("readiness contract cannot write Agent Bus tasks")
        if self.approval_execution_allowed:
            raise ValueError("readiness contract cannot execute approvals")
        if self.memory_approval_allowed:
            raise ValueError("readiness contract cannot approve memory")
        if self.autonomous_promotion_allowed:
            raise ValueError("readiness contract cannot autonomously promote sources")
        if self.canonical_writeback_allowed:
            raise ValueError("readiness contract cannot write canonical state")
        if set(self.blocked_effects) != set(BLOCKED_EFFECTS):
            raise ValueError("readiness contract must declare blocked effects")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "generated_at": self.generated_at,
            "readiness_status": self.readiness_status,
            "source_surface_count": self.source_surface_count,
            "ready_source_surface_count": self.ready_source_surface_count,
            "connector_count": self.connector_count,
            "external_connector_count": self.external_connector_count,
            "live_enabled_connector_count": self.live_enabled_connector_count,
            "local_source_surfaces": [surface.to_dict() for surface in self.local_source_surfaces],
            "connector_contracts": [connector.to_dict() for connector in self.connector_contracts],
            "allowed_source_classes": list(self.allowed_source_classes),
            "denied_source_classes": list(self.denied_source_classes),
            "next_recommended_pass": self.next_recommended_pass,
            "read_only": self.read_only,
            "local_inventory_only": self.local_inventory_only,
            "reads_source_content": self.reads_source_content,
            "writes_artifacts": self.writes_artifacts,
            "live_connector_execution_enabled": self.live_connector_execution_enabled,
            "provider_or_connector_call_allowed": self.provider_or_connector_call_allowed,
            "unrestricted_web_scan_allowed": self.unrestricted_web_scan_allowed,
            "browser_history_ingest_allowed": self.browser_history_ingest_allowed,
            "credential_or_secret_read_allowed": self.credential_or_secret_read_allowed,
            "schedule_activation_allowed": self.schedule_activation_allowed,
            "agent_bus_task_write_allowed": self.agent_bus_task_write_allowed,
            "approval_execution_allowed": self.approval_execution_allowed,
            "memory_approval_allowed": self.memory_approval_allowed,
            "autonomous_promotion_allowed": self.autonomous_promotion_allowed,
            "canonical_writeback_allowed": self.canonical_writeback_allowed,
            "blocked_effects": list(self.blocked_effects),
        }


def build_pulse_connector_source_scanner_readiness(
    vault_root: str | Path,
    *,
    generated_at: str | None = None,
) -> PulseConnectorSourceScannerReadiness:
    """Return read-only Pulse connector/source-scanner readiness."""

    vault = _vault_path(vault_root)
    surfaces: list[PulseSourceSurface] = []
    for surface_id, rel_path, label in LOCAL_SOURCE_SURFACES:
        path = vault / rel_path
        status = SOURCE_SURFACE_STATUS_READY if path.exists() else SOURCE_SURFACE_STATUS_MISSING
        surfaces.append(
            PulseSourceSurface(
                surface_id=surface_id,
                path=rel_path,
                label=label,
                status=status,
                file_count_bounded=_count_files_bounded(path),
            )
        )

    connectors: list[PulseConnectorContract] = []
    allowed_source_classes: set[str] = set()
    for declaration in CONNECTOR_CONTRACTS:
        adapter_path = str(declaration["adapter_path"])
        present = (vault / adapter_path).is_file()
        status = (
            str(declaration["status_if_present"])
            if present
            else CONNECTOR_STATUS_MISSING
        )
        source_class = str(declaration["source_class"])
        if present:
            allowed_source_classes.add(source_class)
        connectors.append(
            PulseConnectorContract(
                connector_id=str(declaration["connector_id"]),
                label=str(declaration["label"]),
                adapter_path=adapter_path,
                source_class=source_class,
                execution_mode=str(declaration["execution_mode"]),
                status=status,
                external_call=bool(declaration["external_call"]),
                approval_required_for_live=bool(declaration["approval_required_for_live"]),
            )
        )

    ready_surface_count = sum(1 for surface in surfaces if surface.status == SOURCE_SURFACE_STATUS_READY)
    present_connector_count = sum(1 for connector in connectors if connector.status != CONNECTOR_STATUS_MISSING)
    if ready_surface_count >= 3 and present_connector_count >= 3:
        readiness_status = READINESS_STATUS_READY_BLOCKED
    elif ready_surface_count or present_connector_count:
        readiness_status = READINESS_STATUS_PARTIAL
    else:
        readiness_status = READINESS_STATUS_MISSING

    readiness = PulseConnectorSourceScannerReadiness(
        generated_at=generated_at or now_utc(),
        readiness_status=readiness_status,
        local_source_surfaces=tuple(surfaces),
        connector_contracts=tuple(connectors),
        allowed_source_classes=tuple(sorted(allowed_source_classes)),
    )
    readiness.validate()
    return readiness
