from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
DOMAIN = "https://chaseos.ai"

ROUTES = [
    "",
    "waitlist",
    "studio",
    "demo",
    "forge",
    "standards",
    "open-core",
    "pricing",
    "docs",
    "download",
    "privacy",
    "security",
    "roadmap",
    "support",
    "terms",
    "creators",
    "submit-pack",
    "admin",
]

STANDARD_FILES = [
    "chaseos.pack.json",
    "chaseos.forge-index.json",
    "chaseos.agent.json",
    "chaseos.approval.json",
    "chaseos.graph.json",
    "chaseos.source.json",
    "chaseos.outcome.json",
    "chaseos.entitlement.json",
    "chaseos.managed-job.json",
]

REQUIRED_PACK_FIELDS = {
    "id",
    "name",
    "version",
    "description",
    "category",
    "status",
    "author",
    "price_class",
    "license",
    "certification_status",
    "compatibility",
    "permissions_required",
    "approval_required",
    "manifest_url",
    "docs_url",
    "digest_algorithm",
    "manifest_digest_sha256",
    "install_boundary",
    "submission_url",
    "authority_boundary",
}

FORBIDDEN_PUBLIC_STRINGS = [
    "chaseos.systems",
    "getchaseos",
    "trychaseos",
    "https://chaseos.dev",
    "http://chaseos.dev",
    "https://chaseos.app",
    "http://chaseos.app",
    "fully autonomous company operator",
    "arbitrary browser automation",
    "live marketplace payments",
    "managed agents available now",
    "enterprise ready",
    "auto-post to LinkedIn",
    "auto-DM",
    "payment mutation",
    "CRM mutation",
    "C:\\Users",
    "C:/Users",
    "<WSL_HOME>",
    "API_KEY",
    "SECRET_KEY",
]


def route_file(route: str) -> Path:
    return ROOT / "index.html" if not route else ROOT / route / "index.html"


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def read(path: Path) -> str:
    if not path.exists():
        fail(f"missing file: {path}")
    return path.read_text(encoding="utf-8")


def assert_contains(text: str, expected: str, context: str) -> None:
    if expected not in text:
        fail(f"{context} missing {expected!r}")


def sha256_json(data: dict) -> str:
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def assert_public_pages() -> list[Path]:
    public_files: list[Path] = []
    for route in ROUTES:
        path = route_file(route)
        html = read(path)
        context = route or "home"
        assert_contains(html, DOMAIN, context)
        public_files.append(path)

    home = read(ROOT / "index.html")
    assert_contains(
        home,
        "ChaseOS is the local-first AI operating system for builders running real projects with agents.",
        "homepage",
    )
    assert_contains(
        home,
        "ChaseOS turns scattered AI chats, docs, repos, sources, runtimes, browser workflows, approvals, and outputs into one governed knowledge graph.",
        "homepage",
    )
    assert_contains(home, "Join the early access waitlist", "homepage")
    assert_contains(home, "Explore Chaser Forge", "homepage")
    assert_contains(home, "Read the docs", "homepage")

    waitlist = read(ROOT / "waitlist" / "index.html")
    for field in [
        "email",
        "name",
        "persona",
        "current_tools",
        "biggest_ai_workflow_pain",
        "use_case",
        "interest_type",
        "operating_system",
        "willingness_to_pay",
        "consent_to_contact",
        "source_utm",
    ]:
        assert_contains(waitlist, f'name="{field}"', "waitlist form")
    for required_marker in [
        'name="email" type="email" autocomplete="email" required',
        'name="name" type="text" autocomplete="name" required',
        'name="persona" required',
        'name="current_tools" required',
        'name="biggest_ai_workflow_pain" required',
        'name="use_case" required',
        'name="interest_type" required',
        'name="operating_system" required',
        'name="willingness_to_pay" required',
        'name="source_utm" type="text" required',
        'name="consent_to_contact" type="checkbox" required',
    ]:
        assert_contains(waitlist, required_marker, "waitlist required field")
    assert_contains(waitlist, 'type="email"', "waitlist email")
    assert_contains(waitlist, "No outbound email campaign is wired", "waitlist no email campaign")
    if "<form id=\"waitlist-form\" class=\"panel\" novalidate action=" in waitlist or "method=" in waitlist:
        fail("waitlist form must not post to a backend in the static placeholder")
    site_js = read(ROOT / "site.js")
    for forbidden_call in ["fetch(", "XMLHttpRequest", "mailto:", "sendBeacon", "navigator.sendBeacon"]:
        if forbidden_call in site_js or forbidden_call in waitlist:
            fail(f"waitlist static placeholder must not include outbound primitive: {forbidden_call}")
    for required_js_name in ["email", "name", "persona", "current_tools", "biggest_ai_workflow_pain", "use_case", "interest_type", "operating_system", "willingness_to_pay", "source_utm", "consent_to_contact"]:
        assert_contains(site_js, required_js_name, "waitlist required client validation")
    assert_contains(waitlist, "Safe static placeholder", "waitlist storage placeholder")
    assert_contains(waitlist, "Backend/storage decision required", "waitlist storage decision")

    admin = read(ROOT / "admin" / "index.html")
    assert_contains(admin, 'name="robots" content="noindex,nofollow"', "admin noindex")
    assert_contains(admin, "DISABLED / AUTH REQUIRED STUB / NO PII", "admin boundary")
    assert_contains(admin, "auth allowlist", "admin protection")
    assert_contains(admin, "Safe export preview", "admin safe surface")
    for forbidden_admin_surface in ["local vaults", "private graphs", "provider keys", "runtime logs", "private project memory"]:
        assert_contains(admin, forbidden_admin_surface, "admin forbidden private surfaces")
    return public_files


