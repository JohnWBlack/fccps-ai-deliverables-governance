# Public Changelog

This changelog tracks changes visible in the public snapshot. Internal changes to source YAML files are not listed here unless they affect the public data.

## [Unreleased]

### Added
- Canonical principle register (`sor/principles.yml`) for convergence linkage IDs (`P-###`)
- Canonical risk register (`sor/risks.yml`) for convergence linkage IDs (`R-###`)
- Meeting 4 convergence instrumentation on key deliverables via `principle_refs` and `risk_refs`
- Decision ID extraction support (`DEC-YYYY-MM-DD-##`) in `public/ref_index.json`
- Health dashboard pipeline with deterministic KPI generation (`public/kpis.json`)
- Public file inventory generation (`public/file_catalog.json`)
- Expanded governance document corpus in `governance_docs/`
- Initial repository setup with governance structure
- Source of Truth YAML schema for workstreams, timeline, and deliverables
- Public snapshot generation system
- Validation scripts for data integrity

### Changed
- `final_talk_track` now references canonical workstream `WS-CCI` to remove dangling workstream linkage.
- Reference extraction now normalizes legacy workstream aliases (`WS-001..WS-008`) to canonical SoR IDs.
- Quality checks now validate `principle_refs` and `risk_refs` IDs against canonical SoR registers.

### Fixed
- Meeting 4 convergence instrumentation now supports non-zero KPI linkage coverage metrics.
- Workstream drift reporting now treats explicit allowlisted aliases as non-blocking.

## [2026-02-23] - Initial Release

### Features
- Workstream management system
- Timeline and milestone tracking
- Deliverable status tracking
- Public-safe JSON snapshot generation
- Automated validation system

### Documentation
- Governance rules and procedures
- Schema documentation
- Publishing workflow instructions

---

## Changelog Format

This changelog follows [Keep a Changelog](https://keepachangelog.com/) format and only includes changes that affect the public snapshot data.

### Categories
- **Added** - New public-facing features or data
- **Changed** - Modifications to existing public data
- **Deprecated** - Public features marked for future removal
- **Removed** - Public features or data removed
- **Fixed** - Corrections to public data
- **Security** - Security-related changes affecting public data

### Version Numbers
Versions follow semantic versioning (MAJOR.MINOR.PATCH):
- **MAJOR** - Breaking changes to public schema
- **MINOR** - New features or backward-compatible changes
- **PATCH** - Bug fixes or minor updates
