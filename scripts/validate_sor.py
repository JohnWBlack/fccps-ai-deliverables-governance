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
from datetime import datetime
from typing import Dict, List, Any

# Valid enum values
VALID_WORKSTREAM_STATUS = ["active", "completed", "paused", "cancelled"]
VALID_DELIVERABLE_STATUS = ["not_started", "in_progress", "completed", "cancelled"]
VALID_TIMELINE_STATUS = ["completed", "upcoming", "cancelled"]
VALID_PRIORITY = ["high", "medium", "low"]
VALID_TIMELINE_TYPE = ["milestone", "deadline", "meeting", "review"]
VALID_DELIVERABLE_TYPE = ["document", "presentation", "software", "other"]

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

def validate_deliverables(data: Dict[str, Any], workstream_ids: set, timeline_event_ids: set) -> None:
    """Validate deliverables.yml structure and content."""
    validate_metadata(data["metadata"], "deliverables.yml")
    
    deliverables = data.get("deliverables", [])
    deliverable_ids = set()
    
    for i, deliverable in enumerate(deliverables):
        del_id = deliverable.get("id")
        if not del_id:
            print(f"❌ Deliverable {i+1} missing required field 'id'")
            sys.exit(1)
        
        if del_id in deliverable_ids:
            print(f"❌ Duplicate deliverable ID: {del_id}")
            sys.exit(1)
        deliverable_ids.add(del_id)
        
        # Validate required fields
        required_fields = ["title", "description", "status", "workstream_id", "assigned_to", "due_date", "priority", "deliverable_type", "public_facing"]
        for field in required_fields:
            if field not in deliverable:
                print(f"❌ Deliverable {del_id} missing required field '{field}'")
                sys.exit(1)
        
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
        
        # Validate workstream reference
        ws_id = deliverable["workstream_id"]
        if ws_id not in workstream_ids:
            print(f"❌ Deliverable {del_id} references non-existent workstream '{ws_id}'")
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

        # Validate visibility/public artifact fields
        if "public_url" in deliverable and not isinstance(deliverable.get("public_url"), str):
            print(f"❌ Deliverable {del_id} optional field 'public_url' must be a string when present")
            sys.exit(1)
        if "committee_only" in deliverable and not isinstance(deliverable.get("committee_only"), bool):
            print(f"❌ Deliverable {del_id} optional field 'committee_only' must be a boolean when present")
            sys.exit(1)

    deliverable_ids = {d["id"] for d in deliverables}

    # Validate deliverable dependency references after IDs are known
    for deliverable in deliverables:
        del_id = deliverable["id"]
        for dep in deliverable.get("depends_on", []) or []:
            if dep not in deliverable_ids:
                print(f"❌ Deliverable {del_id} depends_on references non-existent deliverable '{dep}'")
                sys.exit(1)

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
    
    workstreams_data = load_yaml_file(workstreams_file)
    timeline_data = load_yaml_file(timeline_file)
    deliverables_data = load_yaml_file(deliverables_file)

    # Precompute IDs for cross-reference checks
    deliverable_ids = {d["id"] for d in deliverables_data.get("deliverables", []) if d.get("id")}
    timeline_event_ids = {e["id"] for e in timeline_data.get("timeline_events", []) if e.get("id")}
    
    # Validate workstreams first to get workstream IDs
    validate_workstreams(workstreams_data)
    workstream_ids = {ws["id"] for ws in workstreams_data.get("workstreams", [])}
    
    # Validate timeline and deliverables with workstream references
    validate_timeline(timeline_data, workstream_ids, deliverable_ids)
    validate_deliverables(deliverables_data, workstream_ids, timeline_event_ids)
    
    print("✅ All validations passed!")
    print(f"📊 Validated {len(workstreams_data.get('workstreams', []))} workstreams")
    print(f"📅 Validated {len(timeline_data.get('timeline_events', []))} timeline events")
    print(f"📦 Validated {len(deliverables_data.get('deliverables', []))} deliverables")

if __name__ == "__main__":
    main()