def assert_demo_route() -> list[Path]:
    demo = ROOT / "demo" / "index.html"
    html = read(demo)
    for expected in [
        "Public-safe demo fixture",
        "Graph visibility",
        "Source/project organization",
        "Runtime/agent awareness",
        "Approval visibility",
        "Mission pack preview",
        "No runtime authority is granted by this route",
        "fixtures/demo/chaseos_launch/graph_nodes.json",
    ]:
        assert_contains(html, expected, "demo route")
    return [demo]


def assert_forge() -> list[Path]:
    index_path = ROOT / "forge" / "index.json"
    data = json.loads(read(index_path))
    if data.get("base_url") != DOMAIN:
        fail("Forge index base_url is not chaseos.ai")
    if data.get("marketplace_payments") != "not_enabled":
        fail("Forge index must keep marketplace payments disabled")
    packs = data.get("packs")
    if not isinstance(packs, list) or len(packs) < 6:
        fail("Forge index needs at least six preview packs")
    paths = [index_path]
    for pack in packs:
        missing = REQUIRED_PACK_FIELDS - set(pack)
        if missing:
            fail(f"pack {pack.get('id', '<unknown>')} missing fields: {sorted(missing)}")
        if pack["status"] != "preview":
            fail(f"pack {pack['id']} status must be preview")
        if not str(pack["manifest_url"]).startswith(f"{DOMAIN}/forge/packs/"):
            fail(f"pack {pack['id']} manifest_url must use chaseos.ai")
        if pack["digest_algorithm"] != "sha256":
            fail(f"pack {pack['id']} digest_algorithm must be sha256")
        authority = pack.get("authority_boundary") or {}
        if authority.get("payment_required") is not False:
            fail(f"pack {pack['id']} must not require payment")
        if authority.get("license_enforcement_enabled") is not False:
            fail(f"pack {pack['id']} must not enable license enforcement")
        if authority.get("auto_install_enabled") is not False:
            fail(f"pack {pack['id']} must not enable auto-install")
        if authority.get("untrusted_remote_install_allowed") is not False:
            fail(f"pack {pack['id']} must not allow untrusted remote install")
        manifest = ROOT / "forge" / "packs" / pack["id"] / "manifest.json"
        manifest_data = json.loads(read(manifest))
        if manifest_data.get("schema") != "chaseos.pack.v1":
            fail(f"pack {pack['id']} manifest schema mismatch")
        if sha256_json(manifest_data) != pack["manifest_digest_sha256"]:
            fail(f"pack {pack['id']} manifest digest mismatch")
        paths.append(manifest)
    return paths


