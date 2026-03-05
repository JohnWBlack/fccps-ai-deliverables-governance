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

    workstreams = workstreams_data.get("workstreams", [])
    timeline_events = timeline_data.get("timeline_events", [])
    deliverables = deliverables_data.get("deliverables", [])

    timeline_ids = {e.get("id") for e in timeline_events if e.get("id")}
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
    blocked = []
    for d in with_deps:
        unmet = [dep for dep in d.get("depends_on", []) if deliverable_by_id.get(dep, {}).get("status") != "completed"]
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
            ["Score = (1 - blocked_rate) * 100."],
            {"deliverables_with_dependencies": len(with_deps), "blocked_count": len(blocked)},
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
    pr_cov = int(len(deliverables_with_principles) / max(1, len(deliverables)) * 100)
    add_kpi(
        kpis,
        evidence_store,
        "KPI-CONV-05",
        "convergence",
        "Principle linkage coverage",
        pr_cov if deliverables_with_principles else 70,
        "Percent of deliverables with principle_refs.",
        [{"type": "deliverable", "id": d.get("id"), "doc_path": "sor/deliverables.yml"} for d in deliverables_with_principles],
        ["Coverage = deliverables with principle_refs / total deliverables."],
        {
            "coverage_pct": pr_cov,
            "authoritative_source": "sor/principles.yml" if authoritative_principles else "derived from references",
        },
        forced_status="yellow" if not deliverables_with_principles else None,
    )

    deliverables_with_risks = [d for d in deliverables if isinstance(d.get("risk_refs"), list) and d.get("risk_refs")]
    rr_cov = int(len(deliverables_with_risks) / max(1, len(deliverables)) * 100)
    add_kpi(
        kpis,
        evidence_store,
        "KPI-CONV-06",
        "convergence",
        "Risk linkage coverage",
        rr_cov if deliverables_with_risks else 70,
        "Percent of deliverables with risk_refs.",
        [{"type": "deliverable", "id": d.get("id"), "doc_path": "sor/deliverables.yml"} for d in deliverables_with_risks],
        ["Coverage = deliverables with risk_refs / total deliverables."],
        {
            "coverage_pct": rr_cov,
            "authoritative_source": "sor/risks.yml" if authoritative_risks else "derived from references",
        },
        forced_status="yellow" if not deliverables_with_risks else None,
    )

    doc_pr_cov = int(len(docs_with_principles) / max(1, len(docs)) * 100) if docs else 0
    add_kpi(
        kpis,
        evidence_store,
        "KPI-CONV-07",
        "convergence",
        "Cross-doc principle coverage",
        doc_pr_cov,
        "Percent of scanned docs that reference at least one principle ID.",
        [{"type": "doc", "id": d.get("doc_path"), "doc_path": d.get("doc_path")} for d in docs_with_principles],
        ["Green >=70, yellow >=40, red <40."],
        {"coverage_pct": doc_pr_cov, "scanned_docs": len(docs)},
        forced_status=(status_from_threshold(doc_pr_cov, 70, 40) if docs else "yellow"),
    )

    doc_rr_cov = int(len(docs_with_risks) / max(1, len(docs)) * 100) if docs else 0
    add_kpi(
        kpis,
        evidence_store,
        "KPI-CONV-08",
        "convergence",
        "Cross-doc risk coverage",
        doc_rr_cov,
        "Percent of scanned docs that reference at least one risk ID.",
        [{"type": "doc", "id": d.get("doc_path"), "doc_path": d.get("doc_path")} for d in docs_with_risks],
        ["Green >=70, yellow >=40, red <40."],
        {"coverage_pct": doc_rr_cov, "scanned_docs": len(docs)},
        forced_status=(status_from_threshold(doc_rr_cov, 70, 40) if docs else "yellow"),
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
        mapped = 0
        total = 0
        for d in deliverables:
            risks = d.get("risk_refs", []) or []
            if not risks:
                continue
            total += len(risks)
            if d.get("principle_refs"):
                mapped += len(risks)
        mapping_score = int(mapped / max(1, total) * 100)
        add_kpi(
            kpis,
            evidence_store,
            "KPI-CONV-09",
            "convergence",
            "Risk→principle mapping readiness",
            mapping_score,
            "Coverage of risk IDs linked to principle IDs.",
            [{"type": "deliverable", "id": d.get("id"), "doc_path": "sor/deliverables.yml"} for d in deliverables_with_risks],
            ["Risk refs are considered mapped when same deliverable has principle_refs."],
            {"mapped_risks": mapped, "total_risks": total},
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
        mapped = [d for d in deliverables if d.get("checkpoint_id") in milestone_ids]
        score = int(len(mapped) / max(1, len(deliverables)) * 100)
        add_kpi(
            kpis,
            evidence_store,
            "KPI-CONV-10",
            "convergence",
            "Milestone gating consistency",
            score,
            "Deliverables are checkpointed against milestone gates.",
            [{"type": "deliverable", "id": d.get("id"), "doc_path": "sor/deliverables.yml"} for d in mapped],
            ["Deliverables should be mapped to ms_* checkpoint IDs when applicable."],
            {"milestones": sorted(milestone_ids), "mapped_deliverables": len(mapped), "total_deliverables": len(deliverables)},
        )

    # FRESHNESS KPIs
    freshness_threshold = now - timedelta(days=FRESHNESS_DAYS)
    sor_paths = [SOR_DIR / "workstreams.yml", SOR_DIR / "timeline.yml", SOR_DIR / "deliverables.yml"]
    stale_sor = [p.name for p in sor_paths if datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc) < freshness_threshold]
    add_kpi(
        kpis,
        evidence_store,
        "KPI-FRESH-01",
        "freshness",
        "SoR recency",
        max(0, 100 - len(stale_sor) * 20),
        "SoR files updated within freshness window.",
        [{"type": "file", "id": f, "doc_path": f"sor/{f}"} for f in stale_sor],
        [f"Files older than {FRESHNESS_DAYS} days are stale."],
        {"stale_sor_files": stale_sor, "threshold_days": FRESHNESS_DAYS},
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
    add_kpi(
        kpis,
        evidence_store,
        "KPI-FRESH-02",
        "freshness",
        "Public artifacts recency",
        max(0, 100 - len(stale_public) * 20),
        "Derived public artifacts are freshly generated.",
        [{"type": "file", "id": f, "doc_path": f"public/{f}"} for f in stale_public],
        [f"Public artifacts should be updated within {FRESHNESS_DAYS} days."],
        {"stale_public_artifacts": stale_public},
    )

    foundation_ages = doc_recency_days(file_catalog, ["governance_docs/", "project_files/"])
    oldest_foundation = max(foundation_ages, default=999)
    if oldest_foundation > 30:
        status = "red"
        score = 40
    elif oldest_foundation > 14:
        status = "yellow"
        score = 70
    else:
        status = "green"
        score = 95
    add_kpi(
        kpis,
        evidence_store,
        "KPI-FRESH-03",
        "freshness",
        "Foundation docs recency",
        score,
        "Recency profile for governance_docs and project_files updates.",
        [],
        ["If no foundation docs updated in >14 days => yellow; >30 days => red."],
        {"oldest_age_days": oldest_foundation, "sample_count": len(foundation_ages)},
        forced_status=status,
    )

    # PUBLICABILITY / HYGIENE KPIs
    missing_links = []
    for d in deliverables:
        public_url = d.get("public_url")
        committee_only = d.get("committee_only")
        if isinstance(public_url, str) and not public_url.strip() and committee_only is None:
            missing_links.append({"id": d.get("id"), "reason": "empty_public_url_without_visibility"})
        elif not public_url and committee_only is not True:
            missing_links.append({"id": d.get("id"), "reason": "missing_public_url_or_committee_only"})
    add_kpi(
        kpis,
        evidence_store,
        "KPI-PUB-01",
        "publicability",
        "Public link hygiene",
        max(0, int((1 - len(missing_links) / max(1, len(deliverables))) * 100)),
        "Deliverables must have public_url or committee_only=true.",
        [{"type": "deliverable", "id": m.get("id"), "doc_path": "sor/deliverables.yml"} for m in missing_links],
        ["Missing visibility metadata reduces score."],
        {"non_compliant": missing_links},
    )

    pii_pattern = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
    pii_hits = []
    for public_file in PUBLIC_DIR.glob("*.json"):
        content = public_file.read_text(encoding="utf-8", errors="ignore")
        if pii_pattern.search(content):
            pii_hits.append(public_file.name)
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
        {"pii_files": pii_hits},
        forced_status="red" if pii_hits else "green",
    )

    evidence_store["KPI-READY-01"] = offender_evidence_ids(
        deliverables,
        lambda d: not d.get("checkpoint_id"),
    )
    evidence_store["KPI-READY-02"] = offender_evidence_ids(
        deliverables,
        lambda d: not d.get("assigned_to")
        and not (isinstance(d.get("owner"), dict) and str(d.get("owner", {}).get("name", "")).strip())
        and not d.get("owner")
        and not d.get("owners"),
    )
    evidence_store["KPI-READY-03"] = offender_evidence_ids(
        deliverables,
        lambda d: not (isinstance(d.get("principle_refs"), list) and d.get("principle_refs")),
    )
    evidence_store["KPI-READY-04"] = offender_evidence_ids(
        deliverables,
        lambda d: not (isinstance(d.get("risk_refs"), list) and d.get("risk_refs")),
    )
    evidence_store["KPI-READY-05"] = offender_evidence_ids(
        deliverables,
        lambda d: not d.get("public_url") and d.get("committee_only") is not True,
    )

    # Summary
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
