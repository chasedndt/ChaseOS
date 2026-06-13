import os
import re
from pathlib import Path

def backfill_build_logs(vault_root: Path):
    build_logs_dir = vault_root / "07_LOGS" / "Build-Logs"
    if not build_logs_dir.exists():
        return

    count = 0
    for file in build_logs_dir.glob("*.md"):
        if file.name == "Build-Logs-Index.md":
            continue

        content = file.read_text(encoding="utf-8")

        # Check if we have a Runtime header
        runtime_match = re.search(r"^Runtime:\s*([a-zA-Z]+)", content, re.MULTILINE)
        if not runtime_match:
            continue

        runtime_name = runtime_match.group(1).capitalize()
        profile_link = f"[[{runtime_name}-Runtime-Profile]]"

        # If it's already linked, skip
        if profile_link in content:
            continue

        # Add the link to the Links section if it exists
        if "## Links" in content:
            content = content.replace("## Links\n", f"## Links\n\n- Runtime Profile: {profile_link}\n")
            file.write_text(content, encoding="utf-8")
            count += 1
            print(f"Backfilled {file.name} with {profile_link}")

    print(f"Total build logs backfilled: {count}")

def backfill_daily_notes(vault_root: Path):
    daily_dir = vault_root / "07_LOGS" / "Daily"
    if not daily_dir.exists():
        return

    count = 0
    for file in daily_dir.glob("*.md"):
        if file.name == "Daily-Index.md":
            continue

        content = file.read_text(encoding="utf-8")

        # Check if already connected to Daily-Index
        if "[[Daily-Index]]" in content:
            continue

        # Append to the bottom
        if not content.endswith("\n"):
            content += "\n"
        content += "\n## Graph Anchors\n\n- [[Daily-Index]]\n"

        file.write_text(content, encoding="utf-8")
        count += 1
        print(f"Backfilled {file.name} with [[Daily-Index]]")

    print(f"Total daily notes backfilled: {count}")

if __name__ == "__main__":
    vault_root = Path(".").resolve()
    print("Running Structural Link Backfill...")
    backfill_build_logs(vault_root)
    backfill_daily_notes(vault_root)
    print("Done.")
