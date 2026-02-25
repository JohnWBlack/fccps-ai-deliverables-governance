#!/usr/bin/env python3
"""
FCCPS AI Committee - Source of Truth Validator

Validates YAML files in the sor/ directory for:
- Required fields
- Valid status enums
- Cross-references
- YAML syntax
"""

import yaml
import sys
import os
import re
from datetime import datetime
from typing import Dict, List, Any

# Valid enum values
VALID_WORKSTREAM_STATUS = ["active", "completed", "paused", "cancelled"]
VALID_DELIVERABLE_STATUS = ["not_started", "in_progress", "completed", "cancelled"]
VALID_TIMELINE_STATUS = ["completed", "upcoming", "cancelled"]
VALID_PRIORITY = ["high", "medium", "low"]
VALID_TIMELINE_TYPE = ["milestone", "deadline", "meeting", "review"]
VALID_DELIVERABLE_TYPE = ["document", "presentation", "software", "other"]
VALID_DELIVERABLE_SCOPE = ["workstream", "committee"]
VALID_OWNER_ROLE = ["Chair", "Workstream Lead", "Co-lead", "Committee"]
LEGACY_WORKSTREAM_ID_PATTERN = re.compile(r"^ws-\d+$", re.IGNORECASE)
LEGACY_DELIVERABLE_ID_PATTERN = re.compile(r"^del-\d+$", re.IGNORECASE)


def extract_id_set(data: Dict[str, Any], list_key: str) -> set:
    """Extract an ID set from either list[dict{id}] or list[str] structures."""
    result = set()
    entries = data.get(list_key, [])
    if not isinstance(entries, list):
        return result

    for entry in entries:
        if isinstance(entry, dict) and entry.get("id"):
            result.add(str(entry["id"]))
        elif isinstance(entry, str):
            result.add(entry)
    return result

