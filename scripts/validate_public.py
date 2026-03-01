#!/usr/bin/env python3
"""Validate derived public artifacts with lightweight structural checks."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DIR = REPO_ROOT / "public"
SCHEMA_PATH = REPO_ROOT / "governance_docs" / "schema" / "glidepath_history.schema.json"
GLIDEPATH_PATH = PUBLIC_DIR / "glidepath_history.json"
PROJECT_INGEST_DIR = PUBLIC_DIR / "project_ingest"
PROJECT_INGEST_ARTIFACTS_DIR = PROJECT_INGEST_DIR / "artifacts"
PROJECT_INGEST_INDEX_PATH = PROJECT_INGEST_DIR / "index.json"
PROJECT_INGEST_DISCOVERY_REPORT_PATH = PROJECT_INGEST_DIR / "discovery_report.json"
PROJECT_INGEST_PII_REPORT_PATH = PROJECT_INGEST_DIR / "pii_report.json"

REQUIRED_TOP_LEVEL = {"meta", "corridor", "weights", "points"}
REQUIRED_POINT_FIELDS = {
    "generated_at",
    "version_key",
    "what_score",
    "how_score",
    "coverage_what",
    "coverage_how",
    "included_kpis",
}
REQUIRED_GATE_IDS = {f"m{i}" for i in range(1, 9)}
REQUIRED_INDEX_ENTRY_FIELDS = {
    "category",
    "source_path",
    "source_hash",
    "generated_at",
    "version_key",
    "records_count",
    "pii_findings_count",
    "output_path",
}
REQUIRED_PII_REPORT_FIELDS = {"generated_at", "total_findings", "findings"}
REQUIRED_DISCOVERY_REPORT_FIELDS = {"generated_at", "entries"}
REQUIRED_DISCOVERY_ENTRY_FIELDS = {
    "source_rel_path",
    "ext",
    "size_bytes",
    "mtime_utc",
    "category_guess",
    "decision",
    "reason_if_skipped",
}
REQUIRED_ARTIFACT_FIELDS = {
    "artifact_id",
    "source_rel_path",
    "source_hash_sha256",
    "file_mtime_utc",
    "extracted_at_utc",
    "doc_type",
    "title",
    "sections",
    "provenance",
}
REQUIRED_SECTION_FIELDS = {"section_id", "heading_path", "text"}
REQUIRED_PROVENANCE_FIELDS = {"project", "pipeline_version", "extractor_version"}
REQUIRED_PII_FINDING_FIELDS = {
    "artifact_id",
    "source_rel_path",
    "section_id",
    "field_path",
    "match_type",
    "redacted_snippet",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def fail(message: str) -> None:
    print(f"❌ {message}")
    sys.exit(1)


def parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    candidate = str(value).strip()
    if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def signed_delta(value: float, min_val: float, max_val: float) -> tuple[bool, float]:
    if value < min_val:
        return False, round(value - min_val, 2)
    if value > max_val:
        return False, round(value - max_val, 2)
    return True, 0.0


def validate_glidepath_history(payload: dict[str, Any]) -> None:
    if not REQUIRED_TOP_LEVEL.issubset(set(payload.keys())):
        missing = sorted(REQUIRED_TOP_LEVEL - set(payload.keys()))
        fail(f"glidepath_history.json missing top-level keys: {missing}")

    corridor = payload.get("corridor")
    if not isinstance(corridor, dict):
        fail("glidepath_history.json corridor must be an object")

    gates = corridor.get("gates")
    if not isinstance(gates, list):
        fail("glidepath_history.json corridor.gates must be a list")

    gate_ids = {str(g.get("gate_id")) for g in gates if isinstance(g, dict) and g.get("gate_id")}
    if not REQUIRED_GATE_IDS.issubset(gate_ids):
        missing = sorted(REQUIRED_GATE_IDS - gate_ids)
        fail(f"glidepath_history.json corridor missing gate(s): {missing}")

    m7 = next((g for g in gates if isinstance(g, dict) and g.get("gate_id") == "m7"), None)
    if not isinstance(m7, dict):
        fail("glidepath_history.json corridor missing m7 gate")
    if str(m7.get("date")) != "2026-04-24":
        fail("glidepath_history.json m7 date must be 2026-04-24")
    if m7.get("board_ready_deadline") is not True:
        fail("glidepath_history.json m7 must set board_ready_deadline=true")

    for gate in gates:
        if not isinstance(gate, dict):
            fail("glidepath_history.json corridor gate entries must be objects")
        if not isinstance(gate.get("label"), str):
            fail(f"glidepath_history.json gate {gate.get('gate_id')} label must be a string")
        if not isinstance(gate.get("description"), str):
            fail(f"glidepath_history.json gate {gate.get('gate_id')} description must be a string")
        if gate.get("hard_stop") is not gate.get("board_ready_deadline"):
            fail(f"glidepath_history.json gate {gate.get('gate_id')} hard_stop must equal board_ready_deadline")
        for field in ("what_min", "what_max", "how_min", "how_max"):
            value = gate.get(field)
            if not isinstance(value, (int, float)):
                fail(f"glidepath_history.json gate {gate.get('gate_id')} field {field} must be numeric")
            if value < 0 or value > 10:
                fail(f"glidepath_history.json gate {gate.get('gate_id')} field {field} must be in [0,10]")

    points = payload.get("points")
    if not isinstance(points, list):
        fail("glidepath_history.json points must be a list")

    seen_version_keys: set[str] = set()
    previous_generated_at: datetime | None = None
    for idx, point in enumerate(points):
        if not isinstance(point, dict):
            fail(f"glidepath_history.json points[{idx}] must be an object")
        if not REQUIRED_POINT_FIELDS.issubset(set(point.keys())):
            missing = sorted(REQUIRED_POINT_FIELDS - set(point.keys()))
            fail(f"glidepath_history.json points[{idx}] missing fields: {missing}")

        version_key = str(point.get("version_key", ""))
        if not version_key:
            fail(f"glidepath_history.json points[{idx}] version_key must be non-empty")
        version_key_short = point.get("version_key_short")
        if version_key_short is not None:
            expected_short = version_key[:12]
            if not isinstance(version_key_short, str) or version_key_short != expected_short:
                fail(f"glidepath_history.json points[{idx}] version_key_short must equal first 12 chars of version_key")
        point_id = point.get("point_id")
        if point_id is not None:
            expected_id = f"{point.get('generated_at')}::{version_key[:12]}"
            if not isinstance(point_id, str) or point_id != expected_id:
                fail(f"glidepath_history.json points[{idx}] point_id must match generated_at::version_key_short")
        if version_key in seen_version_keys:
            fail(f"glidepath_history.json duplicate version_key in points: {version_key}")
        seen_version_keys.add(version_key)

        parsed_generated_at = parse_iso_datetime(point.get("generated_at"))
        if parsed_generated_at is None:
            fail(f"glidepath_history.json points[{idx}] generated_at must be an ISO datetime")
        if previous_generated_at and parsed_generated_at < previous_generated_at:
            fail("glidepath_history.json points must be sorted by generated_at ascending")
        previous_generated_at = parsed_generated_at

        for field in ("what_score", "how_score"):
            value = point.get(field)
            if not isinstance(value, (int, float)) or value < 0 or value > 10:
                fail(f"glidepath_history.json points[{idx}] {field} must be numeric in [0,10]")

        for field in ("coverage_what", "coverage_how"):
            value = point.get(field)
            if not isinstance(value, (int, float)) or value < 0 or value > 1:
                fail(f"glidepath_history.json points[{idx}] {field} must be numeric in [0,1]")

        included = point.get("included_kpis")
        if not isinstance(included, dict):
            fail(f"glidepath_history.json points[{idx}] included_kpis must be an object")
        for axis in ("what", "how"):
            axis_items = included.get(axis)
            if not isinstance(axis_items, list):
                fail(f"glidepath_history.json points[{idx}] included_kpis.{axis} must be a list")

    current_eval = payload.get("current_eval")
    if not isinstance(current_eval, dict):
        fail("glidepath_history.json current_eval must be an object")

    if points:
        latest_point = points[-1]
        latest_gate = next((g for g in gates if g.get("gate_id") == latest_point.get("next_gate_id")), None)
        if not isinstance(latest_gate, dict):
            fail("glidepath_history.json current_eval requires latest point next_gate_id to exist in corridor.gates")

        what_in_range, what_delta = signed_delta(
            float(latest_point.get("what_score", 0.0)),
            float(latest_gate.get("what_min", 0.0)),
            float(latest_gate.get("what_max", 10.0)),
        )
        how_in_range, how_delta = signed_delta(
            float(latest_point.get("how_score", 0.0)),
            float(latest_gate.get("how_min", 0.0)),
            float(latest_gate.get("how_max", 10.0)),
        )
        if what_in_range and how_in_range:
            expected_status = "in_range"
        elif what_in_range or how_in_range:
            expected_status = "one_axis_out"
        else:
            expected_status = "out_of_range"

        expected_current_point_id = latest_point.get("point_id")
        expected_current_gate_id = latest_point.get("next_gate_id")

        if current_eval.get("current_point_id") != expected_current_point_id:
            fail("glidepath_history.json current_eval.current_point_id does not match latest point point_id")
        if current_eval.get("current_gate_id") != expected_current_gate_id:
            fail("glidepath_history.json current_eval.current_gate_id does not match latest point next_gate_id")
        if current_eval.get("what_in_range") is not what_in_range:
            fail("glidepath_history.json current_eval.what_in_range mismatch")
        if current_eval.get("how_in_range") is not how_in_range:
            fail("glidepath_history.json current_eval.how_in_range mismatch")
        if current_eval.get("what_delta") != what_delta:
            fail("glidepath_history.json current_eval.what_delta mismatch")
        if current_eval.get("how_delta") != how_delta:
            fail("glidepath_history.json current_eval.how_delta mismatch")
        if current_eval.get("status") != expected_status:
            fail("glidepath_history.json current_eval.status mismatch")


def validate_project_ingest_index(payload: dict[str, Any]) -> None:
    if not isinstance(payload, dict):
        fail("public/project_ingest/index.json must be an object")

    entries = payload.get("entries")
    if not isinstance(entries, list):
        fail("public/project_ingest/index.json entries must be a list")

    for idx, entry in enumerate(entries):
        if not isinstance(entry, dict):
            fail(f"public/project_ingest/index.json entries[{idx}] must be an object")
        if not REQUIRED_INDEX_ENTRY_FIELDS.issubset(set(entry.keys())):
            missing = sorted(REQUIRED_INDEX_ENTRY_FIELDS - set(entry.keys()))
            fail(f"public/project_ingest/index.json entries[{idx}] missing fields: {missing}")
        if entry.get("category") != "artifacts":
            fail(f"public/project_ingest/index.json entries[{idx}] category must be 'artifacts'")
        if not isinstance(entry.get("source_path"), str) or not str(entry.get("source_path")).strip():
            fail(f"public/project_ingest/index.json entries[{idx}] source_path must be a non-empty string")
        if not isinstance(entry.get("source_hash"), str) or len(str(entry.get("source_hash"))) < 32:
            fail(f"public/project_ingest/index.json entries[{idx}] source_hash must be a hash-like string")
        if parse_iso_datetime(entry.get("generated_at")) is None:
            fail(f"public/project_ingest/index.json entries[{idx}] generated_at must be an ISO datetime")
        if not isinstance(entry.get("version_key"), str) or not str(entry.get("version_key")).strip():
            fail(f"public/project_ingest/index.json entries[{idx}] version_key must be a non-empty string")
        if not isinstance(entry.get("records_count"), int) or int(entry.get("records_count")) < 0:
            fail(f"public/project_ingest/index.json entries[{idx}] records_count must be >= 0")
        if not isinstance(entry.get("pii_findings_count"), int) or int(entry.get("pii_findings_count")) < 0:
            fail(f"public/project_ingest/index.json entries[{idx}] pii_findings_count must be >= 0")
        output_path = entry.get("output_path")
        if not isinstance(output_path, str) or not output_path.strip():
            fail(f"public/project_ingest/index.json entries[{idx}] output_path must be a non-empty string")
        if not output_path.startswith("public/project_ingest/artifacts/"):
            fail(f"public/project_ingest/index.json entries[{idx}] output_path must point to artifacts/")


def validate_project_ingest_discovery_report(payload: dict[str, Any]) -> None:
    if not isinstance(payload, dict):
        fail("public/project_ingest/discovery_report.json must be an object")
    if not REQUIRED_DISCOVERY_REPORT_FIELDS.issubset(set(payload.keys())):
        missing = sorted(REQUIRED_DISCOVERY_REPORT_FIELDS - set(payload.keys()))
        fail(f"public/project_ingest/discovery_report.json missing fields: {missing}")
    if parse_iso_datetime(payload.get("generated_at")) is None:
        fail("public/project_ingest/discovery_report.json generated_at must be an ISO datetime")

    entries = payload.get("entries")
    if not isinstance(entries, list):
        fail("public/project_ingest/discovery_report.json entries must be a list")

    prev_rel = ""
    for idx, entry in enumerate(entries):
        if not isinstance(entry, dict):
            fail(f"public/project_ingest/discovery_report.json entries[{idx}] must be an object")
        if not REQUIRED_DISCOVERY_ENTRY_FIELDS.issubset(set(entry.keys())):
            missing = sorted(REQUIRED_DISCOVERY_ENTRY_FIELDS - set(entry.keys()))
            fail(f"public/project_ingest/discovery_report.json entries[{idx}] missing fields: {missing}")

        rel = entry.get("source_rel_path")
        if not isinstance(rel, str) or not rel.strip():
            fail(f"public/project_ingest/discovery_report.json entries[{idx}] source_rel_path must be non-empty")
        if prev_rel and rel.lower() < prev_rel.lower():
            fail("public/project_ingest/discovery_report.json entries must be sorted by source_rel_path")
        prev_rel = rel

        if not isinstance(entry.get("ext"), str):
            fail(f"public/project_ingest/discovery_report.json entries[{idx}] ext must be a string")
        if not isinstance(entry.get("size_bytes"), int) or int(entry.get("size_bytes")) < 0:
            fail(f"public/project_ingest/discovery_report.json entries[{idx}] size_bytes must be >= 0")
        if parse_iso_datetime(entry.get("mtime_utc")) is None:
            fail(f"public/project_ingest/discovery_report.json entries[{idx}] mtime_utc must be an ISO datetime")
        if not isinstance(entry.get("category_guess"), str):
            fail(f"public/project_ingest/discovery_report.json entries[{idx}] category_guess must be a string")

        decision = entry.get("decision")
        if decision not in {"ingested", "skipped"}:
            fail(f"public/project_ingest/discovery_report.json entries[{idx}] decision must be ingested|skipped")
        reason = entry.get("reason_if_skipped")
        if not isinstance(reason, str):
            fail(f"public/project_ingest/discovery_report.json entries[{idx}] reason_if_skipped must be a string")
        if decision == "ingested" and reason:
            fail(f"public/project_ingest/discovery_report.json entries[{idx}] reason_if_skipped must be empty for ingested")
        if decision == "skipped" and not reason:
            fail(f"public/project_ingest/discovery_report.json entries[{idx}] reason_if_skipped must be populated for skipped")


def validate_project_ingest_pii_report(payload: dict[str, Any]) -> None:
    if not isinstance(payload, dict):
        fail("public/project_ingest/pii_report.json must be an object")
    if not REQUIRED_PII_REPORT_FIELDS.issubset(set(payload.keys())):
        missing = sorted(REQUIRED_PII_REPORT_FIELDS - set(payload.keys()))
        fail(f"public/project_ingest/pii_report.json missing fields: {missing}")
    if parse_iso_datetime(payload.get("generated_at")) is None:
        fail("public/project_ingest/pii_report.json generated_at must be an ISO datetime")
    if not isinstance(payload.get("total_findings"), int) or int(payload.get("total_findings")) < 0:
        fail("public/project_ingest/pii_report.json total_findings must be >= 0")
    findings = payload.get("findings")
    if not isinstance(findings, list):
        fail("public/project_ingest/pii_report.json findings must be a list")
    for idx, finding in enumerate(findings):
        if not isinstance(finding, dict):
            fail(f"public/project_ingest/pii_report.json findings[{idx}] must be an object")
        if not REQUIRED_PII_FINDING_FIELDS.issubset(set(finding.keys())):
            missing = sorted(REQUIRED_PII_FINDING_FIELDS - set(finding.keys()))
            fail(f"public/project_ingest/pii_report.json findings[{idx}] missing fields: {missing}")


def validate_project_ingest_artifact(path: Path, payload: Any) -> None:
    rel = path.relative_to(REPO_ROOT).as_posix()
    if not isinstance(payload, dict):
        fail(f"{rel} must be a JSON object")
    if not REQUIRED_ARTIFACT_FIELDS.issubset(set(payload.keys())):
        missing = sorted(REQUIRED_ARTIFACT_FIELDS - set(payload.keys()))
        fail(f"{rel} missing fields: {missing}")

    if not isinstance(payload.get("artifact_id"), str) or not str(payload.get("artifact_id")).strip():
        fail(f"{rel} artifact_id must be a non-empty string")
    if not isinstance(payload.get("source_rel_path"), str) or not str(payload.get("source_rel_path")).strip():
        fail(f"{rel} source_rel_path must be a non-empty string")
    if not isinstance(payload.get("source_hash_sha256"), str) or len(str(payload.get("source_hash_sha256"))) < 32:
        fail(f"{rel} source_hash_sha256 must be a hash-like string")
    if parse_iso_datetime(payload.get("file_mtime_utc")) is None:
        fail(f"{rel} file_mtime_utc must be an ISO datetime")
    if parse_iso_datetime(payload.get("extracted_at_utc")) is None:
        fail(f"{rel} extracted_at_utc must be an ISO datetime")

    if payload.get("doc_type") not in {"md", "txt", "json", "docx"}:
        fail(f"{rel} doc_type must be md|txt|json|docx")
    if not isinstance(payload.get("title"), str):
        fail(f"{rel} title must be a string")

    sections = payload.get("sections")
    if not isinstance(sections, list):
        fail(f"{rel} sections must be a list")
    for idx, section in enumerate(sections):
        if not isinstance(section, dict):
            fail(f"{rel} sections[{idx}] must be an object")
        if not REQUIRED_SECTION_FIELDS.issubset(set(section.keys())):
            missing = sorted(REQUIRED_SECTION_FIELDS - set(section.keys()))
            fail(f"{rel} sections[{idx}] missing fields: {missing}")
        if not isinstance(section.get("section_id"), str):
            fail(f"{rel} sections[{idx}] section_id must be a string")
        heading_path = section.get("heading_path")
        if not isinstance(heading_path, list) or any(not isinstance(item, str) for item in heading_path):
            fail(f"{rel} sections[{idx}] heading_path must be a list of strings")
        text = section.get("text")
        if not isinstance(text, str):
            fail(f"{rel} sections[{idx}] text must be a string")
        if len(text) > 1200:
            fail(f"{rel} sections[{idx}] text length exceeds 1200 chars")

    provenance = payload.get("provenance")
    if not isinstance(provenance, dict):
        fail(f"{rel} provenance must be an object")
    if not REQUIRED_PROVENANCE_FIELDS.issubset(set(provenance.keys())):
        missing = sorted(REQUIRED_PROVENANCE_FIELDS - set(provenance.keys()))
        fail(f"{rel} provenance missing fields: {missing}")
    for key in sorted(REQUIRED_PROVENANCE_FIELDS):
        if not isinstance(provenance.get(key), str) or not str(provenance.get(key)).strip():
            fail(f"{rel} provenance.{key} must be a non-empty string")


def validate_project_ingest() -> None:
    if not PROJECT_INGEST_DIR.exists():
        fail(f"Required folder not found: {PROJECT_INGEST_DIR}")
    if not PROJECT_INGEST_ARTIFACTS_DIR.exists():
        fail(f"Required folder not found: {PROJECT_INGEST_ARTIFACTS_DIR}")
    if not PROJECT_INGEST_INDEX_PATH.exists():
        fail(f"Required artifact not found: {PROJECT_INGEST_INDEX_PATH}")
    if not PROJECT_INGEST_DISCOVERY_REPORT_PATH.exists():
        fail(f"Required artifact not found: {PROJECT_INGEST_DISCOVERY_REPORT_PATH}")
    if not PROJECT_INGEST_PII_REPORT_PATH.exists():
        fail(f"Required artifact not found: {PROJECT_INGEST_PII_REPORT_PATH}")

    validate_project_ingest_index(load_json(PROJECT_INGEST_INDEX_PATH))
    validate_project_ingest_discovery_report(load_json(PROJECT_INGEST_DISCOVERY_REPORT_PATH))
    validate_project_ingest_pii_report(load_json(PROJECT_INGEST_PII_REPORT_PATH))

    artifact_paths = sorted(
        PROJECT_INGEST_ARTIFACTS_DIR.glob("*.json"),
        key=lambda item: item.name.lower(),
    )
    if not artifact_paths:
        fail("public/project_ingest/artifacts must include at least one artifact json")

    for path in artifact_paths:
        validate_project_ingest_artifact(path, load_json(path))

    index_entries = load_json(PROJECT_INGEST_INDEX_PATH).get("entries", [])
    indexed_outputs = {
        str(entry.get("output_path"))
        for entry in index_entries
        if isinstance(entry, dict)
    }
    for path in artifact_paths:
        rel = path.relative_to(REPO_ROOT).as_posix()
        if rel not in indexed_outputs:
            fail(f"public/project_ingest/index.json missing artifact output_path: {rel}")


def main() -> None:
    if not SCHEMA_PATH.exists():
        fail(f"Schema file not found: {SCHEMA_PATH}")
    if not GLIDEPATH_PATH.exists():
        fail(f"Required artifact not found: {GLIDEPATH_PATH}")

    _ = load_json(SCHEMA_PATH)
    glidepath = load_json(GLIDEPATH_PATH)
    validate_glidepath_history(glidepath)
    validate_project_ingest()

    print("✅ Public artifact validation passed")
    print(f"📄 Validated schema: {SCHEMA_PATH}")
    print(f"📉 Validated artifact: {GLIDEPATH_PATH}")
    print(f"📥 Validated ingest artifacts under: {PROJECT_INGEST_DIR}")


if __name__ == "__main__":
    main()