def assert_standards() -> list[Path]:
    paths: list[Path] = []
    primary_examples = [
        "chaseos.pack.json",
        "chaseos.forge-index.json",
        "chaseos.approval.json",
        "chaseos.graph.json",
        "chaseos.outcome.json",
    ]

    standards_html = read(ROOT / "standards" / "index.html")
    for filename in primary_examples:
        assert_contains(standards_html, f"examples/{filename}", "standards page")
    assert_contains(standards_html, "preview examples only", "standards preview boundary")
    assert_contains(standards_html, "not stable public APIs", "standards stable-api boundary")
    assert_contains(standards_html, "no live managed entitlements", "standards entitlement boundary")
    assert_contains(standards_html, "managed jobs", "standards managed-job boundary")

    for base in [ROOT / "standards" / "examples", REPO / "docs" / "standards" / "examples"]:
        for filename in STANDARD_FILES:
            path = base / filename
            data = json.loads(read(path))
            if not data.get("schema", "").startswith("chaseos."):
                fail(f"{path} missing chaseos schema")
            if filename in primary_examples:
                if "preview" not in data.get("schema", "") and "preview" not in data.get("status", ""):
                    fail(f"{path} must be clearly labeled as preview")
            if filename == "chaseos.approval.json" and data.get("execution_allowed") is not False:
                fail("approval example must not allow execution")
            if filename == "chaseos.graph.json" and data.get("private_graph_exported") is not False:
                fail("graph example must not export a private graph")
            if filename == "chaseos.outcome.json" and data.get("telemetry_opt_in") is not False:
                fail("outcome example must keep telemetry opt-in disabled")
            if filename == "chaseos.forge-index.json":
                if data.get("licensing_entitlements") != "not_enabled":
                    fail("Forge standards example must keep managed entitlements disabled")
                if data.get("remote_install") != "manual_preview_only_approval_gated_future":
                    fail("Forge standards example must not claim live remote install")
            paths.append(path)
    return paths


def assert_fixture() -> list[Path]:
    fixture_root = REPO / "fixtures" / "demo" / "chaseos_launch"
    paths = [
        fixture_root / "README.md",
        fixture_root / "graph_nodes.json",
        fixture_root / "launch_readiness_mission.json",
        fixture_root / "approval_packets.json",
        fixture_root / "outputs.json",
    ]
    for path in paths:
        read(path)
    for path in paths[1:]:
        data = json.loads(read(path))
        if data.get("fixture_visibility") != "public_safe_demo":
            fail(f"{path} must declare public_safe_demo fixture visibility")
        if data.get("runtime_authority") != "none_granted_fixture_only":
            fail(f"{path} must not grant runtime authority")

    graph = json.loads(read(fixture_root / "graph_nodes.json"))
    expected_node_ids = {
        "project.chaseos-public-launch",
        "source.public-launch-brief",
        "runtime.hermes-demo-lane",
        "approval.publish-launch-copy",
        "mission.launch-readiness-preview",
    }
    node_ids = {node.get("id") for node in graph.get("nodes", []) if isinstance(node, dict)}
    missing_nodes = expected_node_ids - node_ids
    if missing_nodes:
        fail(f"graph fixture missing node ids: {sorted(missing_nodes)}")

    approvals = json.loads(read(fixture_root / "approval_packets.json"))
    if any(packet.get("execution_allowed") is not False for packet in approvals.get("packets", [])):
        fail("approval demo packets must keep execution_allowed false")

    mission = json.loads(read(fixture_root / "launch_readiness_mission.json"))
    if mission.get("status") != "preview_fixture_no_execution":
        fail("mission fixture must stay preview_fixture_no_execution")
    return paths


def assert_no_forbidden_strings(paths: list[Path]) -> None:
    for path in paths:
        text = read(path)
        lowered = text.lower()
        for forbidden in FORBIDDEN_PUBLIC_STRINGS:
            if forbidden.lower() in lowered:
                fail(f"{path} contains forbidden public string: {forbidden}")


def main() -> int:
    paths: list[Path] = []
    paths.extend(assert_public_pages())
    paths.extend(assert_demo_route())
    paths.extend(assert_forge())
    paths.extend(assert_standards())
    paths.extend(assert_fixture())
    paths.extend(ROOT.glob("*.css"))
    paths.extend(ROOT.glob("*.js"))
    paths.extend((ROOT / "assets").glob("*.svg"))
    assert_no_forbidden_strings(paths)
    print(f"OK: ChaseOS static launch smoke passed for {len(paths)} files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
