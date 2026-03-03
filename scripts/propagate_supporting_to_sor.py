#!/usr/bin/env python3
"""Propagate supporting-document links into SoR YAML entities deterministically."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SOR_DIR = REPO_ROOT / "sor"
SUPPORTING_PATH = SOR_DIR / "supporting_documents.yml"
DELIVERABLES_PATH = SOR_DIR / "deliverables.yml"
WORKSTREAMS_PATH = SOR_DIR / "workstreams.yml"
TIMELINE_PATH = SOR_DIR / "timeline.yml"
REPORT_PATH = REPO_ROOT / "public" / "project_ingest" / "sor_propagation_report.json"
TRANSFORM_VERSION = "1.0.0"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def today_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def dump_yaml(payload: dict[str, Any]) -> str:
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=False)


def write_text_if_changed(path: Path, text: str) -> bool:
    rendered = text if text.endswith("\n") else text + "\n"
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    if current == rendered:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")
    return True


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Propagate supporting-document links into SoR YAML files.")
    parser.add_argument("--dry-run", action="store_true", help="Compute and report mutations without writing files.")
    parser.add_argument(
        "--max-deliverable-mutations",
        type=int,
        default=30,
        help="Maximum deliverables that can be mutated in one run before failing.",
    )
    args = parser.parse_args()

    required = [SUPPORTING_PATH, DELIVERABLES_PATH, WORKSTREAMS_PATH, TIMELINE_PATH]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise SystemExit("Missing required SoR inputs:\n- " + "\n- ".join(missing))

    supporting = load_yaml(SUPPORTING_PATH)
    deliverables_doc = load_yaml(DELIVERABLES_PATH)
    workstreams_doc = load_yaml(WORKSTREAMS_PATH)
    timeline_doc = load_yaml(TIMELINE_PATH)

    links = supporting.get("links", []) if isinstance(supporting, dict) else []
    links = links if isinstance(links, list) else []

    deliverables = deliverables_doc.get("deliverables", []) if isinstance(deliverables_doc, dict) else []
    workstreams = workstreams_doc.get("workstreams", []) if isinstance(workstreams_doc, dict) else []
    timeline_events = timeline_doc.get("timeline_events", []) if isinstance(timeline_doc, dict) else []

    if not isinstance(deliverables, list) or not isinstance(workstreams, list) or not isinstance(timeline_events, list):
        raise SystemExit("SoR payload shape invalid: expected list fields in deliverables/workstreams/timeline")

    evidence_by_deliverable: dict[str, dict[str, Any]] = {}
    for link in links:
        if not isinstance(link, dict):
            continue
        deliverable_id = str(link.get("deliverable_id") or "").strip()
        if not deliverable_id:
            continue
        evidence_by_deliverable[deliverable_id] = {
            "paths": sorted(str(item) for item in (link.get("evidence_paths") or []) if isinstance(item, str) and item.strip()),
            "sources_count": int(link.get("sources_count") or 0),
            "confidence_max": float(link.get("confidence_max") or 0.0),
            "confidence_mean": float(link.get("confidence_mean") or 0.0),
            "workstream_id": str(link.get("workstream_id") or ""),
            "action": str(link.get("action") or "review_and_update_deliverable_evidence"),
        }

    deliverable_mutations = 0
    deliverables_touched: list[str] = []
    for deliverable in deliverables:
        if not isinstance(deliverable, dict):
            continue
        deliverable_id = str(deliverable.get("id") or "")
        if not deliverable_id:
            continue
        evidence = evidence_by_deliverable.get(deliverable_id)

        previous_payload = {
            "paths": deliverable.get("supporting_evidence_paths", []),
            "count": deliverable.get("supporting_evidence_count", 0),
            "max": deliverable.get("supporting_confidence_max", 0),
            "mean": deliverable.get("supporting_confidence_mean", 0),
            "action": deliverable.get("supporting_action"),
            "status": deliverable.get("status"),
            "status_reason": deliverable.get("status_reason"),
        }
        previous_marker = json.dumps(
            previous_payload,
            sort_keys=True,
        )

        current_payload = {
            "paths": sorted(evidence["paths"]) if evidence else [],
            "count": int(evidence["sources_count"]) if evidence else 0,
            "max": round(float(evidence["confidence_max"]), 4) if evidence else 0.0,
            "mean": round(float(evidence["confidence_mean"]), 4) if evidence else 0.0,
            "action": str(evidence["action"]) if evidence else previous_payload.get("action"),
            "status": str(deliverable.get("status") or ""),
            "status_reason": deliverable.get("status_reason"),
        }

        if evidence and current_payload["count"] > 0 and str(deliverable.get("status") or "") == "not_started":
            current_payload["status"] = "in_progress"
            current_payload["status_reason"] = "auto_advanced_from_supporting_documents"

        current_marker = json.dumps(current_payload, sort_keys=True)

        deliverable["supporting_evidence_paths"] = current_payload["paths"]
        deliverable["supporting_evidence_count"] = current_payload["count"]
        deliverable["supporting_confidence_max"] = current_payload["max"]
        deliverable["supporting_confidence_mean"] = current_payload["mean"]
        if current_payload["action"] is not None:
            deliverable["supporting_action"] = current_payload["action"]
        deliverable["status"] = current_payload["status"]
        if current_payload["status_reason"] is not None:
            deliverable["status_reason"] = current_payload["status_reason"]

        if previous_marker != current_marker:
            deliverable["supporting_last_updated"] = today_iso()
            deliverable_mutations += 1
            deliverables_touched.append(deliverable_id)
        elif "supporting_last_updated" not in deliverable:
            deliverable["supporting_last_updated"] = today_iso()
            deliverable_mutations += 1
            deliverables_touched.append(deliverable_id)

    if deliverable_mutations > args.max_deliverable_mutations:
        raise SystemExit(
            f"Propagation aborted: {deliverable_mutations} deliverables would change (max {args.max_deliverable_mutations})."
        )

    evidence_rollup_by_workstream: dict[str, dict[str, Any]] = {}
    for deliverable in deliverables:
        if not isinstance(deliverable, dict):
            continue
        ws_id = str(deliverable.get("workstream_id") or "")
        if not ws_id:
            continue
        bucket = evidence_rollup_by_workstream.setdefault(ws_id, {"deliverables_with_evidence": 0, "source_count": 0})
        source_count = int(deliverable.get("supporting_evidence_count") or 0)
        if source_count > 0:
            bucket["deliverables_with_evidence"] += 1
            bucket["source_count"] += source_count

    workstreams_touched: list[str] = []
    for ws in workstreams:
        if not isinstance(ws, dict):
            continue
        ws_id = str(ws.get("id") or "")
        if not ws_id:
            continue
        previous = json.dumps(
            {
                "deliverables": ws.get("evidence_deliverables_count", 0),
                "sources": ws.get("evidence_sources_count", 0),
            },
            sort_keys=True,
        )
        agg = evidence_rollup_by_workstream.get(ws_id, {"deliverables_with_evidence": 0, "source_count": 0})
        ws["evidence_deliverables_count"] = int(agg["deliverables_with_evidence"])
        ws["evidence_sources_count"] = int(agg["source_count"])
        if int(agg["deliverables_with_evidence"]) > 0 and str(ws.get("status") or "") == "active":
            ws["status_reason"] = "active_with_supporting_evidence"
        current = json.dumps(
            {
                "deliverables": ws.get("evidence_deliverables_count", 0),
                "sources": ws.get("evidence_sources_count", 0),
            },
            sort_keys=True,
        )
        if previous != current:
            ws["evidence_last_updated"] = today_iso()
            workstreams_touched.append(ws_id)
        elif "evidence_last_updated" not in ws:
            ws["evidence_last_updated"] = today_iso()
            workstreams_touched.append(ws_id)

    timeline_touched: list[str] = []
    deliverable_by_id = {
        str(item.get("id") or ""): item
        for item in deliverables
        if isinstance(item, dict) and str(item.get("id") or "")
    }
    for event in timeline_events:
        if not isinstance(event, dict):
            continue
        event_id = str(event.get("id") or "")
        if not event_id:
            continue
        previous = json.dumps(
            {
                "linked": event.get("linked_deliverables_total", 0),
                "with_evidence": event.get("linked_deliverables_with_evidence", 0),
                "ratio": event.get("evidence_progress_ratio", 0),
            },
            sort_keys=True,
        )

        linked_ids: list[str] = []
        one = event.get("deliverable_id")
        if isinstance(one, str) and one:
            linked_ids.append(one)
        many = event.get("deliverable_ids")
        if isinstance(many, list):
            linked_ids.extend(str(item) for item in many if isinstance(item, str) and item)
        linked_ids = sorted(set(linked_ids), key=str.lower)

        if linked_ids:
            with_evidence = 0
            for did in linked_ids:
                deliverable = deliverable_by_id.get(did)
                if deliverable and int(deliverable.get("supporting_evidence_count") or 0) > 0:
                    with_evidence += 1
            event["linked_deliverables_total"] = len(linked_ids)
            event["linked_deliverables_with_evidence"] = with_evidence
            event["evidence_progress_ratio"] = round(with_evidence / max(1, len(linked_ids)), 4)
        else:
            event["linked_deliverables_total"] = 0
            event["linked_deliverables_with_evidence"] = 0
            event["evidence_progress_ratio"] = 0.0

        current = json.dumps(
            {
                "linked": event.get("linked_deliverables_total", 0),
                "with_evidence": event.get("linked_deliverables_with_evidence", 0),
                "ratio": event.get("evidence_progress_ratio", 0),
            },
            sort_keys=True,
        )
        if previous != current:
            event["evidence_last_updated"] = today_iso()
            timeline_touched.append(event_id)
        elif "evidence_last_updated" not in event:
            event["evidence_last_updated"] = today_iso()
            timeline_touched.append(event_id)

    if deliverables_touched:
        metadata = deliverables_doc.get("metadata") if isinstance(deliverables_doc, dict) else None
        if isinstance(metadata, dict):
            metadata["last_updated"] = today_iso()
    if workstreams_touched:
        metadata = workstreams_doc.get("metadata") if isinstance(workstreams_doc, dict) else None
        if isinstance(metadata, dict):
            metadata["last_updated"] = today_iso()
    if timeline_touched:
        metadata = timeline_doc.get("metadata") if isinstance(timeline_doc, dict) else None
        if isinstance(metadata, dict):
            metadata["last_updated"] = today_iso()

    changed_files: list[str] = []
    if not args.dry_run:
        if write_text_if_changed(DELIVERABLES_PATH, dump_yaml(deliverables_doc)):
            changed_files.append(DELIVERABLES_PATH.relative_to(REPO_ROOT).as_posix())
        if write_text_if_changed(WORKSTREAMS_PATH, dump_yaml(workstreams_doc)):
            changed_files.append(WORKSTREAMS_PATH.relative_to(REPO_ROOT).as_posix())
        if write_text_if_changed(TIMELINE_PATH, dump_yaml(timeline_doc)):
            changed_files.append(TIMELINE_PATH.relative_to(REPO_ROOT).as_posix())

    report = {
        "generated_at": utc_now_iso(),
        "transform_version": TRANSFORM_VERSION,
        "dry_run": bool(args.dry_run),
        "inputs": {
            "supporting_links": len(evidence_by_deliverable),
            "deliverables": len(deliverables),
            "workstreams": len(workstreams),
            "timeline_events": len(timeline_events),
        },
        "changes": {
            "deliverable_mutations": deliverable_mutations,
            "deliverables_touched": sorted(deliverables_touched, key=str.lower),
            "workstreams_touched": sorted(workstreams_touched, key=str.lower),
            "timeline_events_touched": sorted(timeline_touched, key=str.lower),
            "changed_files": changed_files,
        },
    }
    write_json(REPORT_PATH, report)

    print("🧭 SoR propagation completed")
    print(
        "📈 Propagation summary: "
        + f"deliverables={deliverable_mutations}, "
        + f"workstreams={len(workstreams_touched)}, "
        + f"timeline_events={len(timeline_touched)}"
    )
    if args.dry_run:
        print("🔎 Dry-run mode enabled; no SoR files were written")


if __name__ == "__main__":
    main()
