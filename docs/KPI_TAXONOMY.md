# KPI Taxonomy

Deterministic health dashboard KPIs produced by `scripts/build_kpis.py`.

## Schedule

- `KPI-SCHED-01` — Next gate readiness
- `KPI-SCHED-02` — Overdue deliverables
- `KPI-SCHED-03` — Blocked dependency rate
- `KPI-SCHED-04` — Pre-read readiness

## Convergence / Traceability

- `KPI-CONV-01` — SoR reference integrity
- `KPI-CONV-02` — Ownership completeness
- `KPI-CONV-03` — Gate mapping completeness
- `KPI-CONV-04` — Definition-of-done completeness
- `KPI-CONV-05` — Principle linkage coverage
- `KPI-CONV-06` — Risk linkage coverage
- `KPI-CONV-07` — Cross-doc principle coverage
- `KPI-CONV-08` — Cross-doc risk coverage
- `KPI-CONV-09` — Risk→principle mapping readiness
- `KPI-CONV-10` — Milestone gating consistency

## Freshness

- `KPI-FRESH-01` — SoR recency
- `KPI-FRESH-02` — Public artifacts recency
- `KPI-FRESH-03` — Foundation docs recency

## Publicability / Hygiene

- `KPI-PUB-01` — Public link hygiene
- `KPI-PUB-02` — PII lint on public outputs

## Status Bands

Default score bands:

- Green: `>= 85`
- Yellow: `>= 60 and < 85`
- Red: `< 60`

Some KPIs use explicit thresholds documented in `kpis.json.rules` (for example doc coverage thresholds).
