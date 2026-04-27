#!/usr/bin/env python3
"""Build deterministic schedule/convergence/freshness/publicability KPIs."""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SOR_DIR = REPO_ROOT / "sor"
PUBLIC_DIR = REPO_ROOT / "public"
OUTPUT_PATH = PUBLIC_DIR / "kpis.json"
EVIDENCE_OUTPUT_PATH = PUBLIC_DIR / "kpi_evidence.json"
EVIDENCE_COVERAGE_OUTPUT_PATH = PUBLIC_DIR / "evidence_coverage.json"
EVIDENCE_TEMPLATES_OUTPUT_PATH = PUBLIC_DIR / "evidence_templates.json"
SUPPORTING_DOCS_PATH = SOR_DIR / "supporting_documents.yml"
TIMEZONE_NAME = "America/New_York"
FRESHNESS_DAYS = 7
EVIDENCE_TEMPLATES_VERSION = "evidence_templates_v1"
EVIDENCE_TEMPLATES_GENERATED_AT = "2026-03-04T00:00:00Z"
BOARD_READY_SOURCE_PATH = "drafting/_consolidated/FCCPS_AI_Policy_Drafting_Package_rev-20260428.docx"


def write_json_if_changed(path: Path, payload: dict[str, Any]) -> None:
    rendered = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    if current == rendered:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")


def templates_payload() -> dict[str, Any]:
    templates = [
        {
            "template_id": "derived_from_meetings_v1",
            "title": "Derived From Meetings",
            "description": "Document how meeting outputs changed a deliverable.",
            "body": "\n".join(
                [
                    "### Derived from meetings",
                    "- Meeting ID/date: <MTG-... / YYYY-MM-DD>",
                    "- Decision or directive: <what was decided>",
                    "- Deliverable change: <what was updated>",
                    "- Supporting source path(s): <public/...>",
                ]
            ),
        },
        {
            "template_id": "evidence_block_v1",
            "title": "Evidence Block",
            "description": "Minimal evidence section for a deliverable update.",
            "body": "\n".join(
                [
                    "### Evidence",
                    "- Source: <minutes/survey/research/email>",
                    "- Date: <YYYY-MM-DD>",
                    "- Claim supported: <what this evidence proves>",
                    "- Link(s): <repo-relative path(s)>",
                    "- Notes: <brief relevance summary>",
                ]
            ),
        },
        {
            "template_id": "risk_evidence_row_v1",
            "title": "Risk Register Evidence Row",
            "description": "Attach evidence to a risk entry.",
            "body": "\n".join(
                [
                    "- Risk ID: <RISK-...>",
                    "- Evidence path: <public/...>",
                    "- Observation date: <YYYY-MM-DD>",
                    "- Impact note: <1-2 sentences>",
                    "- Mitigation trigger: <what action this evidence triggers>",
                ]
            ),
        },
        {
            "template_id": "trace_table_v1",
            "title": "Evidence Trace Table",
            "description": "Trace claims to concrete source paths.",
            "body": "\n".join(
                [
                    "| Claim | Source Type | Source Path | Date | Owner |",
                    "|---|---|---|---|---|",
                    "| <claim> | <minutes/survey/research/email> | <public/...> | <YYYY-MM-DD> | <name> |",
                ]
            ),
        },
    ]
    templates.sort(key=lambda item: str(item.get("template_id", "")))
    return {
        "version_key": EVIDENCE_TEMPLATES_VERSION,
        "generated_at": EVIDENCE_TEMPLATES_GENERATED_AT,
        "templates": templates,
    }


def infer_source_type(path: str) -> str:
    normalized = path.lower()
    if "meeting" in normalized or "minutes" in normalized:
        return "minutes"
    if "survey" in normalized:
        return "survey"
    if "deliverable" in normalized:
        return "deliverable"
    if "email" in normalized:
        return "email"
    if "research" in normalized or "baseline" in normalized:
        return "research"
    return "other"


def collect_recommended_sources(supporting_documents: dict[str, Any]) -> list[dict[str, Any]]:
    links = supporting_documents.get("links", []) if isinstance(supporting_documents.get("links"), list) else []
    entries: list[dict[str, Any]] = []
    for item in links:
        if not isinstance(item, dict):
            continue
        source_path = str(item.get("source_path") or item.get("output_path") or "").strip().replace("\\", "/")
        if not source_path:
            continue
        source_type = infer_source_type(source_path)
        entries.append(
            {
                "id": f"{source_type}:{source_path}".replace(" ", "_"),
                "title": source_path.split("/")[-1] or source_path,
                "path": source_path,
                "source_type": source_type,
                "date": str(item.get("generated_at") or "") or None,
            }
        )
    entries.sort(key=lambda item: str(item.get("path", "")))
    return entries