def load_yaml_file(filepath: str) -> Dict[str, Any]:
    """Load and parse YAML file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"❌ YAML syntax error in {filepath}: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"❌ File not found: {filepath}")
        sys.exit(1)

def validate_metadata(metadata: Dict[str, Any], filepath: str) -> None:
    """Validate metadata section."""
    required_fields = ["version", "last_updated", "description"]
    
    for field in required_fields:
        if field not in metadata:
            print(f"❌ Missing required metadata field '{field}' in {filepath}")
            sys.exit(1)
    
    # Validate date format
    try:
        datetime.strptime(metadata["last_updated"], "%Y-%m-%d")
    except ValueError:
        print(f"❌ Invalid date format in metadata.last_updated for {filepath}. Expected YYYY-MM-DD")
        sys.exit(1)

def validate_workstreams(data: Dict[str, Any]) -> None:
    """Validate workstreams.yml structure and content."""
    validate_metadata(data["metadata"], "workstreams.yml")
    
    workstreams = data.get("workstreams", [])
    workstream_ids = set()
    
    for i, ws in enumerate(workstreams):
        ws_id = ws.get("id")
        if not ws_id:
            print(f"❌ Workstream {i+1} missing required field 'id'")
            sys.exit(1)
        
        if ws_id in workstream_ids:
            print(f"❌ Duplicate workstream ID: {ws_id}")
            sys.exit(1)
        workstream_ids.add(ws_id)

        if LEGACY_WORKSTREAM_ID_PATTERN.match(str(ws_id)):
            print(
                f"❌ Workstream {ws_id} uses deprecated ID format. "
                "Use canonical WS-* IDs (for example, WS-RSB) or provide an explicit mapping table."
            )
            sys.exit(1)
        
        # Validate required fields
        required_fields = ["name", "description", "status", "lead", "start_date", "target_completion", "priority"]
        for field in required_fields:
            if field not in ws:
                print(f"❌ Workstream {ws_id} missing required field '{field}'")
                sys.exit(1)
        
        # Validate enums
        if ws["status"] not in VALID_WORKSTREAM_STATUS:
            print(f"❌ Workstream {ws_id} has invalid status '{ws['status']}'. Valid: {VALID_WORKSTREAM_STATUS}")
            sys.exit(1)
        
        if ws["priority"] not in VALID_PRIORITY:
            print(f"❌ Workstream {ws_id} has invalid priority '{ws['priority']}'. Valid: {VALID_PRIORITY}")
            sys.exit(1)
        
        # Validate date formats
        for date_field in ["start_date", "target_completion"]:
            try:
                datetime.strptime(ws[date_field], "%Y-%m-%d")
            except ValueError:
                print(f"❌ Workstream {ws_id} has invalid date format for '{date_field}'. Expected YYYY-MM-DD")
                sys.exit(1)

    # Validate workstream dependencies reference known workstreams
    for ws in workstreams:
        ws_id = ws["id"]
        dependencies = ws.get("dependencies", [])
        if dependencies and not isinstance(dependencies, list):
            print(f"❌ Workstream {ws_id} field 'dependencies' must be a list")
            sys.exit(1)
        for dep in dependencies:
            if dep not in workstream_ids:
                print(f"❌ Workstream {ws_id} dependency references non-existent workstream '{dep}'")
                sys.exit(1)

def validate_timeline(data: Dict[str, Any], workstream_ids: set, deliverable_ids: set) -> None:
    """Validate timeline.yml structure and content."""
    validate_metadata(data["metadata"], "timeline.yml")
    
    events = data.get("timeline_events", [])
    event_ids = set()
    
    for i, event in enumerate(events):
        event_id = event.get("id")
        if not event_id:
            print(f"❌ Timeline event {i+1} missing required field 'id'")
            sys.exit(1)
        
        if event_id in event_ids:
            print(f"❌ Duplicate timeline event ID: {event_id}")
            sys.exit(1)
        event_ids.add(event_id)
        
        # Validate required fields
        required_fields = ["title", "description", "date", "type", "status", "importance"]
        for field in required_fields:
            if field not in event:
                print(f"❌ Timeline event {event_id} missing required field '{field}'")
                sys.exit(1)
        
        # Validate enums
        if event["status"] not in VALID_TIMELINE_STATUS:
            print(f"❌ Timeline event {event_id} has invalid status '{event['status']}'. Valid: {VALID_TIMELINE_STATUS}")
            sys.exit(1)
        
        if event["type"] not in VALID_TIMELINE_TYPE:
            print(f"❌ Timeline event {event_id} has invalid type '{event['type']}'. Valid: {VALID_TIMELINE_TYPE}")
            sys.exit(1)
        
        if event["importance"] not in VALID_PRIORITY:
            print(f"❌ Timeline event {event_id} has invalid importance '{event['importance']}'. Valid: {VALID_PRIORITY}")
            sys.exit(1)
        
        # Validate workstream reference
        ws_id = event.get("workstream_id")
        if ws_id and ws_id not in workstream_ids:
            print(f"❌ Timeline event {event_id} references non-existent workstream '{ws_id}'")
            sys.exit(1)

        # Validate optional deliverable references
        del_id = event.get("deliverable_id")
        if del_id and del_id not in deliverable_ids:
            print(f"❌ Timeline event {event_id} references non-existent deliverable '{del_id}'")
            sys.exit(1)

        del_ids = event.get("deliverable_ids")
        if del_ids is not None:
            if not isinstance(del_ids, list):
                print(f"❌ Timeline event {event_id} field 'deliverable_ids' must be a list")
                sys.exit(1)
            for did in del_ids:
                if did not in deliverable_ids:
                    print(f"❌ Timeline event {event_id} references non-existent deliverable '{did}'")
                    sys.exit(1)
        
        # Validate date format
        try:
            datetime.strptime(event["date"], "%Y-%m-%d")
        except ValueError:
            print(f"❌ Timeline event {event_id} has invalid date format. Expected YYYY-MM-DD")
            sys.exit(1)

def validate_deliverables(
    data: Dict[str, Any],
    workstream_ids: set,
    timeline_event_ids: set,
    principle_ids: set,
    risk_ids: set,
) -> None:
    """Validate deliverables.yml structure and content."""
    validate_metadata(data["metadata"], "deliverables.yml")
    
    deliverables = data.get("deliverables", [])
    deliverable_ids = set()
    
    compatibility_warnings: List[str] = []

    for i, deliverable in enumerate(deliverables):
        del_id = deliverable.get("id")
        if not del_id:
            print(f"❌ Deliverable {i+1} missing required field 'id'")
            sys.exit(1)
        
        if del_id in deliverable_ids:
            print(f"❌ Duplicate deliverable ID: {del_id}")
            sys.exit(1)
        deliverable_ids.add(del_id)

        if LEGACY_DELIVERABLE_ID_PATTERN.match(str(del_id)):
            print(
                f"❌ Deliverable {del_id} uses deprecated ID format. "
                "Use canonical D-* or committee artifact IDs consistently, or provide an explicit mapping table."
            )
            sys.exit(1)
        
        # Validate required fields
        required_fields = ["title", "description", "status", "scope", "workstream_id", "owner", "due_date", "priority", "deliverable_type"]
        for field in required_fields:
            if field not in deliverable:
                print(f"❌ Deliverable {del_id} missing required field '{field}'")
                sys.exit(1)

        # Backwards compatibility warnings for legacy fields that may still exist
        for legacy_field in ["workstream", "assigned_to", "owners", "public_facing"]:
            if legacy_field in deliverable:
                compatibility_warnings.append(
                    f"⚠️  Deliverable {del_id} includes legacy field '{legacy_field}' (retained for compatibility)."
                )
        
        # Validate enums
        if deliverable["status"] not in VALID_DELIVERABLE_STATUS:
            print(f"❌ Deliverable {del_id} has invalid status '{deliverable['status']}'. Valid: {VALID_DELIVERABLE_STATUS}")
            sys.exit(1)
        
        if deliverable["priority"] not in VALID_PRIORITY:
            print(f"❌ Deliverable {del_id} has invalid priority '{deliverable['priority']}'. Valid: {VALID_PRIORITY}")
            sys.exit(1)
        
        if deliverable["deliverable_type"] not in VALID_DELIVERABLE_TYPE:
            print(f"❌ Deliverable {del_id} has invalid type '{deliverable['deliverable_type']}'. Valid: {VALID_DELIVERABLE_TYPE}")
            sys.exit(1)

        scope = deliverable.get("scope")
        if scope not in VALID_DELIVERABLE_SCOPE:
            print(f"❌ Deliverable {del_id} has invalid scope '{scope}'. Valid: {VALID_DELIVERABLE_SCOPE}")
            sys.exit(1)

        owner = deliverable.get("owner")
        if not isinstance(owner, dict):
            print(f"❌ Deliverable {del_id} field 'owner' must be an object with name and role")
            sys.exit(1)
        owner_name = owner.get("name")
        owner_role = owner.get("role")
        if not isinstance(owner_name, str) or not owner_name.strip():
            print(f"❌ Deliverable {del_id} owner.name must be a non-empty string")
            sys.exit(1)
        if owner_role not in VALID_OWNER_ROLE:
            print(f"❌ Deliverable {del_id} owner.role must be one of {VALID_OWNER_ROLE}")
            sys.exit(1)

        # Validate workstream reference based on scope rules
        ws_id = deliverable.get("workstream_id")
        if ws_id is not None and not isinstance(ws_id, str):
            print(f"❌ Deliverable {del_id} field 'workstream_id' must be string or null")
            sys.exit(1)

        if scope == "workstream":
            if not ws_id:
                print(f"❌ Deliverable {del_id} with scope=workstream must set workstream_id")
                sys.exit(1)
            if ws_id not in workstream_ids:
                print(f"❌ Deliverable {del_id} references non-existent workstream '{ws_id}'")
                sys.exit(1)
        elif scope == "committee" and ws_id and ws_id not in workstream_ids:
            print(f"❌ Deliverable {del_id} committee scope coordination workstream_id '{ws_id}' does not exist")
            sys.exit(1)
        
        # Validate date format
        try:
            datetime.strptime(deliverable["due_date"], "%Y-%m-%d")
        except ValueError:
            print(f"❌ Deliverable {del_id} has invalid due_date format. Expected YYYY-MM-DD")
            sys.exit(1)

        # Validate optional checkpoint mapping
        checkpoint_id = deliverable.get("checkpoint_id")
        if checkpoint_id and checkpoint_id not in timeline_event_ids:
            print(f"❌ Deliverable {del_id} checkpoint_id references non-existent timeline event '{checkpoint_id}'")
            sys.exit(1)

        # Validate optional linkage fields
        for field in ["principle_refs", "risk_refs", "depends_on"]:
            value = deliverable.get(field)
            if value is not None and not isinstance(value, list):
                print(f"❌ Deliverable {del_id} optional field '{field}' must be a list when present")
                sys.exit(1)

        if principle_ids:
            for pref in deliverable.get("principle_refs", []) or []:
                if pref not in principle_ids:
                    print(f"❌ Deliverable {del_id} principle_refs contains unknown principle '{pref}'")
                    sys.exit(1)

        if risk_ids:
            for rref in deliverable.get("risk_refs", []) or []:
                if rref not in risk_ids:
                    print(f"❌ Deliverable {del_id} risk_refs contains unknown risk '{rref}'")
                    sys.exit(1)

        # Validate visibility/public artifact fields
        public_url = deliverable.get("public_url")
        if public_url is not None and not isinstance(public_url, str):
            print(f"❌ Deliverable {del_id} optional field 'public_url' must be a string or null")
            sys.exit(1)
        if "committee_only" in deliverable and not isinstance(deliverable.get("committee_only"), bool):
            print(f"❌ Deliverable {del_id} optional field 'committee_only' must be a boolean when present")
            sys.exit(1)

        if "depends_on" in deliverable and not isinstance(deliverable.get("depends_on"), list):
            print(f"❌ Deliverable {del_id} optional field 'depends_on' must be a list when present")
            sys.exit(1)

    deliverable_ids = {d["id"] for d in deliverables}

    # Validate deliverable dependency references after IDs are known
    for deliverable in deliverables:
        del_id = deliverable["id"]
        for dep in deliverable.get("depends_on", []) or []:
            if dep not in deliverable_ids:
                print(f"❌ Deliverable {del_id} depends_on references non-existent deliverable '{dep}'")
                sys.exit(1)

    for warning in sorted(set(compatibility_warnings)):
        print(warning)

def main():
    """Main validation function."""
    print("🔍 Validating FCCPS AI Committee Source of Truth...")
    
    sor_dir = "sor"
    if not os.path.exists(sor_dir):
        print(f"❌ Source directory '{sor_dir}' not found")
        sys.exit(1)
    
    # Load all YAML files
    workstreams_file = os.path.join(sor_dir, "workstreams.yml")
    timeline_file = os.path.join(sor_dir, "timeline.yml")
    deliverables_file = os.path.join(sor_dir, "deliverables.yml")
    principles_file = os.path.join(sor_dir, "principles.yml")
    risks_file = os.path.join(sor_dir, "risks.yml")
    
    workstreams_data = load_yaml_file(workstreams_file)
    timeline_data = load_yaml_file(timeline_file)
    deliverables_data = load_yaml_file(deliverables_file)

    principle_ids = set()
    if os.path.exists(principles_file):
        principle_ids = extract_id_set(load_yaml_file(principles_file), "principles")

    risk_ids = set()
    if os.path.exists(risks_file):
        risk_ids = extract_id_set(load_yaml_file(risks_file), "risks")

    # Precompute IDs for cross-reference checks
    deliverable_ids = {d["id"] for d in deliverables_data.get("deliverables", []) if d.get("id")}
    timeline_event_ids = {e["id"] for e in timeline_data.get("timeline_events", []) if e.get("id")}
    
    # Validate workstreams first to get workstream IDs
    validate_workstreams(workstreams_data)
    workstream_ids = {ws["id"] for ws in workstreams_data.get("workstreams", [])}
    
    # Validate timeline and deliverables with workstream references
    validate_timeline(timeline_data, workstream_ids, deliverable_ids)
    validate_deliverables(
        deliverables_data,
        workstream_ids,
        timeline_event_ids,
        principle_ids,
        risk_ids,
    )
    
    print("✅ All validations passed!")
    print(f"📊 Validated {len(workstreams_data.get('workstreams', []))} workstreams")
    print(f"📅 Validated {len(timeline_data.get('timeline_events', []))} timeline events")
    print(f"📦 Validated {len(deliverables_data.get('deliverables', []))} deliverables")

if __name__ == "__main__":
    main()
