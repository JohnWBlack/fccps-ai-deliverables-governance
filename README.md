# FCCPS AI Deliverables Governance

Repository for managing FCCPS AI Committee deliverables with strong governance and traceability.

## Overview

This repository serves as the single source-of-truth (SoR) for FCCPS AI Committee workstreams, timelines, and deliverables. It maintains YAML-based source data and generates public-safe JSON snapshots for external consumption.

## Repository Structure

```
/
├── README.md
├── LICENSE
├── sor/                    # Source of Truth (YAML files)
│   ├── workstreams.yml
│   ├── timeline.yml
│   └── deliverables.yml
├── public/
│   └── public_snapshot.json  # Generated public snapshot
├── scripts/
│   ├── validate_sor.py       # YAML validation
│   └── build_snapshot.py     # JSON generation
├── docs/
│   ├── schema_notes.md       # Schema documentation
│   └── governance_rule.md    # Governance rules
└── CHANGELOG_PUBLIC.md       # Public changelog
```

## Publishing Workflow

To publish updates to the public snapshot:

```bash
# 1. Validate source data
python scripts/validate_sor.py

# 2. Build public snapshot
python scripts/build_snapshot.py

# 3. Commit changes
git add sor/ public/public_snapshot.json CHANGELOG_PUBLIC.md
git commit -m "Update deliverables: [description]"
git push
```

## Governance Rules

1. **Source of Truth First**: All edits must be made to YAML files in `sor/` directory
2. **Derived Content**: Public JSON is generated from source, never edited directly
3. **Chair-Managed Workflow**: Changes are tracked via commits with clear traceability
4. **Public Safety**: Generated snapshots exclude internal-only fields

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