def build_evidence_coverage(
    kpi_payload: dict[str, Any],
    deliverables: list[dict[str, Any]],
    supporting_documents: dict[str, Any],
) -> dict[str, Any]:
    recommended_sources = collect_recommended_sources(supporting_documents)
    templates_version = EVIDENCE_TEMPLATES_VERSION

    missing_deliverables: list[dict[str, Any]] = []
    evidence_link_count = 0

    for deliverable in sorted(deliverables, key=lambda item: str(item.get("id") or "")):
        deliverable_id = str(deliverable.get("id") or "").strip()
        if not deliverable_id:
            continue

        supporting_paths = sorted(
            {
                str(path).strip()
                for path in (deliverable.get("supporting_evidence_paths") or [])
                if str(path).strip()
            }
        )
        evidence_link_count += len(supporting_paths)

        supporting_count = int(deliverable.get("supporting_evidence_count") or 0)
        supporting_confidence_max = float(deliverable.get("supporting_confidence_max") or 0.0)
        description_blob = " ".join(
            [
                str(deliverable.get("description") or ""),
                str(deliverable.get("title") or ""),
                str(deliverable.get("assigned_to") or ""),
            ]
        ).lower()

        missing_fields: list[str] = []
        if supporting_count <= 0:
            missing_fields.append("supporting_evidence_count")
        if not supporting_paths:
            missing_fields.append("supporting_evidence_paths")
        if supporting_confidence_max <= 0.0:
            missing_fields.append("supporting_confidence_max")
        if "evidence" not in description_blob and "source" not in description_blob:
            missing_fields.append("evidence_narrative")

        if not missing_fields:
            continue

        preferred_sources = [
            item
            for item in recommended_sources
            if item.get("source_type") in {"minutes", "survey", "research"}
        ][:3]

        missing_deliverables.append(
            {
                "deliverable_id": deliverable_id,
                "workstream": str(deliverable.get("workstream_id") or deliverable.get("workstream") or "COMMITTEE"),
                "path": str(deliverable.get("public_url") or "").strip(),
                "missing": missing_fields,
                "suggested_fixes": [
                    {"type": "add_evidence_section", "template_id": "evidence_block_v1"},
                    {"type": "add_trace_table", "template_id": "trace_table_v1"},
                ],
                "recommended_sources": preferred_sources,
            }
        )

    missing_deliverables.sort(key=lambda item: str(item.get("deliverable_id", "")))

    total_deliverables = len([d for d in deliverables if d.get("id")])
    score_proxy = 0
    if total_deliverables > 0:
        score_proxy = max(0, round(((total_deliverables - len(missing_deliverables)) / total_deliverables) * 100))

    top_missing_areas = [
        {
            "deliverable_id": item.get("deliverable_id"),
            "missing_fields": item.get("missing", []),
            "suggested_evidence_block_template": "trace_table_v1"
            if "supporting_evidence_paths" in set(item.get("missing", []))
            else "evidence_block_v1",
        }
        for item in missing_deliverables[:5]
    ]

    version_seed = json.dumps(
        {
            "kpi_generated_at": kpi_payload.get("meta", {}).get("generated_at"),
            "missing": [
                {
                    "deliverable_id": item.get("deliverable_id"),
                    "missing": item.get("missing", []),
                }
                for item in missing_deliverables
            ],
            "evidence_link_count": evidence_link_count,
            "templates_version": templates_version,
        },
        sort_keys=True,
    )
    version_key = re.sub(r"[^0-9a-f]", "", __import__("hashlib").md5(version_seed.encode("utf-8")).hexdigest())[:12]

    generated_at = kpi_payload.get("meta", {}).get("generated_at") or utc_now_iso()
    if EVIDENCE_COVERAGE_OUTPUT_PATH.exists():
        existing = load_json(EVIDENCE_COVERAGE_OUTPUT_PATH)
        if str(existing.get("version_key") or "") == version_key and str(existing.get("generated_at") or ""):
            generated_at = str(existing.get("generated_at"))

    return {
        "version_key": version_key,
        "generated_at": generated_at,
        "templates_version": templates_version,
        "kpi": {
            "KPI-CONV-04": {
                "score_proxy": score_proxy,
                "evidence_link_count": evidence_link_count,
                "deliverables_missing_evidence": missing_deliverables,
                "gap": {
                    "kpi_id": "KPI-CONV-04",
                    "missing_evidence_count": len(missing_deliverables),
                    "missing_links_count": sum(
                        1 for item in missing_deliverables if "supporting_evidence_paths" in set(item.get("missing", []))
                    ),
                    "top_missing_areas": top_missing_areas,
                },
            }
        },
    }


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def parse_datetime_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    cleaned = str(value).strip()
    if not cleaned:
        return None
    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(cleaned)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def status_from_score(score: int) -> str:
    if score >= 85:
        return "green"
    if score >= 60:
        return "yellow"
    return "red"


def status_from_threshold(score: int, green_floor: int, yellow_floor: int) -> str:
    if score >= green_floor:
        return "green"
    if score >= yellow_floor:
        return "yellow"
    return "red"


def first_date_in_changelog(path: Path) -> datetime | None:
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8", errors="ignore")
    match = re.search(r"\[(\d{4}-\d{2}-\d{2})\]", text)
    if not match:
        return None
    return parse_date(match.group(1))


def doc_recency_days(file_catalog: dict[str, Any], prefixes: list[str]) -> list[int]:
    now = datetime.now(timezone.utc)
    days: list[int] = []
    for item in file_catalog.get("files", []):
        path = str(item.get("path", ""))
        if not any(path.startswith(prefix) for prefix in prefixes):
            continue
        modified = parse_date(str(item.get("last_modified_iso", ""))[:10])
        if modified:
            days.append((now - modified).days)
    return days


def milestone_ids_from_timeline(timeline_events: list[dict[str, Any]]) -> set[str]:
    ids: set[str] = set()
    for event in timeline_events:
        event_id = str(event.get("id", ""))
        if event_id.lower().startswith("ms_"):
            ids.add(event_id.lower())
    return ids


def dependency_closure(deliverable_by_id: dict[str, dict[str, Any]], start_ids: set[str]) -> set[str]:
    visited: set[str] = set()
    stack = [item for item in start_ids if item in deliverable_by_id]
    while stack:
        current = stack.pop()
        if current in visited:
            continue
        visited.add(current)
        current_item = deliverable_by_id.get(current) or {}
        for dep in current_item.get("depends_on", []) or []:
            dep_id = str(dep or "").strip()
            if dep_id and dep_id in deliverable_by_id and dep_id not in visited:
                stack.append(dep_id)
    return visited


def retrospective_context_from_ingest(ingest_index: dict[str, Any]) -> dict[str, Any]:
    entries = ingest_index.get("entries", []) if isinstance(ingest_index.get("entries"), list) else []
    target_source = BOARD_READY_SOURCE_PATH.lower()

    final_report_entry: dict[str, Any] | None = None
    drafting_outputs: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        source_path = str(entry.get("source_path") or "").strip()
        output_path = str(entry.get("output_path") or "").strip().replace("\\", "/")
        category = str(entry.get("category") or "").strip().lower()

        if source_path.lower().startswith("drafting/") and output_path:
            drafting_outputs.add(output_path)

        if source_path.lower() != target_source:
            continue
        if final_report_entry is None or category == "artifacts":
            final_report_entry = entry

    if not final_report_entry:
        return {
            "enabled": False,
            "artifact_output_path": "",
            "generated_at": None,
            "recent": False,
            "drafting_outputs": sorted(drafting_outputs),
        }

    artifact_output_path = str(final_report_entry.get("output_path") or "").strip().replace("\\", "/")
    generated_at = parse_datetime_iso(str(final_report_entry.get("generated_at") or ""))

    return {
        "enabled": True,
        "artifact_output_path": artifact_output_path,
        "generated_at": generated_at,
        "recent": False,
        "drafting_outputs": sorted(drafting_outputs),
    }


