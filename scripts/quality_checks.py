#!/usr/bin/env python3
"""Run deterministic quality checks and emit public/quality_report.json."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SOR_DIR = REPO_ROOT / "sor"
PUBLIC_DIR = REPO_ROOT / "public"
OUTPUT_PATH = PUBLIC_DIR / "quality_report.json"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def add_issue(
    issues: list[dict[str, Any]],
    severity: str,
    code: str,
    message: str,
    evidence: list[dict[str, Any]],
) -> None:
    issues.append(
        {
            "severity": severity,
            "code": code,
            "message": message,
            "evidence": evidence,
        }
    )


def detect_placeholder(text: str) -> bool:
    return bool(re.search(r"\b(TBD|TODO|\?\?\?)\b", text, flags=re.IGNORECASE))


def build_quality_report() -> dict[str, Any]:
    workstreams_data = load_yaml(SOR_DIR / "workstreams.yml")
    timeline_data = load_yaml(SOR_DIR / "timeline.yml")
    deliverables_data = load_yaml(SOR_DIR / "deliverables.yml")
    ref_index = load_json(PUBLIC_DIR / "ref_index.json")

    workstreams = workstreams_data.get("workstreams", [])
    timeline_events = timeline_data.get("timeline_events", [])
    deliverables = deliverables_data.get("deliverables", [])

    timeline_ids = {e.get("id") for e in timeline_events if e.get("id")}
    workstream_ids = {w.get("id") for w in workstreams if w.get("id")}
    deliverable_ids = {d.get("id") for d in deliverables if d.get("id")}

    issues: list[dict[str, Any]] = []

    # 1) ID integrity across SoR
    dangling_ws_refs = [d.get("id") for d in deliverables if d.get("workstream_id") not in workstream_ids]
    if dangling_ws_refs:
        add_issue(
            issues,
            "error",
            "ID-DANGLING-WORKSTREAM",
            "Some deliverables reference unknown workstream IDs.",
            [{"deliverable_id": did} for did in dangling_ws_refs],
        )

    dangling_cp_refs = [
        d.get("id")
        for d in deliverables
        if d.get("checkpoint_id") and d.get("checkpoint_id") not in timeline_ids
    ]
    if dangling_cp_refs:
        add_issue(
            issues,
            "error",
            "ID-DANGLING-CHECKPOINT",
            "Some deliverables reference unknown checkpoint IDs.",
            [{"deliverable_id": did} for did in dangling_cp_refs],
        )

    dep_issues = []
    for d in deliverables:
        for dep in d.get("depends_on", []) or []:
            if dep not in deliverable_ids:
                dep_issues.append({"deliverable_id": d.get("id"), "depends_on": dep})
    if dep_issues:
        add_issue(
            issues,
            "error",
            "ID-DANGLING-DEPENDENCY",
            "Some deliverables depend on unknown deliverable IDs.",
            dep_issues,
        )

    # 2) Placeholder detection
    dod_placeholder = []
    for d in deliverables:
        for item in d.get("definition_of_done", []) or []:
            if detect_placeholder(str(item)):
                dod_placeholder.append({"deliverable_id": d.get("id"), "dod_item": item})
    if dod_placeholder:
        add_issue(
            issues,
            "warning",
            "PLACEHOLDER-DOD",
            "Definition-of-done contains placeholder text.",
            dod_placeholder,
        )

    md_placeholder = []
    for doc in ref_index.get("docs", []):
        if doc.get("doc_type") != "md":
            continue
        path = REPO_ROOT / doc.get("doc_path", "")
        if path.exists() and detect_placeholder(path.read_text(encoding="utf-8", errors="ignore")):
            md_placeholder.append({"doc_path": doc.get("doc_path")})
    if md_placeholder:
        add_issue(
            issues,
            "info",
            "PLACEHOLDER-MARKDOWN",
            "Markdown supporting docs include TBD/TODO/??? tokens.",
            md_placeholder,
        )

    # 3) Ownership completeness
    missing_deliverable_owners = [
        d.get("id")
        for d in deliverables
        if not d.get("assigned_to") and not (isinstance(d.get("owners"), list) and d.get("owners"))
    ]
    if missing_deliverable_owners:
        add_issue(
            issues,
            "error",
            "OWNER-MISSING-DELIVERABLE",
            "Some deliverables are missing owners.",
            [{"deliverable_id": did} for did in missing_deliverable_owners],
        )

    missing_workstream_leads = [w.get("id") for w in workstreams if not w.get("lead")]
    if missing_workstream_leads:
        add_issue(
            issues,
            "error",
            "OWNER-MISSING-WORKSTREAM",
            "Some workstreams are missing leads.",
            [{"workstream_id": wid} for wid in missing_workstream_leads],
        )

    # 4) Gate mapping completeness
    unmapped_checkpoints = [d.get("id") for d in deliverables if not d.get("checkpoint_id")]
    if unmapped_checkpoints:
        add_issue(
            issues,
            "warning",
            "GATE-MAPPING-MISSING",
            "Some deliverables do not have checkpoint_id mappings.",
            [{"deliverable_id": did} for did in unmapped_checkpoints],
        )

    # 5) Instrumentation coverage
    principle_cov = sum(1 for d in deliverables if isinstance(d.get("principle_refs"), list) and d.get("principle_refs"))
    risk_cov = sum(1 for d in deliverables if isinstance(d.get("risk_refs"), list) and d.get("risk_refs"))

    docs = ref_index.get("docs", [])
    docs_with_pr = sum(1 for d in docs if d.get("extracted", {}).get("principle_ids"))
    docs_with_rr = sum(1 for d in docs if d.get("extracted", {}).get("risk_ids"))

    ws_pattern = re.compile(r"^WS-[A-Z0-9-]+$")
    docs_workstream_ids = {
        str(ws).upper()
        for doc in docs
        for ws in (doc.get("extracted", {}).get("workstream_ids") or [])
        if isinstance(ws, str) and ws_pattern.match(str(ws).upper())
    }
    sor_workstream_ids = {str(ws).upper() for ws in workstream_ids if isinstance(ws, str)}
    drift_docs_not_in_sor = sorted(docs_workstream_ids - sor_workstream_ids)
    drift_sor_not_in_docs = sorted(sor_workstream_ids - docs_workstream_ids)

    if drift_docs_not_in_sor or drift_sor_not_in_docs:
        add_issue(
            issues,
            "warning",
            "DRIFT-WORKSTREAM-IDS",
            "SoR workstream IDs and doc-extracted WS-* IDs are not fully aligned.",
            [
                {
                    "docs_not_in_sor": drift_docs_not_in_sor,
                    "sor_not_in_docs": drift_sor_not_in_docs,
                }
            ],
        )

    if deliverables and principle_cov == 0:
        add_issue(
            issues,
            "warning",
            "INSTRUMENTATION-PRINCIPLES",
            "No deliverables currently include principle_refs.",
            [{"deliverable_count": len(deliverables)}],
        )

    if deliverables and risk_cov == 0:
        add_issue(
            issues,
            "warning",
            "INSTRUMENTATION-RISKS",
            "No deliverables currently include risk_refs.",
            [{"deliverable_count": len(deliverables)}],
        )

    if docs and docs_with_pr == 0:
        add_issue(
            issues,
            "warning",
            "DOC-COVERAGE-PRINCIPLES",
            "No scanned docs contain principle references.",
            [{"scanned_docs": len(docs)}],
        )

    if docs and docs_with_rr == 0:
        add_issue(
            issues,
            "warning",
            "DOC-COVERAGE-RISKS",
            "No scanned docs contain risk references.",
            [{"scanned_docs": len(docs)}],
        )

    summary_counts = {
        "error": sum(1 for i in issues if i["severity"] == "error"),
        "warning": sum(1 for i in issues if i["severity"] == "warning"),
        "info": sum(1 for i in issues if i["severity"] == "info"),
    }

    return {
        "meta": {
            "generated_at": utc_now_iso(),
            "sources": [
                "sor/workstreams.yml",
                "sor/timeline.yml",
                "sor/deliverables.yml",
                "public/ref_index.json",
            ],
        },
        "summary_counts": summary_counts,
        "issues": issues,
        "metrics": {
            "deliverable_principle_refs_pct": (principle_cov / len(deliverables) * 100) if deliverables else 0,
            "deliverable_risk_refs_pct": (risk_cov / len(deliverables) * 100) if deliverables else 0,
            "docs_with_principles_pct": (docs_with_pr / len(docs) * 100) if docs else 0,
            "docs_with_risks_pct": (docs_with_rr / len(docs) * 100) if docs else 0,
            "sor_vs_docs_workstream_drift": {
                "sor_count": len(sor_workstream_ids),
                "docs_count": len(docs_workstream_ids),
                "docs_not_in_sor": drift_docs_not_in_sor,
                "sor_not_in_docs": drift_sor_not_in_docs,
                "mismatch_count": len(drift_docs_not_in_sor) + len(drift_sor_not_in_docs),
            },
        },
    }


def main() -> None:
    report = build_quality_report()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"🧪 Quality report written to {OUTPUT_PATH}")
    print(f"⚠️  Issues: {len(report['issues'])}")


if __name__ == "__main__":
    main()
