#!/usr/bin/env python3
"""
FCCPS AI Committee - Public Snapshot Builder

Builds a public-safe JSON snapshot from the Source of Truth YAML files.
Strips internal-only fields and prepares data for public consumption.
"""

import yaml
import json
import os
import hashlib
import subprocess
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SOR_DIR = REPO_ROOT / "sor"
OUTPUT_PATH = REPO_ROOT / "public" / "public_snapshot.json"
DECISION_CHANGE_LOG_PATH = REPO_ROOT / "governance_docs" / "FCCPS_AIAC_Decision_Change_Log.md"


def resolve_version_key() -> str:
    """Resolve stable version key from git HEAD SHA, fallback to SoR content hash."""
    try:
        sha = subprocess.check_output(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        if sha:
            return sha
    except Exception:
        pass

    digest = hashlib.sha256()
    for path in sorted((SOR_DIR / name) for name in ["workstreams.yml", "deliverables.yml", "timeline.yml"]):
        digest.update(path.read_bytes())
    return f"sor-{digest.hexdigest()[:16]}"

def load_yaml_file(filepath: str) -> Dict[str, Any]:
    """Load and parse YAML file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def sanitize_workstream(workstream: Dict[str, Any]) -> Dict[str, Any]:
    """Remove internal-only fields from workstream data."""
    public_fields = [
        "id", "name", "status", "lead", "co_lead"
    ]
    return {k: v for k, v in workstream.items() if k in public_fields}

def sanitize_timeline_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """Remove internal-only fields from timeline event data."""
    public_fields = [
        "id", "title", "description", "date", "type", "status", "importance"
    ]
    return {k: v for k, v in event.items() if k in public_fields}

def sanitize_deliverable(deliverable: Dict[str, Any]) -> Dict[str, Any]:
    """Remove internal-only fields from deliverable data."""
    public_fields = [
        "id",
        "title",
        "status",
        "due_date",
        "checkpoint_id",
        "depends_on",
        "scope",
        "workstream_id",
        "owner",
        "committee_only",
        "public_url",
    ]
    sanitized = {k: v for k, v in deliverable.items() if k in public_fields}

    if "depends_on" not in sanitized or sanitized["depends_on"] is None:
        sanitized["depends_on"] = []
    if "committee_only" not in sanitized or sanitized["committee_only"] is None:
        sanitized["committee_only"] = False
    if "public_url" not in sanitized:
        sanitized["public_url"] = None
    
    # Only include deliverables marked as public-facing
    if not deliverable.get("public_facing", False):
        return None
    
    return sanitized


def parse_markdown_table_row(line: str) -> list[str] | None:
    raw = line.strip()
    if not (raw.startswith("|") and raw.endswith("|")):
        return None
    columns = [col.strip() for col in raw.strip("|").split("|")]
    if not columns:
        return None
    return columns


def parse_decision_change_log() -> list[Dict[str, Any]]:
    if not DECISION_CHANGE_LOG_PATH.exists():
        return []

    text = DECISION_CHANGE_LOG_PATH.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()

    entries: list[Dict[str, Any]] = []
    section: str | None = None

    for line in lines:
        striped = line.strip()
        lower = striped.lower()
        if lower == "## decision log":
            section = "decision"
            continue
        if lower == "## change log":
            section = "change"
            continue
        if not section:
            continue

        row = parse_markdown_table_row(line)
        if not row:
            continue
        if len(row) < 6:
            continue
        if all(re.fullmatch(r"-+", col.replace(":", "").replace(" ", "")) for col in row):
            continue

        if section == "decision":
            if row[0].lower().startswith("decision id"):
                continue
            entry_id, date, decision, status, impacted, notes = row[:6]
            if not entry_id or not date:
                continue
            entries.append(
                {
                    "id": entry_id,
                    "date": date,
                    "type": "decision",
                    "description": decision,
                    "trigger": "Recorded governance decision",
                    "impact": impacted or None,
                    "owner": None,
                    "status": status or None,
                    "impacted_artifacts": impacted or None,
                    "notes": notes or None,
                }
            )
        elif section == "change":
            if row[0].lower().startswith("change id"):
                continue
            entry_id, date, changed, trigger, impact, owner = row[:6]
            if not entry_id or not date:
                continue
            entries.append(
                {
                    "id": entry_id,
                    "date": date,
                    "type": "change",
                    "description": changed,
                    "trigger": trigger or None,
                    "impact": impact or None,
                    "owner": owner or None,
                    "status": "recorded",
                    "impacted_artifacts": impact or None,
                    "notes": None,
                }
            )

    entries.sort(key=lambda item: (str(item.get("date") or ""), str(item.get("id") or "")), reverse=True)
    return entries

def build_snapshot() -> Dict[str, Any]:
    """Build the public snapshot from source YAML files."""
    # Load source data
    workstreams_data = load_yaml_file(str(SOR_DIR / "workstreams.yml"))
    timeline_data = load_yaml_file(str(SOR_DIR / "timeline.yml"))
    deliverables_data = load_yaml_file(str(SOR_DIR / "deliverables.yml"))
    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    version_key = resolve_version_key()
    
    # Build snapshot structure
    snapshot = {
        "meta": {
            "generated_at": generated_at,
            "source_version": workstreams_data["metadata"]["version"],
            "version_key": version_key,
        },
        "metadata": {
            "generated_at": generated_at,
            "source_version": workstreams_data["metadata"]["version"],
            "version_key": version_key,
            "description": "FCCPS AI Committee public snapshot - derived from Source of Truth"
        },
        "workstreams": [],
        "timeline_events": [],
        "deliverables": [],
        "change_log": parse_decision_change_log(),
    }
    
    # Process workstreams
    for ws in workstreams_data.get("workstreams", []):
        snapshot["workstreams"].append(sanitize_workstream(ws))
    
    # Process timeline events
    for event in timeline_data.get("timeline_events", []):
        snapshot["timeline_events"].append(sanitize_timeline_event(event))
    
    # Process deliverables (only public-facing ones)
    for deliverable in deliverables_data.get("deliverables", []):
        sanitized = sanitize_deliverable(deliverable)
        if sanitized:
            snapshot["deliverables"].append(sanitized)
    
    return snapshot

def write_snapshot(snapshot: Dict[str, Any], output_path: Path) -> None:
    """Write snapshot to JSON file."""
    os.makedirs(output_path.parent, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)
    
    print(f"📄 Public snapshot written to: {output_path}")

def main():
    """Main function to build and save the public snapshot."""
    print("🏗️  Building FCCPS AI Committee public snapshot...")
    
    # Build snapshot
    snapshot = build_snapshot()
    
    # Write to public directory
    write_snapshot(snapshot, OUTPUT_PATH)
    
    # Print summary
    print(f"✅ Snapshot built successfully!")
    print(f"📊 {len(snapshot['workstreams'])} workstreams")
    print(f"📅 {len(snapshot['timeline_events'])} timeline events")
    print(f"📦 {len(snapshot['deliverables'])} public deliverables")
    print(f"🔒 Internal data stripped for public consumption")

if __name__ == "__main__":
    main()
