# Pipeline and Data Analysis Guide

## Repo and Data Zones

This project operates across two data zones:

1. **External source documents (local only, not committed to GitHub):**
   - `.../FCCPS AI Committee/project_files/...`
2. **Published ingest outputs (committed in repo):**
   - `public/project_ingest/...`

Use the published outputs for analysis in GitHub-backed workflows.

---

## Ingest Pipeline: What It Does

Primary script:

- `scripts/pii_scan.py`

The pipeline scans external `project_files`, extracts content, applies PII gating/redaction rules, and writes publishable outputs under `public/project_ingest`.

### Core outputs

- `public/project_ingest/index.json`
  - Master source-to-output map (`source_path` -> artifact/markdown/spreadsheet outputs)
- `public/project_ingest/artifacts/*.json`
  - Canonical structured artifact per ingested source file
- `public/project_ingest/markdown/*.md`
  - DOCX-to-markdown derivatives
- `public/project_ingest/spreadsheets/*.json`
  - XLSX sidecar payloads
- `public/project_ingest/discovery_report.json`
  - Candidate-level include/skip decisions and skip reasons
- `public/project_ingest/pii_report.json`
  - PII findings
- `public/project_ingest/ingest_summary.json`
  - Promotion/conversion counts and summaries
- `public/project_ingest/cognitive_control_report.json`
  - Deterministic cognitive report built from ingest outputs

---

## Standard Local Run Sequence

Set environment variable:

- `PROJECT_FILES_ROOT=<absolute path to project_files>`

Run steps:

1. `python scripts/pii_scan.py`
   - Optional: `python scripts/pii_scan.py --allow-pii`
2. `python scripts/run_cognitive_agent.py`
3. `python scripts/validate_public.py`
4. `python scripts/validate_no_pii.py` (if present)

---

## How to Map Source Files to Outputs

Use `public/project_ingest/index.json`:

- Match by `entries[].source_path`
- `entries[].output_path` -> artifact JSON path
- `entries[].associated_outputs.md_path` -> markdown path (DOCX)
- `entries[].associated_outputs.xlsx_json_path` -> spreadsheet path (XLSX)

For drafting-specific mappings, use:

- `docs/DRAFTING_OUTPUT_MAP.md` (repo paths)
- `docs/DRAFTING_OUTPUT_MAP_GITHUB_LINKS.md` (clickable GitHub links)

---

## Recommended Analysis Workflow

1. **Start from `index.json`**
   - Filter by `source_path` prefix (e.g., `drafting/`, `workstreams/`, `Meetings/`)
   - Filter by `category` (`artifacts`, `markdown`, `spreadsheets`)
2. **Use `artifacts/*.json` for structured analysis**
   - Best for section-level NLP and downstream modeling
3. **Use `markdown/*.md` for human-readable review/diffing**
4. **Use `spreadsheets/*.json` for tabular analysis**
5. **Use discovery/pii reports for data quality context**
   - `discovery_report.json` explains skipped files
   - `pii_report.json` tracks findings/redactions

---

## Caveats

- `project_files` is not stored in GitHub; it is external/local.
- GitHub stores the **ingested outputs**, not raw private source files.
- Unreadable/malformed files are recorded as skipped in discovery report (`skipped_unreadable_or_malformed`) rather than aborting the entire ingest run.
- Using `--allow-pii` changes inclusion behavior and can significantly alter coverage.

---

## GitHub Output Locations

- `public/project_ingest/artifacts/`
- `public/project_ingest/markdown/`
- `public/project_ingest/spreadsheets/`
- `public/project_ingest/index.json`
