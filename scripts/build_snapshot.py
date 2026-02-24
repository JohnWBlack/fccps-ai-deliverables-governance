#!/usr/bin/env python3
"""
FCCPS AI Committee - Public Snapshot Builder

Builds a public-safe JSON snapshot from the Source of Truth YAML files.
Strips internal-only fields and prepares data for public consumption.
"""

import yaml
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SOR_DIR = REPO_ROOT / "sor"
OUTPUT_PATH = REPO_ROOT / "public" / "public_snapshot.json"

def load_yaml_file(filepath: str) -> Dict[str, Any]:
    """Load and parse YAML file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def sanitize_workstream(workstream: Dict[str, Any]) -> Dict[str, Any]:
    """Remove internal-only fields from workstream data."""
    public_fields = [
        "id", "name", "description", "status", "start_date", 
        "target_completion", "priority", "tags"
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
        "id", "title", "description", "status", "due_date", 
        "priority", "deliverable_type", "public_facing"
    ]
    sanitized = {k: v for k, v in deliverable.items() if k in public_fields}
    
    # Only include deliverables marked as public-facing
    if not deliverable.get("public_facing", False):
        return None
    
    return sanitized

def build_snapshot() -> Dict[str, Any]:
    """Build the public snapshot from source YAML files."""
    # Load source data
    workstreams_data = load_yaml_file(str(SOR_DIR / "workstreams.yml"))
    timeline_data = load_yaml_file(str(SOR_DIR / "timeline.yml"))
    deliverables_data = load_yaml_file(str(SOR_DIR / "deliverables.yml"))
    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    # Build snapshot structure
    snapshot = {
        "meta": {
            "generated_at": generated_at,
            "source_version": workstreams_data["metadata"]["version"]
        },
        "metadata": {
            "generated_at": generated_at,
            "source_version": workstreams_data["metadata"]["version"],
            "description": "FCCPS AI Committee public snapshot - derived from Source of Truth"
        },
        "workstreams": [],
        "timeline_events": [],
        "deliverables": []
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