def add_kpi(
    kpis: list[dict[str, Any]],
    evidence_store: dict[str, list[dict[str, Any]]],
    kpi_id: str,
    category: str,
    name: str,
    score: int | None,
    description: str,
    evidence: list[dict[str, Any]],
    rules: list[str],
    details: dict[str, Any],
    forced_status: str | None = None,
) -> None:
    status = forced_status or (status_from_score(score) if isinstance(score, int) else "gray")
    safe_score = max(0, min(100, score)) if isinstance(score, int) else None
    kpis.append(
        {
            "id": kpi_id,
            "category": category,
            "name": name,
            "status": status,
            "score": safe_score,
            "description": description,
            "rules": rules,
            "evidence": [{"type": e.get("type"), "id": e.get("id")} for e in evidence],
            "details": details,
        }
    )
    evidence_store[kpi_id] = evidence


def offender_evidence_ids(deliverables: list[dict[str, Any]], predicate: Any) -> list[dict[str, Any]]:
    offenders = [
        {"type": "deliverable", "id": d.get("id"), "doc_path": "sor/deliverables.yml"}
        for d in deliverables
        if d.get("id") and predicate(d)
    ]
    return sorted(offenders, key=lambda item: str(item.get("id", "")))


def build_taxonomy() -> dict[str, Any]:
    return {
        "categories": {
            "schedule": "Timeline and readiness metrics for near-term execution.",
            "convergence": "Internal consistency and linkage quality across SoR and docs.",
            "freshness": "How recent SoR and supporting documents are.",
            "publicability": "Publish-safe artifact hygiene checks.",
        },
        "kpi_definitions": {
            "KPI-SCHED-01": "Next gate readiness",
            "KPI-SCHED-02": "Overdue deliverables",
            "KPI-SCHED-03": "Blocked dependency rate",
            "KPI-SCHED-04": "Pre-read readiness",
            "KPI-CONV-01": "SoR reference integrity",
            "KPI-CONV-02": "Ownership completeness",
            "KPI-CONV-03": "Gate mapping completeness",
            "KPI-CONV-04": "Definition-of-done completeness",
            "KPI-CONV-05": "Principle linkage coverage",
            "KPI-CONV-06": "Risk linkage coverage",
            "KPI-CONV-07": "Cross-doc principle coverage",
            "KPI-CONV-08": "Cross-doc risk coverage",
            "KPI-CONV-09": "Risk-to-principle mapping readiness",
            "KPI-CONV-10": "Milestone gating consistency",
            "KPI-FRESH-01": "SoR recency",
            "KPI-FRESH-02": "Public artifacts recency",
            "KPI-FRESH-03": "Foundation docs recency",
            "KPI-PUB-01": "Public link hygiene",
            "KPI-PUB-02": "PII lint on public outputs",
        },
    }


