# FCCPS AI Deliverables Governance

Repository for managing FCCPS AI Committee deliverables with strong governance and traceability.

## Overview

This repository serves as the single source-of-truth (SoR) for FCCPS AI Committee workstreams, timelines, and deliverables. It maintains YAML-based source data and generates public-safe JSON snapshots for external consumption.

## Repository Structure

```
/
├── README.md
├── LICENSE
├── CHECKLIST.md
├── sor/                    # Source of Truth (YAML files)
│   ├── workstreams.yml
│   ├── timeline.yml
│   └── deliverables.yml
├── governance_docs/         # Foundation docs and committee history (md/docx/pdf)
├── public/
│   ├── public_snapshot.json  # Main public data contract
│   ├── file_catalog.json     # Repository file inventory
│   └── kpis.json             # Deterministic health dashboard KPIs
├── scripts/
│   ├── validate_sor.py       # YAML validation
│   ├── build_snapshot.py     # Snapshot generation
│   ├── build_catalog.py      # File inventory generation
│   └── build_kpis.py         # KPI generation
├── docs/
│   ├── schema_notes.md       # Schema documentation
│   └── governance_rule.md    # Governance rules
├── CHANGELOG_PUBLIC.md       # Public changelog
├── requirements.txt
└── .github/workflows/
    └── validate_build_publish.yml
```

## Publishing Workflow

To publish updates to the public snapshot:

```bash
# 1. Validate source data
python scripts/validate_sor.py

# 2. Build public snapshot
python scripts/build_snapshot.py

# 3. Build additional public artifacts
python scripts/build_catalog.py
python scripts/build_kpis.py

# 4. Commit changes
git add sor/ public/public_snapshot.json public/file_catalog.json public/kpis.json CHANGELOG_PUBLIC.md
git commit -m "Update deliverables: [description]"
git push
```

## Publish-on-Change Automation

GitHub Actions automatically publishes the snapshot when relevant files change.

- Workflow: `.github/workflows/validate_build_publish.yml`
- Triggers:
  - Push to `main` when any of these paths change: `sor/**`, `governance_docs/**`, `scripts/**`, `CHANGELOG_PUBLIC.md`, `requirements.txt`, `.github/workflows/**`
  - Manual run via `workflow_dispatch`
  - Daily safety rebuild at `03:00 UTC`
- Pipeline behavior:
  1. Validate SoR (`python scripts/validate_sor.py`)
  2. Build snapshot (`python scripts/build_snapshot.py`)
  3. Build file catalog (`python scripts/build_catalog.py`)
  4. Build KPIs (`python scripts/build_kpis.py`)
  5. If public artifacts changed, commit and push them back to `main`

## Public Data Products

The repository publishes these derived JSON artifacts:

- `public/public_snapshot.json` (primary public data contract)
- `public/file_catalog.json` (file inventory)
- `public/kpis.json` (deterministic alignment/convergence indicators)

Raw URL format:

- `https://raw.githubusercontent.com/JohnWBlack/fccps-ai-deliverables-governance/main/public/public_snapshot.json`
- `https://raw.githubusercontent.com/JohnWBlack/fccps-ai-deliverables-governance/main/public/file_catalog.json`
- `https://raw.githubusercontent.com/JohnWBlack/fccps-ai-deliverables-governance/main/public/kpis.json`

## PII Safety

Do not commit email addresses, phone numbers, student data, API tokens, or private/internal links into files that feed public artifacts.

## Public Snapshot Access

The public snapshot is available at:
- **Repository path**: `public/public_snapshot.json`
- **Raw URL**: https://raw.githubusercontent.com/JohnWBlack/fccps-ai-deliverables-governance/main/public/public_snapshot.json

## Governance Documents

Current governance documents are stored in `governance_docs/`:

- `governance_docs/FCCPS_AIAC_Decision_Change_Log.md`
- `governance_docs/FCCPS_AIAC_Deliverables_Index.md`
- `governance_docs/FCCPS_AIAC_Master_Timeline_Workstream_Aligned.md`
- `governance_docs/FCCPS_AIAC_Workstreams_Registry.md`
- `governance_docs/FCCPS-AI-Advisory-Committee_Workstream-Development-Summary-and-Assignments.md`
- `governance_docs/Policy_Recommendations_Process_and_Timeline.md`
- `governance_docs/Workstream_Assignments_FCCPS_AI_Advisory_Committee.md`

## Governance Rules

1. **Source of Truth First**: All edits must be made to YAML files in `sor/` directory
2. **Supporting Docs Second**: `governance_docs/` captures background/history, not SoR
3. **Derived Content**: `/public` JSON files are generated from source, never edited directly
4. **Public Contract Priority**: `public/public_snapshot.json` remains the primary contract for public consumers
5. **Chair-Managed Workflow**: Changes are tracked via commits with clear traceability
6. **Public Safety**: Generated snapshots exclude internal-only fields

## Schema Documentation

See `docs/schema_notes.md` for detailed schema information and field descriptions.

## Validation

The repository includes automated validation to ensure data integrity:

- Required fields validation
- Status enum validation
- YAML syntax validation
- Cross-reference validation

Run validation locally:
```bash
python scripts/validate_sor.py
```

## License

MIT License - see LICENSE file for details.
