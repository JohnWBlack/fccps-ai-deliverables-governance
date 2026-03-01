#!/usr/bin/env python3
"""Write a deterministic autopilot summary report for ingest + derived artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DIR = REPO_ROOT / "public"
INGEST_DIR = PUBLIC_DIR / "project_ingest"
DISCOVERY_REPORT_PATH = INGEST_DIR / "discovery_report.json"
PII_REPORT_PATH = INGEST_DIR / "pii_report.json"
INDEX_PATH = INGEST_DIR / "index.json"
OUTPUT_PATH = PUBLIC_DIR / "autopilot_report.json"
TRANSFORM_VERSION = "2.0.0"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json_if_changed(path: Path, payload: Any) -> bool:
    serialized = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == serialized:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialized, encoding="utf-8")
    return True


def main() -> None:
    if not DISCOVERY_REPORT_PATH.exists():
        raise SystemExit(f"Missing required ingest discovery report: {DISCOVERY_REPORT_PATH}")
    if not PII_REPORT_PATH.exists():
        raise SystemExit(f"Missing required ingest PII report: {PII_REPORT_PATH}")
    if not INDEX_PATH.exists():
        raise SystemExit(f"Missing required ingest index: {INDEX_PATH}")

    discovery = load_json(DISCOVERY_REPORT_PATH)
    pii_report = load_json(PII_REPORT_PATH)
    index = load_json(INDEX_PATH)

    entries = discovery.get("entries", []) if isinstance(discovery, dict) else []
    if not isinstance(entries, list):
        entries = []

    index_entries = index.get("entries", []) if isinstance(index, dict) else []
    if not isinstance(index_entries, list):
        index_entries = []

    ingested_entries = [
        item
        for item in entries
        if isinstance(item, dict) and str(item.get("decision") or "") == "ingested"
    ]

    ingested_by_type = {"md": 0, "txt": 0, "json": 0, "docx": 0}
    for item in ingested_entries:
        ext = str(item.get("ext") or "").lower().lstrip(".")
        if ext in ingested_by_type:
            ingested_by_type[ext] += 1

    skipped_due_to_pii = sum(
        1
        for item in entries
        if isinstance(item, dict) and str(item.get("reason_if_skipped") or "") == "skipped_pii_findings"
    )

    total_sections = sum(
        int(item.get("records_count") or 0)
        for item in index_entries
        if isinstance(item, dict)
    )

    pii_findings_total = 0
    if isinstance(pii_report, dict):
        pii_findings_total = int(pii_report.get("total_findings") or 0)

    timestamp = ""
    if isinstance(index, dict):
        timestamp = str(index.get("generated_at") or "")
    if not timestamp and isinstance(discovery, dict):
        timestamp = str(discovery.get("generated_at") or "")
    if not timestamp and isinstance(pii_report, dict):
        timestamp = str(pii_report.get("generated_at") or "")

    version_material = {
        "ingested_by_type": ingested_by_type,
        "pii_findings_total": pii_findings_total,
        "skipped_due_to_pii": skipped_due_to_pii,
        "timestamp": timestamp,
        "total_candidates_scanned": len(entries),
        "total_ingested_artifacts": len(ingested_entries),
        "total_sections": total_sections,
        "transform_version": TRANSFORM_VERSION,
    }
    version_key = hashlib.sha256(
        json.dumps(version_material, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    payload = {
        "generated_at": timestamp,
        "ingested_by_type": ingested_by_type,
        "pii_findings_total": pii_findings_total,
        "skipped_due_to_pii": skipped_due_to_pii,
        "total_candidates_scanned": len(entries),
        "total_ingested_artifacts": len(ingested_entries),
        "total_sections": total_sections,
        "transform_version": TRANSFORM_VERSION,
        "version_key": version_key,
    }

    changed = write_json_if_changed(OUTPUT_PATH, payload)
    action = "updated" if changed else "unchanged"
    print(f"✅ Autopilot report {action}: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