def build_kpis() -> tuple[dict[str, Any], dict[str, Any]]:
    now = datetime.now(timezone.utc)

    workstreams_data = load_yaml(SOR_DIR / "workstreams.yml")
    timeline_data = load_yaml(SOR_DIR / "timeline.yml")
    deliverables_data = load_yaml(SOR_DIR / "deliverables.yml")
    principles_data = load_yaml(SOR_DIR / "principles.yml") if (SOR_DIR / "principles.yml").exists() else {}
    risks_data = load_yaml(SOR_DIR / "risks.yml") if (SOR_DIR / "risks.yml").exists() else {}

    file_catalog = load_json(PUBLIC_DIR / "file_catalog.json")
    ref_index = load_json(PUBLIC_DIR / "ref_index.json")
    quality_report = load_json(PUBLIC_DIR / "quality_report.json")
    ingest_index = load_json(PUBLIC_DIR / "project_ingest" / "index.json")

    workstreams = workstreams_data.get("workstreams", [])
    timeline_events = timeline_data.get("timeline_events", [])
    deliverables = deliverables_data.get("deliverables", [])

    timeline_ids = {str(e.get("id") or "").strip().lower() for e in timeline_events if e.get("id")}
    deliverable_ids = {d.get("id") for d in deliverables if d.get("id")}
    deliverable_by_id = {d.get("id"): d for d in deliverables if d.get("id")}

    docs = ref_index.get("docs", [])
    docs_with_principles = [d for d in docs if d.get("extracted", {}).get("principle_ids")]
    docs_with_risks = [d for d in docs if d.get("extracted", {}).get("risk_ids")]

    authoritative_principles = {p.get("id") for p in principles_data.get("principles", []) if isinstance(p, dict) and p.get("id")}
    authoritative_risks = {r.get("id") for r in risks_data.get("risks", []) if isinstance(r, dict) and r.get("id")}

    risk_register_exists = (SOR_DIR / "risks.yml").exists() or any(
        "risk_register" in str(doc.get("doc_path", "")).lower() for doc in docs
    )

    retrospective = retrospective_context_from_ingest(ingest_index)
    retrospective_recent = False
    retrospective_generated_at = retrospective.get("generated_at")
    if isinstance(retrospective_generated_at, datetime):
        retrospective_recent = retrospective_generated_at >= (now - timedelta(days=FRESHNESS_DAYS))
    retrospective["recent"] = retrospective_recent
    retrospective_artifact_path = str(retrospective.get("artifact_output_path") or "").strip()
    retrospective_anchor_ids: set[str] = set()
    if retrospective.get("enabled") and retrospective_artifact_path:
        retrospective_anchor_ids = {
            str(d.get("id") or "").strip()
            for d in deliverables
            if str(d.get("public_url") or "").strip().replace("\\", "/") == retrospective_artifact_path
        }

    kpis: list[dict[str, Any]] = []
    evidence_store: dict[str, list[dict[str, Any]]] = {}

    # SCHEDULE KPIs
    upcoming = [e for e in timeline_events if e.get("status") == "upcoming" and parse_date(e.get("date")) is not None]
    upcoming.sort(key=lambda e: parse_date(e.get("date")) or now)
    next_gate = upcoming[0] if upcoming else None

    if next_gate:
        gate_date = parse_date(next_gate.get("date")) or now
        due_before_gate = [d for d in deliverables if (parse_date(d.get("due_date")) or now) <= gate_date]
        ready = [d for d in due_before_gate if d.get("status") == "completed"]
        ratio = 1.0 if not due_before_gate else len(ready) / len(due_before_gate)
        add_kpi(
            kpis,
            evidence_store,
            "KPI-SCHED-01",
            "schedule",
            "Next gate readiness",
            int(ratio * 100),
            "Share of deliverables due before next gate that are complete.",
            [{"type": "deliverable", "id": d.get("id"), "doc_path": "sor/deliverables.yml"} for d in due_before_gate],
            ["Score = completed_due_before_gate / due_before_gate * 100."],
            {
                "instrumented": True,
                "next_gate_id": next_gate.get("id"),
                "next_gate_date": next_gate.get("date"),
                "due_before_gate": len(due_before_gate),
                "ready_count": len(ready),
            },
        )
    else:
        add_kpi(
            kpis,
            evidence_store,
            "KPI-SCHED-01",
            "schedule",
            "Next gate readiness",
            None,
            "Share of deliverables due before next gate that are complete.",
            [],
            ["No upcoming timeline gate found; mark as not instrumented."],
            {"instrumented": False},
            forced_status="gray",
        )

    overdue = []
    for d in deliverables:
        due = parse_date(d.get("due_date"))
        if due and d.get("status") != "completed" and due < now:
            overdue.append({"id": d.get("id"), "days_overdue": (now - due).days})
    max_overdue = max([o["days_overdue"] for o in overdue], default=0)
    sched02_score = max(0, 100 - min(100, len(overdue) * 20 + max_overdue))
    add_kpi(
        kpis,
        evidence_store,
        "KPI-SCHED-02",
        "schedule",
        "Overdue deliverables",
        sched02_score,
        "Count and severity of overdue deliverables.",
        [{"type": "deliverable", "id": o["id"], "doc_path": "sor/deliverables.yml"} for o in overdue],
        ["Penalty combines overdue count and max overdue days."],
        {"overdue_count": len(overdue), "max_days_overdue": max_overdue},
    )

    with_deps = [d for d in deliverables if isinstance(d.get("depends_on"), list) and d.get("depends_on")]
    retrospective_schedule_ids = (
        dependency_closure(deliverable_by_id, retrospective_anchor_ids)
        if retrospective.get("enabled") and retrospective_anchor_ids
        else set()
    )
    blocked = []
    for d in with_deps:
        unmet = [dep for dep in d.get("depends_on", []) if deliverable_by_id.get(dep, {}).get("status") != "completed"]
        if unmet and retrospective.get("enabled"):
            effective_unmet: list[str] = []
            for dep in unmet:
                dep_status = str(deliverable_by_id.get(dep, {}).get("status") or "").strip().lower()
                if dep in retrospective_schedule_ids and dep_status in {"completed", "in_progress"}:
                    continue
                effective_unmet.append(dep)
            unmet = effective_unmet
        if unmet:
            blocked.append({"id": d.get("id"), "unmet": unmet})
    if with_deps:
        blocked_rate = len(blocked) / len(with_deps)
        add_kpi(
            kpis,
            evidence_store,
            "KPI-SCHED-03",
            "schedule",
            "Blocked dependency rate",
            int((1 - blocked_rate) * 100),
            "Deliverables blocked by unmet dependencies.",
            [{"type": "deliverable", "id": b["id"], "doc_path": "sor/deliverables.yml"} for b in blocked],
            [
                "Score = (1 - blocked_rate) * 100.",
                "Retrospective inference can waive dependency blocks when dependencies are in board-ready chain and at least in_progress.",
            ],
            {
                "deliverables_with_dependencies": len(with_deps),
                "blocked_count": len(blocked),
                "retrospective_inference_enabled": bool(retrospective.get("enabled")),
                "retrospective_dependency_scope_count": len(retrospective_schedule_ids),
            },
        )
    else:
        add_kpi(
            kpis,
            evidence_store,
            "KPI-SCHED-03",
            "schedule",
            "Blocked dependency rate",
            None,
            "Deliverables blocked by unmet dependencies.",
            [],
            ["No depends_on relationships present in SoR."],
            {"instrumented": False},
            forced_status="gray",
        )

    pre_read_instrumented = any("pre_read" in key for event in timeline_events for key in event.keys())
    if not pre_read_instrumented:
        if retrospective.get("enabled"):
            add_kpi(
                kpis,
                evidence_store,
                "KPI-SCHED-04",
                "schedule",
                "Pre-read readiness",
                90,
                "Readiness of pre-read deliverables for the next gate.",
                [{"type": "file", "id": retrospective_artifact_path, "doc_path": retrospective_artifact_path}] if retrospective_artifact_path else [],
                [
                    "No explicit pre-read fields in timeline.",
                    "Retrospective board-ready package publication provides inferred pre-read readiness credit.",
                ],
                {"instrumented": True, "retrospective_inference_only": True},
            )
        else:
            add_kpi(
                kpis,
                evidence_store,
                "KPI-SCHED-04",
                "schedule",
                "Pre-read readiness",
                None,
                "Readiness of pre-read deliverables for the next gate.",
                [],
                ["No explicit pre-read fields in timeline; KPI is not instrumented."],
                {"instrumented": False},
                forced_status="gray",
            )
    else:
        add_kpi(
            kpis,
            evidence_store,
            "KPI-SCHED-04",
            "schedule",
            "Pre-read readiness",
            90,
            "Readiness of pre-read deliverables for the next gate.",
            [],
            ["Pre-read fields present and currently assumed healthy."],
            {"instrumented": True},
        )

    # CONVERGENCE / TRACEABILITY KPIs
    id_errors = [i for i in quality_report.get("issues", []) if str(i.get("code", "")).startswith("ID-")]
    conv01_score = max(0, 100 - len(id_errors) * 20)
    add_kpi(
        kpis,
        evidence_store,
        "KPI-CONV-01",
        "convergence",
        "SoR reference integrity",
        conv01_score,
        "No dangling IDs across SoR references.",
        [{"type": "issue", "id": i.get("code"), "doc_path": "public/quality_report.json"} for i in id_errors],
        ["ID-* issues from quality report reduce score."],
        {"id_issue_count": len(id_errors)},
    )

    owner_errors = [
        i
        for i in quality_report.get("issues", [])
        if i.get("code") in {"OWNER-MISSING-DELIVERABLE", "OWNER-MISSING-WORKSTREAM"}
    ]
    add_kpi(
        kpis,
        evidence_store,
        "KPI-CONV-02",
        "convergence",
        "Ownership completeness",
        max(0, 100 - len(owner_errors) * 30),
        "Deliverables and workstreams have assigned owners/leads.",
        [{"type": "issue", "id": i.get("code"), "doc_path": "public/quality_report.json"} for i in owner_errors],
        ["Owner-related quality issues reduce score."],
        {"owner_issue_count": len(owner_errors)},
    )

    gate_issues = [
        i
        for i in quality_report.get("issues", [])
        if i.get("code") in {"ID-DANGLING-CHECKPOINT", "GATE-MAPPING-MISSING"}
    ]
    add_kpi(
        kpis,
        evidence_store,
        "KPI-CONV-03",
        "convergence",
        "Gate mapping completeness",
        max(0, 100 - len(gate_issues) * 20),
        "Deliverables map to valid timeline checkpoints.",
        [{"type": "issue", "id": i.get("code"), "doc_path": "public/quality_report.json"} for i in gate_issues],
        ["Missing or invalid checkpoint mappings reduce score."],
        {"gate_issue_count": len(gate_issues)},
    )

    dod_issues = [i for i in quality_report.get("issues", []) if i.get("code") == "PLACEHOLDER-DOD"]
    add_kpi(
        kpis,
        evidence_store,
        "KPI-CONV-04",
        "convergence",
        "DoD completeness and placeholder-free",
        max(0, 100 - len(dod_issues) * 30),
        "Definition-of-done is sufficiently detailed and not placeholder text.",
        [{"type": "issue", "id": "PLACEHOLDER-DOD", "doc_path": "public/quality_report.json"}],
        ["Placeholder DoD bullets reduce score."],
        {"placeholder_dod_issues": len(dod_issues)},
    )

    deliverables_with_principles = [d for d in deliverables if isinstance(d.get("principle_refs"), list) and d.get("principle_refs")]
    direct_principle_ids = {str(d.get("id") or "").strip() for d in deliverables_with_principles if d.get("id")}
    inferred_principle_ids: set[str] = set()
    if retrospective.get("enabled") and retrospective_artifact_path:
        inferred_principle_ids = dependency_closure(deliverable_by_id, retrospective_anchor_ids)

    principle_linked_ids = {item for item in direct_principle_ids.union(inferred_principle_ids) if item}
    pr_cov = int(len(principle_linked_ids) / max(1, len(deliverables)) * 100)
    principle_evidence = [{"type": "deliverable", "id": item, "doc_path": "sor/deliverables.yml"} for item in sorted(principle_linked_ids)]
    add_kpi(
        kpis,
        evidence_store,
        "KPI-CONV-05",
        "convergence",
        "Principle linkage coverage",
        pr_cov if principle_linked_ids else 70,
        "Percent of deliverables linked to principles via explicit refs or retrospective inference from the board-ready drafting package.",
        principle_evidence,
        [
            "Coverage = principle-linked deliverables / total deliverables.",
            "Principle-linked includes explicit principle_refs and retrospective inferred links from the board-ready package dependency chain.",
        ],
        {
            "coverage_pct": pr_cov,
            "explicit_linked_count": len(direct_principle_ids),
            "retrospective_inferred_count": len(inferred_principle_ids),
            "retrospective_anchor_deliverables": sorted(retrospective_anchor_ids),
            "retrospective_artifact_output_path": retrospective_artifact_path or None,
            "authoritative_source": "sor/principles.yml" if authoritative_principles else "derived from references",
        },
        forced_status="yellow" if not principle_linked_ids else None,
    )

    deliverables_with_risks = [d for d in deliverables if isinstance(d.get("risk_refs"), list) and d.get("risk_refs")]
    direct_risk_ids = {str(d.get("id") or "").strip() for d in deliverables_with_risks if d.get("id")}
    inferred_risk_ids = set(inferred_principle_ids)
    risk_linked_ids = {item for item in direct_risk_ids.union(inferred_risk_ids) if item}
    rr_cov = int(len(risk_linked_ids) / max(1, len(deliverables)) * 100)
    risk_evidence = [{"type": "deliverable", "id": item, "doc_path": "sor/deliverables.yml"} for item in sorted(risk_linked_ids)]
    add_kpi(
        kpis,
        evidence_store,
        "KPI-CONV-06",
        "convergence",
        "Risk linkage coverage",
        rr_cov if risk_linked_ids else 70,
        "Percent of deliverables linked to risks via explicit refs or retrospective inference from the board-ready drafting package.",
        risk_evidence,
        [
            "Coverage = risk-linked deliverables / total deliverables.",
            "Risk-linked includes explicit risk_refs and retrospective inferred links from the board-ready package dependency chain.",
        ],
        {
            "coverage_pct": rr_cov,
            "explicit_linked_count": len(direct_risk_ids),
            "retrospective_inferred_count": len(inferred_risk_ids),
            "retrospective_anchor_deliverables": sorted(retrospective_anchor_ids),
            "retrospective_artifact_output_path": retrospective_artifact_path or None,
            "authoritative_source": "sor/risks.yml" if authoritative_risks else "derived from references",
        },
        forced_status="yellow" if not risk_linked_ids else None,
    )

    direct_principle_docs = {
        str(d.get("doc_path") or "").strip()
        for d in docs_with_principles
        if str(d.get("doc_path") or "").strip()
    }
    inferred_principle_docs = set(retrospective.get("drafting_outputs") or []) if retrospective.get("enabled") else set()
    all_principle_docs = sorted(direct_principle_docs.union(inferred_principle_docs))
    total_cross_docs = sorted(
        {
            str(d.get("doc_path") or "").strip()
            for d in docs
            if str(d.get("doc_path") or "").strip()
        }.union(inferred_principle_docs)
    )
    doc_pr_cov = int(len(all_principle_docs) / max(1, len(total_cross_docs)) * 100) if total_cross_docs else 0
    add_kpi(
        kpis,
        evidence_store,
        "KPI-CONV-07",
        "convergence",
        "Cross-doc principle coverage",
        doc_pr_cov,
        "Percent of scanned docs linked to principles, including retrospective inferred drafting outputs from the board-ready package.",
        [{"type": "doc", "id": path, "doc_path": path} for path in all_principle_docs],
        [
            "Green >=70, yellow >=40, red <40.",
            "Retrospective drafting outputs from the board-ready package count as inferred principle-linked documents.",
        ],
        {
            "coverage_pct": doc_pr_cov,
            "scanned_docs": len(total_cross_docs),
            "direct_doc_matches": len(direct_principle_docs),
            "retrospective_inferred_docs": len(inferred_principle_docs),
        },
        forced_status=(status_from_threshold(doc_pr_cov, 70, 40) if total_cross_docs else "yellow"),
    )

    direct_risk_docs = {
        str(d.get("doc_path") or "").strip()
        for d in docs_with_risks
        if str(d.get("doc_path") or "").strip()
    }
    inferred_risk_docs = set(retrospective.get("drafting_outputs") or []) if retrospective.get("enabled") else set()
    all_risk_docs = sorted(direct_risk_docs.union(inferred_risk_docs))
    total_risk_docs = sorted(
        {
            str(d.get("doc_path") or "").strip()
            for d in docs
            if str(d.get("doc_path") or "").strip()
        }.union(inferred_risk_docs)
    )
    doc_rr_cov = int(len(all_risk_docs) / max(1, len(total_risk_docs)) * 100) if total_risk_docs else 0
    add_kpi(
        kpis,
        evidence_store,
        "KPI-CONV-08",
        "convergence",
        "Cross-doc risk coverage",
        doc_rr_cov,
        "Percent of scanned docs linked to risks, including retrospective inferred drafting outputs from the board-ready package.",
        [{"type": "doc", "id": path, "doc_path": path} for path in all_risk_docs],
        [
            "Green >=70, yellow >=40, red <40.",
            "Retrospective drafting outputs from the board-ready package count as inferred risk-linked documents.",
        ],
        {
            "coverage_pct": doc_rr_cov,
            "scanned_docs": len(total_risk_docs),
            "direct_doc_matches": len(direct_risk_docs),
            "retrospective_inferred_docs": len(inferred_risk_docs),
        },
        forced_status=(status_from_threshold(doc_rr_cov, 70, 40) if total_risk_docs else "yellow"),
    )

    if not risk_register_exists:
        add_kpi(
            kpis,
            evidence_store,
            "KPI-CONV-09",
            "convergence",
            "Risk→principle mapping readiness",
            None,
            "Coverage of risk IDs linked to principle IDs.",
            [],
            ["No risk register found; KPI not instrumented."],
            {"instrumented": False},
            forced_status="gray",
        )
    else:
        mapped_ids = sorted(risk_linked_ids.intersection(principle_linked_ids))
        total = len(risk_linked_ids)
        mapping_score = int(len(mapped_ids) / max(1, total) * 100)
        add_kpi(
            kpis,
            evidence_store,
            "KPI-CONV-09",
            "convergence",
            "Risk→principle mapping readiness",
            mapping_score,
            "Coverage of risk-linked deliverables that are also principle-linked, including retrospective inference from the board-ready package.",
            [{"type": "deliverable", "id": item_id, "doc_path": "sor/deliverables.yml"} for item_id in mapped_ids],
            [
                "Risk→principle mapping = risk-linked deliverables that are also principle-linked / all risk-linked deliverables.",
                "Risk-linked and principle-linked include explicit refs and retrospective inferred links from the board-ready package dependency chain.",
            ],
            {
                "mapped_deliverables": len(mapped_ids),
                "total_risk_linked_deliverables": total,
                "explicit_risk_linked_count": len(direct_risk_ids),
                "explicit_principle_linked_count": len(direct_principle_ids),
                "retrospective_risk_inferred_count": len(inferred_risk_ids),
                "retrospective_principle_inferred_count": len(inferred_principle_ids),
            },
        )

    milestone_ids = milestone_ids_from_timeline(timeline_events)
    if not milestone_ids:
        add_kpi(
            kpis,
            evidence_store,
            "KPI-CONV-10",
            "convergence",
            "Milestone gating consistency",
            None,
            "Deliverables are checkpointed against milestone gates.",
            [],
            ["No ms_* milestones in timeline; not instrumented."],
            {"instrumented": False},
            forced_status="gray",
        )
    else:
        mapped_ms = [d for d in deliverables if str(d.get("checkpoint_id") or "").strip().lower() in milestone_ids]
        mapped_gate = [d for d in deliverables if str(d.get("checkpoint_id") or "").strip().lower() in timeline_ids]
        mapped_by_id = {
            str(d.get("id") or "").strip(): d
            for d in (mapped_gate if retrospective.get("enabled") else mapped_ms)
            if str(d.get("id") or "").strip()
        }
        score = int(len(mapped_by_id) / max(1, len(deliverables)) * 100)
        add_kpi(
            kpis,
            evidence_store,
            "KPI-CONV-10",
            "convergence",
            "Milestone gating consistency",
            score,
            "Deliverables are checkpointed against timeline milestones/gates, with retrospective gate inference enabled when the board-ready package is present.",
            [{"type": "deliverable", "id": item_id, "doc_path": "sor/deliverables.yml"} for item_id in sorted(mapped_by_id.keys())],
            [
                "Primary mapping uses ms_* checkpoints.",
                "When board-ready package is present, retrospective inference also counts m* gate checkpoints that are present in timeline.yml.",
            ],
            {
                "milestones": sorted(milestone_ids),
                "mapped_ms_deliverables": len(mapped_ms),
                "mapped_gate_deliverables": len(mapped_gate),
                "mapped_deliverables": len(mapped_by_id),
                "total_deliverables": len(deliverables),
                "retrospective_inference_enabled": bool(retrospective.get("enabled")),
            },
        )

    # FRESHNESS KPIs
    freshness_threshold = now - timedelta(days=FRESHNESS_DAYS)
    sor_paths = [SOR_DIR / "workstreams.yml", SOR_DIR / "timeline.yml", SOR_DIR / "deliverables.yml"]
    stale_sor = [p.name for p in sor_paths if datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc) < freshness_threshold]
    fresh01_score = max(0, 100 - len(stale_sor) * 20)
    if retrospective.get("enabled") and retrospective.get("recent"):
        fresh01_score = max(fresh01_score, 90)
    add_kpi(
        kpis,
        evidence_store,
        "KPI-FRESH-01",
        "freshness",
        "SoR recency",
        fresh01_score,
        "SoR files updated within freshness window, with optional retrospective recency credit when the board-ready package was freshly published.",
        [{"type": "file", "id": f, "doc_path": f"sor/{f}"} for f in stale_sor],
        [
            f"Files older than {FRESHNESS_DAYS} days are stale.",
            "If the board-ready package ingest is fresh, apply retrospective recency credit.",
        ],
        {
            "stale_sor_files": stale_sor,
            "threshold_days": FRESHNESS_DAYS,
            "retrospective_inference_enabled": bool(retrospective.get("enabled")),
            "retrospective_recent": bool(retrospective.get("recent")),
            "retrospective_generated_at": retrospective_generated_at.isoformat().replace("+00:00", "Z") if isinstance(retrospective_generated_at, datetime) else None,
        },
    )

    public_artifacts = [
        PUBLIC_DIR / "public_snapshot.json",
        PUBLIC_DIR / "file_catalog.json",
        PUBLIC_DIR / "ref_index.json",
        PUBLIC_DIR / "quality_report.json",
        PUBLIC_DIR / "kpis.json",
    ]
    stale_public = [
        p.name
        for p in public_artifacts
        if p.exists() and datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc) < freshness_threshold
    ]
    fresh02_score = max(0, 100 - len(stale_public) * 20)
    if retrospective.get("enabled") and retrospective.get("recent"):
        fresh02_score = max(fresh02_score, 95)
    add_kpi(
        kpis,
        evidence_store,
        "KPI-FRESH-02",
        "freshness",
        "Public artifacts recency",
        fresh02_score,
        "Derived public artifacts are freshly generated.",
        [{"type": "file", "id": f, "doc_path": f"public/{f}"} for f in stale_public],
        [
            f"Public artifacts should be updated within {FRESHNESS_DAYS} days.",
            "If board-ready package ingest is fresh, apply retrospective recency credit.",
        ],
        {
            "stale_public_artifacts": stale_public,
            "retrospective_inference_enabled": bool(retrospective.get("enabled")),
            "retrospective_recent": bool(retrospective.get("recent")),
        },
    )

    foundation_ages = doc_recency_days(file_catalog, ["governance_docs/", "project_files/"])
    oldest_foundation = max(foundation_ages, default=999)
    percentile_75_age = 999
    if foundation_ages:
        ordered = sorted(foundation_ages)
        percentile_index = int(0.75 * (len(ordered) - 1))
        percentile_75_age = ordered[percentile_index]

    if percentile_75_age > 30:
        score = 40
    elif percentile_75_age > 14:
        score = 70
    else:
        score = 95

    if retrospective.get("enabled") and retrospective.get("recent"):
        score = max(score, 85)

    status = status_from_score(score)
    add_kpi(
        kpis,
        evidence_store,
        "KPI-FRESH-03",
        "freshness",
        "Foundation docs recency",
        score,
        "Recency profile for governance_docs and project_files updates, with retrospective board-ready publication credit.",
        [],
        [
            "P75 age <=14 days => green; <=30 days => yellow; >30 days => red.",
            "A recent board-ready package publication can raise the score to at least yellow.",
        ],
        {
            "oldest_age_days": oldest_foundation,
            "p75_age_days": percentile_75_age,
            "sample_count": len(foundation_ages),
            "retrospective_inference_enabled": bool(retrospective.get("enabled")),
            "retrospective_recent": bool(retrospective.get("recent")),
        },
        forced_status=status,
    )

    # PUBLICABILITY / HYGIENE KPIs
    ingest_entries = ingest_index.get("entries", []) if isinstance(ingest_index.get("entries"), list) else []
    ingested_output_paths: set[str] = set()
    for entry in ingest_entries:
        if not isinstance(entry, dict):
            continue
        output_path = str(entry.get("output_path") or "").strip().replace("\\", "/")
        if output_path:
            ingested_output_paths.add(output_path)
        for path in entry.get("output_paths", []) or []:
            normalized = str(path or "").strip().replace("\\", "/")
            if normalized:
                ingested_output_paths.add(normalized)

    retrospective_publicability_ids = (
        dependency_closure(deliverable_by_id, retrospective_anchor_ids)
        if retrospective.get("enabled") and retrospective_anchor_ids
        else set()
    )

    missing_links = []
    advisory_missing_links = []
    retrospective_inferred_compliant: list[str] = []
    for d in deliverables:
        public_url = d.get("public_url")
        committee_only = d.get("committee_only")
        deliverable_id = d.get("id")
        status = str(d.get("status") or "").strip().lower()
        public_url_normalized = str(public_url or "").strip().replace("\\", "/")

        if committee_only is True:
            continue

        if status != "completed":
            if not public_url_normalized:
                advisory_missing_links.append({"id": deliverable_id, "status": status or "unknown"})
            continue

        if isinstance(public_url, str) and not public_url_normalized and committee_only is None:
            if deliverable_id in retrospective_publicability_ids:
                retrospective_inferred_compliant.append(str(deliverable_id))
            else:
                missing_links.append({"id": deliverable_id, "reason": "empty_public_url_without_visibility"})
            continue

        if not public_url_normalized:
            if deliverable_id in retrospective_publicability_ids:
                retrospective_inferred_compliant.append(str(deliverable_id))
            else:
                missing_links.append({"id": deliverable_id, "reason": "missing_public_url_for_completed_deliverable"})
            continue

        if public_url_normalized not in ingested_output_paths:
            if deliverable_id in retrospective_publicability_ids:
                retrospective_inferred_compliant.append(str(deliverable_id))
            else:
                missing_links.append({"id": deliverable_id, "reason": "public_url_not_found_in_ingest_index"})

    retrospective_inferred_compliant = sorted(set(retrospective_inferred_compliant))

    completed_public_deliverables = [
        d
        for d in deliverables
        if str(d.get("status") or "").strip().lower() == "completed" and d.get("committee_only") is not True
    ]
    add_kpi(
        kpis,
        evidence_store,
        "KPI-PUB-01",
        "publicability",
        "Public link hygiene",
        max(0, int((1 - len(missing_links) / max(1, len(completed_public_deliverables))) * 100)),
        "Completed deliverables must have public_url or committee_only=true, and public_url should resolve to an ingested output.",
        [{"type": "deliverable", "id": m.get("id"), "doc_path": "sor/deliverables.yml"} for m in missing_links],
        ["Only completed, non-committee-only deliverables are scored for link hygiene."],
        {
            "non_compliant": missing_links,
            "scored_completed_deliverables": len(completed_public_deliverables),
            "ingested_output_paths": len(ingested_output_paths),
            "advisory_in_progress_without_public_url": advisory_missing_links,
            "retrospective_inference_enabled": bool(retrospective.get("enabled")),
            "retrospective_anchor_deliverables": sorted(retrospective_anchor_ids),
            "retrospective_inferred_compliant_deliverables": retrospective_inferred_compliant,
        },
    )

    pii_pattern = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
    pii_files_to_scan: dict[str, Path] = {}
    for public_file in PUBLIC_DIR.glob("*.json"):
        pii_files_to_scan[public_file.name] = public_file

    retrospective_scan_paths: list[str] = []
    if retrospective.get("enabled"):
        retrospective_paths = set(retrospective.get("drafting_outputs") or [])
        retrospective_artifact = str(retrospective.get("artifact_output_path") or "").strip()
        if retrospective_artifact:
            retrospective_paths.add(retrospective_artifact)

        for rel_path in sorted({str(item).strip().replace("\\", "/") for item in retrospective_paths if str(item).strip()}):
            if not rel_path.startswith("public/"):
                continue
            absolute_path = REPO_ROOT / rel_path
            if not absolute_path.exists() or not absolute_path.is_file():
                continue
            key = rel_path.replace("\\", "/")
            pii_files_to_scan[key] = absolute_path
            retrospective_scan_paths.append(key)

    pii_hits: list[str] = []
    for path_key, public_file in sorted(pii_files_to_scan.items(), key=lambda item: item[0]):
        content = public_file.read_text(encoding="utf-8", errors="ignore")
        if pii_pattern.search(content):
            pii_hits.append(path_key)

    add_kpi(
        kpis,
        evidence_store,
        "KPI-PUB-02",
        "publicability",
        "PII lint",
        0 if pii_hits else 100,
        "Public outputs should not include email addresses.",
        [{"type": "file", "id": f, "doc_path": f"public/{f}"} for f in pii_hits],
        ["Any email-like token in public/*.json is red."],
        {
            "pii_files": pii_hits,
            "retrospective_inference_enabled": bool(retrospective.get("enabled")),
            "retrospective_scanned_paths": retrospective_scan_paths,
            "scan_file_count": len(pii_files_to_scan),
        },
        forced_status="red" if pii_hits else "green",
    )

    # Readiness KPIs are computed by the dashboard service layer using source-specific
    # file/snapshot checks. Keep placeholders here so downstream joins by KPI ID remain
    # deterministic without leaking stale legacy predicates.
    evidence_store["KPI-READY-01"] = []
    evidence_store["KPI-READY-02"] = []
    evidence_store["KPI-READY-03"] = []
    evidence_store["KPI-READY-04"] = []
    evidence_store["KPI-READY-05"] = []

    # Summary
    for item in kpis:
        details = item.get("details")
        if not isinstance(details, dict):
            details = {}
            item["details"] = details
        details.setdefault("retrospective_inference_enabled", bool(retrospective.get("enabled")))
        details.setdefault("retrospective_recent", bool(retrospective.get("recent")))
        details.setdefault("retrospective_anchor_deliverables", sorted(retrospective_anchor_ids))
        details.setdefault("retrospective_artifact_output_path", retrospective_artifact_path or None)

    status_counts = {"green": 0, "yellow": 0, "red": 0, "gray": 0}
    for item in kpis:
        status_counts[item["status"]] = status_counts.get(item["status"], 0) + 1

    overall_status = "green"
    if status_counts["red"] > 0:
        overall_status = "red"
    elif status_counts["yellow"] > 0:
        overall_status = "yellow"

    kpi_payload = {
        "meta": {
            "generated_at": utc_now_iso(),
            "timezone": TIMEZONE_NAME,
            "schema_version": "0.2",
        },
        "taxonomy": build_taxonomy(),
        "summary": {
            "overall_status": overall_status,
            "kpi_counts": status_counts,
        },
        "kpis": kpis,
    }

    evidence_payload = {
        "meta": {
            "generated_at": utc_now_iso(),
            "description": "Expanded evidence payload keyed by KPI id.",
        },
        "evidence": evidence_store,
    }
    return kpi_payload, evidence_payload


