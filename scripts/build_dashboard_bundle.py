#!/usr/bin/env python3
"""Build dashboard_bundle/full_export and Meeting 4 readiness drilldown payloads."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile

REPO_ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DIR = REPO_ROOT / "public"

SNAPSHOT_PATH = PUBLIC_DIR / "public_snapshot.json"
FILE_CATALOG_PATH = PUBLIC_DIR / "file_catalog.json"
REF_INDEX_PATH = PUBLIC_DIR / "ref_index.json"
QUALITY_PATH = PUBLIC_DIR / "quality_report.json"
KPIS_PATH = PUBLIC_DIR / "kpis.json"
KPI_EVIDENCE_PATH = PUBLIC_DIR / "kpi_evidence.json"
GLIDEPATH_HISTORY_PATH = PUBLIC_DIR / "glidepath_history.json"
GLIDEPATH_DIAG_PATH = PUBLIC_DIR / "glidepath_diagnostics.json"
AUTOPILOT_REPORT_PATH = PUBLIC_DIR / "autopilot_report.json"

MEETING4_PATH = PUBLIC_DIR / "meeting4_readiness.json"
DASHBOARD_BUNDLE_PATH = PUBLIC_DIR / "dashboard_bundle.json"
DASHBOARD_BUNDLE_ZIP = PUBLIC_DIR / "dashboard_bundle.zip"
FULL_EXPORT_PATH = PUBLIC_DIR / "full_export.json"
FULL_EXPORT_ZIP = PUBLIC_DIR / "full_export.zip"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_decision_to_deliverables(ref_index: dict[str, Any]) -> dict[str, list[str]]:
    mapping: dict[str, set[str]] = {}
    for doc in ref_index.get("docs", []):
        if not isinstance(doc, dict):
            continue
        extracted = doc.get("extracted", {})
        if not isinstance(extracted, dict):
            continue
        decision_ids = [str(x) for x in (extracted.get("decision_ids") or []) if str(x)]
        deliverable_ids = [str(x) for x in (extracted.get("deliverable_ids") or []) if str(x)]
        if not decision_ids or not deliverable_ids:
            continue
        for decision_id in decision_ids:
            mapping.setdefault(decision_id, set()).update(deliverable_ids)
    return {k: sorted(v) for k, v in sorted(mapping.items())}


def build_meeting4_readiness(
    snapshot: dict[str, Any],
    kpis: dict[str, Any],
    ref_index: dict[str, Any],
) -> dict[str, Any]:
    deliverables = snapshot.get("deliverables", []) if isinstance(snapshot.get("deliverables"), list) else []
    kpi_items = kpis.get("kpis", []) if isinstance(kpis.get("kpis"), list) else []
    kpi_by_id = {
        str(item.get("id")): item
        for item in kpi_items
        if isinstance(item, dict) and item.get("id")
    }

    principle_pct = (
        kpi_by_id.get("KPI-CONV-05", {}).get("details", {}).get("coverage_pct")
        if isinstance(kpi_by_id.get("KPI-CONV-05", {}).get("details"), dict)
        else None
    )
    risk_pct = (
        kpi_by_id.get("KPI-CONV-06", {}).get("details", {}).get("coverage_pct")
        if isinstance(kpi_by_id.get("KPI-CONV-06", {}).get("details"), dict)
        else None
    )

    if not isinstance(principle_pct, (int, float)):
        total = len(deliverables)
        with_refs = sum(1 for d in deliverables if isinstance(d.get("principle_refs"), list) and d.get("principle_refs"))
        principle_pct = round((with_refs / total) * 100, 2) if total else 0.0
    if not isinstance(risk_pct, (int, float)):
        total = len(deliverables)
        with_refs = sum(1 for d in deliverables if isinstance(d.get("risk_refs"), list) and d.get("risk_refs"))
        risk_pct = round((with_refs / total) * 100, 2) if total else 0.0

    missing_refs = []
    by_principle: dict[str, set[str]] = {}
    by_decision = {k: set(v) for k, v in build_decision_to_deliverables(ref_index).items()}

    for d in deliverables:
        if not isinstance(d, dict):
            continue
        deliverable_id = str(d.get("id") or "")
        if not deliverable_id:
            continue
        principle_refs = sorted({str(x) for x in (d.get("principle_refs") or []) if str(x)})
        risk_refs = sorted({str(x) for x in (d.get("risk_refs") or []) if str(x)})

        if not principle_refs or not risk_refs:
            missing_refs.append(
                {
                    "deliverable_id": deliverable_id,
                    "title": str(d.get("title") or deliverable_id),
                    "checkpoint_id": d.get("checkpoint_id"),
                    "missing_principle_refs": len(principle_refs) == 0,
                    "missing_risk_refs": len(risk_refs) == 0,
                }
            )

        for principle_id in principle_refs:
            by_principle.setdefault(principle_id, set()).add(deliverable_id)

    principle_fanout = sorted(
        (
            {
                "id": principle_id,
                "deliverable_count": len(ids),
                "deliverable_ids": sorted(ids),
            }
            for principle_id, ids in by_principle.items()
        ),
        key=lambda item: (-int(item["deliverable_count"]), item["id"]),
    )
    decision_fanout = sorted(
        (
            {
                "id": decision_id,
                "deliverable_count": len(ids),
                "deliverable_ids": sorted(ids),
            }
            for decision_id, ids in by_decision.items()
        ),
        key=lambda item: (-int(item["deliverable_count"]), item["id"]),
    )

    deliverable_drilldown = {
        str(d.get("id")): {
            "title": str(d.get("title") or d.get("id") or "deliverable"),
            "checkpoint_id": d.get("checkpoint_id"),
            "principle_refs": sorted({str(x) for x in (d.get("principle_refs") or []) if str(x)}),
            "risk_refs": sorted({str(x) for x in (d.get("risk_refs") or []) if str(x)}),
            "depends_on": sorted({str(x) for x in (d.get("depends_on") or []) if str(x)}),
            "status": str(d.get("status") or "unknown"),
        }
        for d in deliverables
        if isinstance(d, dict) and d.get("id")
    }

    return {
        "meta": {
            "generated_at": utc_now_iso(),
            "source": ["public/kpis.json", "public/ref_index.json", "public/public_snapshot.json"],
            "label": "Meeting 4 Readiness",
            "committee_safe": True,
        },
        "coverage": {
            "principle_linkage_pct": round(float(principle_pct), 2),
            "risk_linkage_pct": round(float(risk_pct), 2),
        },
        "missing_refs": sorted(missing_refs, key=lambda item: (str(item.get("checkpoint_id") or ""), item["deliverable_id"])),
        "dependency_fanout": {
            "principles": principle_fanout,
            "decisions": decision_fanout,
        },
        "drilldowns": {
            "by_principle": {
                item["id"]: item["deliverable_ids"]
                for item in principle_fanout
            },
            "by_decision": {
                item["id"]: item["deliverable_ids"]
                for item in decision_fanout
            },
            "by_deliverable": deliverable_drilldown,
        },
    }


def build_dashboard_bundle(
    snapshot: dict[str, Any],
    kpis: dict[str, Any],
    quality: dict[str, Any],
    ref_index: dict[str, Any],
    meeting4_readiness: dict[str, Any],
) -> dict[str, Any]:
    return {
        "meta": {
            "generated_at": utc_now_iso(),
            "snapshot_version_key": snapshot.get("meta", {}).get("version_key"),
        },
        "snapshot": snapshot,
        "kpis": kpis,
        "quality_report": quality,
        "ref_index": ref_index,
        "meeting4_readiness": meeting4_readiness,
    }


def build_full_export(artifacts: dict[str, Any]) -> dict[str, Any]:
    ordered_files = [
        "public_snapshot.json",
        "file_catalog.json",
        "ref_index.json",
        "quality_report.json",
        "kpis.json",
        "kpi_evidence.json",
        "glidepath_history.json",
        "glidepath_diagnostics.json",
        "meeting4_readiness.json",
        "dashboard_bundle.json",
    ]

    sha_map: dict[str, str] = {}
    for name in ordered_files:
        path = PUBLIC_DIR / name
        if path.exists():
            sha_map[name] = file_sha256(path)

    return {
        "manifest": {
            "generated_at": utc_now_iso(),
            "files": [name for name in ordered_files if name in sha_map],
            "sha256": sha_map,
        },
        "artifacts": artifacts,
    }


def write_zip(target_zip: Path, json_files: list[Path]) -> None:
    target_zip.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(target_zip, mode="w", compression=ZIP_DEFLATED) as archive:
        for path in json_files:
            if path.exists():
                archive.write(path, arcname=path.name)


def main() -> None:
    snapshot = load_json(SNAPSHOT_PATH)
    file_catalog = load_json(FILE_CATALOG_PATH)
    ref_index = load_json(REF_INDEX_PATH)
    quality = load_json(QUALITY_PATH)
    kpis = load_json(KPIS_PATH)
    kpi_evidence = load_json(KPI_EVIDENCE_PATH)
    glidepath_history = load_json(GLIDEPATH_HISTORY_PATH)
    glidepath_diagnostics = load_json(GLIDEPATH_DIAG_PATH)
    autopilot_report = load_json(AUTOPILOT_REPORT_PATH)

    meeting4_readiness = build_meeting4_readiness(snapshot, kpis, ref_index)
    write_json(MEETING4_PATH, meeting4_readiness)

    dashboard_bundle = build_dashboard_bundle(snapshot, kpis, quality, ref_index, meeting4_readiness)
    write_json(DASHBOARD_BUNDLE_PATH, dashboard_bundle)

    artifacts = {
        "public_snapshot.json": snapshot,
        "file_catalog.json": file_catalog,
        "ref_index.json": ref_index,
        "quality_report.json": quality,
        "kpis.json": kpis,
        "kpi_evidence.json": kpi_evidence,
        "glidepath_history.json": glidepath_history,
        "glidepath_diagnostics.json": glidepath_diagnostics,
        "meeting4_readiness.json": meeting4_readiness,
        "dashboard_bundle.json": dashboard_bundle,
    }
    if autopilot_report:
        artifacts["autopilot_report.json"] = autopilot_report

    full_export = build_full_export(artifacts)
    write_json(FULL_EXPORT_PATH, full_export)

    write_zip(DASHBOARD_BUNDLE_ZIP, [DASHBOARD_BUNDLE_PATH, MEETING4_PATH])
    write_zip(
        FULL_EXPORT_ZIP,
        [
            FULL_EXPORT_PATH,
            DASHBOARD_BUNDLE_PATH,
            MEETING4_PATH,
            SNAPSHOT_PATH,
            KPIS_PATH,
            QUALITY_PATH,
            REF_INDEX_PATH,
            KPI_EVIDENCE_PATH,
        ],
    )

    print(f"📦 Dashboard bundle written: {DASHBOARD_BUNDLE_PATH}")
    print(f"🧾 Full export written: {FULL_EXPORT_PATH}")
    print(f"🎯 Meeting 4 readiness written: {MEETING4_PATH}")


if __name__ == "__main__":
    main()
