#!/usr/bin/env python3
"""Build an advisory, inspectable memory layer from deterministic public artifacts.

This artifact is non-authoritative by design and must not overwrite SoR state.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

TRANSFORM_VERSION = "0.1.0"

REPO_ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DIR = REPO_ROOT / "public"

SNAPSHOT_PATH = PUBLIC_DIR / "public_snapshot.json"
KPIS_PATH = PUBLIC_DIR / "kpis.json"
KPI_EVIDENCE_PATH = PUBLIC_DIR / "kpi_evidence.json"
QUALITY_PATH = PUBLIC_DIR / "quality_report.json"
REF_INDEX_PATH = PUBLIC_DIR / "ref_index.json"
COGNITIVE_PATH = PUBLIC_DIR / "project_ingest" / "cognitive_control_report.json"

MEMORY_PATH = PUBLIC_DIR / "advisory_memory.json"
MEMORY_INDEX_PATH = PUBLIC_DIR / "advisory_memory_index.json"
MEMORY_AUDIT_PATH = PUBLIC_DIR / "advisory_memory_audit.json"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    return utc_now().isoformat().replace("+00:00", "Z")


def expires_iso(days: int) -> str:
    return (utc_now() + timedelta(days=days)).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json_if_changed(path: Path, payload: dict[str, Any]) -> bool:
    rendered = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    if current == rendered:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")
    return True


def canonical_kpi_id(item: dict[str, Any]) -> str:
    return str(item.get("kpi_id") or item.get("id") or "")


def collect_episodic(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    deliverables = snapshot.get("deliverables", []) if isinstance(snapshot.get("deliverables"), list) else []
    status_counts = Counter(str(item.get("status") or "unknown") for item in deliverables if isinstance(item, dict))
    change_log = snapshot.get("change_log", []) if isinstance(snapshot.get("change_log"), list) else []

    entries: list[dict[str, Any]] = [
        {
            "id": "ep_status_distribution",
            "title": "Deliverable status distribution",
            "summary": "Current distribution of public deliverable statuses in the deterministic snapshot.",
            "confidence": 1.0,
            "expires_at": expires_iso(30),
            "derived_from_version_key": str(snapshot.get("meta", {}).get("version_key") or snapshot.get("metadata", {}).get("version_key") or ""),
            "citations": [{"path": "public/public_snapshot.json", "type": "deterministic"}],
            "details": {
                "deliverable_total": len(deliverables),
                "status_counts": dict(sorted(status_counts.items())),
            },
        }
    ]

    if change_log:
        latest = []
        for item in change_log[:8]:
            if not isinstance(item, dict):
                continue
            latest.append(
                {
                    "id": str(item.get("id") or ""),
                    "date": str(item.get("date") or ""),
                    "type": str(item.get("type") or ""),
                    "description": str(item.get("description") or ""),
                }
            )
        entries.append(
            {
                "id": "ep_recent_changes",
                "title": "Recent decision/change log activity",
                "summary": "Recent change_log entries from the authoritative snapshot.",
                "confidence": 1.0,
                "expires_at": expires_iso(30),
                "derived_from_version_key": str(snapshot.get("meta", {}).get("version_key") or snapshot.get("metadata", {}).get("version_key") or ""),
                "citations": [{"path": "public/public_snapshot.json", "type": "deterministic"}],
                "details": {"latest_change_log_entries": latest},
            }
        )

    return entries


def collect_thematic(snapshot: dict[str, Any], ref_index: dict[str, Any]) -> list[dict[str, Any]]:
    deliverables = snapshot.get("deliverables", []) if isinstance(snapshot.get("deliverables"), list) else []

    principle_counts: Counter[str] = Counter()
    risk_counts: Counter[str] = Counter()
    for item in deliverables:
        if not isinstance(item, dict):
            continue
        for pid in item.get("principle_refs") or []:
            principle_counts[str(pid)] += 1
        for rid in item.get("risk_refs") or []:
            risk_counts[str(rid)] += 1

    decision_counts: Counter[str] = Counter()
    for doc in ref_index.get("docs", []) if isinstance(ref_index.get("docs"), list) else []:
        if not isinstance(doc, dict):
            continue
        extracted = doc.get("extracted", {})
        if not isinstance(extracted, dict):
            continue
        for decision_id in extracted.get("decision_ids") or []:
            decision_counts[str(decision_id)] += 1

    return [
        {
            "id": "th_principle_risk_fanout",
            "title": "Principle/risk linkage fanout",
            "summary": "Most frequently referenced principles and risks across deliverables.",
            "confidence": 0.98,
            "expires_at": expires_iso(180),
            "derived_from_version_key": str(snapshot.get("meta", {}).get("version_key") or snapshot.get("metadata", {}).get("version_key") or ""),
            "citations": [{"path": "public/public_snapshot.json", "type": "deterministic"}],
            "details": {
                "top_principles": [{"id": k, "count": v} for k, v in principle_counts.most_common(8)],
                "top_risks": [{"id": k, "count": v} for k, v in risk_counts.most_common(8)],
            },
        },
        {
            "id": "th_decision_density",
            "title": "Decision reference density",
            "summary": "Decision IDs most frequently extracted from indexed public documents.",
            "confidence": 0.9,
            "expires_at": expires_iso(120),
            "derived_from_version_key": str(snapshot.get("meta", {}).get("version_key") or snapshot.get("metadata", {}).get("version_key") or ""),
            "citations": [{"path": "public/ref_index.json", "type": "deterministic"}],
            "details": {
                "top_decisions": [{"id": k, "count": v} for k, v in decision_counts.most_common(8)],
                "indexed_docs": len(ref_index.get("docs", [])) if isinstance(ref_index.get("docs"), list) else 0,
            },
        },
    ]


def collect_open_loops(snapshot: dict[str, Any], quality: dict[str, Any]) -> list[dict[str, Any]]:
    deliverables = snapshot.get("deliverables", []) if isinstance(snapshot.get("deliverables"), list) else []
    unresolved = []
    for item in deliverables:
        if not isinstance(item, dict):
            continue
        status = str(item.get("status") or "")
        if status not in {"in_progress", "not_started"}:
            continue
        if item.get("public_url"):
            continue
        unresolved.append(
            {
                "deliverable_id": str(item.get("id") or ""),
                "title": str(item.get("title") or ""),
                "status": status,
                "checkpoint_id": item.get("checkpoint_id"),
            }
        )

    quality_issues = quality.get("issues", []) if isinstance(quality.get("issues"), list) else []

    return [
        {
            "id": "ol_missing_public_links",
            "title": "Open loop: deliverables without public source links",
            "summary": "In-progress or not-started deliverables that do not yet have public_url linkage.",
            "confidence": 1.0,
            "expires_at": expires_iso(45),
            "derived_from_version_key": str(snapshot.get("meta", {}).get("version_key") or snapshot.get("metadata", {}).get("version_key") or ""),
            "citations": [{"path": "public/public_snapshot.json", "type": "deterministic"}],
            "details": {
                "count": len(unresolved),
                "items": unresolved[:25],
            },
        },
        {
            "id": "ol_quality_flags",
            "title": "Open loop: quality check flags",
            "summary": "Outstanding quality issues reported by deterministic quality checks.",
            "confidence": 1.0,
            "expires_at": expires_iso(30),
            "derived_from_version_key": str(snapshot.get("meta", {}).get("version_key") or snapshot.get("metadata", {}).get("version_key") or ""),
            "citations": [{"path": "public/quality_report.json", "type": "deterministic"}],
            "details": {
                "issue_count": len(quality_issues),
                "issues": quality_issues[:20],
            },
        },
    ]


def collect_actions(kpis_payload: dict[str, Any], cognitive: dict[str, Any]) -> list[dict[str, Any]]:
    kpis = kpis_payload.get("kpis", []) if isinstance(kpis_payload.get("kpis"), list) else []
    reds = []
    yellows = []
    for item in kpis:
        if not isinstance(item, dict):
            continue
        status = str(item.get("status") or "").lower()
        if status == "red":
            reds.append(item)
        elif status == "yellow":
            yellows.append(item)

    top_red = sorted(reds, key=lambda k: (float(k.get("score") or 10.0), canonical_kpi_id(k)))[:5]
    top_yellow = sorted(yellows, key=lambda k: (float(k.get("score") or 10.0), canonical_kpi_id(k)))[:5]

    recommended_actions = (
        cognitive.get("recommended_actions", [])
        if isinstance(cognitive.get("recommended_actions"), list)
        else []
    )

    return [
        {
            "id": "ac_top_risk_kpis",
            "title": "Action memory: prioritize red/yellow KPI drivers",
            "summary": "Prioritized KPI set for next-cycle intervention planning.",
            "confidence": 0.95,
            "expires_at": expires_iso(21),
            "derived_from_version_key": str(kpis_payload.get("meta", {}).get("version_key") or ""),
            "citations": [{"path": "public/kpis.json", "type": "deterministic"}],
            "details": {
                "red_kpis": [
                    {"kpi_id": canonical_kpi_id(item), "name": item.get("name"), "score": item.get("score")}
                    for item in top_red
                ],
                "yellow_kpis": [
                    {"kpi_id": canonical_kpi_id(item), "name": item.get("name"), "score": item.get("score")}
                    for item in top_yellow
                ],
            },
        },
        {
            "id": "ac_supporting_linkage_candidates",
            "title": "Action memory: supporting evidence linkage candidates",
            "summary": "Candidate deliverable/source link updates from cognitive control report for human review.",
            "confidence": 0.8,
            "expires_at": expires_iso(14),
            "derived_from_version_key": str(cognitive.get("transform_version") or ""),
            "citations": [{"path": "public/project_ingest/cognitive_control_report.json", "type": "advisory"}],
            "details": {
                "recommended_review_mode": cognitive.get("recommended_review_mode"),
                "candidate_count": len(recommended_actions),
                "candidates": [
                    {
                        "recommended_deliverable_id": item.get("recommended_deliverable_id"),
                        "source_path": item.get("source_path"),
                        "confidence_adjusted": item.get("confidence_adjusted"),
                        "risk_flags": item.get("risk_flags"),
                    }
                    for item in recommended_actions[:20]
                    if isinstance(item, dict)
                ],
            },
        },
    ]


def build_memory_payload() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    snapshot = load_json(SNAPSHOT_PATH)
    kpis = load_json(KPIS_PATH)
    _ = load_json(KPI_EVIDENCE_PATH)
    quality = load_json(QUALITY_PATH)
    ref_index = load_json(REF_INDEX_PATH)
    cognitive = load_json(COGNITIVE_PATH)

    version_key = str(snapshot.get("meta", {}).get("version_key") or snapshot.get("metadata", {}).get("version_key") or "")

    memory = {
        "episodic": collect_episodic(snapshot),
        "thematic": collect_thematic(snapshot, ref_index),
        "open_loops": collect_open_loops(snapshot, quality),
        "action_recommendations": collect_actions(kpis, cognitive),
    }

    citation_paths = sorted(
        {
            str(citation.get("path"))
            for section in memory.values()
            for item in section
            for citation in (item.get("citations") or [])
            if isinstance(citation, dict) and citation.get("path")
        }
    )

    payload = {
        "meta": {
            "generated_at": utc_now_iso(),
            "version_key": version_key,
            "transform_version": TRANSFORM_VERSION,
            "advisory": True,
            "authoritative": False,
            "producer": "fccps-memory-poc",
            "policy": {
                "sor_authoritative": True,
                "deterministic_artifacts_authoritative": True,
                "memory_outputs_advisory_only": True,
                "conflict_rule": "SoR and deterministic KPIs always override memory statements.",
            },
        },
        "memory": memory,
        "citations_catalog": citation_paths,
    }

    index_payload = {
        "meta": {
            "generated_at": payload["meta"]["generated_at"],
            "version_key": version_key,
            "transform_version": TRANSFORM_VERSION,
            "advisory": True,
            "authoritative": False,
        },
        "counts": {section: len(entries) for section, entries in memory.items()},
        "memory_ids": {
            section: [str(item.get("id") or "") for item in entries]
            for section, entries in memory.items()
        },
        "citation_paths": citation_paths,
    }

    audit_payload = {
        "meta": {
            "generated_at": payload["meta"]["generated_at"],
            "version_key": version_key,
            "transform_version": TRANSFORM_VERSION,
            "advisory": True,
            "authoritative": False,
        },
        "quality": {
            "total_memory_entries": sum(len(entries) for entries in memory.values()),
            "entries_with_citations": sum(
                1 for entries in memory.values() for item in entries if isinstance(item.get("citations"), list) and len(item["citations"]) > 0
            ),
            "missing_citation_entries": [
                str(item.get("id") or "")
                for entries in memory.values()
                for item in entries
                if not isinstance(item.get("citations"), list) or len(item["citations"]) == 0
            ],
            "citation_path_count": len(citation_paths),
        },
    }

    return payload, index_payload, audit_payload


def main() -> None:
    payload, index_payload, audit_payload = build_memory_payload()
    changed = [
        (MEMORY_PATH, write_json_if_changed(MEMORY_PATH, payload)),
        (MEMORY_INDEX_PATH, write_json_if_changed(MEMORY_INDEX_PATH, index_payload)),
        (MEMORY_AUDIT_PATH, write_json_if_changed(MEMORY_AUDIT_PATH, audit_payload)),
    ]

    changed_files = [path for path, was_changed in changed if was_changed]
    status = "updated" if changed_files else "unchanged"
    print(f"🧠 Advisory memory artifacts {status}")
    print(f"   - {MEMORY_PATH}")
    print(f"   - {MEMORY_INDEX_PATH}")
    print(f"   - {MEMORY_AUDIT_PATH}")
    print(f"📊 entries={sum(index_payload['counts'].values())} citation_paths={len(index_payload['citation_paths'])}")


if __name__ == "__main__":
    main()