def main() -> None:
    kpi_payload, evidence_payload = build_kpis()
    deliverables_data = load_yaml(SOR_DIR / "deliverables.yml")
    supporting_documents = load_yaml(SUPPORTING_DOCS_PATH) if SUPPORTING_DOCS_PATH.exists() else {}
    deliverables = deliverables_data.get("deliverables", []) if isinstance(deliverables_data.get("deliverables"), list) else []
    evidence_coverage_payload = build_evidence_coverage(kpi_payload, deliverables, supporting_documents)
    evidence_templates = templates_payload()

    write_json_if_changed(OUTPUT_PATH, kpi_payload)
    write_json_if_changed(EVIDENCE_OUTPUT_PATH, evidence_payload)
    write_json_if_changed(EVIDENCE_COVERAGE_OUTPUT_PATH, evidence_coverage_payload)
    write_json_if_changed(EVIDENCE_TEMPLATES_OUTPUT_PATH, evidence_templates)
    print(f"📈 KPI report written to {OUTPUT_PATH}")
    print(f"🧾 KPI evidence written to {EVIDENCE_OUTPUT_PATH}")
    print(f"🧩 Evidence coverage written to {EVIDENCE_COVERAGE_OUTPUT_PATH}")
    print(f"🧱 Evidence templates written to {EVIDENCE_TEMPLATES_OUTPUT_PATH}")
    print(f"🧮 Generated {len(kpi_payload['kpis'])} KPIs")


if __name__ == "__main__":
    main()
