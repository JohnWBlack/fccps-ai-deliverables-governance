#!/usr/bin/env python3
"""Render governance registry markdown docs from SoR YAML sources."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SOR_DIR = REPO_ROOT / "sor"
DOCS_DIR = REPO_ROOT / "governance_docs"

WORKSTREAMS_PATH = SOR_DIR / "workstreams.yml"
DELIVERABLES_PATH = SOR_DIR / "deliverables.yml"
TIMELINE_PATH = SOR_DIR / "timeline.yml"

WORKSTREAMS_DOC_PATH = DOCS_DIR / "FCCPS_AIAC_Workstreams_Registry.md"
DELIVERABLES_DOC_PATH = DOCS_DIR / "FCCPS_AIAC_Deliverables_Index.md"
TIMELINE_DOC_PATH = DOCS_DIR / "FCCPS_AIAC_Master_Timeline_Workstream_Aligned.md"


def today_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def write_text_if_changed(path: Path, text: str) -> bool:
    rendered = text if text.endswith("\n") else text + "\n"
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    if current == rendered:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")
    return True


def md_escape(value: Any) -> str:
    text = str(value) if value is not None else ""
    return text.replace("|", "\\|").replace("\n", " ").strip()


def checkpoint_lookup(timeline_events: list[dict[str, Any]]) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for event in timeline_events:
        if not isinstance(event, dict):
            continue
        event_id = str(event.get("id") or "")
        title = str(event.get("title") or "")
        date = str(event.get("date") or "")
        if event_id:
            if title and date:
                lookup[event_id] = f"{title} ({date})"
            elif title:
                lookup[event_id] = title
            else:
                lookup[event_id] = event_id
    return lookup


def build_workstreams_doc(workstreams: list[dict[str, Any]], deliverables: list[dict[str, Any]]) -> str:
    active_by_ws: dict[str, list[dict[str, Any]]] = {}
    for item in deliverables:
        if not isinstance(item, dict):
            continue
        ws_id = str(item.get("workstream_id") or "")
        if not ws_id:
            continue
        active_by_ws.setdefault(ws_id, []).append(item)

    lines: list[str] = [
        "# FCCPS AI Advisory Committee — Workstreams Registry (System of Record)",
        f"**Version:** auto-generated  ",
        f"**Last updated:** {today_iso()}  ",
        "**Purpose:** Canonical list of workstreams and current delivery signal from SoR YAML.",
        "",
        "## Workstreams at a glance",
        "| Workstream ID | Workstream | Lead | Co-lead | Status | Evidence Sources | Next deliverable (ID) |",
        "|---|---|---|---|---|---:|---|",
    ]

    for ws in sorted(workstreams, key=lambda item: str(item.get("id") or "")):
        ws_id = str(ws.get("id") or "")
        linked = sorted(
            active_by_ws.get(ws_id, []),
            key=lambda d: (
                str(d.get("status") or "") != "in_progress",
                str(d.get("due_date") or ""),
                str(d.get("id") or ""),
            ),
        )
        next_deliverable = ""
        if linked:
            target = linked[0]
            next_deliverable = f"{md_escape(target.get('title') or '')} ({md_escape(target.get('id') or '')})"

        lines.append(
            "| "
            + " | ".join(
                [
                    md_escape(ws_id),
                    md_escape(ws.get("name") or ""),
                    md_escape(ws.get("lead") or ""),
                    md_escape(ws.get("co_lead") or ""),
                    md_escape(ws.get("status") or ""),
                    md_escape(ws.get("evidence_sources_count") or 0),
                    next_deliverable,
                ]
            )
            + " |"
        )

    return "\n".join(lines) + "\n"


def build_deliverables_doc(deliverables: list[dict[str, Any]], checkpoint_by_id: dict[str, str]) -> str:
    lines: list[str] = [
        "# FCCPS AI Advisory Committee — Deliverables Index",
        "",
        f"**Version:** auto-generated  ",
        f"**Last updated:** {today_iso()}  ",
        "**Purpose:** SoR-backed deliverables index with evidence and checkpoint alignment.",
        "",
        "## Deliverables table",
        "",
        "| Due date | ID | Deliverable | Owner | Workstream | Checkpoint | Depends on | Status | Evidence Sources |",
        "|---|---|---|---|---|---|---|---|---:|",
    ]

    sorted_deliverables = sorted(
        (d for d in deliverables if isinstance(d, dict)),
        key=lambda d: (str(d.get("due_date") or ""), str(d.get("id") or "")),
    )
    for d in sorted_deliverables:
        checkpoint_id = str(d.get("checkpoint_id") or "")
        checkpoint_label = checkpoint_by_id.get(checkpoint_id, checkpoint_id)
        depends = d.get("depends_on") or []
        depends_text = "; ".join(str(item) for item in depends if item) if isinstance(depends, list) else ""
        owner = d.get("owner") if isinstance(d.get("owner"), dict) else {}
        owner_text = str(owner.get("name") or "")

        lines.append(
            "| "
            + " | ".join(
                [
                    md_escape(d.get("due_date") or ""),
                    md_escape(d.get("id") or ""),
                    md_escape(d.get("title") or ""),
                    md_escape(owner_text),
                    md_escape(d.get("workstream_id") or ""),
                    md_escape(checkpoint_label),
                    md_escape(depends_text),
                    md_escape(d.get("status") or ""),
                    md_escape(d.get("supporting_evidence_count") or 0),
                ]
            )
            + " |"
        )

    return "\n".join(lines) + "\n"


def build_timeline_doc(timeline_events: list[dict[str, Any]]) -> str:
    lines: list[str] = [
        "# FCCPS AI Advisory Committee — Master Timeline (Workstream-aligned)",
        "",
        f"**Version:** auto-generated  ",
        f"**Last updated:** {today_iso()}  ",
        "**Purpose:** SoR-backed timeline of meetings/milestones with evidence progress.",
        "",
        "## Timeline",
        "",
        "| Date | Event ID | Title | Type | Status | Workstream | Evidence Progress |",
        "|---|---|---|---|---|---|---:|",
    ]

    sorted_events = sorted(
        (e for e in timeline_events if isinstance(e, dict)),
        key=lambda e: (str(e.get("date") or ""), str(e.get("id") or "")),
    )
    for e in sorted_events:
        progress_ratio = float(e.get("evidence_progress_ratio") or 0.0)
        lines.append(
            "| "
            + " | ".join(
                [
                    md_escape(e.get("date") or ""),
                    md_escape(e.get("id") or ""),
                    md_escape(e.get("title") or ""),
                    md_escape(e.get("type") or ""),
                    md_escape(e.get("status") or ""),
                    md_escape(e.get("workstream_id") or ""),
                    md_escape(f"{progress_ratio:.2f}"),
                ]
            )
            + " |"
        )

    return "\n".join(lines) + "\n"


def main() -> None:
    required = [WORKSTREAMS_PATH, DELIVERABLES_PATH, TIMELINE_PATH]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise SystemExit("Missing SoR source file(s):\n- " + "\n- ".join(missing))

    workstreams_doc = load_yaml(WORKSTREAMS_PATH)
    deliverables_doc = load_yaml(DELIVERABLES_PATH)
    timeline_doc = load_yaml(TIMELINE_PATH)

    workstreams = workstreams_doc.get("workstreams", []) if isinstance(workstreams_doc, dict) else []
    deliverables = deliverables_doc.get("deliverables", []) if isinstance(deliverables_doc, dict) else []
    timeline_events = timeline_doc.get("timeline_events", []) if isinstance(timeline_doc, dict) else []

    if not isinstance(workstreams, list) or not isinstance(deliverables, list) or not isinstance(timeline_events, list):
        raise SystemExit("Invalid SoR schema: expected workstreams/deliverables/timeline_events lists")

    checkpoint_by_id = checkpoint_lookup(timeline_events)

    changed_files: list[str] = []
    if write_text_if_changed(WORKSTREAMS_DOC_PATH, build_workstreams_doc(workstreams, deliverables)):
        changed_files.append(WORKSTREAMS_DOC_PATH.relative_to(REPO_ROOT).as_posix())
    if write_text_if_changed(DELIVERABLES_DOC_PATH, build_deliverables_doc(deliverables, checkpoint_by_id)):
        changed_files.append(DELIVERABLES_DOC_PATH.relative_to(REPO_ROOT).as_posix())
    if write_text_if_changed(TIMELINE_DOC_PATH, build_timeline_doc(timeline_events)):
        changed_files.append(TIMELINE_DOC_PATH.relative_to(REPO_ROOT).as_posix())

    print("🧾 Registry docs render completed")
    print("📚 Updated docs: " + (", ".join(changed_files) if changed_files else "none"))


if __name__ == "__main__":
    main()
