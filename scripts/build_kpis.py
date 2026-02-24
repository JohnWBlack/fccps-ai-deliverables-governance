#!/usr/bin/env python3
"""Build deterministic health KPIs for schedule and convergence."""

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
TIMEZONE_NAME = "America/New_York"
FRESHNESS_DAYS = 7


def load_yaml(path: Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def load_json(path: Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def status_from_score(score: int) -> str:
    if score >= 85:
        return "green"
    if score >= 60:
        return "yellow"
    return "red"


def add_kpi(
    kpis: list[dict[str, Any]],
    kpi_id: str,
    category: str,
    name: str,
    score: int,
    description: str,
    evidence: list[dict[str, str]],
    rules: list[str],
    details: dict[str, Any],
    forced_status: str | None = None,
) -> None:
    status = forced_status or status_from_score(score)
    kpis.append(
        {
            "id": kpi_id,
            "category": category,
            "name": name,
            "status": status,
            "score": max(0, min(100, score)),
            "description": description,
            "evidence": evidence,
            "rules": rules,
            "details": details,
        }
    )


def first_date_in_changelog(path: Path) -> datetime | None:
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8", errors="ignore")
    match = re.search(r"\[(\d{4}-\d{2}-\d{2})\]", text)
    if not match:
        return None
    return parse_date(match.group(1))


def build_kpis() -> dict[str, Any]:
    now = datetime.now(timezone.utc)

    workstreams_data = load_yaml(SOR_DIR / "workstreams.yml")
    timeline_data = load_yaml(SOR_DIR / "timeline.yml")
    deliverables_data = load_yaml(SOR_DIR / "deliverables.yml")
    file_catalog = load_json(PUBLIC_DIR / "file_catalog.json")

    workstreams = workstreams_data.get("workstreams", [])
    timeline_events = timeline_data.get("timeline_events", [])
    deliverables = deliverables_data.get("deliverables", [])

    workstream_ids = {w.get("id") for w in workstreams if w.get("id")}
    timeline_ids = {e.get("id") for e in timeline_events if e.get("id")}
    deliverable_ids = {d.get("id") for d in deliverables if d.get("id")}
    deliverable_by_id = {d.get("id"): d for d in deliverables if d.get("id")}

    kpis: list[dict[str, Any]] = []

    # KPI-SCHED-01: next gate readiness
    upcoming = [
        e for e in timeline_events if e.get("status") == "upcoming" and parse_date(e.get("date")) is not None
    ]
    upcoming.sort(key=lambda item: parse_date(item.get("date")) or now)
    next_meeting = upcoming[0] if upcoming else None

    if not next_meeting:
        add_kpi(
            kpis,
            "KPI-SCHED-01",
            "schedule",
            "Meeting gate readiness",
            70,
            "Are next-meeting inputs on track by pre-read deadline?",
            [],
            ["If no upcoming meeting exists in timeline, report yellow pending schedule instrumentation."],
            {"next_meeting": None, "ready_deliverables": 0, "total_due_before_meeting": 0},
            forced_status="yellow",
        )
    else:
        next_date = parse_date(next_meeting.get("date")) or now
        due_before = [d for d in deliverables if (parse_date(d.get("due_date")) or now) <= next_date]
        ready = [d for d in due_before if d.get("status") == "completed"]
        ratio = 1.0 if not due_before else len(ready) / len(due_before)
        score = int(ratio * 100)
        add_kpi(
            kpis,
            "KPI-SCHED-01",
            "schedule",
            "Meeting gate readiness",
            score,
            "Are next-meeting inputs on track by pre-read deadline?",
            [{"type": "timeline_event", "id": str(next_meeting.get("id", "unknown"))}],
            [
                "Deliverables due on/before next upcoming meeting date should be completed.",
                "Score is completion ratio x 100.",
            ],
            {
                "next_meeting": {
                    "id": next_meeting.get("id"),
                    "date": next_meeting.get("date"),
                    "title": next_meeting.get("title"),
                },
                "ready_deliverables": len(ready),
                "total_due_before_meeting": len(due_before),
            },
        )

    # KPI-SCHED-02: overdue deliverables
    overdue = []
    for d in deliverables:
        due = parse_date(d.get("due_date"))
        if due and d.get("status") != "completed" and due < now:
            overdue.append({"id": d.get("id"), "days_overdue": (now - due).days})
    max_days = max([item["days_overdue"] for item in overdue], default=0)
    score = max(0, 100 - min(100, len(overdue) * 20 + max_days))
    add_kpi(
        kpis,
        "KPI-SCHED-02",
        "schedule",
        "Overdue deliverables",
        score,
        "Count and severity of overdue deliverables.",
        [{"type": "deliverable", "id": str(item["id"])} for item in overdue],
        [
            "Deliverables past due and not completed are overdue.",
            "Score decays with overdue count and max overdue days.",
        ],
        {"overdue_count": len(overdue), "max_days_overdue": max_days, "items": overdue},
    )

    # KPI-SCHED-03: blocked-by-dependency rate
    with_deps = []
    blocked = []
    for d in deliverables:
        deps = d.get("depends_on", [])
        if isinstance(deps, list) and deps:
            with_deps.append(d)
            unmet = [dep for dep in deps if deliverable_by_id.get(dep, {}).get("status") != "completed"]
            if unmet:
                blocked.append({"id": d.get("id"), "unmet_dependencies": unmet})
    if not with_deps:
        add_kpi(
            kpis,
            "KPI-SCHED-03",
            "schedule",
            "Blocked-by-dependency rate",
            70,
            "Rate of deliverables blocked by unmet dependencies.",
            [],
            ["If no depends_on fields are present, KPI is yellow (not yet instrumented)."],
            {"instrumented": False, "blocked_count": 0, "deliverables_with_dependencies": 0},
            forced_status="yellow",
        )
    else:
        blocked_rate = len(blocked) / len(with_deps)
        score = int((1 - blocked_rate) * 100)
        add_kpi(
            kpis,
            "KPI-SCHED-03",
            "schedule",
            "Blocked-by-dependency rate",
            score,
            "Rate of deliverables blocked by unmet dependencies.",
            [{"type": "deliverable", "id": str(item["id"])} for item in blocked],
            ["Deliverables with unmet depends_on IDs are blocked.", "Score is (1 - blocked_rate) x 100."],
            {
                "instrumented": True,
                "blocked_count": len(blocked),
                "deliverables_with_dependencies": len(with_deps),
                "blocked_items": blocked,
            },
        )

    # KPI-CONV-01: ID integrity across references
    dangling = []
    for e in timeline_events:
        if e.get("deliverable_id") and e["deliverable_id"] not in deliverable_ids:
            dangling.append({"source": "timeline", "source_id": e.get("id"), "missing": e["deliverable_id"]})
        if isinstance(e.get("deliverable_ids"), list):
            for did in e["deliverable_ids"]:
                if did not in deliverable_ids:
                    dangling.append({"source": "timeline", "source_id": e.get("id"), "missing": did})
    for w in workstreams:
        if isinstance(w.get("deliverable_ids"), list):
            for did in w["deliverable_ids"]:
                if did not in deliverable_ids:
                    dangling.append({"source": "workstream", "source_id": w.get("id"), "missing": did})
    score = 100 if not dangling else max(0, 100 - len(dangling) * 20)
    add_kpi(
        kpis,
        "KPI-CONV-01",
        "convergence",
        "ID integrity",
        score,
        "No dangling deliverable references across SoR files.",
        [{"type": item["source"], "id": str(item["source_id"])} for item in dangling],
        ["All referenced deliverable IDs must exist in sor/deliverables.yml."],
        {"dangling_references": dangling, "dangling_count": len(dangling)},
    )

    # KPI-CONV-02: Ownership completeness
    missing_owners = []
    unknown_name_tokens = {"tbd", "unknown", "later", "n/a"}
    unknown_owners = []
    for d in deliverables:
        owners = d.get("owners") if isinstance(d.get("owners"), list) else [d.get("assigned_to")]
        owners = [o for o in owners if o]
        if not owners:
            missing_owners.append(d.get("id"))
        for owner in owners:
            if str(owner).strip().lower() in unknown_name_tokens:
                unknown_owners.append({"id": d.get("id"), "owner": owner})

    missing_leads = []
    for w in workstreams:
        lead = w.get("lead")
        if not lead:
            missing_leads.append(w.get("id"))
        elif str(lead).strip().lower() in unknown_name_tokens:
            unknown_owners.append({"id": w.get("id"), "owner": lead})

    penalties = len(missing_owners) * 20 + len(missing_leads) * 20 + len(unknown_owners) * 10
    score = max(0, 100 - penalties)
    add_kpi(
        kpis,
        "KPI-CONV-02",
        "convergence",
        "Ownership completeness",
        score,
        "Deliverables and workstreams have explicit, non-placeholder ownership.",
        [{"type": "deliverable", "id": str(i)} for i in missing_owners],
        [
            "Each deliverable needs at least one owner (owners[] or assigned_to).",
            "Each workstream must have a lead (co-lead optional).",
        ],
        {
            "missing_deliverable_owners": missing_owners,
            "missing_workstream_leads": missing_leads,
            "unknown_owner_values": unknown_owners,
        },
    )

    # KPI-CONV-03: checkpoint mapping
    with_checkpoint = [d for d in deliverables if d.get("checkpoint_id")]
    if not with_checkpoint:
        add_kpi(
            kpis,
            "KPI-CONV-03",
            "convergence",
            "Gate mapping completeness",
            70,
            "Deliverables map to valid timeline checkpoints.",
            [],
            ["If checkpoint_id is absent, report yellow as not yet instrumented."],
            {"instrumented": False, "mapped": 0, "total_deliverables": len(deliverables)},
            forced_status="yellow",
        )
    else:
        invalid = [d.get("id") for d in with_checkpoint if d.get("checkpoint_id") not in timeline_ids]
        score = int((1 - (len(invalid) / len(deliverables or [1]))) * 100)
        add_kpi(
            kpis,
            "KPI-CONV-03",
            "convergence",
            "Gate mapping completeness",
            score,
            "Deliverables map to valid timeline checkpoints.",
            [{"type": "deliverable", "id": str(i)} for i in invalid],
            ["checkpoint_id must exist in timeline_events IDs."],
            {
                "instrumented": True,
                "with_checkpoint": len(with_checkpoint),
                "invalid_checkpoint_mappings": invalid,
                "total_deliverables": len(deliverables),
            },
        )

    # KPI-CONV-04: definition of done completeness
    with_dod = [d for d in deliverables if isinstance(d.get("definition_of_done"), list)]
    placeholders = {"tbd", "later", "todo", "placeholder"}
    if not with_dod:
        add_kpi(
            kpis,
            "KPI-CONV-04",
            "convergence",
            "Definition-of-done completeness",
            70,
            "Deliverables include clear definition-of-done criteria.",
            [],
            ["If definition_of_done is absent, report yellow as not yet instrumented."],
            {"instrumented": False, "complete": 0, "total_deliverables": len(deliverables)},
            forced_status="yellow",
        )
    else:
        incomplete = []
        for d in with_dod:
            dod = [str(item).strip() for item in d.get("definition_of_done", []) if str(item).strip()]
            has_placeholder = any(item.lower() in placeholders for item in dod)
            if len(dod) < 2 or has_placeholder:
                incomplete.append({"id": d.get("id"), "dod_count": len(dod), "has_placeholder": has_placeholder})
        score = max(0, int((1 - len(incomplete) / len(with_dod)) * 100))
        add_kpi(
            kpis,
            "KPI-CONV-04",
            "convergence",
            "Definition-of-done completeness",
            score,
            "Deliverables include clear definition-of-done criteria.",
            [{"type": "deliverable", "id": str(item["id"])} for item in incomplete],
            ["Each deliverable should have >=2 definition_of_done bullets with no placeholders."],
            {"instrumented": True, "incomplete": incomplete, "checked": len(with_dod)},
        )

    # KPI-CONV-05/06 placeholders or coverage
    def coverage_kpi(field: str, kpi_id: str, name: str) -> None:
        with_field = [d for d in deliverables if isinstance(d.get(field), list) and d.get(field)]
        if not any(field in d for d in deliverables):
            add_kpi(
                kpis,
                kpi_id,
                "convergence",
                name,
                70,
                f"Coverage of {field} across deliverables.",
                [],
                [f"If {field} is absent from schema usage, report yellow not yet instrumented."],
                {"instrumented": False, "coverage_pct": 0, "notes": "not yet instrumented"},
                forced_status="yellow",
            )
            return
        coverage_pct = int((len(with_field) / max(1, len(deliverables))) * 100)
        add_kpi(
            kpis,
            kpi_id,
            "convergence",
            name,
            coverage_pct,
            f"Coverage of {field} across deliverables.",
            [{"type": "deliverable", "id": str(d.get("id"))} for d in with_field],
            [f"Coverage is deliverables with non-empty {field} / total deliverables."],
            {"instrumented": True, "coverage_pct": coverage_pct, "with_field": len(with_field), "total": len(deliverables)},
        )

    coverage_kpi("principle_refs", "KPI-CONV-05", "Principle linkage readiness")
    coverage_kpi("risk_refs", "KPI-CONV-06", "Risk register linkage readiness")

    # KPI-CONV-07: freshness
    freshness_threshold = now - timedelta(days=FRESHNESS_DAYS)
    sor_files = [SOR_DIR / "workstreams.yml", SOR_DIR / "timeline.yml", SOR_DIR / "deliverables.yml"]
    stale_sor = [p.name for p in sor_files if datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc) < freshness_threshold]

    changelog_date = first_date_in_changelog(REPO_ROOT / "CHANGELOG_PUBLIC.md")
    changelog_stale = changelog_date is None or changelog_date < freshness_threshold

    score = 100
    if stale_sor:
        score -= min(60, len(stale_sor) * 20)
    if changelog_stale:
        score -= 30
    score = max(0, score)

    add_kpi(
        kpis,
        "KPI-CONV-07",
        "convergence",
        "Freshness",
        score,
        "SoR and public changelog are updated within freshness threshold.",
        [{"type": "file", "id": f} for f in stale_sor],
        [f"SoR files and changelog should be updated within {FRESHNESS_DAYS} days."],
        {
            "threshold_days": FRESHNESS_DAYS,
            "stale_sor_files": stale_sor,
            "changelog_stale": changelog_stale,
            "catalog_generated_at": file_catalog.get("meta", {}).get("generated_at"),
        },
    )

    # KPI-CONV-08: public artifact availability
    missing_artifacts = []
    for d in deliverables:
        public_url = d.get("public_url")
        committee_only = d.get("committee_only")
        empty_link = isinstance(public_url, str) and not public_url.strip()
        if empty_link and committee_only is None:
            missing_artifacts.append({"id": d.get("id"), "reason": "empty_public_url_without_visibility"})
            continue
        if not public_url and committee_only is not True:
            missing_artifacts.append({"id": d.get("id"), "reason": "missing_public_url_or_committee_only"})

    score = max(0, int((1 - len(missing_artifacts) / max(1, len(deliverables))) * 100))
    add_kpi(
        kpis,
        "KPI-CONV-08",
        "convergence",
        "Public artifact availability",
        score,
        "Deliverables should have public_url or be explicitly committee_only.",
        [{"type": "deliverable", "id": str(item["id"])} for item in missing_artifacts],
        ["A deliverable is compliant when public_url exists or committee_only=true."],
        {"non_compliant": missing_artifacts, "total_deliverables": len(deliverables)},
    )

    status_counts = {"green": 0, "yellow": 0, "red": 0}
    for k in kpis:
        status_counts[k["status"]] += 1

    overall_status = "green"
    if status_counts["red"] > 0:
        overall_status = "red"
    elif status_counts["yellow"] > 0:
        overall_status = "yellow"

    return {
        "meta": {
            "generated_at": now.isoformat().replace("+00:00", "Z"),
            "timezone": TIMEZONE_NAME,
            "schema_version": "0.1",
        },
        "summary": {
            "overall_status": overall_status,
            "kpi_counts": status_counts,
        },
        "kpis": kpis,
    }


def main() -> None:
    result = build_kpis()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, ensure_ascii=False)
    print(f"📈 KPI report written to {OUTPUT_PATH}")
    print(f"🧮 Generated {len(result['kpis'])} KPIs")


if __name__ == "__main__":
    main()
