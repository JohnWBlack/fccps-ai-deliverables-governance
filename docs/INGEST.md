# Project Ingest Guide

## Local run

Set `PROJECT_FILES_ROOT` to the external source folder, then run ingest and validation.

### PowerShell (Windows)

```powershell
$env:PROJECT_FILES_ROOT = "C:\path\to\project_files"
py scripts/pii_scan.py
py scripts/validate_public.py
```

### Bash

```bash
export PROJECT_FILES_ROOT="/absolute/path/to/project_files"
python scripts/pii_scan.py
python scripts/validate_public.py
```

## What is ignored

The ingest scanner excludes:

- any path segment named `media` (case-insensitive)
- allowlist-only ingest for: `.md`, `.txt`, `.json`, `.docx`, `.xlsx`
- explicit non-ingest (for now): `.pdf`, `.pptx`

## Determinism guarantees

- Output filenames are stable: `<slug>__<hash12>`.
- `write_json_if_changed` and `write_text_if_changed` prevent unnecessary file rewrites.
- `index.json` and discovery output are sorted before write.
- DOCX sidecar markdown and XLSX sidecar JSON include provenance metadata.
