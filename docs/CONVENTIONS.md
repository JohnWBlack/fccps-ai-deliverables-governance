# Reference Conventions for Alignment + Convergence Dashboard

These conventions enable deterministic extraction in `scripts/extract_refs.py` and improve KPI traceability.

## Recommended Header Blocks in Markdown Docs

Prefer a compact block near the top of each markdown file:

- `Principles: P-01, P-03`
- `Risks: R-02, R-09`
- `Workstreams: WS-POL, WS-AIN`
- `Deliverables: D-POL-1, D-AIN-1`

## Token Patterns (Case-Insensitive)

The extractor recognizes tokens anywhere in markdown content:

- Principle IDs: `P-##` or `P-###`
- Risk IDs: `R-##` or `R-###`
- Workstream IDs: `WS-...`
- Deliverable IDs: `D-...`
- Milestone IDs: `ms_*`

## Placement Guidance

1. Put reference headers near the top of the document.
2. Keep IDs stable once published.
3. Use consistent delimiter style (comma-separated lists recommended).
4. Use SoR identifiers when possible so references map cleanly to `sor/*.yml`.

## Source of Record Rule

- `sor/*.yml` remains authoritative.
- `governance_docs/` and `project_files/` are supporting evidence.
- Public outputs in `/public` are generated artifacts and should not be edited directly.
