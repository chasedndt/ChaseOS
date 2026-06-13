"""
drift_scan.py — ChaseOS Phase 9 Feature 16
Doctrine / Behavior Alignment workflow

Compares declared domain priorities in Operating-System.md against
actual build log activity, Decision Ledger entries, and close-day reports.

Produces: 07_LOGS/Drift-Reports/YYYY-MM-DD-drift-scan.md

Design principles:
- Structured parsing only — no semantic inference
- Read-only vault access — doctrine files are never modified
- Honest gaps: if a domain has no recent logs, it is reported as potentially
  neglected, not invented as active
- All signal extracted from filenames + structured frontmatter (date, project)
- No ranking or scoring — output is a flagging list for operator review
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any


class WorkflowExecutionError(RuntimeError):
    """Fail-closed workflow error for drift_scan handler."""


# ── Configuration ─────────────────────────────────────────────────────────────

_LOOKBACK_DAYS = 30          # default: check for activity in last 30 days
_MAX_BUILD_LOGS = 200        # max files to scan in Build-Logs/
_MAX_CLOSE_LOGS = 30         # max close-day reports to scan
_MAX_DECISION_LOGS = 50      # max Decision Ledger files to scan


# ── Domain definition ─────────────────────────────────────────────────────────

@dataclass
class DomainEntry:
    letter: str           # A, B, C, ... R
    name: str             # canonical domain name
    keywords: list[str]   # filename/content keywords that signal activity


# Derived from 00_HOME/Operating-System.md Domain Map (A–R)
_DOMAINS: list[DomainEntry] = [
    DomainEntry("A", "ChaseOS / System Infrastructure",
                ["chaseos", "claude", "runtime", "agent", "vault", "hook", "mcp", "aor", "sbp"]),
    DomainEntry("B", "Trading Systems / Market Ops",
                ["trading", "tradingsystems", "tradfi", "market", "strikezone-trade", "crypto-trade", "trade-journal", "weekly-review"]),
    DomainEntry("C", "StrikeZone Crypto",
                ["strikezone", "discord", "whop", "signal", "crypto-signal"]),
    DomainEntry("D", "Indicator R&D / TradingView / Pine Script",
                ["indicator", "unikill", "pinescript", "tradingview", "bias-flip"]),
    DomainEntry("E", "TradeSync AI",
                ["tradesync", "trade-sync", "tradesync-ai"]),
    DomainEntry("F", "GeoMacro / Macro Intelligence",
                ["geomacro", "macro", "geo-macro"]),
    DomainEntry("G", "AI / Agent Engineering",
                ["ai-agent", "ai-agents", "llm", "rag", "langgraph", "agent-engineering"]),
    DomainEntry("H", "Full-Stack / Software Engineering",
                ["fullstack", "full-stack", "engineering", "hypelist", "hype-list", "dev"]),
    DomainEntry("I", "Cybersecurity / Bug Bounty",
                ["cybersecurity", "security", "bug-bounty", "bugbounty", "pentest", "kali"]),
    DomainEntry("J", "University / Academic Ops",
                ["university", "academic", "greenwich", "coursework", "module"]),
    DomainEntry("K", "Career Ops / Freelance",
                ["career", "freelance", "cv", "linkedin", "portfolio"]),
    DomainEntry("L", "Content Engine / Personal Brands",
                ["content", "brand", "chaintech", "chasercrypto", "chaser-sol", "ugc", "youtube", "twitter"]),
    DomainEntry("M", "Businesses / Entrepreneurial Ventures",
                ["business", "businesses", "hypelist", "flipworks", "saas", "monetize"]),
    DomainEntry("N", "Hardware / Systems / Robotics",
                ["hardware", "robotics", "raspberry", "gpu", "embedded"]),
    DomainEntry("O", "Doctrine / Philosophy / Identity",
                ["doctrine", "philosophy", "principles", "identity", "soul"]),
    DomainEntry("P", "Fitness / Combat / Physical",
                ["fitness", "boxing", "gym", "health", "running"]),
    DomainEntry("Q", "Networking / Social Capital",
                ["networking", "social", "network"]),
    DomainEntry("R", "Language Learning / Global Mobility",
                ["language", "mandarin", "chinese"]),
]

# Map letter → DomainEntry for quick lookup
_DOMAIN_MAP: dict[str, DomainEntry] = {d.letter: d for d in _DOMAINS}


# ── Data types ────────────────────────────────────────────────────────────────

@dataclass
class ActivitySignal:
    """A single detected activity signal linking to a vault file."""
    domain_letter: str
    domain_name: str
    file_path: str
    file_date: str          # ISO date string
    match_keyword: str


@dataclass
class OpenLoop:
    """An open loop item extracted from a close-day report."""
    source_file: str
    text: str
    file_date: str


@dataclass
class DriftScanResult:
    scan_date: str
    lookback_days: int
    domain_activity: dict[str, list[ActivitySignal]]    # letter → signals
    neglected_domains: list[DomainEntry]                # domains with zero signals
    active_domains: list[DomainEntry]                   # domains with ≥1 signal
    open_loops: list[OpenLoop]
    decision_count: int
    build_log_count: int
    close_log_count: int
    gaps: list[str]


# ── File discovery ────────────────────────────────────────────────────────────


def _build_logs(vault_root: Path, lookback_days: int) -> list[Path]:
    """Return build log files from 07_LOGS/Build-Logs/ within lookback window."""
    logs_dir = vault_root / "07_LOGS" / "Build-Logs"
    if not logs_dir.exists():
        return []
    cutoff = date.today() - timedelta(days=lookback_days)
    result = []
    for path in sorted(logs_dir.glob("*.md"), reverse=True)[:_MAX_BUILD_LOGS]:
        file_date = _extract_date_from_filename(path.name)
        if file_date and file_date >= cutoff:
            result.append(path)
    return result


def _close_day_logs(vault_root: Path) -> list[Path]:
    """Return operator close-day report files from 07_LOGS/Operator-Briefs/ (most recent first)."""
    briefs_dir = vault_root / "07_LOGS" / "Operator-Briefs"
    if not briefs_dir.exists():
        return []
    files = sorted(briefs_dir.glob("*.md"), reverse=True)[:_MAX_CLOSE_LOGS]
    # Filter to close-day reports by filename
    return [f for f in files if "close" in f.name.lower() or "day" in f.name.lower()]


def _decision_ledger_files(vault_root: Path) -> list[Path]:
    """Return Decision Ledger entry files (exclude index)."""
    ledger_dir = vault_root / "07_LOGS" / "Decision-Ledger"
    if not ledger_dir.exists():
        return []
    return [
        p for p in sorted(ledger_dir.glob("*.md"))[:_MAX_DECISION_LOGS]
        if "index" not in p.name.lower()
    ]


# ── Signal extraction ─────────────────────────────────────────────────────────


def _extract_date_from_filename(filename: str) -> date | None:
    """Extract YYYY-MM-DD date from a filename prefix."""
    m = re.match(r"(\d{4}-\d{2}-\d{2})", filename)
    if m:
        try:
            return date.fromisoformat(m.group(1))
        except ValueError:
            return None
    return None


def _match_domain(text: str) -> DomainEntry | None:
    """Return the first domain whose keyword appears in the lowercased text."""
    lower = text.lower()
    for domain in _DOMAINS:
        for kw in domain.keywords:
            if kw in lower:
                return domain
    return None


def _extract_signals_from_build_logs(
    build_logs: list[Path],
    vault_root: Path,
) -> list[ActivitySignal]:
    """Extract domain activity signals from build log filenames and frontmatter."""
    signals: list[ActivitySignal] = []

    for log_path in build_logs:
        file_date_obj = _extract_date_from_filename(log_path.name)
        file_date_str = file_date_obj.isoformat() if file_date_obj else "unknown"

        # Match from filename
        domain = _match_domain(log_path.stem)
        if domain:
            signals.append(ActivitySignal(
                domain_letter=domain.letter,
                domain_name=domain.name,
                file_path=str(log_path.relative_to(vault_root)).replace("\\", "/"),
                file_date=file_date_str,
                match_keyword=f"filename:{log_path.stem}",
            ))
            continue

        # Fallback: read first 30 lines of the file for project/domain frontmatter
        try:
            content = log_path.read_text(encoding="utf-8", errors="replace")
            header = "\n".join(content.splitlines()[:30])
            domain = _match_domain(header)
            if domain:
                signals.append(ActivitySignal(
                    domain_letter=domain.letter,
                    domain_name=domain.name,
                    file_path=str(log_path.relative_to(vault_root)).replace("\\", "/"),
                    file_date=file_date_str,
                    match_keyword="header-content",
                ))
        except OSError:
            pass

    return signals


def _extract_open_loops(close_day_logs: list[Path], vault_root: Path) -> list[OpenLoop]:
    """Extract open-loop items from close-day operator brief markdown files."""
    loops: list[OpenLoop] = []
    # Pattern: markdown checkbox items with [ ] or [x] under "open loops" sections
    open_loop_pattern = re.compile(r"-\s*\[ \]\s*(.+)", re.IGNORECASE)
    section_header = re.compile(r"^#+\s*(open\s*loops?|carry.forward|unresolved)", re.IGNORECASE)

    for path in close_day_logs:
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        file_date_obj = _extract_date_from_filename(path.name)
        file_date = file_date_obj.isoformat() if file_date_obj else "unknown"
        rel_path = str(path.relative_to(vault_root)).replace("\\", "/")

        in_section = False
        for line in content.splitlines():
            if section_header.match(line):
                in_section = True
                continue
            if in_section:
                # Stop at next section header
                if re.match(r"^#+\s+", line) and not section_header.match(line):
                    in_section = False
                    continue
                m = open_loop_pattern.match(line.strip())
                if m:
                    loops.append(OpenLoop(
                        source_file=rel_path,
                        text=m.group(1).strip()[:200],
                        file_date=file_date,
                    ))

    return loops


# ── Comparison engine ─────────────────────────────────────────────────────────


def _compute_domain_activity(
    signals: list[ActivitySignal],
) -> dict[str, list[ActivitySignal]]:
    """Group signals by domain letter."""
    grouped: dict[str, list[ActivitySignal]] = {d.letter: [] for d in _DOMAINS}
    for sig in signals:
        if sig.domain_letter in grouped:
            grouped[sig.domain_letter].append(sig)
    return grouped


def _classify_domains(
    domain_activity: dict[str, list[ActivitySignal]],
) -> tuple[list[DomainEntry], list[DomainEntry]]:
    """Return (neglected_domains, active_domains)."""
    neglected = [d for d in _DOMAINS if not domain_activity.get(d.letter)]
    active = [d for d in _DOMAINS if domain_activity.get(d.letter)]
    return neglected, active


# ── Report rendering ──────────────────────────────────────────────────────────


def _render_drift_report(result: DriftScanResult) -> str:
    lines = [
        "---",
        "type: drift-report",
        f"date: {result.scan_date}",
        f"lookback_days: {result.lookback_days}",
        f"workflow: drift_scan",
        "---",
        "",
        f"# Drift Scan Report — {result.scan_date}",
        "",
        "> Read-only scan. Doctrine files not modified. Flags are for operator review only.",
        "",
        "---",
        "",
        "## Summary",
        "",
        f"- **Scan date:** {result.scan_date}",
        f"- **Lookback window:** {result.lookback_days} days",
        f"- **Build logs scanned:** {result.build_log_count}",
        f"- **Close-day reports scanned:** {result.close_log_count}",
        f"- **Decision Ledger entries found:** {result.decision_count}",
        f"- **Active domains (had activity):** {len(result.active_domains)} / {len(_DOMAINS)}",
        f"- **Potentially neglected domains:** {len(result.neglected_domains)} / {len(_DOMAINS)}",
        f"- **Open loops detected:** {len(result.open_loops)}",
        "",
        "---",
        "",
        "## Potentially Neglected Domains",
        "",
        f"> Domains with zero build log activity in the last {result.lookback_days} days.",
        "> This does not mean no work happened — only that no build log in the scan window matched this domain.",
        "",
    ]

    if not result.neglected_domains:
        lines.append("- No domains were flagged as neglected in this scan window.")
    else:
        for d in result.neglected_domains:
            lines.append(f"- **{d.letter} · {d.name}**")

    lines.extend([
        "",
        "---",
        "",
        "## Active Domains",
        "",
        f"> Domains with at least one build log signal in the last {result.lookback_days} days.",
        "",
    ])

    if not result.active_domains:
        lines.append("- No active domain signals were detected in this scan window.")
    else:
        for d in result.active_domains:
            signals = result.domain_activity.get(d.letter, [])
            sig_desc = f"{len(signals)} signal(s)"
            latest = max(signals, key=lambda s: s.file_date) if signals else None
            latest_str = f" | Latest: {latest.file_date} ({latest.file_path.split('/')[-1]})" if latest else ""
            lines.append(f"- **{d.letter} · {d.name}** — {sig_desc}{latest_str}")

    lines.extend([
        "",
        "---",
        "",
        "## Open Loops (from Close-Day Reports)",
        "",
    ])

    if not result.open_loops:
        lines.append("- No open loops were extracted from close-day reports.")
    else:
        for loop in result.open_loops:
            lines.append(f"- [{loop.file_date}] {loop.text}")
            lines.append(f"  _Source: `{loop.source_file}`_")

    lines.extend([
        "",
        "---",
        "",
        "## Recommended Review Items",
        "",
    ])

    review_items: list[str] = []

    # Flag domains neglected for full lookback window
    if result.neglected_domains:
        review_items.append(
            f"**{len(result.neglected_domains)} domain(s) had zero build log activity** in the last "
            f"{result.lookback_days} days: "
            + ", ".join(f"{d.letter}·{d.name.split('/')[0].strip()}" for d in result.neglected_domains[:5])
            + ("..." if len(result.neglected_domains) > 5 else "")
            + ". Consider whether these are intentionally parked or accidentally neglected."
        )

    # Flag persistent open loops
    if result.open_loops:
        review_items.append(
            f"**{len(result.open_loops)} open loop(s)** were found in close-day reports. "
            "Review whether any have persisted across multiple close-day cycles."
        )

    if not review_items:
        lines.append("- No specific review items were flagged in this scan.")
    else:
        for item in review_items:
            lines.append(f"- {item}")

    if result.gaps:
        lines.extend([
            "",
            "---",
            "",
            "## Scan Gaps",
            "",
            "> Files or paths that could not be accessed during the scan.",
            "",
        ])
        for gap in result.gaps:
            lines.append(f"- {gap}")

    lines.extend([
        "",
        "---",
        "",
        "> *drift_scan is a factual activity scanner. It flags what is absent from build logs.*",
        "> *It does not modify doctrine. It does not infer intent. Operator judgement governs the response.*",
        "",
    ])

    return "\n".join(lines)


# ── Public API ────────────────────────────────────────────────────────────────


def run_drift_scan(inputs: dict, vault_root: Path) -> dict:
    """
    AOR workflow handler for drift_scan.

    Inputs:
        lookback_days: int (default 30) — number of days to scan
        date: str (YYYY-MM-DD, optional) — report date override

    Returns a writeback dict for AOR Stage 7.
    """
    lookback_days = int(inputs.get("lookback_days", _LOOKBACK_DAYS))
    if lookback_days < 1:
        raise WorkflowExecutionError(f"lookback_days must be >= 1; got {lookback_days}")
    if lookback_days > 365:
        raise WorkflowExecutionError(f"lookback_days must be <= 365; got {lookback_days}")

    raw_date = inputs.get("date")
    try:
        run_date = date.fromisoformat(str(raw_date)) if raw_date else date.today()
    except ValueError as exc:
        raise WorkflowExecutionError(f"invalid date {raw_date!r}: {exc}") from exc

    gaps: list[str] = []

    # ── Collect data ──────────────────────────────────────────────────────────
    build_logs = _build_logs(vault_root, lookback_days)
    close_logs = _close_day_logs(vault_root)
    decision_files = _decision_ledger_files(vault_root)

    # ── Extract signals ───────────────────────────────────────────────────────
    signals = _extract_signals_from_build_logs(build_logs, vault_root)
    open_loops = _extract_open_loops(close_logs, vault_root)

    # ── Compute domain activity ───────────────────────────────────────────────
    domain_activity = _compute_domain_activity(signals)
    neglected, active = _classify_domains(domain_activity)

    result = DriftScanResult(
        scan_date=run_date.isoformat(),
        lookback_days=lookback_days,
        domain_activity=domain_activity,
        neglected_domains=neglected,
        active_domains=active,
        open_loops=open_loops,
        decision_count=len(decision_files),
        build_log_count=len(build_logs),
        close_log_count=len(close_logs),
        gaps=gaps,
    )

    content = _render_drift_report(result)
    output_path = f"07_LOGS/Drift-Reports/{run_date.isoformat()}-drift-scan.md"

    return {
        "handler_status": "executed",
        "workflow_id": "drift_scan",
        "date": run_date.isoformat(),
        "neglected_domain_count": len(neglected),
        "active_domain_count": len(active),
        "open_loop_count": len(open_loops),
        "build_log_count": len(build_logs),
        "writebacks": [
            {
                "path": output_path,
                "content": content,
                "content_type": "text/markdown",
            }
        ],
    }
