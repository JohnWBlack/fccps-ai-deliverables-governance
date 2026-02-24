# FCCPS AI Committee Schema Documentation

## Overview

This document describes the schema structure for all YAML files in the Source of Truth (`sor/`) directory.

## Common Metadata Structure

All YAML files share a common metadata section:

```yaml
metadata:
  version: "1.0.0"           # Schema version
  last_updated: "2026-02-23" # Last modification date (YYYY-MM-DD)
  description: "Description of file contents"
```

## workstreams.yml

Defines committee workstreams and their current status.

### Structure
```yaml
metadata: { ... }
workstreams:
  - id: "unique-id"
    name: "Workstream Name"
    description: "Detailed description"
    status: "active|completed|paused|cancelled"
    lead: "Person or group responsible"
    start_date: "YYYY-MM-DD"
    target_completion: "YYYY-MM-DD"
    priority: "high|medium|low"
    dependencies: ["ws-002", "ws-003"]  # Optional: dependent workstream IDs
    tags: ["tag1", "tag2"]             # Optional: categorization tags
```

### Field Descriptions
- **id**: Unique identifier (format: ws-XXX)
- **name**: Human-readable workstream name
- **description**: Detailed purpose and scope
- **status**: Current workstream status
- **lead**: Responsible party (person or subcommittee)
- **start_date**: Planned start date
- **target_completion**: Expected completion date
- **priority**: Priority level for resource allocation
- **dependencies**: Optional list of dependent workstream IDs
- **tags**: Optional categorization tags

## timeline.yml

Defines key milestones and timeline events.

### Structure
```yaml
metadata: { ... }
timeline_events:
  - id: "unique-id"
    title: "Event Title"
    description: "Event description"
    date: "YYYY-MM-DD"
    type: "milestone|deadline|meeting|review"
    status: "completed|upcoming|cancelled"
    workstream_id: "ws-001"           # Optional: associated workstream
    importance: "high|medium|low"
```

### Field Descriptions
- **id**: Unique identifier (format: te-XXX)
- **title**: Brief event title
- **description**: Detailed event description
- **date**: Event date
- **type**: Event classification
- **status**: Current event status
- **workstream_id**: Optional reference to associated workstream
- **importance**: Event priority/significance

## deliverables.yml

Defines all committee deliverables and their status.

### Structure
```yaml
metadata: { ... }
deliverables:
  - id: "unique-id"
    title: "Deliverable Title"
    description: "Detailed description"
    status: "not_started|in_progress|completed|cancelled"
    workstream_id: "ws-001"
    assigned_to: "Person or group"
    due_date: "YYYY-MM-DD"
    priority: "high|medium|low"
    deliverable_type: "document|presentation|software|other"
    public_facing: true|false
    internal_notes: "Internal notes (not in public snapshot)"
    checkpoint_id: "te-001"              # Optional: maps deliverable to timeline gate/checkpoint
    definition_of_done: ["bullet 1", "bullet 2"]  # Optional: used for KPI quality checks
    depends_on: ["del-002"]              # Optional: deliverable dependencies
    public_url: "https://..."            # Optional: public artifact URL
    committee_only: true|false            # Optional: true when no public URL should exist
    principle_refs: ["P-001", "P-002"] # Optional: linkage to principle IDs
    risk_refs: ["R-001"]                 # Optional: linkage to risk IDs
```

### Field Descriptions
- **id**: Unique identifier (format: del-XXX)
- **title**: Human-readable deliverable name
- **description**: Detailed deliverable description
- **status**: Current deliverable status
- **workstream_id**: Reference to parent workstream (required)
- **assigned_to**: Responsible person or group
- **due_date**: Expected completion date
- **priority**: Priority level
- **deliverable_type**: Type of deliverable
- **public_facing**: Whether this appears in public snapshots
- **internal_notes**: Internal notes (stripped from public snapshots)
- **checkpoint_id**: Optional timeline event ID this deliverable supports
- **definition_of_done**: Optional list of completion criteria for quality KPI checks
- **depends_on**: Optional list of upstream deliverable IDs
- **public_url**: Optional public artifact link
- **committee_only**: Optional visibility marker when no public URL should exist
- **principle_refs**: Optional list of principle IDs (convergence KPI instrumentation)
- **risk_refs**: Optional list of risk IDs (convergence KPI instrumentation)

## Validation Rules

### Required Fields
- All entities must have required fields populated
- Date fields must follow YYYY-MM-DD format
- ID fields must be unique within their file

### Enum Values
- **workstream.status**: active, completed, paused, cancelled
- **deliverable.status**: not_started, in_progress, completed, cancelled
- **timeline.status**: completed, upcoming, cancelled
- **priority**: high, medium, low
- **timeline.type**: milestone, deadline, meeting, review
- **deliverable.type**: document, presentation, software, other

### Cross-References
- `deliverable.workstream_id` must reference valid workstream ID
- `timeline.workstream_id` (if present) must reference valid workstream ID
- `deliverable.checkpoint_id` (if present) must reference valid timeline event ID
- `deliverable.depends_on` (if present) must reference valid deliverable IDs

## Adding `principle_refs` and `risk_refs` Later

To instrument KPI-CONV-05 and KPI-CONV-06 without breaking current schema:

1. Add optional arrays to each applicable deliverable:
   - `principle_refs: ["P-001", "P-002"]`
   - `risk_refs: ["R-001"]`
2. Keep IDs stable and use your committee's canonical principle/risk register IDs.
3. Validate with `python scripts/validate_sor.py`.
4. Regenerate public artifacts:
   - `python scripts/build_snapshot.py`
   - `python scripts/build_catalog.py`
   - `python scripts/build_kpis.py`
5. Commit SoR first, generated public files second.

## Public Snapshot Generation

The public snapshot (`public/public_snapshot.json`) includes:

### Workstreams (Public Fields)
- id, name, description, status, start_date, target_completion, priority, tags

### Timeline Events (Public Fields)
- id, title, description, date, type, status, importance

### Deliverables (Public Fields, Only if public_facing=true)
- id, title, description, status, due_date, priority, deliverable_type, public_facing

### Stripped Fields
- Internal notes
- Assigned person details
- Workstream leads
- Dependencies
- Any field not explicitly listed as public

## Schema Evolution

When updating schemas:
1. Update version number in metadata
2. Maintain backward compatibility when possible
3. Update validation scripts
4. Update this documentation
5. Update CHANGELOG_PUBLIC.md
