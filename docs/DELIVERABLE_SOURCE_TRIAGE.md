# Deliverable Source Triage (Completed Items)

Purpose: identify completed deliverables that currently have no linked source document in published artifacts, so each item can be explicitly marked as either:

- keep_completed_without_source, or
- link_source_and_publish

## Current data signals

- `public/public_snapshot.json` currently shows completed deliverables with `public_url: null` and no direct source path fields.
- `public/project_ingest/cognitive_control_report.json` currently maps only a small subset of deliverables, and not the completed set below.
- `public/project_ingest/index.json` has ingest outputs, but no current mapping to the completed IDs below.

## Triage table

| Deliverable ID | Status | Deliverable Title | Snapshot link present | Ingest mapping present | Candidate source documents (from `project_files`) | Decision | Notes |
|---|---|---|---|---|---|---|---|
| `charter_v0` | completed | Team Charter v0 | no | no | `Meetings/02 - Meeting 06-FEB-26/20260205_One-page-Team-Charter v1.0 (for Feb 6 review + vote).md`; `Meetings/02 - Meeting 06-FEB-26/FCCPS_AI_Team_Charter_v1_0_one_page.pdf` | ☐ keep_completed_without_source ☐ link_source_and_publish | |
| `working_agreements` | completed | Working agreements and collaboration operating rules | no | no | No clearly named standalone artifact found; likely embedded in meeting agenda/minutes/transcript | ☐ keep_completed_without_source ☐ link_source_and_publish | |
| `pre_m3_defs` | completed | Definitions and assumptions pre-read | no | no | No obvious standalone filename match found in `project_files` | ☐ keep_completed_without_source ☐ link_source_and_publish | |
| `pre_m3_risks_ops` | completed | Meeting 3 risks/opportunities synthesis | no | no | `03 - Values & Principles/F1  Inputs- Top Risks + Top Opportunities (Synthesized Themes).csv`; `03 - Values & Principles/derived_json/F1  Inputs- Top Risks + Top Opportunities (Synthesized Themes).json` | ☐ keep_completed_without_source ☐ link_source_and_publish | |
| `D-RSB-1` | completed | Shared Baseline Brief v1 | no | no | `workstreams/rsb/Shared Baseline v01.md`; `workstreams/rsb/Shared Baseline v01.docx`; `Meetings/03 - Meeting 20-FEB-26/Shared_Baseline_OnePager_v0.1a.docx` | ☐ keep_completed_without_source ☐ link_source_and_publish | |

## Recommended next action per row

1. Mark one decision checkbox per deliverable.
2. For each `link_source_and_publish` decision:
   - add canonical source linkage in SoR/pipeline metadata,
   - regenerate public artifacts,
   - verify `/api/deliverables/document?deliverable_id=<ID>` returns preview content.
3. For each `keep_completed_without_source` decision:
   - keep status as completed,
   - optionally add a rationale in Notes (e.g., evidence resides in meeting minutes rather than standalone document).
